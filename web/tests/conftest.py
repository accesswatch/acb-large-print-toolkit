import pytest
from acb_large_print_web import ai_features


def _ai_available() -> bool:
    try:
        return ai_features.ai_chat_enabled()
    except Exception:
        return False


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "ai_live: mark test as requiring a live AI provider (OpenRouter) and skip when AI is disabled",
    )
    config.addinivalue_line(
        "markers",
        "ai_whisper: mark test as requiring the Whisper audio feature and skip when disabled",
    )


def pytest_runtest_setup(item):
    # If a test is marked ai_live, skip when AI platform is not available
    if item.get_closest_marker("ai_live") and not _ai_available():
        pytest.skip("AI not configured or disabled")

    # If a test is marked ai_whisper, ensure whisperer feature is enabled
    if item.get_closest_marker("ai_whisper"):
        try:
            if not ai_features.ai_whisperer_enabled():
                pytest.skip("AI whisperer disabled via feature flags")
        except Exception:
            pytest.skip("AI whisperer check failed; skipping")


@pytest.fixture
def require_ai_feature():
    """Callable fixture tests can call to require a particular AI feature at runtime.

    Usage in tests::
        def test_x(require_ai_feature):
            require_ai_feature('whisper')
            ...
    """

    def _require(feature: str) -> None:
        if feature == "whisper":
            if not ai_features.ai_whisperer_enabled():
                pytest.skip("AI whisperer disabled")
        else:
            if not _ai_available():
                pytest.skip(f"AI feature '{feature}' unavailable")

    return _require


@pytest.fixture
def feature_flags_fixture(tmp_path):
    """Fixture to temporarily override server-side feature flags for tests.

    Usage::
        def test_x(feature_flags_fixture):
            feature_flags_fixture.set('GLOW_ENABLE_AI_CHAT', False)
    """
    from acb_large_print_web import feature_flags

    # Snapshot current flags and restore after test
    orig = feature_flags.get_all_flags()

    class _Ctl:
        def set(self, name: str, value: bool) -> None:
            feature_flags.set_flag(name, bool(value))

        def get(self, name: str) -> bool:
            return feature_flags.get_flag(name)

        def all(self) -> dict:
            return feature_flags.get_all_flags()

    ctl = _Ctl()
    yield ctl

    # restore
    for k, v in orig.items():
        feature_flags.set_flag(k, v)
