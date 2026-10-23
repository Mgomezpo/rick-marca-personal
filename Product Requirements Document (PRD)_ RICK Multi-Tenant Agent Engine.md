# **Product Requirements Document (PRD): RICK Multi-Tenant Agent Engine (Hermes-Inspired)**

> [!NOTE]
> **Estado de Implementación:** Completamente implementado y en producción (v1.0.1).  
> Los requerimientos descritos en este PRD fueron materializados y ampliados en el motor de grafos [`src/graph/engine.py`](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/src/graph/engine.py).  
> Para consultar la especificación técnica vigente, diagramas de flujo y registros de decisiones, revise:
> - [**ARQUITECTURA_RICK_MULTITENANT.md**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/ARQUITECTURA_RICK_MULTITENANT.md)
> - [**README.md**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/README.md)
> - [**docs/decisions/**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/README.md)

## **1\. Executive Summary & Architecture Blueprint**

This Product Requirements Document (PRD) specifies the transformation of the local mono-user RICK system into a production-grade, **Multi-Tenant Stateless Agent Engine** deployed on FastAPI (Railway/Cloud Run) with Supabase PostgreSQL, serving users via Meta WhatsApp Cloud API and Web endpoints. Drawing architecture patterns directly from [Nous Research Hermes Agent](https://github.com/nousresearch/hermes-agent), RICK combines a dual-tier memory system, ReAct tool execution loops, dynamic context window compression, and strict voice/tone decoupling.

### **Core Architectural Principles:**

1. **Immediate ACK Pattern:** Webhook endpoints acknowledge incoming WhatsApp messages (HTTP 200 OK) in \< 200ms, offloading processing to asynchronous background tasks.  
2. **Strict Multi-Tenant Isolation:** All state, memories, drafts, and telemetry are strictly segregated by creator\_id using Row-Level Security (RLS) in PostgreSQL.  
3. **Hermes-Style Memory Architecture:** Separates high-frequency active scratchpad memory (curated identity & state) from long-term vector retrieval memory (RAG on past scripts and learnings).  
4. **Decoupled Reasoning & Generation:** Lightweight models handle intent routing and tool calling, while high-capacity models generate final Anti-Slop content.  
5. **Phantom Cost & Token Telemetry:** Mandatory accounting of input/output tokens, latencies, and financial costs per turn and tenant.

## **2\. Key Architectural Takeaways from Hermes Agent**

Adapting the core innovations of [Nous Research Hermes Agent](https://github.com/nousresearch/hermes-agent) to a multi-tenant web application unlocks superior agentic memory, modular tool usage, and context survival:

### **A. Two-Tier Memory System in Postgres**

* **Curated Active Memory (Tier 1):** A persistent, curated key-value / structured store in creators.tone\_profile and active state tables. Contains always-loaded creator rules, forbidden words, target audience, and active project state. The agent can explicitly inspect and mutate this tier via memory management tools.  
* **Long-Term Vector Memory (Tier 2):** Semantically indexed storage in creator\_memories using pgvector. Stores historical feedback, past scripts, user preferences, and performance learnings, queried dynamically via cosine similarity.

### **B. Modular Agentic Skills & Toolset Registry**

Following Hermes Agent's modular skill pattern, tools are defined in src/engine/tools/ as isolated, decorated functions with strict Pydantic schemas. The router uses tool calling to execute database mutations, semantic retrieval, or external API calls before generating user responses.

### **C. Dynamic Context Compression & Window Protection**

To prevent context overflow during long chat threads, RICK adopts Hermes Agent's context truncation and summarization logic. Older chat turns are compressed into a compact conversation summary, while preserving the system prompt, active memory block, and recent message history.

### **D. Decoupled Pipeline (ReAct Tool Execution vs Author Tone Generation)**

To prevent tool-calling syntax and JSON output from corrupting author tone, RICK separates the execution lifecycle into two distinct roles:

* **Orchestrator Agent (Tool Engine):** Fast, function-calling model (e.g., Gemini 2.5 Flash / Claude 3.5 Haiku) that decides actions, updates memory, and fetches context.  
* **Writer Agent (Voice & Tone Engine):** High-capacity model (e.g., Gemini 2.5 Pro / Claude 3.5 Sonnet) operating strictly without tool-calling abilities, focusing 100% on craft, hooks, retention, and Anti-Slop guidelines loaded from brain/01\_philosophy/.

## **3\. Proposed Directory Structure for rick-marca-personal**

```
rick-marca-personal/
├── .antigravity/                   # Workflow specifications & Antigravity directives
├── brain/                          # Read-Only Knowledge Base & Templates
│   ├── 01_philosophy/              # Anti-slop rules, immutable author philosophy
│   └── 03_studio/                  # Frameworks, hook templates, retention guides
├── src/
│   ├── api/
│   │   ├── routers/
│   │   │   └── webhook.py          # WhatsApp/Web GET verification & POST ACK ingest
│   │   └── dependencies.py         # FastApi dependency injection for DB & services
│   ├── core/
│   │   ├── config.py               # Pydantic Settings & environment validation
│   │   └── telemetry.py            # Token usage & phantom cost logging decorator
│   ├── db/
│   │   ├── supabase.py             # Supabase PostgreSQL client wrapper
│   │   └── migrations/             # SQL schema & DDL migrations
│   │       └── 001_initial_schema.sql
│   ├── engine/
│   │   ├── context_builder.py      # Assembles System Prompts (Brain + Tenant + Memories)
│   │   ├── context_compressor.py   # Hermes-inspired chat history window truncation
│   │   ├── orchestrator.py         # Router & ReAct tool loop agent
│   │   ├── writer.py               # Pure-tone script generation agent
│   │   └── tools/                  # Modular Toolset Registry (Hermes Skills)
│   │       ├── base.py             # Tool base class & decorator
│   │       ├── memory_tools.py     # Active memory curation tools
│   │       ├── script_tools.py     # Script CRUD & state management
│   │       └── vector_tools.py     # RAG search across long-term memory
│   └── services/
│       ├── whatsapp.py             # Meta Cloud API HTTP client
│       └── memory_service.py       # pgvector embedding calculation & hybrid search
├── Dockerfile
├── requirements.txt
└── README.md
```

## **4\. Database Schema (Supabase PostgreSQL \+ pgvector)**

File location: src/db/migrations/001\_initial\_schema.sql

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Creators / Multi-Tenant Profiles
CREATE TABLE creators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    niche TEXT,
    tone_profile JSONB DEFAULT '{
        "vibe": "punchy, direct, anti-slop",
        "target_audience": "general",
        "prohibited_words": ["en este mundo cambiante", "descubre el secreto", "desata tu potencial"]
    }'::jsonb,
    active_memory JSONB DEFAULT '{}'::jsonb, -- Hermes Tier-1 Active Memory Scratchpad
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Tier-2 Long-Term Vector Memory
CREATE TABLE creator_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID REFERENCES creators(id) ON DELETE CASCADE NOT NULL,
    memory_type TEXT NOT NULL CHECK (memory_type IN ('learning', 'identity', 'feedback', 'pattern')),
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_creator_memories_embedding ON creator_memories USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_creator_memories_creator_id ON creator_memories(creator_id);

-- 3. Scripts / Output Artifacts
CREATE TABLE scripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID REFERENCES creators(id) ON DELETE CASCADE NOT NULL,
    title TEXT,
    hook TEXT,
    body TEXT,
    framework_used TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'refined', 'approved', 'published')),
    raw_input TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scripts_creator_id ON scripts(creator_id);

-- 4. Chat History & Conversation Turns
CREATE TABLE chat_turns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID REFERENCES creators(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_turns_creator ON chat_turns(creator_id, created_at DESC);

-- 5. Agent Telemetry & Phantom Cost Accounting
CREATE TABLE agent_telemetry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID REFERENCES creators(id) ON DELETE SET NULL,
    phase TEXT NOT NULL, -- 'routing', 'tool_calling', 'writing', 'compression'
    model_name TEXT NOT NULL,
    prompt_tokens INT NOT NULL,
    completion_tokens INT NOT NULL,
    latency_ms INT NOT NULL,
    cost_usd NUMERIC(10, 6) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_telemetry_creator ON agent_telemetry(creator_id);
```

## **5\. Step-by-Step Execution Pipeline**

### **Fase A: Webhook Ingest & ACK Pattern (\< 200ms)**

* **GET /webhook:** Meta verification challenge matching hub.verify\_token.  
* **POST /webhook:** Parse WhatsApp payload, extract sender phone and message content, queue background task via FastAPI BackgroundTasks, and return {"status": "ok"} immediately.

### **Fase B: Tenant Context Ingestion & Window Compression**

* Fetch tenant record from creators using sender phone number. Initialize new tenant if absent.  
* Load static Anti-Slop philosophy from brain/01\_philosophy/ and studio frameworks from brain/03\_studio/.  
* Run context\_compressor.py on past chat turns in chat\_turns to ensure system prompt and active memory window fit within LLM limits.

### **Fase C: ReAct Orchestration & Tool Execution (Hermes Style)**

The Orchestrator agent evaluates user intent using lightweight models (e.g., Gemini 2.5 Flash / Haiku). It executes ReAct loops against available skills in src/engine/tools/:

* update\_active\_memory: Mutate Tier-1 curated scratchpad (e.g., active topic, current mood).  
* search\_vector\_memory: Perform similarity search over Tier-2 vector embeddings for past relevant feedback or scripts.  
* save\_script\_draft: Create or update script record in PostgreSQL.

### **Fase D: Tone & Author Script Generation**

Once tools have gathered required context and updated state, the payload is forwarded to writer.py running high-capability models (e.g., Gemini 2.5 Pro / Sonnet). The writer synthesizes the final message strictly enforcing:

* First 3-second hook structure.  
* Retention rhythm and bullet pacing.  
* Zero usage of prohibited words defined in creators.tone\_profile.

### **Fase E: Telemetry & Response Dispatch**

* **Telemetry Logging:** Compute cost based on model token rates and persist record into agent\_telemetry.  
* **WhatsApp Dispatch:** Send finalized message via Meta Cloud API HTTP POST to https\://graph.facebook.com/v20.0/{phone\_number\_id}/messages.

## **6\. Antigravity Execution Directive**

To scaffold and build this system using Antigravity, execute the following prompt against the repository root:

```
Act as Staff AI Engineer. Scaffold and implement the multi-tenant RICK engine on 'rick-marca-personal' following the Hermes Agent architecture patterns:

1. Database Schema: Create src/db/migrations/001_initial_schema.sql including creators, creator_memories (pgvector), scripts, chat_turns, and agent_telemetry.
2. Core & Config: Implement Pydantic settings in src/core/config.py and the token/cost telemetry logger in src/core/telemetry.py.
3. FastApi Webhook: Build src/api/routers/webhook.py with Meta verification (GET) and immediate ACK <200ms background execution (POST).
4. Context & Memory Engine: Build src/engine/context_builder.py (integrating brain/01_philosophy/ and brain/03_studio/) and src/engine/context_compressor.py for chat window protection.
5. Hermes Skill Registry: Create modular tools in src/engine/tools/ for active memory mutation, script storage, and pgvector RAG search.
6. Orchestrator & Writer Decoupling: Implement the ReAct tool calling router in src/engine/orchestrator.py and pure Anti-Slop author script generation in src/engine/writer.py.
7. Services: Implement src/services/whatsapp.py for Meta Cloud API integration.
```

