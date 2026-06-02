# DorbinHome — Telegram Shop Bot v2

Python 3.11 + aiogram 3.7 + SQLite + Docker

## Install
```bash
git clone https://github.com/moha100h/dorbinhome.git
cd dorbinhome
chmod +x install.sh
sudo bash install.sh
```

## Update
```bash
cd ~/dorbinhome
git pull
docker compose up -d --build
```

## Commands
```bash
docker compose logs -f bot
docker compose restart bot
docker compose down -v
docker cp dorbinhome_bot:/data/shop.db ./backup.db
```

## Admin Commands
- /delcat
- /delbrand
- /delusage

## First Setup
1. Admin Panel -> Categories (format: Parent > Child)
2. Brands, Usages
3. Settings: channel, support, welcome, help
4. Add Product -> wizard -> photos -> Done button
