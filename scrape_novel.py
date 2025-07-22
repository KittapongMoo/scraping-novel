"""
Novel Scraper for KatReadingCafe and NovelBin websites
Supports downloading multiple chapters with automatic resuming
"""

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
import random

# Configuration
URLS_FILE = "novel_urls.txt"
BASE_OUTPUT_DIR = "chapters"

def ask_chapters_to_download():
    """Ask user how many chapters to download"""
    while True:
        try:
            chapters = input("\n📚 How many chapters do you want to download? (1-1000): ").strip()
            chapters_num = int(chapters)
            if 1 <= chapters_num <= 1000:
                print(f"✅ Will download {chapters_num} chapters")
                return chapters_num
            else:
                print("❌ Please enter a number between 1 and 1000")
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
        return []
    
    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
    
    return urls


def get_novel_folder_name(url):
    """Extract novel name from URL and create a safe folder name"""
    novel_name = url.rstrip('/').split('/')[-1]
    safe_name = re.sub(r'[<>:"/\\|?*]', '', novel_name)
    return safe_name


def detect_website_type(url):
    """Detect which website type based on URL"""
    if "katreadingcafe.com" in url:
        return "katreadingcafe"
    elif "novelbin.me" in url:
        return "novelbin"
    else:
        return "unknown"

def select_url(urls):
    """Let user select which URL to scrape"""
    if not urls:
        return None, None, None
    
    print("\n📚 Available novels:")
    for i, url in enumerate(urls, 1):
        if "katreadingcafe.com" in url:
            novel_name = url.split('/')[-2].replace('-', ' ').title()
            website = "KatReadingCafe"
        elif "novelbin.me" in url:
            novel_name = url.split('/')[-1].replace('-', ' ').title()
            website = "NovelBin"
        else:
            novel_name = url.split('/')[-1].replace('-', ' ').title()
            website = "Unknown"
        
        print(f"   {i}. {novel_name} ({website})")
    
    while True:
        try:
            choice = input(f"\n🔢 Select novel to download (1-{len(urls)}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(urls):
                selected_url = urls[choice_num - 1]
                folder_name = get_novel_folder_name(selected_url)
                website_type = detect_website_type(selected_url)
                
                if "katreadingcafe.com" in selected_url:
                    novel_name = selected_url.split('/')[-2].replace('-', ' ').title()
                elif "novelbin.me" in selected_url:
                    novel_name = selected_url.split('/')[-1].replace('-', ' ').title()
                else:
                    novel_name = folder_name.replace('-', ' ').title()
                
                print(f"✅ Selected: {novel_name}")
                print(f"🌐 Website: {website_type}")
                print(f"📁 Will save to: {BASE_OUTPUT_DIR}/{folder_name}/")
                return selected_url, folder_name, website_type
            else:
                print(f"❌ Please enter a number between 1 and {len(urls)}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return None, None, None


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


def save_chapter(title, content, chapter_num, output_dir):
    """Save chapter content to file with safe filename"""
    safe_title = re.sub(r'[<>:"/\\|?*#]', '', title)
    safe_title = re.sub(r'\s+', ' ', safe_title)
    
    # Limit filename length
    max_title_length = 80
    if len(safe_title) > max_title_length:
        safe_title = safe_title[:max_title_length] + "..."
    
    filename = os.path.join(output_dir, f"{chapter_num:03d}_{safe_title}.txt")
    
    # Check path length and use fallback if needed
    if len(filename) > 240:
        filename = os.path.join(output_dir, f"{chapter_num:03d}_Chapter_{chapter_num}.txt")
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(title + "\n\n" + content)
        print(f"✅ Saved: {os.path.basename(filename)}")
        return True
    except OSError:
        # Final fallback filename
        filename = os.path.join(output_dir, f"{chapter_num:03d}_Chapter_{chapter_num}.txt")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(title + "\n\n" + content)
            print(f"✅ Saved (fallback): {os.path.basename(filename)}")
            return True
        except Exception as e:
            print(f"❌ Failed to save chapter {chapter_num}: {e}")
            return False

def scrape_katreadingcafe(driver, wait, series_url, chapters_per_run, start, end, output_dir):
    """Scrape chapters from KatReadingCafe"""
    print("🔍 KatReadingCafe: Checking if Vol. 1 is already expanded...")
    
    # Navigate to series page
    driver.get(series_url)
    time.sleep(3)
    
    # Check if Vol. 1 chapters are already visible
    chapters_already_visible = False
    new_chapter_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'New Chapter')]")
    
    if new_chapter_elements:
        print(f"Found {len(new_chapter_elements)} 'New Chapter' elements")
        for elem in new_chapter_elements:
            try:
                next_sibling = driver.execute_script("return arguments[0].nextElementSibling;", elem)
                if next_sibling and "Vol. 1" in next_sibling.text:
                    print("✅ Vol. 1 chapters are already visible!")
                    chapters_already_visible = True
                    break
            except:
                continue
    
    # If not visible, try to expand Vol. 1
    if not chapters_already_visible:
        print("🔍 Looking for Vol. 1 expand button...")
        vol1_selectors = [
            "//span[text()='Vol. 1']",
            "//span[normalize-space(text())='Vol. 1']",
        ]
        
        for selector in vol1_selectors:
            try:
                vol1_element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                driver.execute_script("arguments[0].scrollIntoView(true);", vol1_element)
                time.sleep(1)
                vol1_element.click()
                print("✅ Clicked Vol. 1 to expand")
                time.sleep(3)
                break
            except:
                continue
    
    # Collect chapter links
    links = driver.find_elements(By.TAG_NAME, "a")
    chap_map = {}
    for a in links:
        txt = a.text.strip()
        m = re.match(r'Vol\. 1 Ch\. (\d+)', txt)
        if m:
            num = int(m.group(1))
            chap_map[num] = a.get_attribute("href")
    
    # Download chapters
    downloaded = 0
    all_nums = sorted(chap_map.keys())
    print(f"📋 Chapters found: {all_nums[:10]} ... {all_nums[-1] if all_nums else 'None'}")
    
    for num in all_nums:
        if num < start or num > end or downloaded >= chapters_per_run:
            continue
        
        url = chap_map[num]
        print(f"🌐 Loading Chapter {num} -> {url}")
        driver.get(url)
        time.sleep(2)
        
        title = driver.title.strip()
        
        # Try different content selectors
        content = ""
        selectors = ["div.entry-content", ".post-content", ".chapter-content", "article", ".content"]
        
        for sel in selectors:
            try:
                content = driver.find_element(By.CSS_SELECTOR, sel).text
                break
            except:
                continue
        
        if not content:
            print(f"❌ Could not extract content for chapter {num}")
            continue
        
        if save_chapter(title, content, num, output_dir):
            downloaded += 1
    
    return downloaded

