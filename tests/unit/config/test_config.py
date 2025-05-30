"""
Unit test for configuration settings validation.
Clean test to verify .env values are loaded correctly.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config.settings import settings


def test_print_all_settings():
    """Print all configuration values for verification"""
    print("\n" + "=" * 60)
    print("📋 CONFIGURATION VALUES")
    print("=" * 60)

    # App Settings
    print(f"🔧 Environment: {settings.environment}")
    print(f"🔧 App Name: {settings.app_name}")
    print(f"🔧 Log Level: {settings.log_level}")

    # Telegram Settings
    print(f"📱 Telegram API ID: {settings.telegram_api_id}")
    print(f"📱 Telegram API Hash: {settings.telegram_api_hash}")
    print(f"📱 Session String: {settings.telegram_session_string[:50]}...")

    # MongoDB Settings
    print(f"🗄️ MongoDB URI: {settings.mongodb_uri}")
    print(f"🗄️ MongoDB Database: {settings.mongodb_database}")
    print(f"🗄️ MongoDB Timeout: {settings.mongodb_connection_timeout}")

    # Discord Settings
    print(f"💬 Discord Incidents: {settings.discord_incidents_webhook}")
    print(f"💬 Discord Monitoring: {settings.discord_monitoring_webhook}")

    # DataDog Settings
    print(f"📊 DataDog Enabled: {settings.datadog_enabled}")
    print(f"📊 DataDog API Key: {settings.datadog_api_key or 'Not set'}")

    # Sentry Settings
    print(f"🚨 Sentry Enabled: {settings.sentry_enabled}")
    print(f"🚨 Sentry DSN: {settings.sentry_dsn or 'Not set'}")

    # API Settings
    print(f"🌐 API Host: {settings.api_service_host}")
    print(f"🌐 API Port: {settings.api_service_port}")

    print("=" * 60)


if __name__ == "__main__":
    test_print_all_settings()