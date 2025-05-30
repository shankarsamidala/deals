#!/bin/bash

echo "📁 Creating telegram-deal-monitor structure..."

folders=(
  # Root files
  "."
  "infrastructure/k8s"
  "infrastructure/scripts"
  "core/config"
  "core/database"
  "core/monitoring"
  "core/notifications"
  "core/utils"
  "services/api/routers"
  "services/api/schemas"
  "services/api/handlers"
  "services/listener/telegram"
  "services/listener/processors"
  "services/listener/storage"
  "services/parser/parsers"
  "services/parser/processors"
  "services/parser/storage"
  "tests/unit/core"
  "tests/unit/services"
  "tests/integration/api"
  "tests/integration/listener"
  "tests/integration/parser"
  "docs/api"
)

files=(
  # Root files
  ".env"
  ".env.example"
  "requirements.txt"
  "pyproject.toml"
  "README.md"
  "docker-compose.yml"

  # Scripts
  "infrastructure/scripts/setup.sh"
  "infrastructure/scripts/build-all.sh"
  "infrastructure/scripts/deploy-all.sh"

  # Core files
  "core/__init__.py"
  "core/config/__init__.py"
  "core/config/settings.py"
  "core/config/database.py"
  "core/config/logging.py"
  "core/database/__init__.py"
  "core/database/connection.py"
  "core/database/models.py"
  "core/database/repositories.py"
  "core/monitoring/__init__.py"
  "core/monitoring/datadog.py"
  "core/monitoring/sentry.py"
  "core/monitoring/metrics.py"
  "core/notifications/__init__.py"
  "core/notifications/discord.py"
  "core/notifications/base.py"
  "core/utils/__init__.py"
  "core/utils/validators.py"
  "core/utils/helpers.py"
  "core/utils/exceptions.py"

  # API Service
  "services/api/Dockerfile"
  "services/api/docker-compose.yml"
  "services/api/requirements.txt"
  "services/api/.env.example"
  "services/api/__init__.py"
  "services/api/main.py"
  "services/api/dependencies.py"
  "services/api/middleware.py"
  "services/api/routers/__init__.py"
  "services/api/routers/health.py"
  "services/api/routers/database.py"
  "services/api/routers/monitoring.py"
  "services/api/routers/admin.py"
  "services/api/schemas/__init__.py"
  "services/api/schemas/health.py"
  "services/api/schemas/database.py"
  "services/api/schemas/responses.py"
  "services/api/handlers/__init__.py"
  "services/api/handlers/health_handler.py"
  "services/api/handlers/database_handler.py"

  # Listener Service
  "services/listener/Dockerfile"
  "services/listener/docker-compose.yml"
  "services/listener/requirements.txt"
  "services/listener/.env.example"
  "services/listener/__init__.py"
  "services/listener/main.py"
  "services/listener/telegram/__init__.py"
  "services/listener/telegram/client.py"
  "services/listener/telegram/monitor.py"
  "services/listener/telegram/handlers.py"
  "services/listener/processors/__init__.py"
  "services/listener/processors/message_processor.py"
  "services/listener/processors/channel_manager.py"
  "services/listener/storage/__init__.py"
  "services/listener/storage/message_storage.py"

  # Parser Service
  "services/parser/Dockerfile"
  "services/parser/docker-compose.yml"
  "services/parser/requirements.txt"
  "services/parser/.env.example"
  "services/parser/__init__.py"
  "services/parser/main.py"
  "services/parser/parsers/__init__.py"
  "services/parser/parsers/url_extractor.py"
  "services/parser/parsers/content_parser.py"
  "services/parser/parsers/deal_analyzer.py"
  "services/parser/processors/__init__.py"
  "services/parser/processors/url_processor.py"
  "services/parser/processors/content_processor.py"
  "services/parser/storage/__init__.py"
  "services/parser/storage/url_storage.py"

  # Tests
  "tests/__init__.py"
  "tests/conftest.py"
  "tests/unit/core/.gitkeep"
  "tests/unit/services/.gitkeep"
  "tests/integration/api/.gitkeep"
  "tests/integration/listener/.gitkeep"
  "tests/integration/parser/.gitkeep"

  # Docs
  "docs/api/.gitkeep"
  "docs/architecture.md"
  "docs/deployment.md"
)

# Create folders
for folder in "${folders[@]}"; do
  mkdir -p "$folder"
done

# Create files
for file in "${files[@]}"; do
  touch "$file"
done

echo "✅ Project folder structure created at ./"
