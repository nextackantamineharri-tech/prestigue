from flask_apscheduler import APScheduler
from app.services.investment_service import process_daily_profits

scheduler = APScheduler()

def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()
    
    # Schedule the profit processing task
    # For production, this should run once a day
    # For testing/demo, you might want it more frequent
    @scheduler.task('interval', id='process_profits', hours=24)
    def scheduled_profit_task():
        with app.app_context():
            process_daily_profits()
            app.logger.info("Daily profits processed successfully.")
