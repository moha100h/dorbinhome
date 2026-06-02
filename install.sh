#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   🛍  DorbinHome Shop Bot  —  Installer  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

if ! command -v docker &>/dev/null; then
    warn "Docker not found. Installing..."
    curl -fsSL https://get.docker.com | sh
    info "Docker installed."
fi

if ! docker compose version &>/dev/null 2>&1; then
    warn "Docker Compose plugin not found. Installing..."
    apt-get update -qq && apt-get install -y -qq docker-compose-plugin
    info "Docker Compose installed."
fi

echo ""
read -rp "🤖  Bot Token (from @BotFather): " BOT_TOKEN
[[ -z "$BOT_TOKEN" ]] && error "BOT_TOKEN cannot be empty."

read -rp "👑  Admin Telegram ID (numeric): " ADMIN_ID
[[ ! "$ADMIN_ID" =~ ^[0-9]+$ ]] && error "ADMIN_ID must be a number."

read -rp "📢  Channel ID (e.g. @mychannel) or Enter to skip: " CHANNEL_ID

cat > .env <<EOF
BOT_TOKEN=${BOT_TOKEN}
ADMIN_ID=${ADMIN_ID}
CHANNEL_ID=${CHANNEL_ID}
DB_PATH=/data/shop.db
EOF
info ".env created."

echo ""
info "Building and starting..."
docker compose down --remove-orphans 2>/dev/null || true
docker compose up -d --build

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   ✅  Bot is running!                    ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  📋  Logs:     docker compose logs -f bot"
echo "  🔄  Restart:  docker compose restart bot"
echo "  🛑  Stop:     docker compose down"
echo "  ⬆️   Update:   git pull && docker compose up -d --build"
echo ""
