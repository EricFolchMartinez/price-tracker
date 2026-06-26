"""Seed the database with realistic sample data for the public demo.

The public demo runs with the scraper disabled, so the dashboard needs a
populated, good-looking dataset. This script is idempotent: it does nothing if
products already exist, unless run with --force (which wipes and reseeds).

Usage (inside the container):
    docker compose -f docker-compose.prod.yml run --rm price-tracker \
        python scripts/seed_demo.py --force
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.database import Base, SessionLocal, engine
from src.models import PriceHistory, Product

# (name, amazon-style url, base_price, target_price)
DEMO_PRODUCTS = [
    ("ELEGOO PLA+ Filament 1.75mm 1KG (Black)", "https://www.amazon.es/dp/B0D4Z3CZQH", 17.99, 15.50),
    ("Creality Ender-3 V3 SE 3D Printer", "https://www.amazon.es/dp/B0CGxxxx01", 199.00, 169.00),
    ("Logitech MX Master 3S Wireless Mouse", "https://www.amazon.es/dp/B0B11xxxx2", 119.99, 99.00),
    ("Anker 737 Power Bank (PowerCore 24K)", "https://www.amazon.es/dp/B09VPxxxx3", 149.99, 129.99),
    ("SanDisk Extreme PRO 1TB NVMe SSD", "https://www.amazon.es/dp/B09QVxxxx4", 109.90, 89.00),
    ("Keychron K2 Mechanical Keyboard (Brown)", "https://www.amazon.es/dp/B08D9xxxx5", 89.00, 89.00),
]

WEEKS = 12  # ~3 months of weekly history


def build_history(base_price: float, target: float) -> list[tuple[float, datetime]]:
    """Generate a believable weekly price walk ending near (and sometimes below) target."""
    now = datetime.utcnow()
    points: list[tuple[float, datetime]] = []
    price = round(base_price * random.uniform(1.0, 1.08), 2)
    for week in range(WEEKS, 0, -1):
        when = now - timedelta(weeks=week, hours=random.randint(0, 20))
        # Gentle random walk with an occasional dip.
        drift = random.uniform(-0.05, 0.03)
        if random.random() < 0.15:  # occasional promo
            drift -= random.uniform(0.05, 0.12)
        price = max(round(price * (1 + drift), 2), round(base_price * 0.7, 2))
        points.append((price, when))
    # Final/current point: nudge so roughly half the catalogue is an active deal.
    final = target * random.uniform(0.93, 1.06)
    points.append((round(final, 2), now))
    return points


def seed(force: bool) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Product).count()
        if existing and not force:
            print(f"Database already has {existing} product(s); skipping. Use --force to reseed.")
            return
        if force:
            db.query(PriceHistory).delete()
            db.query(Product).delete()
            db.commit()
            print("Cleared existing data (--force).")

        for name, url, base_price, target in DEMO_PRODUCTS:
            product = Product(name=name, url=url, target_price=target)
            db.add(product)
            db.commit()
            db.refresh(product)
            for price, when in build_history(base_price, target):
                db.add(PriceHistory(product_id=product.id, price=price, scraped_at=when))
            db.commit()
            print(f"Seeded: {name}")
        print(f"Done. {len(DEMO_PRODUCTS)} products with {WEEKS + 1} price points each.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data for the Price Tracker dashboard.")
    parser.add_argument("--force", action="store_true", help="Wipe and reseed even if data exists.")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility.")
    args = parser.parse_args()
    random.seed(args.seed)
    seed(args.force)
