"""
Parallel Background Sandbox Runner for RICK Multitenant Engine.
Executes multi-turn user journeys in parallel across distinct creator personas,
measures real latency and quality, and outputs a formatted markdown report.
"""
import asyncio
import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

# Force live LLM execution mode (no mocks)
os.environ["APP_ENV"] = "development"
os.environ.pop("PYTEST_CURRENT_TEST", None)
os.environ["MOCK_LLM"] = "false"

from src.services.session_runner import process_user_turn
from src.db.repository import SupabaseRepository
from src.graph.state import CreatorProfile, StoryReceipt
from tests.test_simulation_aha_moment import AhaMomentOracle

REPORT_OUTPUT_PATH = r"C:\Users\mgome\.gemini\antigravity-ide\brain\612dc27a-75b2-4981-949c-ef83ae0b55c8\sandbox_execution_report.md"

SANDBOX_PERSONAS = [
    {
        "name": "Carlos B2B (Ofertas de Alto Valor)",
        "handle": "carlos_b2b_offers",
        "user_id": "sandbox_user_carlos_01",
        "nicho": "Ventas High-Ticket & Escalado B2B",
        "referentes": ["@alexhormozi", "@dan_martell"],
        "turns": [
            "Hola RICK, cómo andas? Soy Carlos @carlos_b2b_offers.",
            "Ayer perdimos un contrato de $10.000 porque prometimos resultados sin tener la infraestructura lista y me tocó asumir la pérdida.",
            "Armemos el guion técnico para Instagram con el estilo directo de Hormozi."
        ]
    },
    {
        "name": "Diego Code (Apalancamiento & Modelos)",
        "handle": "diego_leverage",
        "user_id": "sandbox_user_diego_02",
        "nicho": "Software, Modelos Mentales & Solopreneurship",
        "referentes": ["@naval", "@matt_gray"],
        "turns": [
            "Buenas RICK, quiero empezar a comunicar sobre código y apalancamiento.",
            "El error que veo a diario son desarrolladores quemándose 14 horas al día en vez de construir sistemas reutilizables.",
            "Listo, redacta el guion en 3 bloques al grano para grabar hoy."
        ]
    },
    {
        "name": "Dra. Lucía (Salud & Neurobiología)",
        "handle": "dra_lucia_salud",
        "user_id": "sandbox_user_lucia_03",
        "nicho": "Neurobiología Aplicada y Rendimiento",
        "referentes": ["@hubermanlab", "@peterattiamd"],
        "turns": [
            "Hola RICK, soy Lucía @dra_lucia_salud. Trabajo en optimización de sueño y fatiga en ejecutivos.",
            "En la clínica mido cortisol y veo pacientes tomando 5 tazas de café mientras usan pantallas antes de que salga el sol.",
            "Escríbeme el guion para un Reel de 45 segundos con gancho de alto impacto."
        ]
    },
    {
        "name": "Andrés Novato (Cold Start Onboarding)",
        "handle": "andres_novato",
        "user_id": "sandbox_user_andres_04",
        "nicho": "Finanzas y Contabilidad para Pymes",
        "referentes": [],
        "turns": [
            "Hola RICK, quiero empezar mi marca personal pero me da pena y no tengo videos.",
            "Mi cuenta es @andres_novato. Veo que todos mis clientes cometen el error de mezclar sus finanzas personales con las de la empresa.",
            "Listo, armemos el guion para mi primer video."
        ]
    }
]


