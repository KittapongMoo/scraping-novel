"""
Local Novel Scraper Application with GUI
"""

import os
import re
import time
import random
import glob
import traceback
import json
import sys
import threading
import subprocess
import datetime
from typing import Optional, Tuple, List, Dict, Set
from tkinter import Tk, Frame, Label, Button, Entry, Text, Scrollbar, StringVar, OptionMenu, messagebox, filedialog, Listbox, BooleanVar, Checkbutton, Spinbox
from tkinter.ttk import Progressbar, Style
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AppConfig:
    """Application configuration"""
    def __init__(self):
        self.URLS_FILE = "novel_urls.txt"  # Use original txt file
        self.BASE_OUTPUT_DIR = os.path.join(os.getcwd(), "chapters")  # Use chapters folder
        
        # Create chapters directory if it doesn't exist
        os.makedirs(self.BASE_OUTPUT_DIR, exist_ok=True)
        print(f"Output directory set to: {self.BASE_OUTPUT_DIR}")
        
        self.VOICE_ENABLED = False
        self.VOICE_RATE = 180
        self.USE_GREETING = True
        self.CHROME_PROFILE_PATH = None
        self.window_width = 800
        self.window_height = 600
        self.theme = "light"  # or "dark"

    def save(self):
        """Save configuration to file"""
        config = {
            "VOICE_ENABLED": self.VOICE_ENABLED,
            "VOICE_RATE": self.VOICE_RATE,
            "USE_GREETING": self.USE_GREETING,
            "CHROME_PROFILE_PATH": self.CHROME_PROFILE_PATH,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "theme": self.theme
        }
        with open(os.path.join(os.path.dirname(__file__), "config.json"), "w") as f:
            json.dump(config, f)

    def load(self):
        """Load configuration from file"""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                self.VOICE_ENABLED = config.get("VOICE_ENABLED", False)
                self.VOICE_RATE = config.get("VOICE_RATE", 180)
                self.USE_GREETING = config.get("USE_GREETING", True)
                self.CHROME_PROFILE_PATH = config.get("CHROME_PROFILE_PATH")
                self.window_width = config.get("window_width", 800)
                self.window_height = config.get("window_height", 600)
                self.theme = config.get("theme", "light")


class TextToSpeechEngine:
    """Handles text-to-speech functionality with multiple fallback methods"""
    
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.available = self._check_tts_availability() if enabled else False
        
    def _check_tts_availability(self) -> bool:
        """Check if any TTS engine is available"""
        try:
            import win32com.client
            return True
        except ImportError:
            try:
                import pyttsx3
                return True
            except ImportError:
                return False
    
    def speak(self, message: str) -> bool:
        """Speak the given message using available TTS engines"""
        if not self.enabled or not self.available:
            print(f"🔊 Voice disabled. Message: {message}")
            return False
            
        # Try Windows SAPI first
        if self._try_sapi(message):
            return True
            
        # Fallback to pyttsx3
        if self._try_pyttsx3(message):
            return True
            
        # Final fallback to PowerShell TTS
        if self._try_powershell_tts(message):
            return True
            
        print(f"🔊 Could not speak message: {message}")
        return False
    
    def _try_sapi(self, message: str) -> bool:
        """Try using Windows SAPI voice"""
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Try to set a pleasant voice
            voices = speaker.GetVoices()
            for voice in voices:
                voice_name = voice.GetDescription().lower()
                if any(name in voice_name for name in ['zira', 'female', 'eva', 'aria']):
                    speaker.Voice = voice
                    break
            
            speaker.Rate = max(-2, min(2, (150 - 200) // 50))
            speaker.Speak(message)
            print(f"🔊 Spoken: {message}")
            return True
        except Exception:
            return False
    
    def _try_pyttsx3(self, message: str) -> bool:
        """Try using pyttsx3"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            
            voices = engine.getProperty('voices')
            if voices:
                for voice in voices:
                    if any(name in voice.name.lower() for name in ['female', 'zira', 'eva', 'aria']):
                        engine.setProperty('voice', voice.id)
                        break
            
            engine.setProperty('rate', 150)
            engine.say(message)
            engine.runAndWait()
            print(f"🔊 Spoken: {message}")
            return True
        except Exception:
            return False
    
    def _try_powershell_tts(self, message: str) -> bool:
        """Try using PowerShell TTS as final fallback"""
        try:
            ps_command = f'''
            Add-Type -AssemblyName System.Speech;
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
            $synth.Rate = {max(-10, min(10, (150 - 200) // 20))};
            $synth.Speak("{message}");
            '''
            subprocess.run(['powershell', '-Command', ps_command], 
                          capture_output=True, timeout=15)
            print(f"🔊 Spoken via PowerShell: {message}")
            return True
        except Exception:
            return False


class NotificationHandler:
    """Handles system notifications and voice announcements"""
    
    def __init__(self, voice_enabled=False, voice_rate=180, use_greeting=True):
        self.tts = TextToSpeechEngine(voice_enabled)
        self.voice_enabled = voice_enabled
        self.voice_rate = voice_rate
        self.use_greeting = use_greeting
        
    def notify_completion(self, downloaded: int, requested: int, success: bool = True):
        """Generate and announce completion message"""
        if success and downloaded > 0:
            if downloaded == requested:
                message = f"Download completed successfully! I have downloaded all {downloaded} chapters as requested."
            else:
                message = f"Download completed! I have downloaded {downloaded} out of {requested} requested chapters."
        elif downloaded == 0:
            message = "Download failed. No chapters were downloaded. Please check for errors."
        else:
            message = f"Download partially completed. I downloaded {downloaded} chapters, but some failed."
        
        self._play_sound(success)
        self._speak_with_greeting(message)
    
    def notify_progress(self, downloaded: int):
        """Announce progress update"""
        message = f"Progress update: I have successfully downloaded {downloaded} chapters so far."
        if self.voice_enabled:
            self.tts.speak(message)
    
    def _play_sound(self, success: bool):
        """Play appropriate sound notification"""
        try:
            import winsound
            if success:
                winsound.MessageBeep(winsound.MB_OK)
                for freq in [800, 1000, 1200]:
                    winsound.Beep(freq, 200)
            else:
                winsound.MessageBeep(winsound.MB_ICONHAND)
                winsound.Beep(400, 500)
        except Exception:
            print("\a")  # Terminal bell fallback
    
    def _speak_with_greeting(self, message: str):
        """Add time-based greeting to message if enabled"""
        if self.use_greeting:
            import datetime
            hour = datetime.datetime.now().hour
            if 5 <= hour < 12:
                greeting = "Good morning! "
            elif 12 <= hour < 17:
                greeting = "Good afternoon! "
            elif 17 <= hour < 21:
                greeting = "Good evening! "
            else:
                greeting = "Hello! "
            full_message = greeting + message
        else:
            full_message = message
        
        print(f"\n🎙️ Voice announcement: {full_message}")
        if self.voice_enabled:
            self.tts.speak(full_message)


class WebDriverManager:
    """Manages the creation and configuration of web drivers"""
    
    @staticmethod
    def create_driver() -> Optional[webdriver.Chrome]:
        """Create and configure a Chrome WebDriver"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.images": 2
        })

        try:
            print("🔧 Setting up Chrome driver...")
            driver = webdriver.Chrome(options=options)
            print("✅ Chrome driver initialized successfully!")
            return driver
        except Exception as e:
            print(f"❌ Failed to start ChromeDriver: {e}")
            print("💡 Solutions:")
            print("   1. Install webdriver-manager: pip install webdriver-manager")
            print("   2. Download chromedriver.exe and place it in this folder")
            print("   3. Add chromedriver to your system PATH")
            print("   4. Make sure Chrome browser is installed")
            return None


class NovelScraperBase:
    """Base class for novel scrapers with common functionality"""
    
    def __init__(self, notification_handler: NotificationHandler):
        self.notifier = notification_handler
    
    def _get_chapter_content(self, driver, chapter_num: int) -> Tuple[Optional[str], Optional[str]]:
        """Extract chapter title and content"""
        raise NotImplementedError
        
    def scrape_chapters(self, series_url: str, start: int, end: int, output_dir: str) -> int:
        """Scrape chapters between start and end (inclusive)"""
        raise NotImplementedError


