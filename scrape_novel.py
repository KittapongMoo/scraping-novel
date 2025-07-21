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
URLS_FILE = "novel_urls.txt"  # File containing all novel URLs
BASE_OUTPUT_DIR = "chapters"  # Base chapters folder

def ask_chapters_to_download():
    """Ask user how many chapters to download"""
    while True:
        try:
            chapters = input(f"\n📚 How many chapters do you want to download? (1-50): ").strip()
            chapters_num = int(chapters)
            if 1 <= chapters_num <= 50:
                print(f"✅ Will download {chapters_num} chapters")
                return chapters_num
            else:
                print("❌ Please enter a number between 1 and 50")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return None

def load_urls():
    """Load URLs from the text file"""
    if not os.path.exists(URLS_FILE):
        print(f"❌ {URLS_FILE} not found!")
        print(f"💡 Please create {URLS_FILE} and add your novel URLs, one per line.")
        print(f"   Example content:")
        print(f"   https://katreadingcafe.com/series/genderswap-reincarnation-i-raised-the-strongest-player/")
        print(f"   https://katreadingcafe.com/series/another-novel/")
        return []
    
    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
    
    return urls

def get_novel_folder_name(url):
    """Extract novel name from URL and create a safe folder name"""
    # Extract the novel name from URL (last part before trailing slash)
    novel_name = url.rstrip('/').split('/')[-1]
    # Clean the name for use as folder name
    safe_name = re.sub(r'[<>:"/\\|?*]', '', novel_name)
    return safe_name

def select_url(urls):
    """Let user select which URL to scrape"""
    if not urls:
        return None, None
    
    print(f"\n📚 Available novels:")
    for i, url in enumerate(urls, 1):
        # Extract novel name from URL for display
        novel_name = url.split('/')[-2].replace('-', ' ').title()
        print(f"   {i}. {novel_name}")
        print(f"      {url}")
    
    while True:
        try:
            choice = input(f"\n🔢 Select novel to download (1-{len(urls)}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(urls):
                selected_url = urls[choice_num - 1]
                novel_name = selected_url.split('/')[-2].replace('-', ' ').title()
                folder_name = get_novel_folder_name(selected_url)
                print(f"✅ Selected: {novel_name}")
                print(f"📁 Will save to: {BASE_OUTPUT_DIR}/{folder_name}/")
                return selected_url, folder_name
            else:
                print(f"❌ Please enter a number between 1 and {len(urls)}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return None, None

def get_latest_chapter(output_dir):
    """Get the latest chapter number from the specific novel folder"""
    if not os.path.exists(output_dir):
        return 0
    chapter_files = glob.glob(os.path.join(output_dir, "*.txt"))
    if not chapter_files:
        return 0
    nums = []
    for f in chapter_files:
        m = re.match(r'^(\d+)_', os.path.basename(f))
        if m:
            nums.append(int(m.group(1)))
    return max(nums) if nums else 0

# Load URLs and let user select
urls = load_urls()
if not urls:
    # If no URLs file exists, use the default URL
    SERIES_URL = "https://katreadingcafe.com/series/genderswap-reincarnation-i-raised-the-strongest-player/"
    novel_folder = get_novel_folder_name(SERIES_URL)
    OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, novel_folder)
    print(f"🔧 Using default URL: {SERIES_URL}")
    print(f"📁 Will save to: {OUTPUT_DIR}/")
else:
    SERIES_URL, novel_folder = select_url(urls)
    if not SERIES_URL:
        exit()
    OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, novel_folder)

# Ask how many chapters to download
CHAPTERS_PER_RUN = ask_chapters_to_download()
if not CHAPTERS_PER_RUN:
    exit()

# Prepare Chrome
options = Options()
options.add_argument("--headless") # Run in background
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=Service(), options=options)
wait = WebDriverWait(driver, 20)

