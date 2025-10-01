import chrome_version
from selenium.common.exceptions import MoveTargetOutOfBoundsException, WebDriverException
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from fake_useragent import UserAgent
from selenium.webdriver import ActionChains
import time
import random
import db



# Screen resolutions (common realistic sizes)
SCREEN_RESOLUTIONS = [
    (1920, 1080),
    (1366, 768),
    (1536, 864),
    (1440, 900),
    (1280, 720),
    (2560, 1440),
]

# Browser languages
LANGUAGES = [
    ['en-US', 'en'],
    ['en-GB', 'en'],
    ['en-CA', 'en'],
]

# WebGL vendors and renderers for realistic fingerprints
WEBGL_VENDORS = [
    "Google Inc.",
    "Intel Inc.",
    "NVIDIA Corporation",
    "ATI Technologies Inc.",
]

WEBGL_RENDERERS = [
    "Intel Iris OpenGL Engine",
    "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0)",
]



def get_chrome_version():
    try:
        # Get the Chrome version using the chrome_version module
        chrome_v = chrome_version.get_chrome_version()
        major_version = int(chrome_v.split('.')[0])
        return major_version
    except Exception as e:
        print(f"Error getting Chrome version: {e}")
        return None


def parse_proxy(proxy_string):
    """Parse proxy string into proper format"""
    if '://' in proxy_string:
        # Already in full format
        return proxy_string

    parts = proxy_string.split(':')
    if len(parts) == 2:
        # Format: IP:PORT
        return f'http://{proxy_string}'
    elif len(parts) == 4:
        # Format: IP:PORT:USER:PASS
        ip, port, user, password = parts
        return f'http://{user}:{password}@{ip}:{port}'
    else:
        raise ValueError(f"Invalid proxy format: {proxy_string}")


