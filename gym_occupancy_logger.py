import sqlite3
import time
import schedule
import os
from datetime import datetime, time as dt_time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ========================
# Configuration
# ========================
URL = "https://fitrec.wit.edu/FacilityOccupancy"
FACILITY_NAME = "Schumann Fitness Center"

# Database with absolute path
SCRIPT_DIR = Path(__file__).parent.absolute()
DB_PATH = SCRIPT_DIR / "gym_occupancy.db"

# Logging interval (15 minutes)
INTERVAL_MINUTES = 15

# Operating hours (24-hour format)
OPERATING_HOURS = {
    0: (dt_time(6, 0), dt_time(23, 0)),   # Monday: 6 AM - 11 PM
    1: (dt_time(6, 0), dt_time(23, 0)),   # Tuesday: 6 AM - 11 PM
    2: (dt_time(6, 0), dt_time(23, 0)),   # Wednesday: 6 AM - 11 PM
    3: (dt_time(6, 0), dt_time(23, 0)),   # Thursday: 6 AM - 11 PM
    4: (dt_time(6, 0), dt_time(21, 0)),   # Friday: 6 AM - 9 PM
    5: (dt_time(11, 0), dt_time(19, 0)),  # Saturday: 11 AM - 7 PM
    6: (dt_time(11, 0), dt_time(21, 0)),  # Sunday: 11 AM - 9 PM
}

# ========================
# Database
# ========================
def init_db():
    print(f"Creating/connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Main occupancy log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS occupancy_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            facility TEXT NOT NULL,
            occupancy INTEGER NOT NULL
        )
    """)
    
    # Error log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS error_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            error_type TEXT NOT NULL,
            error_message TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized successfully")

def log_error(error_type, error_message):
    """Log errors to database for later analysis"""
    try:
        timestamp = datetime.now().isoformat()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO error_log (timestamp, error_type, error_message) VALUES (?, ?, ?)",
            (timestamp, error_type, str(error_message))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log error to database: {e}")

# ========================
# Operating Hours Check
# ========================
def is_within_operating_hours():
    """Check if current time is within gym operating hours"""
    now = datetime.now()
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday not in OPERATING_HOURS:
        return False
    
    open_time, close_time = OPERATING_HOURS[weekday]
    is_open = open_time <= current_time <= close_time
    
    return is_open

# ========================
# Selenium setup
# ========================
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.page_load_strategy = 'normal'

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# ========================
# Scrape occupancy
# ========================
def fetch_occupancy():
    driver = None
    try:
        driver = create_driver()
        driver.set_page_load_timeout(30)
        driver.get(URL)

        wait = WebDriverWait(driver, 20)

        # Locate the Schumann Fitness Center facility card by ID
        facility = wait.until(
            EC.presence_of_element_located(
                (By.ID, "facility-f8636073-d75d-4aa3-bf30-cdc01946899b")
            )
        )

        # Find the occupancy canvas inside the card
        canvas = facility.find_element(
            By.CSS_SELECTOR,
            "canvas.occupancy-chart"
        )

        ratio = float(canvas.get_attribute("data-ratio"))
        occupancy = int(round(ratio * 100))

        if not (0 <= occupancy <= 100):
            raise ValueError(f"Invalid occupancy value: {occupancy}")

        return occupancy
    
    finally:
        if driver:
            driver.quit()

# ========================
# Log to DB
# ========================
def log_occupancy():
    # First check if we're within operating hours
    if not is_within_operating_hours():
        now = datetime.now()
        print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Outside operating hours - skipping")
        return
    
    try:
        percent = fetch_occupancy()
        timestamp = datetime.now().isoformat(timespec="minutes")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO occupancy_log (timestamp, facility, occupancy) VALUES (?, ?, ?)",
            (timestamp, FACILITY_NAME, percent)
        )
        conn.commit()
        conn.close()

        print(f"[{timestamp}] [OK] Logged occupancy: {percent}%")

    except Exception as e:
        error_msg = f"Error logging occupancy: {e}"
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] [ERROR] {error_msg}")
        log_error("fetch_error", error_msg)

# ========================
# Startup check
# ========================
def check_missed_data():
    """Check if we missed logging while computer was asleep"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT MAX(timestamp) FROM occupancy_log")
        result = cur.fetchone()
        conn.close()
        
        if result[0]:
            last_log = datetime.fromisoformat(result[0])
            time_since_last = datetime.now() - last_log
            
            if time_since_last.total_seconds() > 3600:
                hours_missed = time_since_last.total_seconds() / 3600
                print(f"\n[WARNING] Last log was {hours_missed:.1f} hours ago at {last_log}")
                print(f"   Computer may have been asleep. Resuming logging now...\n")
    except Exception as e:
        print(f"Could not check for missed data: {e}")

