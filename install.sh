#!/bin/bash
set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   🛍  DorbinHome Shop Bot Installer  ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check Docker
if ! command -v docker &>/dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com | sh
fi

if ! docker compose version &>/dev/null; then
    echo "📦 Installing Docker Compose plugin..."
    apt-get install -y docker-compose-plugin 2>/dev/null || true
fi

# Input
read -p "🤖 Bot Token: " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then echo "❌ BOT_TOKEN required"; exit 1; fi

read -p "👑 Admin Telegram ID (numeric): " ADMIN_ID
if ! [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then echo "❌ ADMIN_ID must be numeric"; exit 1; fi

read -p "📢 Channel ID (e.g. @mychannel, or leave empty): " CHANNEL_ID

# Write .env
cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
CHANNEL_ID=$CHANNEL_ID
EOF

echo ""
echo "🐳 Building and starting..."
docker compose down -v 2>/dev/null || true
docker compose up -d --build

echo ""
echo "✅ Done! Bot is running."
echo ""
echo "📋 Useful commands:"
echo "  docker compose logs -f bot    # view logs"
echo "  docker compose restart bot    # restart"
echo "  docker compose down           # stop"
