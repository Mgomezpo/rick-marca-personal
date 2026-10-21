import logging
import json
from typing import Any, Dict, List, Optional
from src.db.supabase import DatabaseService
from src.engine.vfs import VirtualFileSystem

logger = logging.getLogger("rick.tools")

OPENAI_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "investigar_huella_creador",
            "description": "Investiga la huella digital del creador en Instagram y la web a partir de su handle o link. Analiza su contenido, estilo y proyectos para conocer su contexto real y guardarlo en su perfil.",
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "Usuario o handle de Instagram (ej: 'usuario_creador' o '@usuario')"
                    }
                },
                "required": ["handle"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "completar_onboarding_creador",
            "description": "Finaliza el onboarding socrático del creador tras calibrar sus 5 dimensiones (nicho, obsesión, enemigo común, anécdota/lore, voz y audiencia). Guarda su perfil definitivo en Supabase, marca su onboarding_status como 'completed' en la base de datos y pasa el estudio a modo producción.",
            "parameters": {
                "type": "object",
                "properties": {
                    "niche": {
                        "type": "string",
                        "description": "Nicho o industria principal del creador"
                    },
                    "obsession": {
                        "type": "string",
                        "description": "Obsesión central o tema recurrente del que hablaría horas sin parar"
                    },
                    "common_enemy": {
                        "type": "string",
                        "description": "Enemigo común o cliché de su industria que combate"
                    },
                    "origin_story": {
                        "type": "string",
                        "description": "Anécdota de trinchera o momento de quiebre donde definió su postura"
                    },
                    "voice_vibe": {
                        "type": "string",
                        "description": "Tono y cadencia natural de su voz"
                    },
                    "target_audience": {
                        "type": "string",
                        "description": "Audiencia espejo a quien le habla (ej: 'su versión de hace 2 años')"
                    }
                },
                "required": ["niche", "obsession", "common_enemy", "voice_vibe"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_identidad_creador",
            "description": "Guarda o actualiza la identidad, nicho, obsesión y voz del creador en su base de datos personal cuando se definen o descubren en la conversación.",
            "parameters": {
                "type": "object",
                "properties": {
                    "niche": {
                        "type": "string",
                        "description": "Nicho o industria principal del creador (ej: 'automatización con IA y agentes para negocios')"
                    },
                    "obsession": {
                        "type": "string",
                        "description": "Obsesión central o tema recurrente del creador (ej: 'darle los domingos de vuelta a mi papá con sistemas')"
                    },
                    "common_enemy": {
                        "type": "string",
                        "description": "Enemigo común o creencia errónea que combate (ej: 'el humo de que la IA te hace rico sin trabajar')"
                    },
                    "voice_vibe": {
                        "type": "string",
                        "description": "Estilo o tono de voz natural (ej: 'sobrio, directo, de trinchera, sin poses corporativas')"
                    },
                    "instagram_handle": {
                        "type": "string",
                        "description": "Handle o usuario de Instagram si fue compartido (ej: 'usuario_creador')"
                    }
                },
                "required": ["niche", "obsession", "common_enemy", "voice_vibe"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_guion_terminado",
            "description": "Guarda un guion finalizado en el inventario de piezas del creador en Supabase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {
                        "type": "string",
                        "description": "Título o concepto del guion"
                    },
                    "gancho": {
                        "type": "string",
                        "description": "Gancho verbal y visual de los primeros 3 segundos"
                    },
                    "cuerpo_en_actos": {
                        "type": "string",
                        "description": "Guion completo con dirección visual, tono y beats"
                    },
                    "framework": {
                        "type": "string",
                        "description": "Framework narrativo utilizado (ej: 'quiebre_cognitivo', 'historia_viva')"
                    }
                },
                "required": ["titulo", "gancho", "cuerpo_en_actos"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_memoria_activa",
            "description": "Registra el tema o proyecto activo y notas de scratchpad en la memoria del creador.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tema_activo": {
                        "type": "string",
                        "description": "Tema, serie o idea que se está trabajando activamente en esta sesión"
                    },
                    "nota_scratchpad": {
                        "type": "string",
                        "description": "Nota clave o aprendizaje para recordar en los siguientes turnos"
                    }
                },
                "required": ["tema_activo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "leer_documento_cerebro",
            "description": "Lee el contenido de un archivo markdown en el cerebro (filosofía de Rubin, frameworks de estudio o perfil del creador).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta": {
                        "type": "string",
                        "description": "Ruta relativa en el cerebro (ej: 'filosofia/canon/01_the_sun_does_not_stop.md', 'studio/frameworks/quiebre_cognitivo.md', 'creator/identity/voice_dna.md')"
                    }
                },
                "required": ["ruta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_en_cerebro",
            "description": "Busca conceptos, capítulos del canon de Rubin o frameworks narrativos por palabras clave.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Palabras clave a buscar en el cerebro"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listar_directorio_cerebro",
            "description": "Lista las carpetas o archivos disponibles en una sección del cerebro virtual.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta": {
                        "type": "string",
                        "description": "Directorio a listar (ej: 'filosofia', 'studio/frameworks', 'skills', 'creator', 'produccion')"
                    }
                },
                "required": ["ruta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_piezas_creador",
            "description": "Consulta las piezas y guiones ya creados previamente en el estudio y guardados en el inventario de Supabase (NO consulta posts de Instagram en vivo).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limite": {
                        "type": "integer",
                        "description": "Cantidad máxima de piezas a consultar (por defecto 10)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_perfil_creador",
            "description": "Consulta la información de marca, handle de Instagram, nicho, audiencia, proyectos y diagnóstico de su feed.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redactar_guion_formato_oficial",
            "description": "Redacta un guion oficial estructurado por pasos con intención, cámara, objetivo de transformación y copy para publicar. Soporta frameworks: 'auto' (selección heurística con el Árbol de Decisión psicológica de Rubin), 'quiebre_cognitivo', 'caso_real', 'historia_leccion', 'pas', 'bab'. Guarda la pieza automáticamente en Supabase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "brief": {
                        "type": "string",
                        "description": "Idea, anécdota de trinchera o dolor a desarrollar en el guion."
                    },
                    "framework": {
                        "type": "string",
                        "description": "Framework narrativo de storytelling ('auto', 'quiebre_cognitivo', 'caso_real', 'historia_leccion', 'pas', 'bab')",
                        "default": "auto"
                    },
                    "formato": {
                        "type": "string",
                        "description": "Formato de distribución ('reel', 'tiktok', 'short')",
                        "default": "reel"
                    }
                },
                "required": ["brief"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_posts_instagram",
            "description": "Consulta los posts y reels recientes de Instagram del creador o analiza su huella digital y temas probados de trinchera.",
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "Handle de Instagram (ej: 'usuario_creador')"
                    }
                }
            }
        }
    }
]

