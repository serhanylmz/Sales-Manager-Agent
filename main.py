import logging
import signal
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
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

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}")
    logger.info("Shutting down Sales Bot gracefully...")
    sys.exit(0)

def main():
    # Initialize database
    init_db()
    
    # Check for first-time setup
    check_onboarding()
    
    # Configure scheduler with proper executors
    settings = Settings()
    executors = {
        'default': {'type': 'threadpool', 'max_workers': 20},
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 1,
        'misfire_grace_time': 15
    }
    
    scheduler = BlockingScheduler(
        executors=executors,
        job_defaults=job_defaults,
        timezone='UTC'
    )

    @scheduler.scheduled_job('interval', minutes=settings.search_interval_minutes)
    def scheduled_job():
        try:
            logger.info("Running prospecting job...")
            run_prospecting_job()
            logger.info("Prospecting job completed")
        except Exception as e:
            logger.error(f"Error in prospecting job: {str(e)}")

    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        logger.info(f"Sales Bot is running! We'll check for new leads every {settings.search_interval_minutes} minutes.")
        logger.info("Press Ctrl+C to exit")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Shutting down Sales Bot")

if __name__ == "__main__":
    main()