def run_persona_session(persona: Dict[str, Any]) -> Dict[str, Any]:
    """Runs a complete multi-turn conversation session for a single persona."""
    repo = SupabaseRepository()
    user_id = persona["user_id"]
    handle = persona["handle"]

    # Inicializar perfil
    profile = CreatorProfile(
        user_id=user_id,
        instagram_handle=handle,
        nicho=persona["nicho"],
        mediana_views=15000.0,
        referentes=persona["referentes"]
    )
    repo.upsert_creator_profile(profile)

    conversation_log = []
    total_latency_ms = 0.0

    for turn_idx, user_text in enumerate(persona["turns"], 1):
        start_t = time.perf_counter()

        response_text = process_user_turn(
            user_id=user_id,
            handle=handle,
            text=user_text,
            channel="whatsapp",
            repo_override=repo
        )

        elapsed_ms = (time.perf_counter() - start_t) * 1000
        total_latency_ms += elapsed_ms

        conversation_log.append({
            "turn": turn_idx,
            "user": user_text,
            "rick": response_text,
            "latency_ms": elapsed_ms
        })

    # Verificar calidad de la última respuesta (debe ser guion)
    final_script = conversation_log[-1]["rick"]
    quality_passed = True
    quality_notes = []
    try:
        AhaMomentOracle.assert_script_quality(final_script)
        quality_notes.append("✅ Estructura canónica 3 bloques verificada (HOOK, DESARROLLO, CIERRE)")
        quality_notes.append("✅ Indicaciones de cámara presentes")
        quality_notes.append("✅ Cero placeholders y cero AI Slop")
    except AssertionError as e:
        quality_passed = False
        quality_notes.append(f"⚠️ Alerta de calidad: {e}")

    return {
        "persona": persona["name"],
        "handle": f"@{handle}",
        "nicho": persona["nicho"],
        "referentes": ", ".join(persona["referentes"]) if persona["referentes"] else "Ninguno (Autónomo)",
        "total_latency_ms": total_latency_ms,
        "avg_latency_turn_ms": total_latency_ms / len(persona["turns"]),
        "turns": conversation_log,
        "quality_passed": quality_passed,
        "quality_notes": quality_notes
    }


def generate_markdown_report(results: List[Dict[str, Any]], elapsed_total_s: float):
    """Formats all parallel results into a comprehensive markdown document."""
    lines = [
        "# Informe de Ejecución del Sandbox en Paralelo — RICK",
        "",
        f"> **Fecha de Ejecución:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"> **Modo:** Sandbox Paralelo Asíncrono en Background  ",
        f"> **Creadores Simulados:** {len(results)}  ",
        f"> **Tiempo Total de Corrida:** {elapsed_total_s:.2f} segundos  ",
        "",
        "---",
        "",
        "## 1. Resumen Ejecutivo de Métricas",
        "",
        "| Creador | Nicho | Referentes | Latencia Media/Turno | Estado del Aha Moment |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]

    for r in results:
        status = "🟢 APROBADO (Score >= 9.0)" if r["quality_passed"] else "🔴 OBSERVACIONES"
        lines.append(f"| **{r['persona']}** | {r['nicho']} | {r['referentes']} | {r['avg_latency_turn_ms']:.1f} ms | {status} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Transcripción Detallada Turno a Turno por Creador")
    lines.append("")

    for r in results:
        lines.append(f"### 🎭 Creador: {r['persona']} ({r['handle']})")
        lines.append(f"- **Nicho:** {r['nicho']}")
        lines.append(f"- **Referentes del Radar:** {r['referentes']}")
        lines.append("")

        for t in r["turns"]:
            lines.append(f"#### 📱 Turno {t['turn']} ({t['latency_ms']:.1f} ms)")
            lines.append(f"**Usuario:**")
            lines.append(f"> *\"{t['user']}\"*")
            lines.append("")
            lines.append(f"**RICK:**")
            # Indentar la respuesta de RICK
            formatted_rick = "\n".join([f"> {line}" for line in t['rick'].split("\n")])
            lines.append(formatted_rick)
            lines.append("")

        lines.append("#### 🔍 Auditoría de Calidad del Guion")
        for note in r["quality_notes"]:
            lines.append(f"- {note}")
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Reporte generado exitosamente en: {REPORT_OUTPUT_PATH}")


def main():
    print("=" * 70)
    print("🚀 INICIANDO SANDBOX PARALELO EN BACKGROUND (4 CREADORES)")
    print("=" * 70)
    start_all = time.perf_counter()

    import concurrent.futures
    results = []

    # Ejecución paralela con ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(run_persona_session, p): p for p in SANDBOX_PERSONAS}
        for future in concurrent.futures.as_completed(futures):
            p = futures[future]
            try:
                res = future.result()
                results.append(res)
                print(f"  [OK] Creador completado: {p['name']} ({res['total_latency_ms']:.1f} ms)")
            except Exception as e:
                print(f"  [ERROR] Falló creador {p['name']}: {e}")

    total_time = time.perf_counter() - start_all
    generate_markdown_report(results, total_time)
    print("=" * 70)
    print(f"🎉 SANDBOX FINALIZADO EN {total_time:.2f} SEGUNDOS.")
    print("=" * 70)


if __name__ == "__main__":
    main()