def execute_tool_call(
    tool_name: str,
    args: Dict[str, Any],
    user_id: str,
    db: DatabaseService,
    vfs: VirtualFileSystem,
    thread_id: Optional[str] = None
) -> str:
    """Ejecuta una herramienta solicitada por el modelo y retorna el resultado en string."""
    logger.info(f"🛠️ [Tool Exec] {tool_name} para usuario {user_id} con args: {list(args.keys())}")
    try:
        if tool_name == "investigar_huella_creador":
            handle_raw = args.get("handle", "")
            from src.services.instagram import InstagramService
            ig_service = InstagramService()
            clean_h = ig_service.clean_handle(handle_raw) or handle_raw.strip().lstrip("@")
            footprint = ig_service.research_creator_footprint(clean_h)
            summary = footprint.get("summary", f"Cuenta @{clean_h} identificada.")
            db.upsert_user_profile(user_id, {
                "analytics_username": clean_h,
                "backstory": summary[:500]
            })
            return json.dumps({
                "status": "success",
                "handle": clean_h,
                "resumen_huella": summary
            }, ensure_ascii=False)

        elif tool_name == "completar_onboarding_creador":
            niche = args.get("niche", "")
            obsession = args.get("obsession", "")
            common_enemy = args.get("common_enemy", "")
            origin_story = args.get("origin_story", "")
            voice_vibe = args.get("voice_vibe", "")
            target_audience = args.get("target_audience", "")

            # Guardar brand assets (voz, lore, cliente_ideal)
            db.upsert_brand_asset(
                user_id=user_id,
                slot_type="voz",
                content={
                    "vibe": voice_vibe,
                    "obsession": obsession,
                    "common_enemy": common_enemy,
                    "niche": niche
                },
                summary=f"Voz: {voice_vibe} | Nicho: {niche}",
                status="ready"
            )
            if origin_story:
                db.upsert_brand_asset(
                    user_id=user_id,
                    slot_type="lore",
                    content={"origin_story": origin_story, "key_moment": origin_story},
                    summary=f"Historia de origen: {origin_story[:100]}",
                    status="ready"
                )
            if target_audience:
                db.upsert_brand_asset(
                    user_id=user_id,
                    slot_type="cliente_ideal",
                    content={"target_audience": target_audience},
                    summary=f"Audiencia: {target_audience}",
                    status="ready"
                )

            # Binario en BD: onboarding_status = 'completed'
            db.upsert_user_profile(user_id, {
                "main_niche": niche,
                "passion": obsession,
                "unique_angle": common_enemy,
                "backstory": origin_story[:500] if origin_story else "",
                "onboarding_status": "completed"
            })

            # Actualizar memoria activa
            st = db.get_active_memory(user_id).get("state") or {}
            st["onboarding_completed"] = True
            db.update_active_memory(user_id, st, summary=f"Onboarding completado. Nicho: {niche}")

            return json.dumps({
                "status": "success",
                "message": "Onboarding completado exitosamente. Creador dado de alta en el estudio.",
                "profile": {
                    "niche": niche,
                    "obsession": obsession,
                    "common_enemy": common_enemy,
                    "voice_vibe": voice_vibe
                }
            }, ensure_ascii=False)

        elif tool_name == "guardar_identidad_creador":
            niche = args.get("niche", "")
            obsession = args.get("obsession", "")
            common_enemy = args.get("common_enemy", "")
            voice_vibe = args.get("voice_vibe", "")
            handle = args.get("instagram_handle", "")

            db.upsert_brand_asset(
                user_id=user_id,
                slot_type="voz",
                content={
                    "vibe": voice_vibe,
                    "obsession": obsession,
                    "common_enemy": common_enemy,
                    "niche": niche
                },
                summary=f"Voz: {voice_vibe} | Obsesión: {obsession}",
                status="ready"
            )
            profile_fields = {
                "main_niche": niche,
                "passion": obsession,
                "unique_angle": common_enemy,
                "onboarding_status": "completed"
            }
            if handle:
                clean_h = handle.strip().lstrip("@")
                profile_fields["analytics_username"] = clean_h

            db.upsert_user_profile(
                user_id=user_id,
                fields=profile_fields
            )
            return json.dumps({
                "status": "success",
                "message": "Identidad del creador guardada exitosamente en Supabase.",
                "profile": {"niche": niche, "obsession": obsession, "common_enemy": common_enemy, "handle": handle}
            }, ensure_ascii=False)

        elif tool_name == "guardar_guion_terminado":
            titulo = args.get("titulo", "Guion sin título")
            gancho = args.get("gancho", "")
            cuerpo = args.get("cuerpo_en_actos", "")
            framework = args.get("framework", "quiebre_cognitivo")
            res = db.save_generated_script(
                user_id=user_id,
                title=titulo,
                hook=gancho,
                body=cuerpo,
                copy="",
                format="reel",
                framework=framework,
                thread_id=thread_id
            )
            return json.dumps({
                "status": "success",
                "message": "Guion guardado en el inventario de piezas.",
                "piece_id": res.get("id", "nuevo"),
                "title": titulo
            }, ensure_ascii=False)

        elif tool_name == "actualizar_memoria_activa":
            tema = args.get("tema_activo", "")
            nota = args.get("nota_scratchpad", "")
            st = db.get_active_memory(user_id).get("state") or {}
            st["active_topic"] = tema
            if nota:
                notes = st.get("scratchpad_notes", [])
                notes.append(nota)
                st["scratchpad_notes"] = notes[-5:]
            db.update_active_memory(user_id, st, summary=f"Tema activo: {tema}")
            return json.dumps({
                "status": "success",
                "message": "Memoria activa actualizada.",
                "active_topic": tema
            }, ensure_ascii=False)

        elif tool_name == "leer_documento_cerebro":
            ruta = args.get("ruta", "")
            content = vfs.read_file(ruta, user_id)
            return content if content else f"Archivo '{ruta}' no encontrado en el cerebro."

        elif tool_name == "buscar_en_cerebro":
            query = args.get("query", "")
            matches = vfs.search_brain(query, user_id)
            return matches if matches else "No se encontraron coincidencias para la búsqueda."

        elif tool_name == "listar_directorio_cerebro":
            ruta = args.get("ruta", "")
            items = vfs.list_dir(ruta, user_id)
            return json.dumps(items, ensure_ascii=False)

        elif tool_name == "consultar_piezas_creador":
            limite = args.get("limite", 10)
            scripts = db.get_user_scripts(user_id, limit=limite)
            if not scripts:
                return "No hay piezas registradas en el inventario del creador."
            resumen = []
            for s in scripts:
                resumen.append({
                    "id": s.get("id"),
                    "title": s.get("title"),
                    "status": s.get("status"),
                    "strategy_tag": s.get("strategy_tag"),
                    "script_excerpt": (s.get("script") or s.get("content") or "")[:400],
                    "created_at": s.get("created_at")
                })
            return json.dumps(resumen, ensure_ascii=False)

        elif tool_name == "consultar_perfil_creador":
            profile = db.get_user_profile(user_id) or {}
            brand_assets = db.get_brand_assets(user_id) or {}
            lore = brand_assets.get("lore", {}).get("content", {})
            voice = brand_assets.get("voz", {}).get("content", {})
            return json.dumps({
                "profile": profile,
                "lore_and_diagnostics": lore,
                "voice": voice
            }, ensure_ascii=False)

        elif tool_name == "redactar_guion_formato_oficial":
            brief = args.get("brief", "")
            framework = args.get("framework", "pas")
            formato = args.get("formato", "reel")
            from google import genai
            from src.core.config import config
            from src.core.telemetry import TelemetryTracker
            from src.engine.subagents.anti_slop_editor import AntiSlopEditor
            from src.engine.subagents.hook_writer import HookWriterSubagent
            from src.engine.subagents.guionista import GuionistaSubagent

            client = genai.Client(api_key=config.GEMINI_API_KEY)
            telemetry = TelemetryTracker(db.client)
            editor = AntiSlopEditor(client, telemetry)
            hook_writer = HookWriterSubagent(client, telemetry)
            guionista = GuionistaSubagent(client, db, telemetry, editor, hook_writer)

            voice_dna = vfs.read_file("creator/identity/voice_dna.md", user_id)
            res = guionista.redactar_guion(
                brief=brief,
                user_id=user_id,
                formato=formato,
                framework=framework,
                voice_context=voice_dna,
                thread_id=thread_id
            )
            return json.dumps(res, ensure_ascii=False)

        elif tool_name == "consultar_posts_instagram":
            handle = args.get("handle", "")
            profile = db.get_user_profile(user_id) or {}
            if not handle:
                handle = profile.get("analytics_username") or profile.get("instagram_handle") or ""
            if not handle:
                return json.dumps({
                    "status": "not_found",
                    "mensaje": "El creador no tiene un usuario de Instagram registrado en su perfil. Pídele su @handle o que te comparta su proyecto en una nota de voz."
                }, ensure_ascii=False)
            from src.services.instagram import InstagramService
            ig_service = InstagramService()
            footprint = ig_service.research_creator_footprint(handle)
            reels = footprint.get("reels", [])
            if reels:
                return json.dumps({
                    "status": "success",
                    "posts": reels[:5]
                }, ensure_ascii=False)
            
            # Degradación elegante: Si el scraping en vivo no trajo reels (ej. rate limit de Meta/Apify)
            cached_context = footprint.get("summary") or profile.get("backstory") or ""
            if cached_context:
                return json.dumps({
                    "status": "cached_context",
                    "handle": handle,
                    "mensaje": (
                        f"El feed en vivo de @{handle} no devolvió reels recientes en este instante debido a protección de la red social. "
                        f"DIRECTRIZ INQUEBRANTABLE PARA RICK: NO menciones scrapers, cuotas, APIs ni excusas técnicas de IA. "
                        f"Habla con total naturalidad y autoridad de Head of Content apoyándote en el contexto que ya conocemos del creador, "
                        f"o pregúntale directamente qué video, tema o anécdota quiere deconstruir hoy."
                    ),
                    "contexto_disponible": cached_context[:400]
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "status": "not_found",
                    "mensaje": (
                        f"No hay piezas recientes accesibles en vivo para @{handle}. "
                        f"DIRECTRIZ PARA RICK: NO des excusas técnicas. Propón trabajar sobre una anécdota o idea de contenido reciente."
                    )
                }, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Herramienta desconocida '{tool_name}'"})

    except Exception as e:
        logger.error(f"Error ejecutando herramienta {tool_name}: {e}")
        return json.dumps({"status": "error", "error": str(e)})
