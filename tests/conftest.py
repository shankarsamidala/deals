"""
Test script to validate configuration loading and Pydantic settings.
Run this to ensure .env file is properly loaded and all settings are valid.
"""

import sys
from pathlib import Path

# Add core to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from core.config.settings import settings

    print("✅ Settings module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import settings: {e}")
    sys.exit(1)


def test_app_settings():
    """Test application settings"""
    print("\n🔧 APP SETTINGS:")
    print(f"  Environment: {settings.app.environment}")
    print(f"  App Name: {settings.app.app_name}")
    print(f"  Log Level: {settings.app.log_level}")

    assert settings.app.environment in {"development", "staging", "production"}
    assert settings.app.log_level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    print("  ✅ App settings valid")


def test_telegram_settings():
    """Test Telegram settings"""
    print("\n📱 TELEGRAM SETTINGS:")
    print(f"  API ID: {settings.telegram.api_id}")
    print(f"  API Hash: {settings.telegram.api_hash[:10]}...")
    print(f"  Session String: {settings.telegram.session_string[:20]}...")

    assert isinstance(settings.telegram.api_id, int)
    assert len(settings.telegram.api_hash) > 0
    assert len(settings.telegram.session_string) > 0
    print("  ✅ Telegram settings valid")


def test_mongodb_settings():
    """Test MongoDB settings"""
    print("\n🗄️ MONGODB SETTINGS:")
    print(f"  URI: {settings.mongodb.uri[:50]}...")
    print(f"  Database: {settings.mongodb.database}")
    print(f"  Timeout: {settings.mongodb.connection_timeout}s")

    assert settings.mongodb.uri.startswith("mongodb")
    assert len(settings.mongodb.database) > 0
    assert settings.mongodb.connection_timeout > 0
    print("  ✅ MongoDB settings valid")


def test_discord_settings():
    """Test Discord settings"""
    print("\n💬 DISCORD SETTINGS:")
    print(f"  Incidents Webhook: {settings.discord.incidents_webhook[:50]}...")
    print(f"  Monitoring Webhook: {settings.discord.monitoring_webhook[:50]}...")

    assert settings.discord.incidents_webhook.startswith("https://discord")
    assert settings.discord.monitoring_webhook.startswith("https://discord")
    print("  ✅ Discord settings valid")


def test_optional_settings():
    """Test optional settings (DataDog, Sentry)"""
    print("\n🔍 OPTIONAL SETTINGS:")
    print(f"  DataDog Enabled: {settings.datadog.enabled}")
    print(f"  DataDog API Key: {'Set' if settings.datadog.api_key else 'Not set'}")
    print(f"  Sentry Enabled: {settings.sentry.enabled}")
    print(f"  Sentry DSN: {'Set' if settings.sentry.dsn else 'Not set'}")
    print("  ✅ Optional settings loaded")


def test_api_settings():
    """Test API settings"""
    print("\n🌐 API SETTINGS:")
    print(f"  Host: {settings.api.host}")
    print(f"  Port: {settings.api.port}")

    assert settings.api.port > 0
    assert settings.api.host in {"0.0.0.0", "localhost", "127.0.0.1"}
    print("  ✅ API settings valid")


def main():
    """Run all configuration tests"""
    print("🚀 TESTING CONFIGURATION LOADING")
    print("=" * 50)

    try:
        test_app_settings()
        test_telegram_settings()
        test_mongodb_settings()
        test_discord_settings()
        test_optional_settings()
        test_api_settings()

        print("\n" + "=" * 50)
        print("🎉 ALL CONFIGURATION TESTS PASSED!")
        print("✅ Ready to proceed with database connection")

    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()