class KatReadingCafeScraper(NovelScraperBase):
    """Scraper for KatReadingCafe website"""
    
    def _get_chapter_content(self, driver, chapter_num: int) -> Tuple[Optional[str], Optional[str]]:
        """Extract chapter title and content from KatReadingCafe"""
        title = driver.title.strip()
        content = ""
        
        # Try different content selectors
        selectors = ["div.entry-content", ".post-content", ".chapter-content", "article", ".content"]
        for sel in selectors:
            try:
                content = driver.find_element(By.CSS_SELECTOR, sel).text
                if content.strip():
                    return title, content
            except:
                continue
        
        return None, None
    
    def scrape_chapters(self, series_url: str, start: int, end: int, output_dir: str) -> int:
        """Scrape chapters from KatReadingCafe with multi-volume support"""
        print("🔍 KatReadingCafe: Checking available volumes and chapters...")
        
        driver = WebDriverManager.create_driver()
        if not driver:
            return 0
            
        wait = WebDriverWait(driver, 30)
        downloaded = 0
        
        try:
            # Navigate to series page
            driver.get(series_url)
            time.sleep(3)
            
            # Collect all chapters from all necessary volumes
            all_chapters = self._discover_chapters(driver)
            sorted_chapters = sorted(all_chapters.keys())
            
            if sorted_chapters:
                print(f"📊 Total chapters available: {len(sorted_chapters)} (Ch. {sorted_chapters[0]} - Ch. {sorted_chapters[-1]})")
                
                # Download the requested chapters
                for chapter_num in sorted_chapters:
                    if chapter_num < start or chapter_num > end:
                        continue
                        
                    if self._download_single_chapter(driver, chapter_num, all_chapters[chapter_num], output_dir):
                        downloaded += 1
            
            return downloaded
        
        except Exception as e:
            print(f"❌ Error during KatReadingCafe scraping: {e}")
            return downloaded
        finally:
            try:
                driver.quit()
                print("👋 Browser closed for KatReadingCafe!")
            except:
                pass
    
    def _discover_chapters(self, driver) -> Dict[int, Tuple[str, int]]:
        """Discover all available chapters with their URLs and volumes"""
        all_chapters = {}
        
        # Find all available volume buttons and expand them
        vol_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Vol.')]")
        all_volumes = self._extract_volumes(vol_elements)
        
        if all_volumes:
            print(f"📚 Available volumes: {all_volumes}")
            
            for vol_num in all_volumes:
                all_chapters.update(self._expand_volume(driver, vol_num))
        
        return all_chapters
    
    def _extract_volumes(self, vol_elements) -> List[int]:
        """Extract volume numbers from volume elements"""
        volumes = set()
        for elem in vol_elements:
            vol_text = elem.text.strip()
            vol_match = re.search(r'Vol\.\s*(\d+)', vol_text)
            if vol_match:
                volumes.add(int(vol_match.group(1)))
        return sorted(volumes)
    
    def _expand_volume(self, driver, vol_num: int) -> Dict[int, Tuple[str, int]]:
        """Expand a volume and collect its chapters"""
        volume_chapters = {}
        vol_selector = f"//span[text()='Vol. {vol_num}']"
        
        try:
            vol_element = driver.find_element(By.XPATH, vol_selector)
            print(f"🔍 Expanding Vol. {vol_num}...")
            driver.execute_script("arguments[0].scrollIntoView(true);", vol_element)
            time.sleep(1)
            vol_element.click()
            time.sleep(3)
            
            # Collect chapter links for this volume
            links = driver.find_elements(By.TAG_NAME, "a")
            for a in links:
                txt = a.text.strip()
                m = re.match(rf'Vol\.\s*{vol_num}\s*Ch\.\s*(\d+)', txt)
                if m:
                    chapter_num = int(m.group(1))
                    chapter_url = a.get_attribute("href")
                    if chapter_url:
                        volume_chapters[chapter_num] = (chapter_url, vol_num)
            
            print(f"📋 Vol. {vol_num}: Found {len(volume_chapters)} chapters")
            
        except Exception as e:
            print(f"❌ Could not expand Vol. {vol_num}: {e}")
        
        return volume_chapters
    
    def _download_single_chapter(self, driver, chapter_num: int, chapter_data: Tuple[str, int], output_dir: str) -> bool:
        """Download and save a single chapter"""
        chapter_url, volume = chapter_data
        print(f"🌐 Loading Chapter {chapter_num} (Vol. {volume}) -> {chapter_url}")
        
        try:
            driver.get(chapter_url)
            time.sleep(2)
            
            title, content = self._get_chapter_content(driver, chapter_num)
            if not content:
                print(f"❌ Could not extract content for chapter {chapter_num}")
                return False
            
            return self._save_chapter(title, content, chapter_num, output_dir)
            
        except Exception as e:
            print(f"❌ Error downloading chapter {chapter_num}: {e}")
            return False
    
    def _save_chapter(self, title: str, content: str, chapter_num: int, output_dir: str) -> bool:
        """Save chapter to file"""
        safe_title = self._sanitize_filename(title)
        filename = os.path.join(output_dir, f"{chapter_num:03d}_{safe_title}.txt")
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(title + "\n\n" + content)
            print(f"✅ Saved chapter {chapter_num} as '{filename}'")
            return True
        except OSError:
            # Fallback filename
            filename = os.path.join(output_dir, f"{chapter_num:03d}_Chapter_{chapter_num}.txt")
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(title + "\n\n" + content)
                print(f"✅ Saved chapter {chapter_num} (fallback filename)")
                return True
            except Exception as e:
                print(f"❌ Failed to save chapter {chapter_num}: {e}")
                return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing invalid characters and truncating"""
        safe_name = re.sub(r'[<>:"/\\|?*#]', '', filename)
        safe_name = re.sub(r'\s+', ' ', safe_name).strip()
        return safe_name[:80] + "..." if len(safe_name) > 80 else safe_name


class NovelBinScraper(NovelScraperBase):
    """Scraper for NovelBin website"""
    
    def scrape_chapters(self, series_url: str, start: int, end: int, output_dir: str) -> int:
        """Download multiple chapters from NovelBin with fresh browser for each chapter"""
        print(f"🔍 NovelBin: Will download chapters {start} to {end}...")
        
        downloaded = 0
        current_chapter = start
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while current_chapter <= end and consecutive_failures < max_consecutive_failures:
            if self._download_single_chapter(series_url, current_chapter, output_dir):
                downloaded += 1
                consecutive_failures = 0
                
                # Announce progress every 10 chapters
                if downloaded % 10 == 0:
                    self.notifier.notify_progress(downloaded)
            else:
                consecutive_failures += 1
            
            current_chapter += 1
        
        if consecutive_failures >= max_consecutive_failures:
            print(f"🛑 Stopping after {max_consecutive_failures} consecutive failures")
        
        return downloaded
    
    def _download_single_chapter(self, series_url: str, chapter_num: int, output_dir: str) -> bool:
        """Download a single chapter using a fresh browser instance"""
        driver = WebDriverManager.create_driver()
        if not driver:
            return False
            
        try:
            print(f"\n{'='*50}")
            print(f"📚 Downloading chapter {chapter_num}")
            print(f"{'='*50}")
            
            # Navigate to chapter page
            if not self._navigate_to_chapter(driver, series_url, chapter_num):
                return False
            
            # Extract content
            title, content = self._get_chapter_content(driver, chapter_num)
            if not content:
                return False
            
            # Save chapter
            return self._save_chapter(title, content, chapter_num, output_dir)
            
        except Exception as e:
            print(f"❌ Error processing chapter {chapter_num}: {e}")
            traceback.print_exc()
            return False
        finally:
            try:
                driver.quit()
            except:
                pass
    
    def _navigate_to_chapter(self, driver, series_url: str, target_chapter: int) -> bool:
        """Navigate to the target chapter page"""
        chapters_list_url = series_url.rstrip('/') + "#tab-chapters-title"
        print(f"📋 Loading chapter list: {chapters_list_url}")
        
        # Navigate to chapter list
        driver.get(chapters_list_url)
        time.sleep(random.uniform(3, 6))
        
        # Activate chapter tab if needed
        self._activate_chapter_tab(driver)
        
        # Find target chapter URL
        chapter_url = self._find_chapter_url(driver, target_chapter)
        if not chapter_url:
            print(f"❌ Chapter {target_chapter} URL not found")
            return False
        
        print(f"🌐 Found Chapter {target_chapter}: {chapter_url}")
        driver.get(chapter_url)
        time.sleep(random.uniform(3, 6))
        
        return True
    
    def _activate_chapter_tab(self, driver):
        """Activate the chapter tab if not already active"""
        try:
            chapter_tab = driver.find_element(By.CSS_SELECTOR, "#tab-chapters-title")
            if not chapter_tab.get_attribute("aria-expanded") == "true":
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth'});", chapter_tab)
                time.sleep(random.uniform(1, 2))
                chapter_tab.click()
                time.sleep(random.uniform(2, 4))
        except:
            pass
    
    def _find_chapter_url(self, driver, target_chapter: int) -> Optional[str]:
        """Find the URL for the target chapter number"""
        # First try to find directly in loaded links
        chapter_url = self._find_in_visible_links(driver, target_chapter)
        if chapter_url:
            return chapter_url
            
        # If not found, try systematic loading
        return self._find_with_scrolling(driver, target_chapter)
    
    def _find_in_visible_links(self, driver, target_chapter: int) -> Optional[str]:
        """Check currently visible links for the target chapter"""
        all_chapter_links = self._get_current_chapter_links(driver)
        for link in all_chapter_links:
            try:
                href = link.get_attribute("href")
                if not href:
                    continue
                    
                chapter_num = self._extract_chapter_number(href)
                if chapter_num == target_chapter:
                    return href
            except:
                continue
        return None
    
    def _find_with_scrolling(self, driver, target_chapter: int) -> Optional[str]:
        """Systematically scroll to find the target chapter"""
        print(f"📜 Performing systematic search for chapter {target_chapter}...")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        found_chapters = set()
        last_count = 0
        stable_iterations = 0
        max_stable = 4
        chapter_url = None
        
        for iteration in range(25):
            # Adaptive scrolling strategy
            scroll_amount = self._calculate_scroll_amount(iteration)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(2, 4))
            
            # Check current chapters
            current_links = self._get_current_chapter_links(driver)
            current_count = len(current_links)
            
            # Check for our target chapter
            for link in current_links:
                href = link.get_attribute("href")
                if not href:
                    continue
                    
                chapter_num = self._extract_chapter_number(href)
                if chapter_num:
                    found_chapters.add(chapter_num)
                    if chapter_num == target_chapter:
                        chapter_url = href
                        print(f"✅ Found target chapter {target_chapter}")
                        return chapter_url
            
            # Stability check
            if current_count == last_count:
                stable_iterations += 1
                if stable_iterations >= max_stable:
                    print("📝 Chapter count stabilized")
                    break
            else:
                stable_iterations = 0
                
            last_count = current_count
            
            # Check if we've reached the bottom
            scroll_height = driver.execute_script("return document.body.scrollHeight;")
            current_scroll = driver.execute_script("return window.pageYOffset;")
            window_height = driver.execute_script("return window.innerHeight;")
            
            if current_scroll + window_height >= scroll_height - 100:
                print("📝 Reached bottom of page")
                break
        
        return chapter_url
    
    def _calculate_scroll_amount(self, iteration: int) -> int:
        """Calculate appropriate scroll amount based on iteration"""
        if iteration < 5:
            return 200 + (iteration * 50)
        elif iteration < 15:
            return 600 + (iteration * 100)
        else:
            return random.randint(1000, 1500)
    
    def _get_current_chapter_links(self, driver):
        """Get all currently visible chapter links"""
        link_selectors = [
            "//a[contains(@href, '/chapter-')]",
            "//a[contains(@class, 'chapter')]",
            ".chapter-item a",
            ".list-chapter a",
            "a[href*='chapter']"
        ]
        
        for selector in link_selectors:
            try:
                if selector.startswith("//"):
                    links = driver.find_elements(By.XPATH, selector)
                else:
                    links = driver.find_elements(By.CSS_SELECTOR, selector)
                if links:
                    return links
            except:
                continue
        return []
    
    def _extract_chapter_number(self, href: str) -> Optional[int]:
        """Extract chapter number from URL"""
        patterns = [
            r'chapter-(\d+)',
            r'ch-(\d+)',
            r'chapter/(\d+)',
            r'c(\d+)',
            r'chap-(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, href)
            if match:
                return int(match.group(1))
        return None
    
    def _get_chapter_content(self, driver, chapter_num: int) -> Tuple[Optional[str], Optional[str]]:
        """Extract chapter title and content"""
        title = driver.title.strip()
        if not title or "404" in title or "not found" in title.lower():
            print(f"❌ Chapter page seems invalid (title: {title})")
            return None, None
        
        # Try multiple content selectors
        content_selectors = [
            ".chr-c", ".chapter-content", ".content", 
            "#chr-content", ".reading-content", "article",
            ".chapter-body", ".chapter-text", ".text-left",
            "#chapter-content", ".entry-content", ".post-content"
        ]
        
        for sel in content_selectors:
            try:
                content_element = driver.find_element(By.CSS_SELECTOR, sel)
                content = content_element.text.strip()
                if len(content) > 100:
                    print(f"✅ Found content using selector: {sel}")
                    return title, content
            except:
                continue
        
        # Fallback methods if no selector worked
        return self._fallback_content_extraction(driver, title, chapter_num)
    
    def _fallback_content_extraction(self, driver, title: str, chapter_num: int) -> Tuple[Optional[str], Optional[str]]:
        """Try alternative methods to extract content when selectors fail"""
        content = ""
        
        # Method 1: Extract from paragraphs
        try:
            all_paragraphs = driver.find_elements(By.TAG_NAME, "p")
            paragraph_texts = [p.text.strip() for p in all_paragraphs if len(p.text.strip()) > 50]
            if paragraph_texts:
                content = "\n\n".join(paragraph_texts)
                print("✅ Extracted content from paragraphs")
                return title, content
        except:
            pass
        
        # Method 2: Extract from main content area
        try:
            main_content = driver.find_element(By.TAG_NAME, "main")
            content = main_content.text.strip()
            if len(content) > 100:
                print("✅ Extracted content from main tag")
                return title, content
        except:
            pass
        
        print(f"❌ Could not extract sufficient content for chapter {chapter_num}")
        return None, None
    
    def _save_chapter(self, title: str, content: str, chapter_num: int, output_dir: str) -> bool:
        """Save chapter to file with fallback naming"""
        if not title:
            title = f"Chapter {chapter_num}"
            
        safe_title = self._sanitize_filename(title)
        filename = os.path.join(output_dir, f"{chapter_num:03d}_{safe_title}.txt")
        
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
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename removing special characters"""
        safe_name = re.sub(r'[<>:"/\\|?*#]', '', filename)
        safe_name = re.sub(r'\s+', ' ', safe_name).strip()
        return safe_name[:80] + "..." if len(safe_name) > 80 else safe_name


