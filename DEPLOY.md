# Deployment — Price Tracker (homelab)

Public, read-only demo of the Streamlit dashboard at
**https://pricetracker.ericfolch.com**, served from the Raspberry Pi 5 homelab
behind Cloudflare Tunnel.

## Architecture

```
Internet ─HTTPS─> Cloudflare Tunnel "homelab" ─> 127.0.0.1:8081 ─> container Streamlit :8501  (PUBLIC, read-only)
                                                 127.0.0.1:8082 ─> container FastAPI   :8000  (localhost only, no CF route)
                                                                   SQLite /app/data/prices.sqlite (own volume, seeded)
                                                                   Scraper scheduler: DISABLED
```

- Single container, entrypoint `src/run_services.py`, driven by env vars.
- `RUN_SCHEDULER=false`: no scraping from the Pi (no IP-ban / ToS / cost risk).
- `ENVIRONMENT=production`: FastAPI hides `/docs`, `/redoc`, `/openapi.json`.
- Ports bound to `127.0.0.1` only. Port 8082 is used because 8000 is reserved by CertiShot.

## One-time setup on the Pi

```bash
ssh tusk@homelab.local

# 0) Verify the ports are free (expect no output)
ss -tlnp | grep -E ':(8081|8082)\b'

# 1) Clone (SSH remote)
cd ~
git clone git@github.com:EricFolchMartinez/<REPO>.git pricetracker
cd pricetracker

# 2) Production env file
cp .env.prod.example .env.prod
# (defaults are fine; edit GITHUB_URL etc. if needed)

# 3) Build & start (ARM64 build on the Pi)
docker compose -f docker-compose.prod.yml up -d --build

# 4) Seed the demo database (one-off, idempotent; --force to reseed)
docker compose -f docker-compose.prod.yml exec price-tracker \
    python scripts/seed_demo.py --force

# 5) Smoke test locally on the Pi
curl -fsS http://127.0.0.1:8081/_stcore/health   # -> "ok"
docker compose -f docker-compose.prod.yml ps      # healthy
docker compose -f docker-compose.prod.yml logs -f # check startup
```

## Cloudflare route

Zero Trust → Networks → Connectors → **homelab** → Published application routes → Add:

| Field      | Value                |
|------------|----------------------|
| Subdomain  | `pricetracker`       |
| Domain     | `ericfolch.com`      |
| Path       | *(empty)*            |
| Type       | `HTTP`               |
| URL        | `localhost:8081`     |

Cloudflare provisions DNS + HTTPS instantly. Visit https://pricetracker.ericfolch.com.

## Updates

```bash
cd ~/pricetracker
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Notes

- The FastAPI service is intentionally **not** exposed through Cloudflare. It runs
  on `127.0.0.1:8082` for local use only. Do not add a Cloudflare route for it
  unless you add rate limiting / auth first (its `POST /products` triggers scraping).
- The database lives in `./data` (git-ignored). Back it up by copying `data/prices.sqlite`.
