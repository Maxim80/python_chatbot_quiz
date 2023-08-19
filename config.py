from dotenv import load_dotenv
import os

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
REDIS_URL = os.getenv('REDIS_URL')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_PASSW = os.getenv('REDIS_PASSW')
