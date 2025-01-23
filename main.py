import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from app.database import init_db, SessionLocal
from app.config import Settings
from app.cron_job import run_prospecting_job
from app.onboarding import collect_company_info, save_to_db
from app.models import User

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_onboarding():
    db = SessionLocal()
    try:
        if not db.query(User).first():
            print("\n" + "="*40)
            print("First time setup needed!")
            company_info, product_info, icp_info = collect_company_info()
            save_to_db(company_info, product_info, icp_info)
    finally:
        db.close()

def main():
    # Initialize database
    init_db()
    
    # Check for first-time setup
    check_onboarding()
    
    # Configure scheduler
    settings = Settings()
    scheduler = BlockingScheduler()

    @scheduler.scheduled_job('interval', minutes=settings.search_interval_minutes)
    def scheduled_job():
        logger.info("Running prospecting job...")
        run_prospecting_job()
        logger.info("Prospecting job completed")

    try:
        logger.info("Sales Bot is running! We'll check for new leads every 24 hours.")
        logger.info("Press Ctrl+C to exit")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down Sales Bot")

if __name__ == "__main__":
    main()