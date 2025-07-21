from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re
import glob

# Configuration
SERIES_URL = "https://katreadingcafe.com/series/genderswap-reincarnation-i-raised-the-strongest-player/"
OUTPUT_DIR = "chapters"
CHAPTERS_PER_RUN = 3  # How many chapters to download per run

def get_latest_chapter():
    if not os.path.exists(OUTPUT_DIR):
        return 0
    chapter_files = glob.glob(os.path.join(OUTPUT_DIR, "*.txt"))
    if not chapter_files:
        return 0
    nums = []
    for f in chapter_files:
        m = re.match(r'^(\d+)_', os.path.basename(f))
        if m:
            nums.append(int(m.group(1)))
    return max(nums) if nums else 0

# Prepare Chrome
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=Service(), options=options)
wait = WebDriverWait(driver, 20)

try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    latest = get_latest_chapter()
    start = latest + 1
    end = latest + CHAPTERS_PER_RUN

    print(f"📁 Found {latest} existing chapters")
    print(f"🚀 Will download chapters {start} to {end}")

    # 1️⃣ Open series page and expand Vol. 1
    driver.get(SERIES_URL)
    print("🔍 Looking for exact 'Vol. 1' expandable section...")

    # Use XPath to find element with exact text "Vol. 1"
    vol1_selectors = [
        "//div[text()='Vol. 1']",           # Exact text match for div
        "//span[text()='Vol. 1']",          # Exact text match for span
        "//button[text()='Vol. 1']",        # Exact text match for button
        "//h3[text()='Vol. 1']",            # Exact text match for heading
        "//h4[text()='Vol. 1']",            # Exact text match for heading
        "//p[text()='Vol. 1']",             # Exact text match for paragraph
        "//*[text()='Vol. 1']",             # Any element with exact text
        "//div[normalize-space(text())='Vol. 1']",  # Exact text ignoring whitespace
        "//span[normalize-space(text())='Vol. 1']", # Exact text ignoring whitespace
    ]
    
    vol1_element = None
    selected_selector = None
    for selector in vol1_selectors:
        try:
            vol1_element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            selected_selector = selector
            print(f"✅ Found exact Vol. 1 element with selector: {selector}")
            
            # Show additional details about the clicked element
            element_tag = vol1_element.tag_name
            element_text = vol1_element.text
            element_class = vol1_element.get_attribute("class") or "No class"
            element_id = vol1_element.get_attribute("id") or "No ID"
            
            print(f"   📋 Element details:")
            print(f"      Tag: <{element_tag}>")
            print(f"      Text: '{element_text}'")
            print(f"      Class: '{element_class}'")
            print(f"      ID: '{element_id}'")
            break
        except:
            continue
    
    if not vol1_element:
        print("❌ Could not find exact Vol. 1 expandable element")
        print("🔍 Let me show you what Vol. 1 related elements exist...")
        
        # Debug: show all elements containing Vol. 1
        all_vol1_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Vol. 1')]")
        for i, elem in enumerate(all_vol1_elements[:10]):
            print(f"   {i+1}. Tag: {elem.tag_name}, Text: '{elem.text.strip()}'")
        
        driver.quit()
        exit()
    
    # Scroll it into view, then click to expand
    driver.execute_script("arguments[0].scrollIntoView(true);", vol1_element)
    time.sleep(1)
    
    vol1_element.click()
    print(f"✅ Successfully clicked Vol. 1 element using selector: {selected_selector}")
    time.sleep(5)  # Wait longer for chapters to load

    # 2️⃣ Gather all chapter links under Vol. 1
    print("📜 Scanning expanded chapter list...")
    # scroll page a few times in case of lazy load
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    links = driver.find_elements(By.TAG_NAME, "a")
    chap_map = {}
    for a in links:
        txt = a.text.strip()
        m = re.match(r'Vol\. 1 Ch\. (\d+)', txt)
        if m:
            num = int(m.group(1))
            chap_map[num] = a.get_attribute("href")

    if not chap_map:
        print("❌ No 'Vol. 1 Ch.' links found after expanding.")
        print("🔍 Let me check what elements are available...")
        
        # Debug: show all clickable elements
        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Vol') or contains(text(), 'Ch') or contains(text(), 'Chapter')]")
        for i, elem in enumerate(all_elements[:10]):
            print(f"   {i+1}. Tag: {elem.tag_name}, Text: '{elem.text.strip()}'")
        
        driver.quit()
        exit()

    all_nums = sorted(chap_map.keys())
    print(f"📋 Chapters found: {all_nums[:10]} ... {all_nums[-1]}")

    # 3️⃣ Download each chapter in range
    downloaded = 0
    for num in all_nums:
        if num < start or num > end:
            continue
        url = chap_map[num]
        print(f"🌐 Loading Vol. 1 Ch. {num} -> {url}")
        driver.get(url)
        time.sleep(2)

        title = driver.title.strip()
        # try multiple selectors
        content = ""
        for sel in ["div.entry-content", ".post-content", ".chapter-content", "article", ".content"]:
            try:
                content = driver.find_element(By.CSS_SELECTOR, sel).text
                break
            except:
                continue

        if not content:
            print(f"❌ Could not extract content for chapter {num}")
            continue

        safe = re.sub(r'[<>:"/\\|?*]', "", title)
        filename = os.path.join(OUTPUT_DIR, f"{num:03d}_{safe}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(title + "\n\n" + content)
        print(f"✅ Saved: {filename}")
        downloaded += 1

    print(f"\n🎉 Completed! Downloaded {downloaded} new chapters.")
    if downloaded == CHAPTERS_PER_RUN:
        print("🔄 Run again to get more chapters.")
except Exception as e:
    print(f"❌ Error: {e}")
