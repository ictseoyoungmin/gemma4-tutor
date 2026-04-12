from gemma_tutor_edge.config import Settings


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
