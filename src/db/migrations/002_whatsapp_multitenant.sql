-- =====================================================================
-- 002_whatsapp_multitenant.sql  —  BORRADOR / NO APLICADO
-- Proyecto: IrealDemo (khoikdwablpqiapxkgqx)
--
-- Principios:
--   * 100% ADITIVO: no borra ni altera datos de IREAL (33 usuarios en vivo).
--   * Tenant = auth.users(id). NO se crea tabla `creators` paralela.
--   * Un usuario que llega por WhatsApp se crea con
--       auth.admin.createUser({ phone, phone_confirm: true })
--     y el trigger existente `on_auth_user_created_create_trial`
--     le crea su trial automáticamente.
--   * Escrituras: solo backend (service_role). Lectura: el propio usuario (RLS).
--   * Embeddings: 768d (gemini-embedding-001), igual que el resto de la BD.
-- =====================================================================

-- 1) Vínculo teléfono WhatsApp -> usuario (tenant)
create table if not exists public.whatsapp_identities (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id) on delete cascade,
  phone_e164   text not null unique,              -- '+573001234567'
  wa_id        text unique,                       -- id que entrega Meta
  display_name text,
  status       text not null default 'active'
               check (status in ('active','blocked','opted_out')),
  verified_at  timestamptz,
  last_seen_at timestamptz,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index if not exists idx_wa_identities_user on public.whatsapp_identities(user_id);

-- 2) Memoria activa Tier-1 (reemplaza memories/active_context.md + reality/current_focus.md)
create table if not exists public.rick_active_memory (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  state      jsonb not null default '{
    "active_topic": null,
    "active_skill": null,
    "inquiry_level": null,
    "inquiry_step": 0,
    "inquiry_answers": {},
    "current_series": null,
    "scratchpad_notes": []
  }'::jsonb,
  summary    text,                                -- resumen comprimido del historial
  updated_at timestamptz not null default now()
);

-- 3) Log de mensajes WhatsApp (idempotencia: Meta reintenta webhooks)
create table if not exists public.whatsapp_messages (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid references auth.users(id) on delete cascade,
  thread_id     uuid references public.rick_threads(id) on delete set null,
  wa_message_id text not null unique,
  direction     text not null check (direction in ('in','out')),
  msg_type      text not null default 'text',      -- text | audio | image | interactive
  body          text,
  media_url     text,
  status        text not null default 'received'
                check (status in ('received','processing','done','failed','sent','delivered','read')),
  error         text,
  created_at    timestamptz not null default now()
);
create index if not exists idx_wa_messages_user on public.whatsapp_messages(user_id, created_at desc);

-- 4) Telemetría de agentes y costo por turno
create table if not exists public.agent_telemetry (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid references auth.users(id) on delete set null,
  thread_id         uuid references public.rick_threads(id) on delete set null,
  channel           text not null default 'whatsapp',
  phase             text not null
                    check (phase in ('guardrail','routing','tool_calling','writing','humanizing','compression','embedding')),
  model_name        text not null,
  prompt_tokens     int not null default 0,
  completion_tokens int not null default 0,
  latency_ms        int not null default 0,
  cost_usd          numeric(10,6) not null default 0,
  metadata          jsonb not null default '{}'::jsonb,
  created_at        timestamptz not null default now()
);
create index if not exists idx_agent_telemetry_user on public.agent_telemetry(user_id, created_at desc);

-- 5) Permitir hilos de WhatsApp en rick_threads (uno por usuario)
alter table public.rick_threads drop constraint if exists rick_threads_kind_check;
alter table public.rick_threads add constraint rick_threads_kind_check
  check (kind in ('item','direct','interview','whatsapp'));
create unique index if not exists idx_rick_threads_whatsapp
  on public.rick_threads(user_id) where kind = 'whatsapp';

-- 6) updated_at triggers (función ya existente en la BD)
drop trigger if exists trg_wa_identities_updated_at on public.whatsapp_identities;
create trigger trg_wa_identities_updated_at before update on public.whatsapp_identities
  for each row execute function update_updated_at_column();
drop trigger if exists trg_rick_active_memory_updated_at on public.rick_active_memory;
create trigger trg_rick_active_memory_updated_at before update on public.rick_active_memory
  for each row execute function update_updated_at_column();

-- 7) RLS: el usuario solo lee lo suyo; escribe solo el backend (service_role bypassa RLS)
alter table public.whatsapp_identities enable row level security;
alter table public.rick_active_memory  enable row level security;
alter table public.whatsapp_messages   enable row level security;
alter table public.agent_telemetry     enable row level security;

drop policy if exists wa_identities_select_own on public.whatsapp_identities;
create policy wa_identities_select_own on public.whatsapp_identities
  for select using (auth.uid() = user_id);
drop policy if exists rick_active_memory_select_own on public.rick_active_memory;
create policy rick_active_memory_select_own on public.rick_active_memory
  for select using (auth.uid() = user_id);
drop policy if exists wa_messages_select_own on public.whatsapp_messages;
create policy wa_messages_select_own on public.whatsapp_messages
  for select using (auth.uid() = user_id);
-- agent_telemetry: sin policy de lectura -> solo service_role/admin.

-- 8) Limpieza de la migración fantasma (tablas nunca creadas).
--    DESCOMENTAR SOLO CON APROBACIÓN EXPLÍCITA:
-- delete from supabase_migrations.schema_migrations
--  where version = '20261010211631' and name = '001_initial_schema';