def scrape_novelbin_single_with_fresh_browser(series_url, target_chapter, output_dir):
    """Scrape a single chapter from NovelBin with fresh browser instance"""
    print(f"🔍 NovelBin: Downloading chapter {target_chapter}...")
    
    # Setup fresh Chrome driver for this chapter
    driver = setup_chrome_driver()
    if not driver:
        print(f"❌ Failed to setup Chrome driver for chapter {target_chapter}")
        return 0
    
    wait = WebDriverWait(driver, 30)
    
    try:
        # Create the chapter list URL
        chapters_list_url = series_url.rstrip('/') + "#tab-chapters-title"
        print(f"📋 Loading chapter list: {chapters_list_url}")
        
        # Navigate to chapter list
        driver.get(chapters_list_url)
        time.sleep(random.uniform(3, 6))
        
        # Activate chapter tab if needed
        try:
            chapter_tab = driver.find_element(By.CSS_SELECTOR, "#tab-chapters-title")
            if not chapter_tab.get_attribute("aria-expanded") == "true":
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth'});", chapter_tab)
                time.sleep(random.uniform(1, 2))
                chapter_tab.click()
                time.sleep(random.uniform(2, 4))
        except:
            pass
        
        # Scroll to load chapters
        print("📜 Loading chapters...")
        for i in range(3):
            scroll_amount = random.randint(500, 1000)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(1, 2))
        
        # Find the specific chapter URL
        chapter_url = None
        chapter_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/chapter-')]")
        
        for link in chapter_links:
            href = link.get_attribute("href")
            chapter_num_match = re.search(r'chapter-(\d+)', href)
            if chapter_num_match:
                chapter_num = int(chapter_num_match.group(1))
                if chapter_num == target_chapter:
                    chapter_url = href
                    break
        
        if not chapter_url:
            print(f"❌ Chapter {target_chapter} not found in the list")
            return 0
        
        print(f"🌐 Found Chapter {target_chapter}: {chapter_url}")
        
        # Navigate directly to the chapter
        driver.get(chapter_url)
        time.sleep(random.uniform(2, 4))
        
        # Extract content
        title = driver.title.strip()
        content = ""
        selectors = [".chr-c", ".chapter-content", ".content", "#chr-content", ".reading-content", "article"]
        
        for sel in selectors:
            try:
                content_element = driver.find_element(By.CSS_SELECTOR, sel)
                content = content_element.text
                print(f"✅ Found content using selector: {sel}")
                break
            except:
                continue
        
        if not content:
            print(f"❌ Could not extract content for chapter {target_chapter}")
            return 0
        
        # Save the chapter
        if save_chapter(title, content, target_chapter, output_dir):
            print(f"✅ Successfully downloaded and saved chapter {target_chapter}")
            return 1
        else:
            print(f"❌ Failed to save chapter {target_chapter}")
            return 0
        
    except Exception as e:
        print(f"❌ Error processing chapter {target_chapter}: {e}")
        return 0
    finally:
        # Always close the browser for this chapter
        try:
            driver.quit()
            print(f"🔄 Closed browser for chapter {target_chapter}")
        except:
            pass

