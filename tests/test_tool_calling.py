import pytest
import json
from src.core.config import config
from src.db.supabase import DatabaseService
from src.engine.vfs import VirtualFileSystem
from src.engine.tools import OPENAI_TOOLS, execute_tool_call
from src.engine.orchestrator import RickOrchestrator

@pytest.fixture
def test_services():
    db = DatabaseService()
    vfs = VirtualFileSystem(db)
    orchestrator = RickOrchestrator(db)
    return {
        "db": db,
        "vfs": vfs,
        "orchestrator": orchestrator,
        "test_user_id": "00000000-0000-0000-0000-000000000000"
    }

def test_tools_schema_valid():
    """Valida que todas las herramientas cumplan el esquema de OpenAI functions."""
    assert len(OPENAI_TOOLS) >= 11
    tool_names = [t["function"]["name"] for t in OPENAI_TOOLS]
    assert "investigar_huella_creador" in tool_names
    assert "completar_onboarding_creador" in tool_names
    assert "guardar_identidad_creador" in tool_names
    assert "guardar_guion_terminado" in tool_names
    assert "actualizar_memoria_activa" in tool_names
    assert "leer_documento_cerebro" in tool_names
    assert "buscar_en_cerebro" in tool_names
    assert "consultar_piezas_creador" in tool_names
    assert "consultar_perfil_creador" in tool_names
    assert "redactar_guion_formato_oficial" in tool_names
    assert "consultar_posts_instagram" in tool_names

def test_execute_investigar_huella(test_services):
    """Prueba la herramienta investigar_huella_creador."""
    db = test_services["db"]
    vfs = test_services["vfs"]
    uid = test_services["test_user_id"]

    res = execute_tool_call(
        tool_name="investigar_huella_creador",
        args={"handle": "@usuario_test"},
        user_id=uid,
        db=db,
        vfs=vfs
    )
    parsed = json.loads(res)
    assert parsed["status"] == "success"
    assert "resumen_huella" in parsed

def test_execute_completar_onboarding(test_services):
    """Prueba la herramienta completar_onboarding_creador que asienta el binario en BD."""
    db = test_services["db"]
    vfs = test_services["vfs"]
    uid = test_services["test_user_id"]

    res = execute_tool_call(
        tool_name="completar_onboarding_creador",
        args={
            "niche": "Automatización con IA para Operaciones",
            "obsession": "Sistemas simples que devuelven el tiempo",
            "common_enemy": "Suscripciones inútiles de software inflado",
            "origin_story": "El día que un cliente gastó $5,000 en apps que nadie abrió",
            "voice_vibe": "Directo, sobrio y de trinchera",
            "target_audience": "Fundadores que no tienen tiempo que perder"
        },
        user_id=uid,
        db=db,
        vfs=vfs
    )
    parsed = json.loads(res)
    assert parsed["status"] == "success"
    assert "completado exitosamente" in parsed["message"]

def test_execute_guardar_identidad(test_services):
    """Prueba la ejecución directa de la herramienta guardar_identidad_creador."""
    db = test_services["db"]
    vfs = test_services["vfs"]
    uid = test_services["test_user_id"]

    res = execute_tool_call(
        tool_name="guardar_identidad_creador",
        args={
            "niche": "SaaS B2B para Clínicas Dentales",
            "obsession": "Eliminar hojas de cálculo manuales",
            "common_enemy": "El software bloated y costoso",
            "voice_vibe": "Directo, sobrio y basado en números"
        },
        user_id=uid,
        db=db,
        vfs=vfs
    )
    parsed = json.loads(res)
    assert parsed["status"] == "success"
    assert "guardada exitosamente" in parsed["message"]

def test_execute_guardar_guion(test_services):
    """Prueba la ejecución de guardar_guion_terminado."""
    db = test_services["db"]
    vfs = test_services["vfs"]
    uid = test_services["test_user_id"]

    res = execute_tool_call(
        tool_name="guardar_guion_terminado",
        args={
            "titulo": "Por qué tu clínica pierde dinero los domingos",
            "gancho": "El 80% de los odontólogos pasa su domingo cuadrando un Excel que se rompe.",
            "cuerpo_en_actos": "Acto I: Dolor real... Acto II: La solución simple...",
            "framework": "quiebre_cognitivo"
        },
        user_id=uid,
        db=db,
        vfs=vfs
    )
    parsed = json.loads(res)
    assert parsed["status"] == "success"
    assert "piece_id" in parsed

def test_execute_actualizar_memoria(test_services):
    """Prueba la herramienta de actualizar memoria activa."""
    db = test_services["db"]
    vfs = test_services["vfs"]
    uid = test_services["test_user_id"]

    res = execute_tool_call(
        tool_name="actualizar_memoria_activa",
        args={
            "tema_activo": "Serie de automatizaciones odontológicas",
            "nota_scratchpad": "Enfocarse en la clínica de ortodoncia de Medellín"
        },
        user_id=uid,
        db=db,
        vfs=vfs
    )
    parsed = json.loads(res)
    assert parsed["status"] == "success"
    assert parsed["active_topic"] == "Serie de automatizaciones odontológicas"

def test_execute_consultar_piezas(test_services):
    """Prueba la herramienta consultar_piezas_creador."""
    db = test_services["db"]
    vfs = test_services["vfs"]
    uid = test_services["test_user_id"]

    res = execute_tool_call(
        tool_name="consultar_piezas_creador",
        args={"limite": 5},
        user_id=uid,
        db=db,
        vfs=vfs
    )
    assert isinstance(res, str)

def test_execute_consultar_perfil(test_services):
    """Prueba la herramienta consultar_perfil_creador."""
    db = test_services["db"]
    vfs = test_services["vfs"]
    uid = test_services["test_user_id"]

    res = execute_tool_call(
        tool_name="consultar_perfil_creador",
        args={},
        user_id=uid,
        db=db,
        vfs=vfs
    )
    parsed = json.loads(res)
    assert "profile" in parsed
    assert "lore_and_diagnostics" in parsed

def test_orchestrator_zero_hardcoding_in_prompt():
    """Valida que no existan referencias fijas a Bancolombia, PRGX, Insightful Arrow ni cuentas hardcodeadas."""
    from pathlib import Path
    for filepath in ["src/engine/orchestrator.py", "src/services/instagram.py", "src/engine/tools.py"]:
        content = Path(filepath).read_text(encoding="utf-8")
        assert "Bancolombia" not in content, f"Encontrado 'Bancolombia' en {filepath}"
        assert "PRGX" not in content, f"Encontrado 'PRGX' en {filepath}"
        assert "The Insightful Arrow" not in content, f"Encontrado 'The Insightful Arrow' en {filepath}"
        assert "miguel_gomezpo" not in content, f"Encontrado 'miguel_gomezpo' en {filepath}"
        assert "casidonovan" not in content, f"Encontrado 'casidonovan' en {filepath}"

def test_orchestrator_onboarding_new_user(test_services):
    """Valida que un creador nuevo reciba la bienvenida de Head of Content sin mencionar identidades ajenas."""
    import uuid
    orch = test_services["orchestrator"]
    random_user_id = str(uuid.uuid4())

    reply = orch.process_message(
        user_message="Hola Rick, acabo de registrarme. ¿Cómo funciona esto?",
        user_id=random_user_id,
        channel="telegram_test"
    )
    assert len(reply) > 20
    # No debe alucinar bancos ni empresas anteriores
    assert "bancolombia" not in reply.lower()
    assert "prgx" not in reply.lower()
    # Debe ser conciso y no contener encabezados pesados
    assert "###" not in reply
