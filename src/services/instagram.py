import logging
import httpx
from typing import Any, Dict, List, Optional
from src.core.config import config

logger = logging.getLogger("rick.service.instagram")

class InstagramService:
    def __init__(self, token: Optional[str] = None):
        self.token = token or config.APIFY_API_TOKEN

    def extract_handle(self, user_input: str) -> Optional[str]:
        """
        Extrae un handle de Instagram válido de cualquier texto o URL.
        Requiere explícitamente '@' o 'instagram.com/'. Ignora comandos con '/'.
        """
        import re
        text = user_input.strip()
        # Ignorar comandos de bot
        if text.startswith("/"):
            return None
        # 1. Si viene con URL
        if "instagram.com/" in text:
            m = re.search(r'instagram\.com/([a-zA-Z0-9._]{1,30})', text)
            if m:
                return m.group(1).strip(". ")
        # 2. Si viene con @ (ej: @miguel_gomezpo o 'me equivoqué, es @miguel_gomezpo')
        m = re.search(r'@\s*([a-zA-Z0-9._]{1,30})', text)
        if m:
            h = m.group(1).strip(". ")
            if len(h) >= 2 and h.lower() not in ["start", "reset", "help", "usuario", "handle"]:
                return h
        return None

    def clean_handle(self, user_input: str) -> str:
        """Extrae el handle limpio de @handle o de una URL de Instagram."""
        extracted = self.extract_handle(user_input)
        if extracted:
            return extracted
        import re
        clean = user_input.strip()
        if "instagram.com/" in clean:
            clean = clean.split("instagram.com/")[-1].split("/")[0].split("?")[0]
        clean = clean.split("?")[0].strip().lstrip("@,;:. ")
        if not re.match(r'^[a-zA-Z0-9._]{1,30}$', clean):
            return ""
        return clean

    def scrape_profile_reels(self, handle_or_url: str, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Ejecuta el actor de Apify (apify/instagram-reel-scraper) para obtener
        los reels recientes, métricas de views/likes y captions del perfil.
        """
        handle = self.clean_handle(handle_or_url)
        if not handle:
            return []

        if not self.token or "PLACEHOLDER" in self.token:
            logger.warning("No hay APIFY_API_TOKEN configurado. Omitiendo scrape real.")
            return []

        logger.info(f"🔍 [Instagram] Scrapeando perfil @{handle} en Apify (límite={limit})...")
        actor_url = f"https://api.apify.com/v2/acts/apify~instagram-reel-scraper/run-sync-get-dataset-items?token={self.token}"
        payload = {
            "username": [handle],
            "resultsLimit": limit,
        }

        try:
            with httpx.Client(timeout=90.0) as client:
                res = client.post(actor_url, json=payload)
                if res.status_code not in (200, 201):
                    logger.error(f"Error Apify ({res.status_code}): {res.text[:200]}")
                    return []

                raw_items = res.json()
                if not isinstance(raw_items, list):
                    return []

                cleaned_posts = []
                for p in raw_items:
                    if p.get("error") or not p.get("shortCode"):
                        continue
                    views = p.get("videoPlayCount") or p.get("videoViewCount") or 0
                    caption = (p.get("caption") or "").replace("\n", " ").strip()
                    cleaned_posts.append({
                        "handle": handle,
                        "url": p.get("url") or f"https://instagram.com/p/{p.get('shortCode')}",
                        "likes": p.get("likesCount", 0),
                        "comments": p.get("commentsCount", 0),
                        "views": views,
                        "date": p.get("timestamp"),
                        "caption": caption[:400]
                    })

                logger.info(f"✅ [Instagram] Se obtuvieron {len(cleaned_posts)} reels de @{handle}")
                return cleaned_posts

        except Exception as e:
            logger.error(f"Error scraping Instagram @{handle}: {e}")
            return []

    def scrape_profile_reels_rapidapi(self, handle_or_url: str, limit: int = 6) -> Dict[str, Any]:
        """
        Fallback a RapidAPI para obtener posts, reels y perfil de Instagram cuando Apify falla o excede cuota.
        Compatible con 'instagram-scraper-stable-api.p.rapidapi.com'.
        """
        handle = self.clean_handle(handle_or_url)
        if not handle:
            return {"profile": {}, "posts": []}

        if not config.RAPIDAPI_KEY or "PLACEHOLDER" in config.RAPIDAPI_KEY:
            logger.info("No hay RAPIDAPI_KEY configurado. Omitiendo fallback RapidAPI.")
            return {"profile": {}, "posts": []}

        logger.info(f"🔍 [Instagram RapidAPI] Consultando @{handle} en {config.RAPIDAPI_HOST}...")
        headers = {
            "x-rapidapi-key": config.RAPIDAPI_KEY,
            "x-rapidapi-host": config.RAPIDAPI_HOST
        }

        profile_info = {}
        # 1. Perfil y Biografía
        try:
            with httpx.Client(timeout=25.0) as client:
                r_prof = client.post(
                    f"https://{config.RAPIDAPI_HOST}/ig_get_fb_profile.php",
                    headers=headers,
                    data={"username_or_url": handle, "data": "basic"}
                )
                if r_prof.status_code == 200:
                    p_data = r_prof.json()
                    profile_info = {
                        "username": p_data.get("username", handle),
                        "full_name": p_data.get("full_name", ""),
                        "biography": p_data.get("biography", ""),
                        "followers": p_data.get("follower_count", 0),
                        "posts_count": p_data.get("media_count", 0)
                    }
        except Exception as e:
            logger.warning(f"Error consultando perfil RapidAPI para @{handle}: {e}")

        # 2. Reels para capturar reproducciones reales
        reels_by_code = {}
        try:
            with httpx.Client(timeout=25.0) as client:
                r_reels = client.post(
                    f"https://{config.RAPIDAPI_HOST}/get_ig_user_reels.php",
                    headers=headers,
                    data={"username_or_url": handle, "amount": str(limit)}
                )
                if r_reels.status_code == 200:
                    raw_reels = r_reels.json().get("reels", []) or []
                    for r in raw_reels:
                        media = r.get("node", {}).get("media", {})
                        code = media.get("code", "")
                        if code:
                            cap_node = media.get("caption") or {}
                            cap_txt = cap_node.get("text", "") if isinstance(cap_node, dict) else str(cap_node or "")
                            reels_by_code[code] = {
                                "views": media.get("play_count") or media.get("view_count") or 0,
                                "likes": media.get("like_count") or 0,
                                "caption": cap_txt
                            }
        except Exception as e:
            logger.warning(f"Error consultando reels RapidAPI para @{handle}: {e}")

        # 3. Posts para capturar descripciones y carruseles
        cleaned_posts = []
        try:
            with httpx.Client(timeout=25.0) as client:
                r_posts = client.post(
                    f"https://{config.RAPIDAPI_HOST}/get_ig_user_posts.php",
                    headers=headers,
                    data={"username_or_url": handle}
                )
                if r_posts.status_code == 200:
                    raw_posts = r_posts.json().get("posts", []) or []
                    for p in raw_posts[:limit]:
                        node = p.get("node", {})
                        code = node.get("code", "")
                        cap_data = node.get("caption") or {}
                        caption = cap_data.get("text", "") if isinstance(cap_data, dict) else str(cap_data)
                        reel_match = reels_by_code.get(code, {})
                        views = reel_match.get("views") or node.get("play_count") or node.get("view_count") or 0
                        likes = reel_match.get("likes") or node.get("like_count") or 0
                        final_caption = caption or reel_match.get("caption") or ""

                        cleaned_posts.append({
                            "handle": handle,
                            "url": f"https://instagram.com/p/{code}",
                            "likes": likes,
                            "comments": node.get("comment_count", 0),
                            "views": views,
                            "date": node.get("taken_at"),
                            "caption": final_caption.replace("\n", " ").strip()[:400]
                        })
        except Exception as e:
            logger.warning(f"Error consultando posts RapidAPI para @{handle}: {e}")

        # Si posts no devolvió nada pero sí reels, usamos reels
        if not cleaned_posts and reels_by_code:
            for code, r_info in list(reels_by_code.items())[:limit]:
                cleaned_posts.append({
                    "handle": handle,
                    "url": f"https://instagram.com/p/{code}",
                    "likes": r_info["likes"],
                    "comments": 0,
                    "views": r_info["views"],
                    "date": None,
                    "caption": r_info["caption"].replace("\n", " ").strip()[:400]
                })

        logger.info(f"✅ [Instagram RapidAPI] Se obtuvieron {len(cleaned_posts)} piezas de @{handle}")
        return {"profile": profile_info, "posts": cleaned_posts}

    def research_creator_footprint(self, handle_or_url: str) -> Dict[str, Any]:
        """
        Investiga el perfil y la huella digital del creador.
        1. Intenta raspar reels vía Apify si hay token y cuota disponible.
        2. Fallback a RapidAPI si Apify falla o excede cuota.
        3. Fallback a Web Grounding (Google Search en vivo vía Gemini).
        4. Fallback a huella verificada de trinchera (para cuentas conocidas).
        """
        handle = self.clean_handle(handle_or_url)
        if not handle:
            return {"handle": "", "reels": [], "summary": "", "source": "none"}

        # 1. Intentar scrape en vivo en Apify
        reels = self.scrape_profile_reels(handle, limit=6)
        if reels:
            return {
                "handle": handle,
                "reels": reels,
                "source": "apify",
                "summary": f"Se obtuvieron {len(reels)} reels recientes de Instagram vía Apify."
            }

        # 2. Fallback con RapidAPI
        rapid_data = self.scrape_profile_reels_rapidapi(handle, limit=6)
        reels_rapid = rapid_data.get("posts", [])
        profile_rapid = rapid_data.get("profile", {})
        if reels_rapid or profile_rapid.get("biography"):
            summary_parts = []
            if profile_rapid.get("full_name") or profile_rapid.get("biography"):
                summary_parts.append(
                    f"Nombre / Bio: {profile_rapid.get('full_name', '')} ({profile_rapid.get('biography', '')}). Seguidores: {profile_rapid.get('followers', 0)}."
                )
            return {
                "handle": handle,
                "reels": reels_rapid,
                "source": "rapidapi",
                "summary": "\n".join(summary_parts) if summary_parts else f"Se obtuvieron {len(reels_rapid)} posts recientes de Instagram vía RapidAPI."
            }

        # 3. Fallback con Web Grounding en vivo (Google Search Grounding)
        if config.GEMINI_API_KEY:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=config.GEMINI_API_KEY)
                resp = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=f"Investiga el perfil público de Instagram @{handle}, su biografía, proyectos, empresas y temas que trata.",
                    config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
                )
                grounded_text = (resp.text or "").strip()
                if grounded_text and len(grounded_text) > 40:
                    logger.info(f"🌐 [Web Grounding] Éxito investigando @{handle} con búsqueda web en vivo.")
                    return {
                        "handle": handle,
                        "reels": [],
                        "source": "web_grounding",
                        "summary": grounded_text
                    }
            except Exception as e:
                logger.warning(f"Aviso Web Grounding para @{handle}: {e}")

        return {
            "handle": handle,
            "reels": [],
            "source": "empty",
            "summary": ""
        }

