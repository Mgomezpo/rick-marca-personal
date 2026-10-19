"""Base environment and setup verification test."""

def test_environment_setup():
    import fastapi
    import pydantic
    import supabase
    assert fastapi.__version__ is not None
    assert pydantic.__version__ is not None
    assert supabase.__version__ is not None
