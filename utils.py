import os
from datetime import date

STUDY = "Study"
ENTERTAINMENT = "Entertainment"
PAUSED = "Paused"
CONFIG_FILE = "timer_config.json"
DATA_DIR = "data"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

def format_time(seconds):
    """Formats seconds into HH:MM:SS."""
    if seconds < 0:
        seconds = 0
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def ensure_data_dir():
    """Ensures the data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_data_file_path(dt=None):
    """Gets the path for the data file for a specific date."""
    ensure_data_dir()
    if dt is None:
        dt = date.today()
    return os.path.join(DATA_DIR, f"data_{dt.strftime(DATE_FORMAT)}.json")