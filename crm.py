import os 
import logging 

from db import db_init
from login import LoginWindow

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR     = os.path.join(BASE_DIR, 'logs')
DATA_DIR     = os.path.join(BASE_DIR, 'data')
LOG_FILE     = os.path.join(LOGS_DIR, 'crm_log.txt')
SESSION_FILE = os.path.join(DATA_DIR, 'session.json')
DB_PATH      = os.path.join(BASE_DIR, 'crm.db')

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def start_app():
    db_init()
    LoginWindow()

