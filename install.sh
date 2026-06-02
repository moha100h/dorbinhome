#!/usr/bin/env bash
set -euo pipefail
ok()   { echo "[OK] $*"; }
warn() { echo "[!!] $*"; }

echo ""
echo "  DorbinHome Shop Bot -- Installer v2"
echo ""

if ! command -v docker &>/dev/null; then
    warn "Docker not found. Installing..."
    curl -fsSL https://get.docker.com | sh
    ok "Docker installed."
fi
if ! docker compose version &>/dev/null 2>&1; then
    warn "Docker Compose plugin not found. Installing..."
    apt-get update -qq && apt-get install -y -qq docker-compose-plugin
    ok "Docker Compose installed."
fi

echo ""
while true; do
    read -rp "  Bot Token (from @BotFather): " BOT_TOKEN
    [[ -n "$BOT_TOKEN" ]] && break
    warn "Bot Token cannot be empty."
done
while true; do
    read -rp "  Admin Telegram ID (numeric): " ADMIN_ID
    [[ "$ADMIN_ID" =~ ^[0-9]+$ ]] && break
    warn "Admin ID must be a number."
done

cat > .env <<EOF
BOT_TOKEN=${BOT_TOKEN}
ADMIN_ID=${ADMIN_ID}
DB_PATH=/data/shop.db
EOF
ok ".env created."

docker compose down --remove-orphans 2>/dev/null || true
docker compose up -d --build
sleep 3

STATUS=$(docker inspect --format='{{.State.Status}}' dorbinhome_bot 2>/dev/null || echo 'unknown')
echo ""
echo "  Bot is running! Status: ${STATUS}"
echo ""
echo "  Logs:    docker compose logs -f bot"
echo "  Restart: docker compose restart bot"
echo "  Update:  git pull && docker compose up -d --build"
echo ""
echo "  After install:"
echo "  1. Open bot -> Admin Panel"
echo "  2. Create categories (format: Parent > Child)"
echo "  3. Create brands and usages"
echo "  4. Settings: set channel + support"
echo "  5. Add products"
echo ""
