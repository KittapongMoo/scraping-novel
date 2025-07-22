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
import winsound  # For Windows notification sound

# Configuration
URLS_FILE = "novel_urls.txt"
BASE_OUTPUT_DIR = "chapters"

def play_notification_sound(success=True):
    """Play notification sound when process finishes"""
    try:
        if success:
            # Success sound - play system default sound
            winsound.MessageBeep(winsound.MB_OK)
            # Also play a pleasant sound sequence
            for freq in [800, 1000, 1200]:
                winsound.Beep(freq, 200)
        else:
            # Error sound - play system error sound
            winsound.MessageBeep(winsound.MB_ICONHAND)
            # Also play a warning tone
            winsound.Beep(400, 500)
    except Exception:
        # Fallback for systems without sound or if winsound fails
        print("\a")  # Terminal bell character

def get_available_chapters_info(series_url, website_type):
    """Get information about available chapters from the website"""
    print(f"\n🔍 Checking available chapters on {website_type}...")
    
    driver = setup_chrome_driver()
    if not driver:
        print("❌ Could not setup browser to check chapters")
        return None, None, None
    
    wait = WebDriverWait(driver, 30)
    available_chapters = []
    latest_volume = 1  # Default to 1, will be updated from "New Chapter" element
    
    try:
        if website_type == "katreadingcafe":
            # Navigate to series page
            driver.get(series_url)
            time.sleep(3)
            
            # First, check what's the latest volume from "New Chapter" element
            new_chapter_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'New Chapter')]")
            if new_chapter_elements:
                for elem in new_chapter_elements:
                    try:
                        next_sibling = driver.execute_script("return arguments[0].nextElementSibling;", elem)
                        if next_sibling:
                            sibling_text = next_sibling.text
                            vol_match = re.search(r'Vol\.\s*(\d+)', sibling_text)
                            if vol_match:
                                latest_volume = int(vol_match.group(1))
                                print(f"🆕 Latest volume detected from 'New Chapter': Vol. {latest_volume}")
                                break
                    except:
                        continue
            
            # Find all available volumes
            all_volumes = []
            vol_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Vol.')]")
            for elem in vol_elements:
                vol_text = elem.text.strip()
                vol_match = re.search(r'Vol\.\s*(\d+)', vol_text)
                if vol_match:
                    vol_num = int(vol_match.group(1))
                    all_volumes.append(vol_num)
            
            all_volumes = sorted(list(set(all_volumes)))
            if all_volumes:
                print(f"📚 Found volumes: {all_volumes}")
            
            # Expand volumes (skip the latest volume as it's already expanded)
            for vol_num in all_volumes:
                # Skip expanding the latest volume since it's already expanded
                if vol_num == latest_volume:
                    print(f"⏩ Skipping Vol. {vol_num} expansion (latest volume, already expanded)")
                    
                    # Just collect chapters from already visible latest volume
                    links = driver.find_elements(By.TAG_NAME, "a")
                    for a in links:
                        txt = a.text.strip()
                        # Match patterns like "Vol. 1 Ch. 1" or "Vol. 2 Ch. 15"  
                        m = re.match(rf'Vol\.\s*{vol_num}\s*Ch\.\s*(\d+)', txt)
                        if m:
                            chapter_num = int(m.group(1))
                            available_chapters.append(chapter_num)
                    
                    print(f"✅ Collected chapters from Vol. {vol_num} (already expanded)")
                else:
                    # Expand older volumes
                    try:
                        vol_selector = f"//span[text()='Vol. {vol_num}']"
                        vol_element = driver.find_element(By.XPATH, vol_selector)
                        driver.execute_script("arguments[0].scrollIntoView(true);", vol_element)
                        time.sleep(1)
                        vol_element.click()
                        time.sleep(3)
                        
                        # Collect chapter links for this volume
                        links = driver.find_elements(By.TAG_NAME, "a")
                        for a in links:
                            txt = a.text.strip()
                            # Match patterns like "Vol. 1 Ch. 1" or "Vol. 2 Ch. 15"  
                            m = re.match(rf'Vol\.\s*{vol_num}\s*Ch\.\s*(\d+)', txt)
                            if m:
                                chapter_num = int(m.group(1))
                                available_chapters.append(chapter_num)
                        
                        print(f"✅ Expanded Vol. {vol_num}")
                    except Exception as e:
                        print(f"❌ Could not expand Vol. {vol_num}: {e}")
                        continue
            
        elif website_type == "novelbin":
            # Create the chapter list URL
            chapters_list_url = series_url.rstrip('/') + "#tab-chapters-title"
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
            for i in range(5):  # More scrolling to load more chapters
                scroll_amount = random.randint(500, 1000)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(1, 2))
            
            # Find chapter links
            chapter_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/chapter-')]")
            for link in chapter_links:
                href = link.get_attribute("href")
                chapter_num_match = re.search(r'chapter-(\d+)', href)
                if chapter_num_match:
                    chapter_num = int(chapter_num_match.group(1))
                    available_chapters.append(chapter_num)
        
        # Sort and remove duplicates
        available_chapters = sorted(list(set(available_chapters)))
        
        if available_chapters:
            min_chapter = min(available_chapters)
            max_chapter = max(available_chapters)
            print(f"✅ Found {len(available_chapters)} chapters")
            print(f"📊 Chapter range: {min_chapter} - {max_chapter}")
            
            # Show some examples
            if len(available_chapters) <= 10:
                print(f"📋 Available chapters: {available_chapters}")
            else:
                print(f"📋 First 10 chapters: {available_chapters[:10]}")
                print(f"📋 Last 10 chapters: {available_chapters[-10:]}")
            
            return min_chapter, max_chapter, latest_volume
        else:
            print("❌ No chapters found")
            return None, None, None
            
    except Exception as e:
        print(f"❌ Error checking chapters: {e}")
        return None, None, None
    finally:
        try:
            driver.quit()
        except:
            pass