try:
    # Create the novel-specific output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    latest = get_latest_chapter(OUTPUT_DIR)
    start = latest + 1
    end = latest + CHAPTERS_PER_RUN

    print(f"\n📁 Found {latest} existing chapters in {OUTPUT_DIR}")
    print(f"🚀 Will download chapters {start} to {end}")

    # 1️⃣ Open series page
    driver.get(SERIES_URL)
    print("🔍 Checking 'New Chapter' to determine if Vol. 1 is already expanded...")

    chapters_already_visible = False
    
    # Look for "New Chapter" element and check the next element for volume info
    print("\n📋 Looking for 'New Chapter' and adjacent volume information...")
    
    new_chapter_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'New Chapter')]")
    
    if new_chapter_elements:
        print(f"Found {len(new_chapter_elements)} 'New Chapter' elements")
        
        for i, new_chapter_elem in enumerate(new_chapter_elements, 1):
            print(f"\n   {i}. New Chapter element:")
            print(f"      Tag: {new_chapter_elem.tag_name}")
            print(f"      Text: '{new_chapter_elem.text.strip()}'")
            
            # Look for the next sibling or nearby elements that contain volume info
            try:
                # Method 1: Check next sibling
                next_sibling = driver.execute_script(
                    "return arguments[0].nextElementSibling;", new_chapter_elem
                )
                if next_sibling and next_sibling.text.strip():
                    sibling_text = next_sibling.text.strip()
                    print(f"      Next sibling text: '{sibling_text}'")
                    
                    if "Vol. 1" in sibling_text:
                        print(f"      ✅ Next element shows 'Vol. 1' - Vol. 1 is already expanded!")
                        chapters_already_visible = True
                    elif "Vol. 2" in sibling_text or "Vol. 3" in sibling_text:
                        print(f"      ❌ Next element shows higher volume - Vol. 1 is collapsed!")
                        chapters_already_visible = False
                
                # Method 2: Check parent element and its children
                parent_elem = new_chapter_elem.find_element(By.XPATH, "..")
                children = parent_elem.find_elements(By.XPATH, "./*")
                
                print(f"      Parent has {len(children)} child elements:")
                for j, child in enumerate(children[:5]):  # Show first 5 children
                    child_text = child.text.strip()
                    print(f"        Child {j+1}: '{child_text}'")
                    
                    if "Vol. 1" in child_text and "Ch." in child_text:
                        print(f"        ✅ Found 'Vol. 1 Ch.' in child element - Vol. 1 is expanded!")
                        chapters_already_visible = True
                    elif ("Vol. 2" in child_text or "Vol. 3" in child_text) and "Ch." in child_text:
                        print(f"        ❌ Found higher volume in child element - Vol. 1 is collapsed!")
                        chapters_already_visible = False
                        
            except Exception as e:
                print(f"      ⚠️ Could not check adjacent elements: {e}")
    else:
        print("❌ No 'New Chapter' elements found")
        
        # Fallback: Look directly for Vol. 1 Ch. elements
        print("\n📋 Fallback: Looking directly for 'Vol. 1 Ch.' elements...")
        vol1_chapter_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Vol. 1 Ch.')]")
        if vol1_chapter_elements:
            print(f"   Found {len(vol1_chapter_elements)} 'Vol. 1 Ch.' elements:")
            for i, elem in enumerate(vol1_chapter_elements[:5], 1):
                print(f"   {i}. Tag: {elem.tag_name}, Text: '{elem.text.strip()}'")
            print("   ✅ Vol. 1 chapters appear to be visible!")
            chapters_already_visible = True
        else:
            print("   ❌ No Vol. 1 chapters visible, need to expand")
            chapters_already_visible = False
    
    print(f"\n📊 Final Decision: Vol. 1 already expanded = {chapters_already_visible}")
    
    # If Vol. 1 is not expanded, click to expand it
    if not chapters_already_visible:
        print("\n🔍 Vol. 1 is collapsed, looking for 'Vol. 1' button to expand...")

        # Use XPath to find element with exact text "Vol. 1"
        vol1_selectors = [
            "//span[text()='Vol. 1']",          # Exact text match for span
            "//span[normalize-space(text())='Vol. 1']", # Exact text ignoring whitespace
            "//div[text()='Vol. 1']",           # Exact text match for div
            "//button[text()='Vol. 1']",        # Exact text match for button
        ]
        
        vol1_element = None
        selected_selector = None
        for selector in vol1_selectors:
            try:
                vol1_element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                selected_selector = selector
                print(f"✅ Found Vol. 1 expand button with selector: {selector}")
                
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
            print("❌ Could not find Vol. 1 expand button")
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
        print(f"✅ Successfully clicked Vol. 1 to expand using selector: {selected_selector}")
        time.sleep(5)  # Wait longer for chapters to load
    else:
        print("\n⏭️ Vol. 1 is already expanded, skipping click")
        time.sleep(2)  # Short wait for page stability

    # 2️⃣ Gather all chapter links under Vol. 1
    print("📜 Scanning for chapter links...")
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
        print("❌ No 'Vol. 1 Ch.' links found.")
        print("🔍 Let me check what elements are available...")
        
        # Debug: show all clickable elements
        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Vol') or contains(text(), 'Ch') or contains(text(), 'Chapter') or contains(text(), 'New')]")
        for i, elem in enumerate(all_elements[:15]):
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
    print(f"📁 Saved to: {OUTPUT_DIR}")
    if downloaded == CHAPTERS_PER_RUN:
        print("🔄 Run again to get more chapters.")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    driver.quit()
