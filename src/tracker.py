import logging
from datetime import datetime
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import Product, PriceHistory
from src.scrapers.factory import get_scraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/tracker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Verifies the URL by scraping the name and current price
def add_product(url: str, target_price: float = None) -> Product:

    db: Session = SessionLocal()
    try:
        scraper = get_scraper(url)
        logger.info(f"Scraping initial data for: {url}")
        name = scraper.extract_name()
        current_price = scraper.extract_price()
        
        if name == "Unknown Product" or current_price == 0.0:
            logger.warning("Could not extract valid data. Check URL or Scraper.")
        
        new_product = Product(
            name=name,
            url=url,
            target_price=target_price
        )
        db.add(new_product)
        db.commit() # To get the ID
        db.refresh(new_product)
        
        # Create initial price history
        if current_price > 0:
            price_entry = PriceHistory(
                product_id=new_product.id,
                price=current_price
            )
            db.add(price_entry)
            db.commit()
            
        logger.info(f"Product added: {name} at {current_price}€")
        return new_product

    except Exception as e:
        logger.error(f"Error adding product: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

# Iterates over the database to update the prices
def track_prices():
    db: Session = SessionLocal()
    try:
        products = db.query(Product).all()
        logger.info(f"Starting tracking for {len(products)} products...")
        
        for product in products:
            try:
                scraper = get_scraper(product.url)
                price = scraper.extract_price()
                
                if price > 0:
                    new_history = PriceHistory(
                        product_id=product.id,
                        price=price,
                        scraped_at=datetime.utcnow()
                    )
                    db.add(new_history)
                    logger.info(f"Updated {product.name}: {price}€")
                    
                else:
                    logger.warning(f"Failed to scrape price for {product.name}")
                    
            except Exception as e:
                logger.error(f"Error tracking product {product.id}: {e}")
                
        db.commit()
        logger.info("Tracking cycle completed.")
        
    except Exception as e:
        logger.error(f"Critical error in tracking cycle: {e}")
    finally:
        db.close()