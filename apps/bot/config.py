import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("TELEGRAM_WEBAPP_URL", "")
INTERNAL_API_URL = os.environ.get("INTERNAL_API_URL", "http://backend:8000")
INTERNAL_API_SECRET = os.environ.get("INTERNAL_API_SECRET", "")
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
TICKET_POLL_INTERVAL_SEC = int(os.environ.get("TICKET_POLL_INTERVAL_SEC", "10"))
NOTIFICATION_POLL_INTERVAL_SEC = float(os.environ.get("NOTIFICATION_POLL_INTERVAL_SEC", "5"))
