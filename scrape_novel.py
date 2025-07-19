from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re

# Configuration
SERIES_URL = "https://katreadingcafe.com/series/genderswap-reincarnation-i-raised-the-strongest-player/"
OUTPUT_DIR = "chapters"
NUM_CHAPTERS = 5

# Prepare Chrome options
options = Options()
options.add_argument("--headless")  # Run in background
options.add_argument("--no-sandbox")  # Fix sandbox error on Windows
options.add_argument("--disable-blink-features=AutomationControlled")

# Initialize driver
driver = webdriver.Chrome(service=Service(), options=options)

# Create output folder
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Open series page
driver.get(SERIES_URL)
wait = WebDriverWait(driver, 20)

# Wait for "First Chapter" button to load and click it
try:
    # Use PARTIAL_LINK_TEXT if button text is like "Vol. 1 Ch. 1"
    first_chapter = wait.until(
        EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Vol. 1 Ch. 1"))
    )
    first_chapter.click()
except Exception as e:
    print("❌ Could not find First Chapter button:", e)
    driver.quit()
    exit()

time.sleep(5)  # wait for chapter to load

# Loop through NUM_CHAPTERS
for i in range(1, NUM_CHAPTERS + 1):
    try:
        title = driver.title
        # Check page source if selector below doesn't match, then adjust accordingly
        content = driver.find_element(By.CSS_SELECTOR, "div.entry-content").text

        # Sanitize filename by removing invalid characters
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_title = safe_title.strip()  # Remove leading/trailing spaces
        
        filename = os.path.join(OUTPUT_DIR, f"{i:03}_{safe_title}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(title + "\n\n")
            f.write(content)
        print(f"✅ Saved: {filename}")

        # Only look for Next Chapter button if we're not on the last chapter
        if i < NUM_CHAPTERS:
            next_chapter = wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Next"))
            )
            next_chapter.click()
            time.sleep(5)  # wait for next chapter to load

    except Exception as e:
        print(f"❌ Error on chapter {i}: {e}")
        break

driver.quit()