class ApplicationWindow(Tk):
    """Main application window"""
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.title("Novel Scraper")
        self.geometry(f"{config.window_width}x{config.window_height}")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # UI Styling
        self.bg_color = "#f0f0f0" if config.theme == "light" else "#333333"
        self.text_bg = "#ffffff" if config.theme == "light" else "#444444"
        self.text_fg = "#000000" if config.theme == "light" else "#ffffff"
        self.button_bg = "#e0e0e0" if config.theme == "light" else "#555555"
        
        # Configure progress bar styling
        self.style = Style()
        self.style.theme_use('clam')  # Use a modern theme
        
        # Custom progress bar style
        self.style.configure("Enhanced.Horizontal.TProgressbar",
                           troughcolor=self.bg_color,
                           background='#4CAF50',  # Green progress color
                           lightcolor='#81C784',
                           darkcolor='#388E3C',
                           borderwidth=1,
                           relief='solid')
        
        self.configure(bg=self.bg_color)
        
        # Application variables
        self.scraping = False
        self.current_task = None
        self.current_novel = None
        self.novels = []  # Initialize novels list
        
        # Initialize notification handler and scrapers
        self.notification_handler = NotificationHandler(
            voice_enabled=config.VOICE_ENABLED,
            voice_rate=config.VOICE_RATE,
            use_greeting=config.USE_GREETING
        )
        self.scrapers = {
            "katreadingcafe": KatReadingCafeScraper(self.notification_handler),
            "novelbin": NovelBinScraper(self.notification_handler),
            "other": NovelBinScraper(self.notification_handler)  # Default fallback
        }
        
        # Initialize UI
        self.create_widgets()
        
    def create_widgets(self):
        """Create and arrange all UI components"""
        # Main frame
        main_frame = Frame(self, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Novel selection
        novel_frame = Frame(main_frame, bg=self.bg_color)
        novel_frame.pack(fill="x", pady=(0, 10))
        
        Label(novel_frame, text="Select Novel:", bg=self.bg_color).pack(side="left", padx=(0, 5))
        
        self.novel_var = StringVar()
        self.novel_dropdown = OptionMenu(novel_frame, self.novel_var, "")
        self.novel_dropdown.config(bg=self.button_bg)
        self.novel_dropdown.pack(side="left", fill="x", expand=True)
        
        Button(novel_frame, text="Edit Novel URLs", command=self.manage_novels, 
               bg=self.button_bg).pack(side="left", padx=(5, 0))
        
        # Chapter selection
        chapter_frame = Frame(main_frame, bg=self.bg_color)
        chapter_frame.pack(fill="x", pady=(0, 10))
        
        Label(chapter_frame, text="Chapters to Download:", bg=self.bg_color).pack(side="left", padx=(0, 5))
        
        self.chapter_entry = Entry(chapter_frame)
        self.chapter_entry.pack(side="left", fill="x", expand=True)
        
        # Progress section
        progress_section = Frame(main_frame, bg=self.bg_color)
        progress_section.pack(fill="x", pady=(0, 10))
        
        # Progress label
        self.progress_label = Label(progress_section, text="Ready to start...", bg=self.bg_color, fg=self.text_fg)
        self.progress_label.pack(anchor="w", pady=(0, 2))
        
        # Progress bar with styling
        self.progress = Progressbar(progress_section, orient="horizontal", mode="determinate", 
                                   length=300, style="Enhanced.Horizontal.TProgressbar")
        self.progress.pack(fill="x")
        
        # Progress percentage label
        self.progress_percent = Label(progress_section, text="0%", bg=self.bg_color, fg=self.text_fg, font=("Arial", 9))
        self.progress_percent.pack(anchor="e", pady=(2, 0))
        
        # Log output
        log_frame = Frame(main_frame, bg=self.bg_color)
        log_frame.pack(fill="both", expand=True)
        
        scrollbar = Scrollbar(log_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.log_text = Text(log_frame, yscrollcommand=scrollbar.set, wrap="word", 
                            bg=self.text_bg, fg=self.text_fg)
        self.log_text.pack(fill="both", expand=True)
        
        scrollbar.config(command=self.log_text.yview)
        
        # Action buttons
        button_frame = Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill="x", pady=(10, 0))
        
        Button(button_frame, text="Start", command=self.start_scraping, 
               bg=self.button_bg).pack(side="left", padx=(0, 5))
        Button(button_frame, text="Stop", command=self.stop_scraping, 
               bg=self.button_bg).pack(side="left", padx=(0, 5))
        Button(button_frame, text="Check Chapters", command=self.check_chapters, 
               bg=self.button_bg).pack(side="left", padx=(0, 5))
        Button(button_frame, text="Settings", command=self.open_settings, 
               bg=self.button_bg).pack(side="left", padx=(0, 5))
        Button(button_frame, text="Open Output Folder", command=self.open_output_folder, 
               bg=self.button_bg).pack(side="right")
        
        # Load initial data
        self.load_novels()
        
    def load_novels(self):
        """Load novels from the URLs file"""
        if not os.path.exists(self.config.URLS_FILE):
            self.novels = []  # Initialize empty list
            self.novel_var.set("No novels found")
            return
            
        with open(self.config.URLS_FILE, "r", encoding="utf-8") as f:
            try:
                # Read URLs from text file format
                lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
                self.novels = []
                
                for line in lines:
                    # Parse line format: "name|url|type" or just "url"
                    parts = line.split('|')
                    if len(parts) >= 3:
                        name, url, novel_type = parts[0], parts[1], parts[2]
                    elif len(parts) == 2:
                        name, url = parts[0], parts[1]
                        novel_type = self._detect_website_type(url)
                    else:
                        url = parts[0]
                        name = self._extract_novel_name_from_url(url)
                        novel_type = self._detect_website_type(url)
                    
                    self.novels.append({
                        "name": name,
                        "url": url,
                        "type": novel_type,
                        "output_dir": os.path.join(self.config.BASE_OUTPUT_DIR, self._get_novel_folder_name(url))
                    })
                
                self.novel_dropdown["menu"].delete(0, "end")
                
                if not self.novels:
                    self.novel_var.set("No novels found")
                    return
                
                for novel in self.novels:
                    self.novel_dropdown["menu"].add_command(
                        label=novel["name"], 
                        command=lambda v=novel: self.novel_var.set(v["name"])
                    )
                
                self.novel_var.set(self.novels[0]["name"])
            except Exception as e:
                self.novels = []  # Initialize empty list on error
                self.log(f"Error loading novels: {str(e)}")
                self.novel_var.set("Invalid data")
    
    def _detect_website_type(self, url: str) -> str:
        """Detect which website type based on URL"""
        if "katreadingcafe.com" in url:
            return "katreadingcafe"
        elif "novelbin.me" in url:
            return "novelbin"
        else:
            return "other"
    
    def _extract_novel_name_from_url(self, url: str) -> str:
        """Extract novel name from URL"""
        if "katreadingcafe.com" in url:
            return url.split('/')[-2].replace('-', ' ').title()
        elif "novelbin.me" in url:
            return url.split('/')[-1].replace('-', ' ').title()
        else:
            return url.split('/')[-1].replace('-', ' ').title()
    
    def _get_novel_folder_name(self, url: str) -> str:
        """Extract novel name from URL and create a safe folder name"""
        novel_name = url.rstrip('/').split('/')[-1]
        return re.sub(r'[<>:"/\\|?*]', '', novel_name)
    
    def manage_novels(self):
        """Open novel_urls.txt file for editing and monitor for changes"""
        # Ensure the file exists
        if not os.path.exists(self.config.URLS_FILE):
            self._create_sample_urls_file()
        
        # Show instructions to user
        instructions = (
            "The novel URLs file will now open in your default text editor.\n\n"
            "File format (one novel per line):\n"
            "Name|URL|Type\n\n"
            "Supported types: katreadingcafe, novelbin, other\n\n"
            "Example:\n"
            "Civil Servant|https://katreadingcafe.com/manga/civil-servant-in-romance-fantasy/|katreadingcafe\n\n"
            "Save the file when done, and the novel list will automatically update!"
        )
        
        messagebox.showinfo("Edit Novel URLs", instructions)
        
        # Get the initial modification time
        initial_mtime = os.path.getmtime(self.config.URLS_FILE)
        
        # Open the file with the default text editor
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.config.URLS_FILE)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', self.config.URLS_FILE])
            else:  # Linux
                subprocess.run(['xdg-open', self.config.URLS_FILE])
            
            self.log(f"📝 Opened {self.config.URLS_FILE} for editing")
            self.log("💡 Tip: Save the file and the novel list will automatically update!")
            
            # Start monitoring the file for changes
            self._start_file_monitoring(initial_mtime)
            
        except Exception as e:
            self.log(f"❌ Could not open file: {str(e)}")
            messagebox.showerror("Error", f"Could not open file for editing: {str(e)}")
            # Fallback: show file location
            messagebox.showinfo("File Location", f"Please manually open this file:\n{os.path.abspath(self.config.URLS_FILE)}")
    
    def _create_sample_urls_file(self):
        """Create a sample URLs file if it doesn't exist"""
        sample_content = """# Novel URLs Configuration File
# Format: Name|URL|Type
# Supported types: katreadingcafe, novelbin, other
# 
# Examples:
# Civil Servant in Romance Fantasy|https://katreadingcafe.com/manga/civil-servant-in-romance-fantasy/|katreadingcafe
# My Novel|https://novelbin.me/novel/my-novel|novelbin
#
# Add your novel URLs below (remove the # to uncomment):

"""
        with open(self.config.URLS_FILE, 'w', encoding='utf-8') as f:
            f.write(sample_content)
    
    def _start_file_monitoring(self, initial_mtime):
        """Start monitoring the URLs file for changes"""
        def check_file_changes():
            nonlocal initial_mtime  # Move this to the beginning
            try:
                if os.path.exists(self.config.URLS_FILE):
                    current_mtime = os.path.getmtime(self.config.URLS_FILE)
                    if current_mtime != initial_mtime:
                        self.log("🔄 URLs file changed, reloading novels...")
                        self.load_novels()
                        self.log("✅ Novel list updated!")
                        
                        # Show notification
                        if self.config.VOICE_ENABLED:
                            self.notification_handler._speak_with_greeting("Novel list has been updated from file changes.")
                        
                        # Update the modification time for next check
                        initial_mtime = current_mtime
                        return  # Stop monitoring after first change
                        
                # Continue monitoring
                self.after(1000, check_file_changes)  # Check every second
                
            except Exception as e:
                self.log(f"⚠️ Error monitoring file: {str(e)}")
        
        # Start monitoring after a short delay
        self.after(2000, check_file_changes)
    
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self, self.config)
        self.wait_window(dialog)
    
    def check_chapters(self):
        """Check available chapters on website vs downloaded chapters"""
        if not hasattr(self, 'novels') or not self.novels:
            messagebox.showerror("Error", "No novels available. Please add novels first.")
            return
            
        selected_novel = next((n for n in self.novels if n["name"] == self.novel_var.get()), None)
        if not selected_novel:
            messagebox.showerror("Error", "No novel selected")
            return
        
        self.log(f"🔍 Checking chapters for {selected_novel['name']}...")
        
        # Show indeterminate progress for chapter checking
        self.set_progress_indeterminate("Checking available chapters...")
        
        # Start checking in separate thread to avoid blocking UI
        threading.Thread(
            target=self._check_chapters_thread,
            args=(selected_novel,),
            daemon=True
        ).start()
    
    def _check_chapters_thread(self, novel: dict):
        """Check chapters in separate thread"""
        try:
            # Get local chapters
            output_dir = novel.get("output_dir", os.path.join(self.config.BASE_OUTPUT_DIR, novel["name"].replace(" ", "_")))
            latest_downloaded = self._get_latest_chapter(output_dir)
            
            self.log(f"📁 Local chapters: {latest_downloaded} chapters downloaded")
            
            # Get available chapters from website
            website_type = novel.get("type", "other").lower()
            min_available, max_available, latest_volume = self._get_available_chapters_info(novel['url'], website_type)
            
            if min_available is not None and max_available is not None:
                total_available = max_available - min_available + 1
                
                # Handle novels that start from Chapter 0
                if min_available == 0 and latest_downloaded == 0:
                    # Novel starts from Chapter 0 and user has no chapters downloaded
                    remaining_chapters = max_available + 1  # Include Chapter 0
                    next_chapter = 0
                    self.log(f"📝 Novel starts from Chapter 0")
                elif min_available == 0:
                    # Novel starts from Chapter 0, calculate remaining including Chapter 0
                    remaining_chapters = max_available - latest_downloaded
                    next_chapter = latest_downloaded + 1
                else:
                    # Standard case: novel starts from Chapter 1
                    remaining_chapters = max_available - latest_downloaded
                    next_chapter = latest_downloaded + 1
                
                self.log(f"🌐 Website chapters: {min_available} - {max_available} ({total_available} total)")
                self.log(f"📊 Status: {latest_downloaded}/{max_available} chapters downloaded")
                
                if remaining_chapters > 0:
                    self.log(f"📋 Next chapter to download: {next_chapter}")
                    self.log(f"📈 Remaining chapters: {remaining_chapters}")
                    
                    # Update chapter entry with suggested amount
                    def update_chapter_entry():
                        self.chapter_entry.delete(0, "end")
                        self.chapter_entry.insert(0, str(remaining_chapters))
                    
                    self.after(0, update_chapter_entry)
                    
                    if latest_volume and latest_volume > 1:
                        self.log(f"📖 Latest volume available: Vol. {latest_volume}")
                        
                    completion_message = f"Analysis complete! You have {latest_downloaded} chapters downloaded out of {max_available} available. {remaining_chapters} chapters remaining."
                    
                    # Special message for Chapter 0 novels
                    if min_available == 0 and latest_downloaded == 0:
                        completion_message += f" This novel starts from Chapter 0."
                        
                else:
                    self.log(f"✅ You have all available chapters! ({latest_downloaded}/{max_available})")
                    completion_message = f"Great! You're up to date with all {latest_downloaded} available chapters."
                    
                    def update_chapter_entry():
                        self.chapter_entry.delete(0, "end")
                        self.chapter_entry.insert(0, "0")
                    
                    self.after(0, update_chapter_entry)
                
                # Show completion dialog
                def show_completion():
                    messagebox.showinfo("Chapter Check Complete", completion_message)
                
                self.after(0, show_completion)
                
                # Voice announcement if enabled
                if self.config.VOICE_ENABLED:
                    if remaining_chapters > 0:
                        if min_available == 0 and latest_downloaded == 0:
                            voice_message = f"Chapter check complete. This novel starts from Chapter 0. You have {remaining_chapters} chapters available to download starting from Chapter 0."
                        else:
                            voice_message = f"Chapter check complete. You have {latest_downloaded} chapters downloaded and {remaining_chapters} chapters remaining to download."
                    else:
                        voice_message = f"Great news! You have all {latest_downloaded} available chapters downloaded. You're completely up to date."
                    
                    self.notification_handler._speak_with_greeting(voice_message)
                
                # Reset progress bar after successful completion
                self.after(0, lambda: self.set_progress_determinate())
                self.after(0, lambda: self.reset_progress("Chapter check completed"))
                
            else:
                self.log("❌ Could not retrieve chapter information from website")
                self.after(0, lambda: self.set_progress_determinate())
                self.after(0, lambda: self.reset_progress("Chapter check failed"))
                self.after(0, lambda: messagebox.showerror("Check Failed", "Could not retrieve chapter information from the website. Please check your internet connection and try again."))
                
        except Exception as e:
            error_message = f"Error during chapter check: {str(e)}"
            self.log(f"❌ {error_message}")
            self.after(0, lambda: self.set_progress_determinate())
            self.after(0, lambda: self.reset_progress("Error during chapter check"))
            self.after(0, lambda: messagebox.showerror("Check Error", error_message))
    
    def _get_available_chapters_info(self, series_url: str, website_type: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Get information about available chapters from the website using improved discovery logic"""
        self.log(f"🔍 Checking available chapters on {website_type}...")
        
        # Voice announcement for chapter discovery
        if self.config.VOICE_ENABLED:
            discovery_message = f"Starting chapter discovery for {website_type} website. This may take a moment."
            self.notification_handler._speak_with_greeting(discovery_message)
        
        driver = WebDriverManager.create_driver()
        if not driver:
            self.log("❌ Could not setup browser to check chapters")
            return None, None, None
        
        try:
            if website_type == "katreadingcafe":
                return self._get_katreadingcafe_chapters_improved(driver, series_url)
            elif website_type == "novelbin":
                return self._get_novelbin_chapters_improved(driver, series_url)
            else:
                self.log(f"❌ Unsupported website type: {website_type}")
                return None, None, None
                
        except Exception as e:
            self.log(f"❌ Error checking chapters: {e}")
            return None, None, None
        finally:
            try:
                driver.quit()
            except:
                pass
    
    def _get_katreadingcafe_chapters_improved(self, driver, series_url: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Get available chapters from KatReadingCafe using improved logic"""
        driver.get(series_url)
        time.sleep(3)
        
        # First, check what's the latest volume from "New Chapter" element
        latest_volume_from_new_chapter = None
        new_chapter_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'New Chapter')]")
        
        if new_chapter_elements:
            self.log(f"Found {len(new_chapter_elements)} 'New Chapter' elements")
            for elem in new_chapter_elements:
                try:
                    next_sibling = driver.execute_script("return arguments[0].nextElementSibling;", elem)
                    if next_sibling:
                        sibling_text = next_sibling.text
                        vol_match = re.search(r'Vol\.\s*(\d+)', sibling_text)
                        if vol_match:
                            latest_volume_from_new_chapter = int(vol_match.group(1))
                            self.log(f"✅ Latest Vol. {latest_volume_from_new_chapter} detected from 'New Chapter' sibling (should be already visible)!")
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
            self.log(f"📚 Available volumes: {all_volumes}")
            if latest_volume_from_new_chapter:
                self.log(f"🎯 Vol. {latest_volume_from_new_chapter} is the latest (from 'New Chapter'), should be already visible")
        
        # Collect chapters from all volumes
        available_chapters = []
        for vol_num in all_volumes:
            vol_selector = f"//span[text()='Vol. {vol_num}']"
            
            # Skip expanding if this is the latest volume (it's always already expanded on page load)
            if latest_volume_from_new_chapter and vol_num == latest_volume_from_new_chapter:
                self.log(f"⏩ Skipping Vol. {vol_num} expansion (latest volume, always already expanded on page load)")
            else:
                # Expand older volumes since they are collapsed by default
                try:
                    vol_element = driver.find_element(By.XPATH, vol_selector)
                    self.log(f"🔍 Expanding Vol. {vol_num} (older volume, needs to be expanded)...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", vol_element)
                    time.sleep(1)
                    vol_element.click()
                    time.sleep(3)
                except Exception as e:
                    self.log(f"❌ Could not expand Vol. {vol_num}: {e}")
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
                        available_chapters.append(chapter_num)
                        vol_chapters += 1
                
                self.log(f"📋 Vol. {vol_num}: Found {vol_chapters} chapters")
                
            except Exception as e:
                self.log(f"❌ Could not collect chapters from Vol. {vol_num}: {e}")
                continue
        
        # Return chapter range and latest volume
        if available_chapters:
            available_chapters = sorted(list(set(available_chapters)))
            min_chapter = min(available_chapters)
            max_chapter = max(available_chapters)
            self.log(f"✅ Found {len(available_chapters)} chapters (Ch. {min_chapter} - Ch. {max_chapter})")
            
            # Voice announcement for discovery results
            if self.config.VOICE_ENABLED:
                result_message = f"Chapter discovery complete. Found {len(available_chapters)} chapters from chapter {min_chapter} to {max_chapter}."
                self.notification_handler._speak_with_greeting(result_message)
            
            return min_chapter, max_chapter, latest_volume_from_new_chapter
        else:
            self.log("❌ No chapters found")
            if self.config.VOICE_ENABLED:
                self.notification_handler._speak_with_greeting("Chapter discovery failed. No chapters were found on this website.")
            return None, None, None
    
    def _get_novelbin_chapters_improved(self, driver, series_url: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Get available chapters from NovelBin using comprehensive discovery logic"""
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
        
        # Advanced chapter loading strategy for NovelBin
        self.log("📜 Loading all available chapters systematically...")
        
        def get_all_chapter_links():
            """Get all chapter links currently loaded on the page with multiple selectors"""
            chapters = set()
            
            # Try multiple selectors for maximum coverage
            selectors = [
                "//a[contains(@href, '/chapter-')]",
                "//a[contains(@href, 'chapter')]",
                ".chapter-item a",
                ".list-chapter a", 
                "a[href*='chapter']",
                ".chapter-list a",
                ".chapter-number",
                "[data-chapter]"
            ]
            
            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        elements = driver.find_elements(By.XPATH, selector)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        href = element.get_attribute("href")
                        if href and 'chapter' in href.lower():
                            # Try multiple patterns for chapter numbers
                            patterns = [
                                r'chapter-(\d+)',
                                r'ch-(\d+)',
                                r'chapter/(\d+)',
                                r'c(\d+)',
                                r'chap-(\d+)',
                                r'chapter(\d+)',
                                r'/(\d+)/?$'  # Numbers at end of URL
                            ]
                            
                            for pattern in patterns:
                                match = re.search(pattern, href)
                                if match:
                                    chapters.add(int(match.group(1)))
                                    break
                except:
                    continue
            
            return chapters
        
        # CRITICAL FIX: Try to navigate to chapter 0 and 1 first to force loading from beginning
        self.log("🎯 Attempting to force load early chapters by navigating to chapter 0 and 1...")
        chapter_0_or_1_found = False
        try:
            # Try common chapter 0 and 1 URL patterns (many novels start with chapter 0)
            base_url = series_url.rstrip('/')
            early_chapter_patterns = [
                f"{base_url}/chapter-0",    # Try chapter 0 first
                f"{base_url}/ch-0", 
                f"{base_url}/c0",
                f"{base_url}/chapter/0",
                f"{base_url}/chapter-1",    # Then try chapter 1
                f"{base_url}/ch-1", 
                f"{base_url}/c1",
                f"{base_url}/chapter/1"
            ]
            
            for pattern in early_chapter_patterns:
                try:
                    self.log(f"   Trying: {pattern}")
                    driver.get(pattern)
                    time.sleep(3)
                    
                    # Check if we got a valid chapter page
                    current_title = driver.title.lower()
                    current_url = driver.current_url.lower()
                    
                    if ("chapter" in current_title and "404" not in current_title and 
                        "not found" not in current_title and "chapter" in current_url):
                        chapter_num = "0" if "/chapter-0" in pattern or "/ch-0" in pattern or "/c0" in pattern or "/chapter/0" in pattern else "1"
                        self.log(f"✅ Successfully accessed chapter {chapter_num} via: {pattern}")
                        chapter_0_or_1_found = True
                        
                        # Now go back to chapter list with early chapters likely cached
                        driver.get(chapters_list_url)
                        time.sleep(4)
                        
                        # Reactivate chapter tab
                        try:
                            chapter_tab = driver.find_element(By.CSS_SELECTOR, "#tab-chapters-title")
                            if not chapter_tab.get_attribute("aria-expanded") == "true":
                                chapter_tab.click()
                                time.sleep(3)
                        except:
                            pass
                        break
                    else:
                        self.log(f"   ❌ Invalid response from {pattern}")
                except Exception as e:
                    self.log(f"   ❌ Failed {pattern}: {e}")
                    continue
            
            if not chapter_0_or_1_found:
                self.log("⚠️ Could not pre-load chapter 0 or 1, proceeding with standard discovery")
                # Go back to chapter list URL
                driver.get(chapters_list_url)
                time.sleep(3)
                
        except Exception as e:
            self.log(f"⚠️ Error during chapter 1 pre-load: {e}")
            # Ensure we're back on the chapter list page
            driver.get(chapters_list_url)
            time.sleep(3)
        
        # Start from the very top AFTER trying to load early chapters
        self.log("📍 Starting systematic chapter discovery from top...")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)
        
        # Track chapters found during scrolling
        all_found_chapters = set()
        last_count = 0
        stable_iterations = 0
        max_stable = 4  # Reduced for faster discovery
        
        # Get initial chapters that might be loaded
        initial_chapters = get_all_chapter_links()
        all_found_chapters.update(initial_chapters)
        self.log(f"🔍 Initial chapters loaded: {len(initial_chapters)}")
        if initial_chapters:
            sorted_initial = sorted(initial_chapters)
            self.log(f"   Range: {sorted_initial[0]} - {sorted_initial[-1]}")
            if 0 in initial_chapters:
                self.log("✅ Chapter 0 found in initial load!")
            elif 1 in initial_chapters:
                self.log("✅ Chapter 1 found in initial load!")
        
        # Progressive scrolling strategy optimized for early chapter discovery  
        self.log("📜 Progressive scrolling to discover all chapters...")
        
        for scroll_iteration in range(25):  # Reasonable limit
            # Smart scrolling: smaller increments early, larger later
            if scroll_iteration < 5:
                # Very small scrolls at the beginning to catch early chapters
                scroll_amount = 200 + (scroll_iteration * 50)
            elif scroll_iteration < 15:
                # Medium scrolls for middle content
                scroll_amount = 600 + (scroll_iteration * 100)
            else:
                # Larger scrolls for comprehensive coverage
                scroll_amount = random.randint(1000, 1500)
            
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(2.5, 4))  # Adequate wait for lazy loading
            
            # Get current chapters
            current_chapters = get_all_chapter_links()
            new_chapters = current_chapters - all_found_chapters
            all_found_chapters.update(current_chapters)
            
            current_count = len(all_found_chapters)
            self.log(f"📊 Iteration {scroll_iteration + 1}: {current_count} total chapters")
            
            if new_chapters:
                new_sorted = sorted(new_chapters)
                self.log(f"   New chapters: {new_sorted[:5]}{'...' if len(new_sorted) > 5 else ''}")
                # Reset stability counter when finding new chapters
                stable_iterations = 0
            else:
                stable_iterations += 1
            
            # Early termination if no new chapters for several iterations
            if stable_iterations >= max_stable:
                self.log(f"📝 Stable at {current_count} chapters for {max_stable} iterations")
                break
            
            # Check if we've reached the bottom
            scroll_height = driver.execute_script("return document.body.scrollHeight;")
            current_scroll = driver.execute_script("return window.pageYOffset;")
            window_height = driver.execute_script("return window.innerHeight;")
            
            if current_scroll + window_height >= scroll_height - 100:
                self.log("📝 Reached bottom of page")
                # Final wait and check
                time.sleep(3)
                final_chapters = get_all_chapter_links()
                all_found_chapters.update(final_chapters)
                break
        
        self.log(f"🎯 Total unique chapters discovered: {len(all_found_chapters)}")
        if all_found_chapters:
            min_found = min(all_found_chapters)
            max_found = max(all_found_chapters)
            self.log(f"📈 Chapter range: {min_found} - {max_found}")
            
            # Verify we got early chapters
            sorted_chapters = sorted(all_found_chapters)
            if 0 in all_found_chapters:
                self.log("✅ SUCCESS: Chapter 0 discovered! (Novel starts from Chapter 0)")
            elif 1 in all_found_chapters:
                self.log("✅ SUCCESS: Chapter 1 discovered! (Novel starts from Chapter 1)")
            else:
                self.log(f"⚠️ Early chapters not found. Earliest: {sorted_chapters[0] if sorted_chapters else 'None'}")
            
            # Show examples
            if len(sorted_chapters) >= 20:
                self.log(f"📋 First 10 chapters: {sorted_chapters[:10]}")
                self.log(f"📋 Last 10 chapters: {sorted_chapters[-10:]}")
            elif len(sorted_chapters) > 0:
                self.log(f"📋 All chapters found: {sorted_chapters}")
            
            # Voice announcement for discovery results
            if self.config.VOICE_ENABLED:
                result_message = f"Chapter discovery complete. Found {len(all_found_chapters)} chapters from chapter {min_found} to {max_found}."
                self.notification_handler._speak_with_greeting(result_message)
            
            return min_found, max_found, None
        else:
            self.log("❌ No chapters found")
            if self.config.VOICE_ENABLED:
                self.notification_handler._speak_with_greeting("Chapter discovery failed. No chapters were found on this website.")
            return None, None, None
    
    def _activate_novelbin_chapter_tab(self, driver):
        """Activate the NovelBin chapter tab if needed"""
        try:
            chapter_tab = driver.find_element(By.CSS_SELECTOR, "#tab-chapters-title")
            if not chapter_tab.get_attribute("aria-expanded") == "true":
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth'});", chapter_tab)
                time.sleep(random.uniform(1, 2))
                chapter_tab.click()
                time.sleep(random.uniform(2, 4))
        except:
            pass
    
    def _discover_novelbin_chapters(self, driver, series_url: str) -> Set[int]:
        """Discover all available chapters through systematic scrolling"""
        # Start from top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)
        
        found_chapters = set()
        last_count = 0
        stable_iterations = 0
        max_stable = 4
        
        self.log("📜 Performing systematic chapter discovery...")
        
        for iteration in range(25):
            # Adaptive scrolling
            scroll_amount = self._calculate_scroll_amount(iteration)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(2, 4))
            
            # Get current chapters
            current_chapters = self._get_current_novelbin_chapters(driver, series_url)
            new_chapters = current_chapters - found_chapters
            found_chapters.update(current_chapters)
            
            current_count = len(found_chapters)
            self.log(f"📊 Iteration {iteration + 1}: {current_count} total chapters")
            
            if new_chapters:
                new_sorted = sorted(new_chapters)
                self.log(f"   New chapters: {new_sorted[:5]}{'...' if len(new_sorted) > 5 else ''}")
                stable_iterations = 0
            else:
                stable_iterations += 1
                if stable_iterations >= max_stable:
                    self.log("📝 Chapter count stabilized")
                    break
            
            # Check if we've reached the bottom
            scroll_height = driver.execute_script("return document.body.scrollHeight;")
            current_scroll = driver.execute_script("return window.pageYOffset;")
            window_height = driver.execute_script("return window.innerHeight;")
            
            if current_scroll + window_height >= scroll_height - 100:
                self.log("📝 Reached bottom of page")
                break
        
        return found_chapters
    
    def _calculate_scroll_amount(self, iteration: int) -> int:
        """Calculate scroll amount based on iteration"""
        if iteration < 5:
            return 200 + (iteration * 50)
        elif iteration < 15:
            return 600 + (iteration * 100)
        else:
            return random.randint(1000, 1500)
    
    def _get_current_novelbin_chapters(self, driver, base_url: str) -> Set[int]:
        """Get chapter numbers from currently visible links"""
        all_chapters = set()
        
        # Try multiple selectors for chapter links
        link_selector_patterns = [
            ("//a[contains(@href, '/chapter-')]", r'chapter-(\d+)'),
            ("//a[contains(@href, '/ch-')]", r'ch-(\d+)'),
            ("//a[contains(@href, 'chapter')]", r'chapter/(\d+)'),
            ("//a[contains(@href, 'chapter')]", r'c(\d+)'),
            (".chapter-item a", r'chapter-(\d+)'),
            (".chapter-number", r'(\d+)')
        ]
        
        for selector, pattern in link_selector_patterns:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    href = element.get_attribute("href")
                    if not href:
                        continue
                    
                    match = re.search(pattern, href)
                    if match:
                        all_chapters.add(int(match.group(1)))
            except:
                continue
        
        return all_chapters
    
    def _get_latest_chapter(self, output_dir: str) -> int:
        """Get the latest chapter number from downloaded files"""
        if not os.path.exists(output_dir):
            return 0
        
        chapter_files = []
        for file in os.listdir(output_dir):
            if file.endswith('.txt'):
                # Extract chapter number from filename
                # Expected format: 000_Title.txt, 001_Title.txt, etc.
                match = re.match(r'^(\d+)_', file)
                if match:
                    chapter_files.append(int(match.group(1)))
        
        return max(chapter_files) if chapter_files else 0
    
    def start_scraping(self):
        """Start the scraping process"""
        if self.scraping:
            messagebox.showwarning("Warning", "Scraping is already in progress")
            return
            
        # Check if novels list exists and is not empty
        if not hasattr(self, 'novels') or not self.novels:
            messagebox.showerror("Error", "No novels available. Please add novels first.")
            return
            
        selected_novel = next((n for n in self.novels if n["name"] == self.novel_var.get()), None)
        if not selected_novel:
            messagebox.showerror("Error", "No novel selected")
            return
            
        try:
            chapters = int(self.chapter_entry.get())
            if chapters < 1:
                messagebox.showerror("Error", "Please enter a positive number")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
            return
        
        # Show initial progress
        self.update_progress(0, chapters, "Initializing download...")
            
        self.current_novel = selected_novel
        self.scraping = True
        self.log(f"Starting download for {selected_novel['name']}...")
        
        # Start the scraper in a separate thread
        self.current_task = threading.Thread(
            target=self.run_scraper,
            args=(selected_novel, chapters),
            daemon=True
        )
        self.current_task.start()
        
        # Start monitoring the scraper
        self.after(100, self.check_scraper_status)
    
    def stop_scraping(self):
        """Stop the scraping process"""
        if not self.scraping:
            messagebox.showinfo("Info", "No scraping in progress")
            return
            
        self.scraping = False
        self.log("Stopping scraper...")
    
    def run_scraper(self, novel: dict, chapters: int):
        """Run the scraper (in a separate thread)"""
        self.log(f"Setting up scraper for {novel['url']}...")
        
        try:
            # Create output directory for this novel
            output_dir = novel.get("output_dir", os.path.join(self.config.BASE_OUTPUT_DIR, novel["name"].replace(" ", "_")))
            os.makedirs(output_dir, exist_ok=True)
            
            # Get the latest downloaded chapter
            latest_downloaded = self._get_latest_chapter(output_dir)
            self.log(f"Latest downloaded chapter: {latest_downloaded}")
            
            # Calculate start and end chapters
            start_chapter = latest_downloaded + 1
            end_chapter = start_chapter + chapters - 1
            
            self.log(f"Will download chapters {start_chapter} to {end_chapter}")
            
            # Get the appropriate scraper
            website_type = novel.get("type", "other").lower()
            scraper = self.scrapers.get(website_type, self.scrapers["other"])
            
            self.log(f"Using {website_type} scraper")
            
            # Update notification handler settings
            self.notification_handler.voice_enabled = self.config.VOICE_ENABLED
            self.notification_handler.voice_rate = self.config.VOICE_RATE
            self.notification_handler.use_greeting = self.config.USE_GREETING
            
            # Track start time for progress estimation
            start_time = time.time()
            
            # Start scraping
            downloaded = 0
            for i in range(start_chapter, end_chapter + 1):
                if not self.scraping:
                    break
                    
                self.log(f"Attempting to download chapter {i}...")
                
                # Update progress with current status and time estimation
                self.after(0, lambda curr=downloaded, tot=chapters, ch=i, st=start_time: 
                          self.update_progress(curr, tot, f"Downloading Chapter {ch}", "Downloading", st))
                
                # Try to download single chapter
                if website_type == "katreadingcafe":
                    # For KatReadingCafe, we need to discover chapters first
                    chapter_downloaded = scraper.scrape_chapters(novel['url'], i, i, output_dir)
                else:
                    # For NovelBin and others, download individual chapters
                    chapter_downloaded = scraper._download_single_chapter(novel['url'], i, output_dir)
                    chapter_downloaded = 1 if chapter_downloaded else 0
                
                if chapter_downloaded > 0:
                    downloaded += chapter_downloaded
                    self.log(f"✅ Successfully downloaded chapter {i}")
                    
                    # Update progress with success status and time estimation
                    self.after(0, lambda curr=downloaded, tot=chapters, ch=i, st=start_time: 
                              self.update_progress(curr, tot, f"Chapter {ch} completed", "Downloading", st))
                    
                    # Announce progress every 10 chapters
                    if downloaded % 10 == 0:
                        self.notification_handler.notify_progress(downloaded)
                else:
                    self.log(f"❌ Failed to download chapter {i}")
                    # Update progress showing failure with time estimation
                    self.after(0, lambda curr=downloaded, tot=chapters, ch=i, st=start_time: 
                              self.update_progress(curr, tot, f"Chapter {ch} failed", "Downloading", st))
                
                # Add delay between chapters
                time.sleep(random.uniform(2, 4))
                
            if self.scraping:
                self.log(f"✅ Download completed! Successfully downloaded {downloaded} chapters.")
                self.notification_handler.notify_completion(downloaded, chapters, success=downloaded > 0)
                # Final progress update
                self.after(0, lambda: self.update_progress(downloaded, chapters, "Download completed!"))
            else:
                self.log("⏹️ Download stopped by user")
                self.after(0, lambda: self.reset_progress("Download stopped by user"))
                
            # Show completion message
            def show_completion():
                if downloaded > 0:
                    messagebox.showinfo("Download Complete", 
                                      f"Successfully downloaded {downloaded} chapters!\n"
                                      f"Saved to: {output_dir}")
                else:
                    messagebox.showwarning("Download Failed", 
                                         "No chapters were downloaded. Please check the logs for errors.")
            
            self.after(0, show_completion)
            
        except Exception as e:
            self.log(f"❌ Error during scraping: {str(e)}")
            traceback.print_exc()
            self.after(0, lambda: messagebox.showerror("Scraping Error", f"An error occurred: {str(e)}"))
            self.after(0, lambda: self.reset_progress("Error occurred during download"))
        
        finally:
            self.scraping = False
            self.after(0, lambda: self.reset_progress("Ready to start..."))
    
    def _get_latest_chapter(self, output_dir: str) -> int:
        """Get the latest chapter number from the output directory"""
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
    
    def update_progress(self, current: int, total: int, status: str = "", operation: str = "Downloading", start_time=None):
        """Update progress bar with detailed information and time estimation"""
        if total > 0:
            percentage = (current / total) * 100
            self.progress["value"] = percentage
            
            # Update percentage label
            self.progress_percent.config(text=f"{percentage:.1f}%")
            
            # Calculate time estimation if start time is provided and we have progress
            time_info = ""
            if start_time and current > 0:
                elapsed = time.time() - start_time
                avg_time_per_chapter = elapsed / current
                remaining_chapters = total - current
                estimated_remaining = remaining_chapters * avg_time_per_chapter
                
                if estimated_remaining > 60:
                    minutes = int(estimated_remaining // 60)
                    seconds = int(estimated_remaining % 60)
                    time_info = f" (Est. {minutes}m {seconds}s remaining)"
                else:
                    time_info = f" (Est. {int(estimated_remaining)}s remaining)"
            
            # Update progress label with detailed status
            if status:
                progress_text = f"{operation}: {current}/{total} chapters - {status}{time_info}"
            else:
                progress_text = f"{operation}: {current}/{total} chapters{time_info}"
            
            self.progress_label.config(text=progress_text)
        else:
            self.progress["value"] = 0
            self.progress_percent.config(text="0%")
            self.progress_label.config(text=status if status else "Ready to start...")
    
    def reset_progress(self, message: str = "Ready to start..."):
        """Reset progress bar to initial state"""
        self.progress["value"] = 0
        self.progress_percent.config(text="0%")
        self.progress_label.config(text=message)
    
    def set_progress_indeterminate(self, message: str = "Processing..."):
        """Set progress bar to indeterminate mode for unknown progress operations"""
        self.progress.config(mode="indeterminate")
        self.progress.start(10)  # Start animation
        self.progress_label.config(text=message)
        self.progress_percent.config(text="...")
    
    def set_progress_determinate(self):
        """Set progress bar back to determinate mode"""
        self.progress.stop()  # Stop animation
        self.progress.config(mode="determinate")
    
    def check_scraper_status(self):
        """Check and update scraper status"""
        if self.scraping:
            self.after(100, self.check_scraper_status)
    
    def log(self, message: str):
        """Add a message to the log"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
    
    def open_output_folder(self):
        """Open the output folder in file explorer"""
        output_dir = self.current_novel["output_dir"] if self.current_novel else self.config.BASE_OUTPUT_DIR
        if output_dir and os.path.exists(output_dir):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(output_dir)
                elif os.name == 'posix':  # macOS, Linux
                    subprocess.run(['open', output_dir] if sys.platform == 'darwin' 
                                  else ['xdg-open', output_dir])
            except Exception as e:
                self.log(f"Failed to open folder: {str(e)}")
        else:
            self.log(f"Output directory does not exist: {output_dir}")
    
    def on_close(self):
        """Handle window close event"""
        if self.scraping:
            if messagebox.askokcancel("Quit", "Scraping in progress. Are you sure you want to quit?"):
                self.scraping = False
                self.destroy()
        else:
            self.destroy()


class NovelManager(Tk):
    """Novel management dialog"""
    def __init__(self, parent, config: AppConfig):
        super().__init__()
        self.parent = parent
        self.config = config
        self.title("Manage Novels")
        self.geometry("600x400")
        
        # Load novels
        self.load_novels()
        
        # Create UI
        self.create_widgets()
    
    def load_novels(self):
        """Load novels from text file"""
        self.novels = []
        if os.path.exists(self.config.URLS_FILE):
            with open(self.config.URLS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Parse format: Name|URL|Type
                        parts = line.split("|")
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            url = parts[1].strip()
                            novel_type = parts[2].strip() if len(parts) > 2 else "other"
                            
                            # Create output directory path
                            safe_name = re.sub(r'[<>:"/\\|?*]', '_', name).replace(" ", "-").lower()
                            output_dir = os.path.join(self.config.BASE_OUTPUT_DIR, safe_name)
                            
                            self.novels.append({
                                "name": name,
                                "url": url,
                                "type": novel_type,
                                "output_dir": output_dir
                            })
    
    def save_novels(self):
        """Save novels to text file"""
        with open(self.config.URLS_FILE, "w", encoding="utf-8") as f:
            f.write("# Novel URLs\n")
            f.write("# Format: Name|URL|Type\n")
            f.write("# Supported types: katreadingcafe, novelbin, other\n\n")
            for novel in self.novels:
                f.write(f"{novel['name']}|{novel['url']}|{novel.get('type', 'other')}\n")
    
    def create_widgets(self):
        """Create UI widgets"""
        # Main frame
        main_frame = Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Novel list with scrollbar
        frame = Frame(main_frame)
        frame.pack(fill="both", expand=True, pady=(0, 10))
        
        scrollbar = Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        self.listbox = Listbox(frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        scrollbar.config(command=self.listbox.yview)
        
        # Populate list
        self.refresh_list()
        
        # Form fields for adding/editing
        form_frame = Frame(main_frame)
        form_frame.pack(fill="x", pady=(0, 10))
        
        Label(form_frame, text="Name:").grid(row=0, column=0, sticky="e", padx=(0, 5))
        self.name_entry = Entry(form_frame)
        self.name_entry.grid(row=0, column=1, sticky="we")
        
        Label(form_frame, text="URL:").grid(row=1, column=0, sticky="e", padx=(0, 5))
        self.url_entry = Entry(form_frame)
        self.url_entry.grid(row=1, column=1, sticky="we")
        
        Label(form_frame, text="Type:").grid(row=2, column=0, sticky="e", padx=(0, 5))
        self.type_var = StringVar(value="katreadingcafe")
        self.type_dropdown = OptionMenu(form_frame, self.type_var, "katreadingcafe", "novelbin", "other")
        self.type_dropdown.grid(row=2, column=1, sticky="we")
        
        form_frame.columnconfigure(1, weight=1)
        
        # Button controls
        button_frame = Frame(main_frame)
        button_frame.pack(fill="x")
        
        Button(button_frame, text="Add", command=self.add_novel).pack(side="left", padx=(0, 5))
        Button(button_frame, text="Update", command=self.update_novel).pack(side="left", padx=(0, 5))
        Button(button_frame, text="Remove", command=self.remove_novel).pack(side="left", padx=(0, 5))
        Button(button_frame, text="Close", command=self.destroy).pack(side="right")
    
    def refresh_list(self):
        """Refresh the novel list"""
        self.listbox.delete(0, "end")
        for novel in self.novels:
            self.listbox.insert("end", f"{novel['name']} - {novel['url']}")
    
    def on_select(self, event):
        """Handle listbox selection"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            novel = self.novels[index]
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, novel["name"])
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, novel["url"])
            self.type_var.set(novel["type"])
    
    def add_novel(self):
        """Add a new novel"""
        name = self.name_entry.get().strip()
        url = self.url_entry.get().strip()
        novel_type = self.type_var.get()
        
        if not name or not url or not novel_type:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        if any(n["name"].lower() == name.lower() for n in self.novels):
            messagebox.showerror("Error", "A novel with this name already exists")
            return
        
        # Create safe directory name
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name).replace(" ", "-").lower()
        output_dir = os.path.join(self.config.BASE_OUTPUT_DIR, safe_name)
            
        self.novels.append({
            "name": name,
            "url": url,
            "type": novel_type,
            "output_dir": output_dir
        })
        
        self.save_novels()
        self.refresh_list()
        self.name_entry.delete(0, "end")
        self.url_entry.delete(0, "end")
    
    def update_novel(self):
        """Update selected novel"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a novel")
            return
            
        name = self.name_entry.get().strip()
        url = self.url_entry.get().strip()
        novel_type = self.type_var.get()
        
        if not name or not url or not novel_type:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        index = selection[0]
        
        # Check for duplicate name (except for the selected novel)
        if any(i != index and n["name"].lower() == name.lower() for i, n in enumerate(self.novels)):
            messagebox.showerror("Error", "A novel with this name already exists")
            return
            
        self.novels[index] = {
            "name": name,
            "url": url,
            "type": novel_type,
            "output_dir": self.novels[index]["output_dir"]  # Keep existing output dir
        }
        
        self.save_novels()
        self.refresh_list()
    
    def remove_novel(self):
        """Remove selected novel"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a novel")
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to remove this novel?"):
            del self.novels[selection[0]]
            self.save_novels()
            self.refresh_list()


class SettingsDialog(Tk):
    """Settings dialog window"""
    def __init__(self, parent, config: AppConfig):
        super().__init__()
        self.parent = parent
        self.config = config
        self.title("Settings")
        self.geometry("400x300")
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create settings UI widgets"""
        main_frame = Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Output directory
        dir_frame = Frame(main_frame)
        dir_frame.pack(fill="x", pady=(0, 10))
        
        Label(dir_frame, text="Output Directory:").pack(side="left")
        self.dir_var = StringVar(value=self.config.BASE_OUTPUT_DIR)
        Entry(dir_frame, textvariable=self.dir_var).pack(side="left", fill="x", expand=True, padx=(5, 0))
        Button(dir_frame, text="Browse", command=self.select_directory).pack(side="left", padx=(5, 0))
        
        # Voice settings
        voice_frame = Frame(main_frame)
        voice_frame.pack(fill="x", pady=(0, 10))
        
        self.voice_var = BooleanVar(value=self.config.VOICE_ENABLED)
        Checkbutton(voice_frame, text="Enable Voice Notifications", variable=self.voice_var).pack(anchor="w")
        
        Label(voice_frame, text="Voice Speed:").pack(anchor="w", pady=(5, 0))
        self.rate_var = StringVar(value=str(self.config.VOICE_RATE))
        Spinbox(voice_frame, from_=50, to=300, textvariable=self.rate_var).pack(anchor="w")
        
        # Chrome settings
        chrome_frame = Frame(main_frame)
        chrome_frame.pack(fill="x", pady=(0, 10))
        
        Label(chrome_frame, text="Chrome Profile Path:").pack(anchor="w")
        self.chrome_var = StringVar(value=self.config.CHROME_PROFILE_PATH or "")
        Entry(chrome_frame, textvariable=self.chrome_var).pack(fill="x")
        Button(chrome_frame, text="Browse", command=self.select_chrome_profile).pack(anchor="e")
        
        # Theme selection
        theme_frame = Frame(main_frame)
        theme_frame.pack(fill="x", pady=(0, 10))
        
        Label(theme_frame, text="Theme:").pack(anchor="w")
        self.theme_var = StringVar(value=self.config.theme)
        OptionMenu(theme_frame, self.theme_var, "light", "dark").pack(anchor="w")
        
        # Buttons
        button_frame = Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        Button(button_frame, text="Save", command=self.save_settings).pack(side="left", padx=(0, 5))
        Button(button_frame, text="Cancel", command=self.destroy).pack(side="left")
    
    def select_directory(self):
        """Select output directory"""
        dir_path = filedialog.askdirectory(initialdir=self.config.BASE_OUTPUT_DIR)
        if dir_path:
            self.dir_var.set(dir_path)
    
    def select_chrome_profile(self):
        """Select Chrome profile directory"""
        dir_path = filedialog.askdirectory(title="Select Chrome Profile Directory")
        if dir_path:
            self.chrome_var.set(dir_path)
    
    def save_settings(self):
        """Save settings and close"""
        self.config.BASE_OUTPUT_DIR = self.dir_var.get()
        self.config.VOICE_ENABLED = self.voice_var.get()
        self.config.VOICE_RATE = int(self.rate_var.get())
        self.config.CHROME_PROFILE_PATH = self.chrome_var.get() or None
        self.config.theme = self.theme_var.get()
        
        # Update notification handler if parent has one
        if hasattr(self.parent, 'notification_handler'):
            self.parent.notification_handler.voice_enabled = self.config.VOICE_ENABLED
            self.parent.notification_handler.voice_rate = self.config.VOICE_RATE
        
        self.config.save()
        messagebox.showinfo("Info", "Settings saved successfully")
        self.destroy()


if __name__ == "__main__":
    config = AppConfig()
    config.load()
    
    app = ApplicationWindow(config)
    app.mainloop()