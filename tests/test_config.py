from telemetry_stream.config import Settings


def test_default_settings() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "Persistent Telemetry Stream API"
    assert settings.app_version == "2.0.0"
    assert settings.environment == "development"


def test_settings_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "TELEMETRY_STREAM_ENVIRONMENT",
        "testing",
    )
    monkeypatch.setenv(
        "TELEMETRY_STREAM_API_KEY",
        "test-api-key",
    )

    settings = Settings(_env_file=None)

    assert settings.environment == "testing"
    assert settings.api_key == "test-api-key"