def ask_chapters_to_download(latest_downloaded, min_available=None, max_available=None, latest_volume=None):
    """Ask user how many chapters to download with context about available chapters"""
    print(f"\n📚 Chapter Download Selection")
    print(f"📁 You currently have: {latest_downloaded} chapters downloaded")
    
    if min_available and max_available:
        print(f"🌐 Website has chapters: {min_available} - {max_available}")
        if latest_volume and latest_volume > 1:
            print(f"📖 Latest volume available: Vol. {latest_volume}")
        next_chapter = latest_downloaded + 1
        remaining_chapters = max_available - latest_downloaded
        
        if remaining_chapters > 0:
            print(f"🎯 Next chapter to download: {next_chapter}")
            print(f"📊 Remaining chapters available: {remaining_chapters}")
            if latest_volume and latest_volume > 1:
                print(f"💡 Tip: Download all {remaining_chapters} chapters to get the complete story up to Vol. {latest_volume}")
        else:
            print(f"✅ You have all available chapters!")
            if latest_volume and latest_volume > 1:
                print(f"🎉 You're caught up through Vol. {latest_volume}!")
            return 0
    
    while True:
        try:
            if min_available and max_available:
                max_suggestion = min(remaining_chapters, 1000)
                if remaining_chapters <= 1000:
                    prompt = f"\n📚 How many chapters do you want to download? (1-{remaining_chapters} for all): "
                else:
                    prompt = f"\n📚 How many chapters do you want to download? (1-{max_suggestion}, or {remaining_chapters} for all): "
            else:
                prompt = "\n📚 How many chapters do you want to download? (1-1000): "
            
            chapters = input(prompt).strip()
            chapters_num = int(chapters)
            
            # Validate based on available info
            if min_available and max_available:
                if chapters_num > remaining_chapters:
                    print(f"❌ Only {remaining_chapters} chapters remain. Please enter a smaller number.")
                    continue
                elif chapters_num < 1:
                    print("❌ Please enter a positive number")
                    continue
            else:
                if not (1 <= chapters_num <= 1000):
                    print("❌ Please enter a number between 1 and 1000")
                    continue
            
            # Show what the user will get
            if min_available and max_available and latest_volume:
                final_chapter = latest_downloaded + chapters_num
                if chapters_num == remaining_chapters:
                    print(f"✅ Will download {chapters_num} chapters (complete through Vol. {latest_volume})")
                else:
                    print(f"✅ Will download {chapters_num} chapters (up to chapter {final_chapter})")
            else:
                print(f"✅ Will download {chapters_num} chapters")
            
            return chapters_num
            
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
    """Scrape chapters from KatReadingCafe with multi-volume support"""
    print("🔍 KatReadingCafe: Checking available volumes and chapters...")
    
    # Navigate to series page
    driver.get(series_url)
    time.sleep(3)
    
    # Detect the latest volume from "New Chapter" elements (this is typically already visible)
    latest_volume_from_new_chapter = None
    new_chapter_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'New Chapter')]")
    
    if new_chapter_elements:
        print(f"Found {len(new_chapter_elements)} 'New Chapter' elements")
        for elem in new_chapter_elements:
            try:
                next_sibling = driver.execute_script("return arguments[0].nextElementSibling;", elem)
                if next_sibling:
                    sibling_text = next_sibling.text
                    vol_match = re.search(r'Vol\.\s*(\d+)', sibling_text)
                    if vol_match:
                        latest_volume_from_new_chapter = int(vol_match.group(1))
                        print(f"✅ Latest Vol. {latest_volume_from_new_chapter} detected from 'New Chapter' sibling (should be already visible)!")
                        break
            except:
                continue
    
    # Find all available volume buttons
    all_volumes = []
    vol_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Vol.')]")
    for elem in vol_elements:
        vol_text = elem.text.strip()
        vol_match = re.search(r'Vol\.\s*(\d+)', vol_text)
        if vol_match:
            vol_num = int(vol_match.group(1))
            all_volumes.append(vol_num)
    
    all_volumes = sorted(list(set(all_volumes)))
    if all_volumes:
        print(f"📚 Available volumes: {all_volumes}")
        if latest_volume_from_new_chapter:
            print(f"🎯 Vol. {latest_volume_from_new_chapter} is the latest (from 'New Chapter'), should be already visible")
    
    # Collect all chapters from all necessary volumes
    all_chapters = {}  # {chapter_num: (url, volume)}
    
    for vol_num in all_volumes:
        vol_selector = f"//span[text()='Vol. {vol_num}']"
        
        # Skip expanding if this is the latest volume (it's always already expanded on page load)
        if latest_volume_from_new_chapter and vol_num == latest_volume_from_new_chapter:
            print(f"⏩ Skipping Vol. {vol_num} expansion (latest volume, always already expanded on page load)")
        else:
            # Expand older volumes since they are collapsed by default
            try:
                vol_element = driver.find_element(By.XPATH, vol_selector)
                print(f"🔍 Expanding Vol. {vol_num} (older volume, needs to be expanded)...")
                driver.execute_script("arguments[0].scrollIntoView(true);", vol_element)
                time.sleep(1)
                vol_element.click()
                time.sleep(3)
            except Exception as e:
                print(f"❌ Could not expand Vol. {vol_num}: {e}")
                continue
        
        # Collect chapter links for this volume (whether it was already visible or just expanded)
        try:
            links = driver.find_elements(By.TAG_NAME, "a")
            vol_chapters = 0
            
            for a in links:
                txt = a.text.strip()
                # Match patterns like "Vol. 1 Ch. 1" or "Vol. 2 Ch. 15"
                m = re.match(rf'Vol\.\s*{vol_num}\s*Ch\.\s*(\d+)', txt)
                if m:
                    chapter_num = int(m.group(1))
                    chapter_url = a.get_attribute("href")
                    if chapter_url:
                        all_chapters[chapter_num] = (chapter_url, vol_num)
                        vol_chapters += 1
            
            print(f"📋 Vol. {vol_num}: Found {vol_chapters} chapters")
            
        except Exception as e:
            print(f"❌ Could not collect chapters from Vol. {vol_num}: {e}")
            continue
    
    # Sort chapters by number
    sorted_chapters = sorted(all_chapters.keys())
    if sorted_chapters:
        print(f"📊 Total chapters available: {len(sorted_chapters)} (Ch. {sorted_chapters[0]} - Ch. {sorted_chapters[-1]})")
    
    # Download the requested chapters
    downloaded = 0
    
    for chapter_num in sorted_chapters:
        if chapter_num < start or chapter_num > end or downloaded >= chapters_per_run:
            continue
        
        chapter_url, volume = all_chapters[chapter_num]
        print(f"🌐 Loading Chapter {chapter_num} (Vol. {volume}) -> {chapter_url}")
        
        try:
            driver.get(chapter_url)
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
                print(f"❌ Could not extract content for chapter {chapter_num}")
                continue
            
            if save_chapter(title, content, chapter_num, output_dir):
                downloaded += 1
                print(f"✅ Downloaded Chapter {chapter_num} from Vol. {volume}")
            
        except Exception as e:
            print(f"❌ Error downloading chapter {chapter_num}: {e}")
            continue
    
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
            print(f"💡 This might mean:")
            print(f"   - Chapter {target_chapter} doesn't exist yet")
            print(f"   - We've reached the end of available chapters")
            print(f"   - The chapter numbering might be different")
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
    consecutive_failures = 0
    max_consecutive_failures = 2  # Stop after 2 consecutive failures

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
            consecutive_failures = 0  # Reset failure counter on success
            print(f"✅ Successfully downloaded chapter {current_chapter}")
            current_chapter += 1
        else:
            consecutive_failures += 1
            print(f"❌ Failed to download chapter {current_chapter}")
            print(f"⚠️ Consecutive failures: {consecutive_failures}/{max_consecutive_failures}")
            
            if consecutive_failures >= max_consecutive_failures:
                print(f"🛑 Stopping after {max_consecutive_failures} consecutive failures")
                print(f"📝 This usually means we've reached the end of available chapters")
                # Play notification sound for early stop
                play_notification_sound(success=True if downloaded > 0 else False)
                break
            
            # Try next chapter
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
    
    # Create the novel-specific output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get latest chapter already downloaded
    latest = get_latest_chapter(output_dir)
    print(f"\n📁 Found {latest} existing chapters in {output_dir}")
    
    # Check available chapters on the website
    min_available, max_available, latest_volume = get_available_chapters_info(series_url, website_type)
    
    # Ask how many chapters to download with context
    chapters_per_run = ask_chapters_to_download(latest, min_available, max_available, latest_volume)
    if not chapters_per_run:
        print("❌ No chapters specified. Exiting...")
        return

    try:
        # Get latest chapter and calculate range
        start = latest + 1
        end = latest + chapters_per_run

        print(f"\n🚀 Will download chapters {start} to {end}")

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
            play_notification_sound(success=True)
        elif downloaded == 0:
            print("❌ No chapters were downloaded. Check for errors above.")
            play_notification_sound(success=False)
        else:
            print(f"📊 Downloaded {downloaded} out of {chapters_per_run} requested chapters.")
            play_notification_sound(success=True)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Goodbye!")


if __name__ == "__main__":
    main()
