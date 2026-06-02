# DorbinHome — Telegram Shop Bot v2

Python 3.11 + aiogram 3.7 + SQLite + Docker

## Features

### User Panel
- Shop: browse categories -> sub-categories -> products -> product card with photo
- Buy: full form (name, mobile, province, city, address, postal code)
- My Orders: history with status
- Help: configurable text from admin
- Support: direct link (configurable from admin)

### Admin Panel
- Add Product: wizard (category -> brand -> usage -> info -> photos + Done button)
- Products: list, edit price/stock, toggle active, delete, publish to channel
- Categories: create parent/sub-category, delete (/delcat)
- Brands: add/delete (/delbrand)
- Usages: add/delete (/delusage)
- Orders: list, change status, auto-notify user
- Reports: sales stats, revenue, best sellers
- Settings (all from inside bot): channel ID, support username, welcome text, help text

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

## Management

```bash
docker compose logs -f bot          # live logs
docker compose restart bot          # restart
docker compose stop                 # stop
docker compose down -v              # full reset + delete DB
docker cp dorbinhome_bot:/data/shop.db ./backup.db  # backup
```

## First Setup

1. Admin Panel -> Categories: type name (e.g. Camera) or sub: Camera > Action Cam
2. Brands: type brand name
3. Usages: type usage name
4. Settings -> set channel, support, welcome text, help text
5. Add Product -> follow wizard -> send photos -> press Done button

## Admin Commands

- /delcat — delete category
- /delbrand — delete brand
- /delusage — delete usage