def create_undetectable_driver(proxy=None):
    """Create an undetected Chrome driver with maximum stealth"""

    # Initialize fake user agent
    ua = UserAgent()
    user_agent = ua.random

    # Randomize screen resolution
    width, height = random.choice(SCREEN_RESOLUTIONS)

    # Randomize language
    languages = random.choice(LANGUAGES)

    # Randomize WebGL fingerprint
    webgl_vendor = random.choice(WEBGL_VENDORS)
    webgl_renderer = random.choice(WEBGL_RENDERERS)

    # Create Chrome options
    options = uc.ChromeOptions()

    # Basic options
    options.add_argument(f'--window-size={width},{height}')
    options.add_argument(f'--lang={languages[0]}')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Set user agent
    options.add_argument(f'--user-agent={user_agent}')

    # ============= PROXY SETUP =============
    if proxy:
        proxy_to_use = random.choice(proxy) if isinstance(proxy, list) else proxy
        proxy_url = parse_proxy(proxy_to_use)
        options.add_argument(f'--proxy-server={proxy_url}')
        print(f"🔒 Using Proxy: {proxy_to_use.split(':')[0]}:****")

    # Set language preferences
    prefs = {
        'intl.accept_languages': ','.join(languages),
        'profile.default_content_setting_values.notifications': 2,  # Block notifications
    }
    options.add_experimental_option('prefs', prefs)

    print(f"✓ User Agent: {user_agent[:70]}...")
    print(f"✓ Resolution: {width}x{height}")
    print(f"✓ Language: {languages[0]}")
    print(f"✓ WebGL Vendor: {webgl_vendor}")

    chrome_version = get_chrome_version()
    if chrome_version:
        print(f"✓ Chrome Version: {chrome_version}")
    else:
        print("❌ Error getting Chrome version.")

    # Initialize undetected Chrome driver
    driver = uc.Chrome(options=options, version_main=chrome_version)

    print(f"✓ Opened undetectable browser successfully!")

    driver.set_window_size(width, height)
    driver.set_window_position(0, 0)

    print(f"✓ Size & Position set successfully!")

    # Apply selenium-stealth for additional masking
    stealth(driver,
            languages=languages,
            vendor=webgl_vendor,
            platform=random.choice(['Win32', 'MacIntel', 'Linux x86_64']),
            webgl_vendor=webgl_vendor,
            renderer=webgl_renderer,
            fix_hairline=True,
            )

    print(f"✓ Browser stealth mode enabled successfully!")

    # Additional fingerprint randomization
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': f'''
            // Randomize hardware concurrency (CPU cores)
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {random.choice([2, 4, 6, 8, 12, 16])}
            }});
            
            // Set realistic device memory
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {random.choice([4, 8, 16])}
            }});
            
            // Randomize screen properties
            Object.defineProperty(screen, 'availWidth', {{
                get: () => {width}
            }});
            Object.defineProperty(screen, 'availHeight', {{
                get: () => {height - random.randint(0, 100)}
            }});
            
            // Mock battery API
            navigator.getBattery = () => {{
                return Promise.resolve({{
                    charging: {str(random.choice([True, False])).lower()},
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: {random.uniform(0.2, 1.0):.2f}
                }});
            }};
        '''
    })
    print(f"✓ Browser initialized successfully!")
    return driver


def human_like_delay(min_seconds=1, max_seconds=3, worker=None):
    """Add random delays to mimic human behavior"""
    delay_time = random.uniform(min_seconds, max_seconds)
    if worker:
        start_time = time.time()
        while time.time() - start_time < delay_time:
            if not worker.is_running:
                return
            time.sleep(0.1)
    else:
        time.sleep(delay_time)


def random_mouse_movements(driver, max_size=500, steps_range=(5, 50), pause_range=(0.02, 0.1)):
    """
    Move the mouse inside a safe rectangular area within the visible viewport.
    - max_size: desired max dimension of safe area (kept <= viewport size)
    - steps_range, pause_range: control smoothness
    """
    body = driver.find_element("tag name", "body")

    # Prefer accurate viewport values from JS (window.innerWidth/innerHeight)
    vw, vh = driver.execute_script(
        "return [window.innerWidth, window.innerHeight];")
    # Ensure integer
    vw, vh = int(vw), int(vh)

    # Build a safe area that never exceeds the viewport
    safe_w = min(max_size, vw - 4)   # keep a small margin
    safe_h = min(max_size, vh - 4)

    if safe_w <= 10 or safe_h <= 10:
        # fallback to single-point no-op if viewport is extremely small
        return

    # choose a top-left corner for the safe box so it's fully inside viewport
    box_x0 = random.randint(2, vw - safe_w - 2) if vw - safe_w - 2 > 2 else 2
    box_y0 = random.randint(2, vh - safe_h - 2) if vh - safe_h - 2 > 2 else 2

    # pick start/end inside the safe box (leave small inner margin for realism)
    margin = 6
    x1 = random.randint(box_x0 + margin, box_x0 + safe_w - margin)
    y1 = random.randint(box_y0 + margin, box_y0 + safe_h - margin)
    x2 = random.randint(box_x0 + margin, box_x0 + safe_w - margin)
    y2 = random.randint(box_y0 + margin, box_y0 + safe_h - margin)

    steps = random.randint(*steps_range)

    print(
        f"Safe-area move from ({x1},{y1}) to ({x2},{y2}) in {steps} steps inside viewport {vw}x{vh} (safe box at {box_x0},{box_y0} size {safe_w}x{safe_h})")

    actions = ActionChains(driver)

    # initial move (wrap in try to avoid raising)
    try:
        actions.move_to_element_with_offset(body, x1, y1).perform()
    except (MoveTargetOutOfBoundsException, WebDriverException) as e:
        # if this unexpectedly fails, abort the movement safely
        print("⚠️ initial move failed, skipping movements:", e)
        return

    for i in range(steps):
        x = int(x1 + (x2 - x1) * (i / steps))
        y = int(y1 + (y2 - y1) * (i / steps))

        # Ensure still inside our safe box (extra clamp for safety)
        x = min(max(x, box_x0 + margin), box_x0 + safe_w - margin)
        y = min(max(y, box_y0 + margin), box_y0 + safe_h - margin)

        try:
            print(f"Moving to ({x},{y})")
            actions.move_to_element_with_offset(body, x, y).perform()
        except (MoveTargetOutOfBoundsException, WebDriverException) as e:
            # skip this step if browser refuses it (very defensive)
            print("⚠️ move skipped (out of bounds):", e)
            continue

        time.sleep(random.uniform(*pause_range))


def random_link_click(driver, worker=None):
    for i in range(3):
        if worker and not worker.is_running:
            break

        print(f"Attempt {i + 1} to click a link...")
        try:
            anchors = driver.find_elements(By.TAG_NAME, "a")

            good_links = [a for a in anchors if a.get_attribute("href") and "javascript" not in a.get_attribute("href")]

            if good_links:
                link = random.choice(good_links)
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth'});", link)
                time.sleep(random.uniform(0.5, 1.5))  # human-like pause
                link.click()
                print("✓ Link clicked successfully!")
                human_like_delay(2, 5, worker=worker)
                break
            else:
                print("No good links found")
        except Exception as e:
            print(f"⚠️  Link click skipped: {str(e)}")


def random_scroll(driver, worker=None):
    random_scroll_count = random.randint(5, 15)
    
    # Simulate human-like scrolling with variations
    try:
        scroll_height = driver.execute_script(
            "return document.body.scrollHeight")
        current_position = 0
        scroll_count = 0

        while current_position < scroll_height and scroll_count < random_scroll_count:
            if worker and not worker.is_running:
                break

            # Random scroll distance and direction
            scroll_by = random.randint(100, 400)

            # Sometimes scroll up a bit (humans do this)
            if random.random() < 0.2 and current_position > 300:
                scroll_by = -random.randint(50, 150)

            driver.execute_script(f"window.scrollBy(0, {scroll_by});")
            current_position += scroll_by
            scroll_count += 1

            # Variable scroll speed
            human_like_delay(0.3, 2.0, worker=worker)

        # Scroll back to top sometimes
        if random.random() < 0.3:
            human_like_delay(1, 2, worker=worker)
            driver.execute_script("window.scrollTo(0, 0);")

    except Exception as e:
        print(f"⚠️  Scrolling skipped: {str(e)}")


def visit_website(url, worker=None, proxy=None):
    """Visit a website with maximum stealth mode enabled"""

    print(f"\n🌐 Creating undetectable driver...")
    driver = create_undetectable_driver(proxy=proxy)
    print(f"✓ Undetectable driver created successfully!")

    try:
        if worker and not worker.is_running:
            return
            
        print(f"\n🌐 Navigating to {url}...")
        driver.get(url)

        # Random delay after loading
        human_like_delay(2, 5, worker=worker)

        if worker and not worker.is_running:
            return

        # Simulate mouse movements
        random_mouse_movements(driver)

        if worker and not worker.is_running:
            return
        
        random_scroll(driver, worker=worker)
        if worker and not worker.is_running:
            return

        random_link_click(driver, worker=worker)
        if worker and not worker.is_running:
            return

        random_scroll(driver, worker=worker)
        if worker and not worker.is_running:
            return

        random_link_click(driver, worker=worker)
        if worker and not worker.is_running:
            return

        print("✓ Page loaded successfully!")
        print(f"✓ Page title: {driver.title}")

        # Keep browser open for inspection (remove in production)
        # input("\n⏸️  Press Enter to close the browser...")

        db.add_visit(url)

    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")

    finally:
        try:
            driver.quit()
            print("✓ Browser closed")
        except Exception as e:
            print(f"❌ Error occurred while closing browser: {str(e)}")


def visit_multiple_sites(urls, delay_between_visits=(30, 120)):
    """Visit multiple sites with random delays between them"""
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"Visit {i}/{len(urls)}")
        print(f"{'='*60}")

        try:
            visit_website(url)
        except Exception as e:
            print(f"❌ Error occurred: {str(e)}")

        if i < len(urls):
            wait_time = random.randint(*delay_between_visits)
            print(f"\n⏳ Waiting {wait_time} seconds before next visit...")
            time.sleep(wait_time)


if __name__ == "__main__":
    print("🚀 Starting Ultra-Stealth Browser Automation")
    print("=" * 60)

    visit_website('http://quotes.toscrape.com/')