def scrape_novelbin_multiple(series_url, chapters_per_run, start, end, output_dir):
    """Execute multiple single chapter downloads with fresh browser for each chapter"""
    print(f"🔍 NovelBin: Will download {chapters_per_run} chapters with fresh browser for each...")
    
    downloaded = 0
    current_chapter = start
    
    for i in range(chapters_per_run):
        if current_chapter > end:
            print(f"📝 Reached end chapter {end}, stopping...")
            break

        print(f"\n{'='*50}")
        print(f"📚 Starting download {i+1}/{chapters_per_run}")
        print(f"🎯 Target: Chapter {current_chapter}")
        print(f"{'='*50}")

        # Download single chapter with fresh browser
        result = scrape_novelbin_single_with_fresh_browser(series_url, current_chapter, output_dir)

        if result == 1:
            downloaded += 1
            print(f"✅ Successfully downloaded chapter {current_chapter}")
            current_chapter += 1
        else:
            print(f"❌ Failed to download chapter {current_chapter}")
            # Try next chapter instead of stopping
            current_chapter += 1

    return downloaded


def setup_chrome_driver():
    """Setup and return Chrome driver with optimal options"""
    options = Options()
    options.add_argument("--headless")  # Enable headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.images": 2  # Block images for faster loading
    })

    # Create Chrome driver
    try:
        print("🔧 Setting up Chrome driver...")
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome driver initialized successfully!")
        return driver
    except Exception as e:
        try:
            # Fallback: try with chromedriver.exe in current directory
            print("🔧 Trying chromedriver.exe in current directory...")
            driver = webdriver.Chrome(service=Service("chromedriver.exe"), options=options)
            print("✅ Chrome driver initialized successfully!")
            return driver
        except Exception as e2:
            print(f"❌ Failed to start ChromeDriver: {e}")
            print("💡 Solutions:")
            print("   1. Install webdriver-manager: pip install webdriver-manager")
            print("   2. Download chromedriver.exe and place it in this folder")
            print("   3. Add chromedriver to your system PATH")
            print("   4. Make sure Chrome browser is installed")
            return None


def main():
    """Main execution function"""
    # Load URLs from file
    urls = load_urls()
    if not urls:
        print("❌ No URLs found. Exiting...")
        return

    # Let user select which novel to download
    series_url, novel_folder, website_type = select_url(urls)
    if not series_url:
        print("❌ No URL selected. Exiting...")
        return

    # Set up output directory
    output_dir = os.path.join(BASE_OUTPUT_DIR, novel_folder)

    # Ask how many chapters to download
    chapters_per_run = ask_chapters_to_download()
    if not chapters_per_run:
        print("❌ No chapters specified. Exiting...")
        return

    try:
        # Create the novel-specific output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get latest chapter and calculate range
        latest = get_latest_chapter(output_dir)
        start = latest + 1
        end = latest + chapters_per_run

        print(f"\n📁 Found {latest} existing chapters in {output_dir}")
        print(f"🚀 Will download chapters {start} to {end}")

        # Use appropriate scraping method based on website
        if website_type == "katreadingcafe":
            # KatReadingCafe uses a single browser session
            driver = setup_chrome_driver()
            if not driver:
                return
            
            wait = WebDriverWait(driver, 30)
            
            try:
                downloaded = scrape_katreadingcafe(driver, wait, series_url, chapters_per_run, start, end, output_dir)
            finally:
                try:
                    driver.quit()
                    print("👋 Browser closed for KatReadingCafe!")
                except:
                    pass
                    
        elif website_type == "novelbin":
            # NovelBin uses fresh browser for each chapter
            downloaded = scrape_novelbin_multiple(series_url, chapters_per_run, start, end, output_dir)
        else:
            print(f"❌ Unsupported website type: {website_type}")
            downloaded = 0

        print(f"\n🎉 Completed! Downloaded {downloaded} new chapters.")
        print(f"📁 Saved to: {output_dir}")
        if downloaded == chapters_per_run:
            print("🔄 Run again to get more chapters.")
        elif downloaded == 0:
            print("❌ No chapters were downloaded. Check for errors above.")
        else:
            print(f"📊 Downloaded {downloaded} out of {chapters_per_run} requested chapters.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Goodbye!")


if __name__ == "__main__":
    main()
