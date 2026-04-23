from gemma_tutor_edge.config import Settings
import pytest


def test_google_key_resolution():
    settings = Settings(
        gemini_api_key="gemini-key",
        google_api_key=None,
        app_db_path="./data/test.db",
        app_storage_dir="./data/storage",
    )
    assert settings.resolved_google_api_key == "gemini-key"


def test_google_key_fallback():
    settings = Settings(
        gemini_api_key=None,
        google_api_key="google-key",
        app_db_path="./data/test.db",
        app_storage_dir="./data/storage",
    )
    assert settings.resolved_google_api_key == "google-key"


def test_llama_asset_defaults_resolve_from_model_dir(tmp_path):
    settings = Settings(
        llm_backend="llama_cpp",
        model_dir=tmp_path,
        app_db_path=tmp_path / "test.db",
        app_storage_dir=tmp_path / "storage",
    )
    assert settings.resolved_llama_gguf_path == tmp_path / "gemma-4-E2B-it-Q4_K_M.gguf"
    assert settings.resolved_llama_mmproj_path == tmp_path / "mmproj-F16.gguf"


def test_llama_asset_validation_fails_with_clear_message(tmp_path):
    with pytest.raises(ValueError, match="Local llama.cpp asset validation failed"):
        Settings(
            llm_backend="llama_cpp",
            validate_llama_assets=True,
            model_dir=tmp_path,
            app_db_path=tmp_path / "test.db",
            app_storage_dir=tmp_path / "storage",
        )


def test_llama_asset_validation_accepts_explicit_paths(tmp_path):
    gguf_path = tmp_path / "custom.gguf"
    mmproj_path = tmp_path / "custom-mmproj.gguf"
    gguf_path.write_bytes(b"gguf")
    mmproj_path.write_bytes(b"mmproj")

    settings = Settings(
        llm_backend="llama_cpp",
        validate_llama_assets=True,
        llama_gguf_path=gguf_path,
        llama_mmproj_path=mmproj_path,
        app_db_path=tmp_path / "test.db",
        app_storage_dir=tmp_path / "storage",
    )

    assert settings.resolved_llama_gguf_path == gguf_path
    assert settings.resolved_llama_mmproj_path == mmproj_path