# ========================
# Main
# ========================
if __name__ == "__main__":
    print("=" * 70)
    print("GYM OCCUPANCY LOGGER - SCHUMANN FITNESS CENTER")
    print("=" * 70)
    print(f"Script location: {SCRIPT_DIR}")
    print(f"Database: {DB_PATH}")
    print(f"Logging interval: Every {INTERVAL_MINUTES} minutes")
    print(f"URL: {URL}")
    
    print("\nOperating Hours:")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for day_num, (open_t, close_t) in OPERATING_HOURS.items():
        print(f"  {days[day_num]}: {open_t.strftime('%I:%M %p')} - {close_t.strftime('%I:%M %p')}")
    
    print("=" * 70)
    
    # Initialize database
    init_db()
    
    # Check for missed data
    check_missed_data()
    
    # Calculate time until next 15-minute mark
    now = datetime.now()
    current_minute = now.minute
    current_second = now.second
    
    # Find next 15-minute interval (00, 15, 30, 45)
    next_interval = ((current_minute // 15) + 1) * 15
    if next_interval >= 60:
        next_interval = 0
        minutes_until_next = 60 - current_minute
    else:
        minutes_until_next = next_interval - current_minute
    
    # Calculate exact seconds to wait
    seconds_until_next = (minutes_until_next * 60) - current_second
    
    # Show when next log will occur
    next_log_time = now.replace(second=0, microsecond=0)
    if next_interval == 0:
        next_log_time = next_log_time.replace(hour=(now.hour + 1) % 24, minute=0)
    else:
        next_log_time = next_log_time.replace(minute=next_interval)
    
    print(f"\n[INFO] Script started at {now.strftime('%I:%M:%S %p')}")
    print(f"[INFO] Next log will be at {next_log_time.strftime('%I:%M %p')} (in {minutes_until_next} min {seconds_until_next % 60} sec)")
    print(f"[INFO] Logs will occur at: XX:00, XX:15, XX:30, XX:45")
    
    # Wait until the next 15-minute mark
    print(f"\n[INFO] Waiting for next 15-minute interval...")
    time.sleep(seconds_until_next)
    
    # Log immediately at the synchronized time if gym is open
    if is_within_operating_hours():
        print(f"\n[OK] Gym is OPEN - starting synchronized logging")
        log_occupancy()
    else:
        print(f"\n[INFO] Gym is CLOSED - will log when gym opens")
    
    # Schedule logging at exact times (prevents drift)
    # This schedules at :00, :15, :30, :45 of EVERY hour
    schedule.every().hour.at(":00").do(log_occupancy)
    schedule.every().hour.at(":15").do(log_occupancy)
    schedule.every().hour.at(":30").do(log_occupancy)
    schedule.every().hour.at(":45").do(log_occupancy)

    print(f"\nLogger is running... (Press Ctrl+C to stop)")
    print(f"Logging synced to 15-minute intervals: XX:00, XX:15, XX:30, XX:45\n")
    
    # Main loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        print("=" * 70)