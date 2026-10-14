import pytest
from src.db.supabase import DatabaseService
from src.engine.vfs import VirtualFileSystem

@pytest.fixture
def vfs():
    db = DatabaseService()
    return VirtualFileSystem(db)

def test_vfs_root_listing(vfs):
    items = vfs.list_dir("", "test-user-id")
    assert any("filosofia" in i for i in items)
    assert any("studio" in i for i in items)
    assert any("creator" in i for i in items)
    assert any("skills" in i for i in items)

def test_vfs_read_static_filosofia(vfs):
    content = vfs.read_file("filosofia/canon/00_index.md", "test-user-id")
    assert len(content) > 50
    assert "The Creative Act" in content or "Índice" in content or "capítulo" in content.lower()

def test_vfs_read_creator_pending_interview(vfs):
    # Un usuario aleatorio no tiene aún voz, debe indicar pendiente de entrevista
    content = vfs.read_file("creator/identity/voice_dna.md", "non-existent-user-1234")
    assert "[PENDIENTE_DE_ENTREVISTA]" in content

def test_vfs_search_brain(vfs):
    res = vfs.search_brain("quiebre cognitivo", "test-user-id")
    assert len(res) > 20
    assert "quiebre cognitivo" in res.lower() or "studio" in res.lower()
