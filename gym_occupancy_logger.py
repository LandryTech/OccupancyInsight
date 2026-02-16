import sqlite3
import time
import schedule
import os
import requests
from datetime import datetime, time as dt_time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables from keys.env
load_dotenv("keys.env")

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

# Weather API Configuration
# Get API key from environment variable (safer for version control)
# If not set, falls back to placeholder
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', 'YOUR_API_KEY_HERE')
BOSTON_LAT = 42.3601
BOSTON_LON = -71.0589

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
    
    # Main occupancy log with weather data
    cur.execute("""
        CREATE TABLE IF NOT EXISTS occupancy_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            facility TEXT NOT NULL,
            occupancy INTEGER NOT NULL,
            temperature REAL,
            precipitation REAL
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
# Weather Data
# ========================
def fetch_weather():
    """
    Fetch current weather data from OpenWeatherMap API
    Returns: (temperature_feels_like, precipitation_1h) in Fahrenheit and inches
    """
    try:
        # Check if API key is set
        if WEATHER_API_KEY == "YOUR_API_KEY_HERE":
            print("[WARNING] Weather API key not set - using default values")
            return None, None
        
        # OpenWeatherMap API endpoint
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': BOSTON_LAT,
            'lon': BOSTON_LON,
            'appid': WEATHER_API_KEY,
            'units': 'imperial'  # Fahrenheit
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract feels-like temperature
        temp_feels_like = data['main']['feels_like']
        
        # Optional: Smooth temperature using recent history to reduce sensor noise
        # This prevents wild fluctuations from multiple weather stations
        temp_smoothed = smooth_temperature(temp_feels_like)
        
        # Extract precipitation (rain in last hour)
        # OpenWeatherMap provides rain volume for last 1 hour in mm
        precipitation_mm = 0.0
        if 'rain' in data and '1h' in data['rain']:
            precipitation_mm = data['rain']['1h']
        elif 'snow' in data and '1h' in data['snow']:
            # Count snow as precipitation too
            precipitation_mm = data['snow']['1h']
        
        # Convert mm to inches (1 mm = 0.0393701 inches)
        precipitation_inches = precipitation_mm * 0.0393701
        
        return temp_smoothed, precipitation_inches
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Weather API request failed: {e}"
        print(f"[ERROR] {error_msg}")
        log_error("weather_api_error", error_msg)
        return None, None
    except Exception as e:
        error_msg = f"Error fetching weather: {e}"
        print(f"[ERROR] {error_msg}")
        log_error("weather_error", error_msg)
        return None, None


def smooth_temperature(current_temp):
    """
    Smooth temperature using exponential moving average to reduce sensor noise.
    This helps with fluctuations from multiple weather stations.
    """
    try:
        # Get last 3 temperature readings
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT temperature 
            FROM occupancy_log 
            WHERE temperature IS NOT NULL 
            ORDER BY timestamp DESC 
            LIMIT 3
        """)
        recent_temps = [row[0] for row in cur.fetchall()]
        conn.close()
        
        if len(recent_temps) == 0:
            # No history, return current
            return current_temp
        
        # Exponential moving average: 70% current, 30% recent history
        # This smooths out station-switching noise while staying responsive
        avg_recent = sum(recent_temps) / len(recent_temps)
        smoothed = (0.7 * current_temp) + (0.3 * avg_recent)
        
        # Sanity check: don't smooth if temperature jumped more than 10°F
        # (indicates real weather change, not sensor noise)
        if abs(current_temp - recent_temps[0]) > 10:
            return current_temp
        
        return smoothed
        
    except Exception as e:
        # If smoothing fails, just return raw temperature
        return current_temp

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
        # Fetch occupancy and weather data
        percent = fetch_occupancy()
        temp, precip = fetch_weather()
        timestamp = datetime.now().isoformat(timespec="minutes")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO occupancy_log (timestamp, facility, occupancy, temperature, precipitation) VALUES (?, ?, ?, ?, ?)",
            (timestamp, FACILITY_NAME, percent, temp, precip)
        )
        conn.commit()
        conn.close()

        # Format output message
        weather_str = ""
        if temp is not None:
            weather_str = f", Temp: {temp:.1f}°F"
        if precip is not None:
            weather_str += f", Precip: {precip:.2f}in"
        
        print(f"[{timestamp}] [OK] Logged occupancy: {percent}%{weather_str}")

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