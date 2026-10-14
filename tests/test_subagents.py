import pytest
from google import genai
from src.core.config import config
from src.core.telemetry import TelemetryTracker
from src.db.supabase import DatabaseService
from src.engine.subagents.anti_slop_editor import AntiSlopEditor
from src.engine.subagents.hook_writer import HookWriterSubagent
from src.engine.subagents.guionista import GuionistaSubagent

@pytest.fixture
def services():
    db = DatabaseService()
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    telemetry = TelemetryTracker(db.client)
    editor = AntiSlopEditor(client, telemetry)
    hook_writer = HookWriterSubagent(client, telemetry)
    guionista = GuionistaSubagent(client, db, telemetry, editor)
    return {
        "db": db,
        "client": client,
        "telemetry": telemetry,
        "editor": editor,
        "hook_writer": hook_writer,
        "guionista": guionista,
    }

def test_anti_slop_quick_scan(services):
    editor = services["editor"]
    slop_text = "En este mundo cambiante, descubre el secreto que es un viaje fascinante para ti."
    detected = editor.quick_scan(slop_text)
    assert "en este mundo cambiante" in detected
    assert "descubre el secreto" in detected
    assert "un viaje fascinante" in detected

def test_anti_slop_refine(services):
    editor = services["editor"]
    dirty = "En este mundo cambiante, te voy a contar la verdad sobre la creación de contenido."
    clean, was_clean, issues = editor.audit_and_refine(dirty, user_id="00000000-0000-0000-0000-000000000000")
    assert not was_clean
    assert "en este mundo cambiante" not in clean.lower()

def test_hook_writer_subagent(services):
    hw = services["hook_writer"]
    res = hw.generar_ganchos(
        tema="La trampa de leer teleprompter en reels",
        angulo="El teleprompter destruye la mirada y huele a robot",
        user_id="00000000-0000-0000-0000-000000000000"
    )
    assert res["success"] is True
    assert len(res["hooks"]) > 100
    assert "Canal Visual" in res["hooks"] or "Gancho" in res["hooks"] or "Beat" in res["hooks"]

def test_guionista_subagent_nuevo_formato(services):
    guionista = services["guionista"]
    res = guionista.redactar_guion(
        brief="La trampa de comprar diez herramientas de IA en vez de ordenar procesos",
        user_id="00000000-0000-0000-0000-000000000000",
        formato="reel",
        framework="pas"
    )
    assert res["success"] is True
    script = res["script"]
    assert "OBJETIVO Y TRANSFORMACIÓN" in script or "OBJETIVO" in script
    assert "HOOK" in script
    assert "• Texto:" in script or "• texto:" in script.lower()
    assert "• Intención:" in script or "• intención:" in script.lower()
    assert "DIRECCIÓN Y COPY" in script or "DIRECCIÓN" in script

