import os
import re
import asyncio
import logging
import random
from typing import Optional, TYPE_CHECKING, List, Dict, Any

if TYPE_CHECKING:
    from playwright.async_api import Page, BrowserContext, Locator

from .exceptions import ScrapingError, BrowserError, AuthenticationError, ValidationError
from .auth import check_login_status, perform_login, validate_credentials
from .client import Icon, Icons8URLs, Icons8Client

logger = logging.getLogger(__name__)


# Default configuration
DEFAULT_SIZE = 256
BROWSER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.browser_data')

# Validation constants
VALID_SIZES = [16, 24, 32, 48, 64, 96, 128, 256, 512]

# Modern User-Agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
]


def validate_size(size: int) -> None:
    if not isinstance(size, int):
        raise ValidationError(
            f"Size must be an integer, got {type(size).__name__}",
            field_name="size"
        )
    
    if size not in VALID_SIZES:
        raise ValidationError(
            f"Invalid size: {size}. Valid sizes are: {VALID_SIZES}",
            field_name="size"
        )


async def launch_browser(headless: bool = True) -> tuple["BrowserContext", any]:
    try:
        from playwright.async_api import async_playwright
    except ImportError as e:
        raise BrowserError(
            "Playwright is not installed. Install it with:\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium",
            original_error=e
        )
    
    os.makedirs(BROWSER_DATA_DIR, exist_ok=True)
    mode_str = "headless" if headless else "visible"
    logger.info(f"Launching browser ({mode_str})...")
    print(f"  🌐 Launching browser ({mode_str})...")
    
    p = await async_playwright().start()
    
    # Handle User-Agent persistence for stable sessions
    ua_path = os.path.join(BROWSER_DATA_DIR, 'user_agent.txt')
    if os.path.exists(ua_path):
        try:
            with open(ua_path, 'r') as f:
                user_agent = f.read().strip()
            logger.debug(f"Loaded saved User-Agent: {user_agent[:30]}...")
        except Exception:
            user_agent = random.choice(USER_AGENTS)
    else:
        user_agent = random.choice(USER_AGENTS)
        try:
            with open(ua_path, 'w') as f:
                f.write(user_agent)
            logger.debug(f"Generated and saved new User-Agent: {user_agent[:30]}...")
        except Exception as e:
            logger.warning(f"Failed to save User-Agent: {e}")

    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--exclude-switches=enable-automation",
        "--no-sandbox",
        "--disable-setuid-sandbox"
    ]
    
    # Try Chrome first, fall back to Chromium
    try:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            headless=headless,
            channel="chrome",
            args=args,
            user_agent=user_agent,
            viewport={"width": 1280, "height": 800} # Standard viewport
        )
        logger.debug("Using Chrome browser")
    except Exception as chrome_error:
        logger.debug(f"Chrome not available: {chrome_error}")
        print(f"  ℹ Chrome not available, using Chromium...")
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_DATA_DIR,
                headless=headless,
                args=args,
                user_agent=user_agent,
                viewport={"width": 1280, "height": 800}
            )
        except Exception as chromium_error:
            await p.stop()
            raise BrowserError(
                "Failed to launch browser. Ensure Playwright browsers are installed: "
                "Run 'python -m playwright install chromium'",
                browser_type="chromium",
                original_error=chromium_error
            )
            
    # Apply advanced stealth scripts to every page
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        // Mock plugins to look like real Chrome
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3] 
        });
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """)
    
    return context, p


async def human_click(page: "Page", selector: str) -> bool:
    """
    Performs a human-like click sequence on an element:
    Hover -> Jitter -> Pause -> Mousedown -> Pause -> Mouseup -> Click.
    """
    try:
        locator = page.locator(selector).first
        if not await locator.is_visible():
            return False
            
        box = await locator.bounding_box()
        if not box:
            return False
            
        # Target a random point within the element
        x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
        y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
        
        await page.mouse.move(x, y, steps=random.randint(5, 15))
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        await page.mouse.down()
        await asyncio.sleep(random.uniform(0.05, 0.15)) # Hold click briefly
        await page.mouse.up()
        
        return True
    except Exception as e:
        logger.debug(f"Human click failed for {selector}: {e}")
        return False


async def human_scroll(page: "Page", max_scrolls: int = 100) -> int:
    """
    Scrolls the page like a human to trigger lazy loading and avoid bot detection.
    Mimics 'better_scalper' behavior: smooth scrolling, random delays, mouse movement.
    """
    logger.debug("Starting human-like scrolling...")
    print("  📜 Scrolling to load content (Human-like behavior)...")
    
    last_height = await page.evaluate("document.body.scrollHeight")
    stable_count_checks = 0
    MAX_STABLE_CHECKS = 4
    
    # Initial random mouse move to wake things up
    try:
        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
    except Exception:
        pass

    for i in range(max_scrolls):
        # 10% chance to scroll UP slightly (mimic reading/checking)
        if random.random() < 0.1:
             up_amount = random.randint(100, 300)
             await page.evaluate(f"window.scrollBy({{top: -{up_amount}, behavior: 'smooth'}})")
             await asyncio.sleep(random.uniform(0.5, 1.0))

        # Random scroll amount (mimics a mouse wheel scroll or page down)
        scroll_amount = random.randint(400, 900)
        
        # Smooth scroll using window.scrollBy
        await page.evaluate(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}})")
        
        # Random wait to let content load (0.5s to 1.5s)
        # Randomness is key to 'better_scalper' stealth
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Occasional mouse movement to simulate user reading/scanning
        if random.random() > 0.6:
            try:
                x = random.randint(50, 1000)
                y = random.randint(100, 800)
                await page.mouse.move(x, y, steps=5)
            except Exception:
                pass
        
        # Check if height changed
        new_height = await page.evaluate("document.body.scrollHeight")
        
        if new_height == last_height:
            stable_count_checks += 1
            if stable_count_checks >= MAX_STABLE_CHECKS:
                logger.info(f"Page height stable at {new_height}px after {i+1} scrolls.")
                break
        else:
            stable_count_checks = 0
            last_height = new_height
            
        if (i + 1) % 5 == 0:
            logger.debug(f"Scroll {i+1}: Height {new_height}px")
            
    return last_height


async def extract_icons_robust(page: "Page", size: int) -> list[Icon]:
    """
    Robustly extracts icons, filtering for the main collection grid to avoid sidebar noise.
    """
    logger.info("Extracting icons using robust heuristic...")
    
    # Execute JS to find candidates
    raw_images = await page.evaluate('''() => {
        // Try to find the main grid container first
        const grid = document.querySelector('.app-collection-view, .collection-grid, main') || document.body;
        
        const images = Array.from(grid.querySelectorAll('img'));
        return images.map(img => {
            const rect = img.getBoundingClientRect();
            // Check if inside a known icon container class
            const isIconContainer = img.closest('.app-grid-icon') !== null || 
                                  img.closest('.collection-icon') !== null;
            
            return {
                src: img.getAttribute('src'),
                srcset: img.getAttribute('srcset'),
                alt: img.getAttribute('alt'),
                width: rect.width,
                height: rect.height,
                top: rect.top,
                isIconContainer: isIconContainer,
                isVisible: rect.width > 20 && rect.height > 20 && rect.top >= 0
            };
        });
    }''')
    
    icons = []
    seen_ids: set[str] = set()
    
    # Heuristic: Filter images. 
    # If we found items with isIconContainer=True, prefer those.
    has_explicit_containers = any(img['isIconContainer'] for img in raw_images)
    
    for img in raw_images:
        if not img['isVisible']:
            continue
            
        # If we found explicit containers, ignore random images that aren't inside one
        if has_explicit_containers and not img['isIconContainer']:
            continue
            
        src = img['src'] or ''
        srcset = img['srcset'] or ''
        
        if 'icons8.com' not in src and 'icons8.com' not in srcset:
            continue
            
        combined_url = src + srcset
        id_match = re.search(r'[?&]id=([A-Za-z0-9_-]+)', combined_url)
        
        if not id_match:
            id_match = re.search(r'/icon/([A-Za-z0-9_-]+)/', combined_url)
            
        if id_match:
            icon_id = id_match.group(1)
            
            # Filter out common UI icons by ID if known, or rely on container
            if icon_id not in seen_ids:
                seen_ids.add(icon_id)
                
                raw_name = img['alt'] or f'icon_{icon_id}'
                name = raw_name.replace(' icon', '').strip()
                if not name:
                    name = f'icon-{icon_id}'
                
                icons.append(Icon(
                    id=icon_id,
                    name=name,
                    url=Icons8URLs.build_icon_url(icon_id, size, fmt="png")
                ))
                logger.debug(f"Found: {name} (ID: {icon_id})")
    
    logger.info(f"Robust extraction found {len(icons)} icons")
    return icons


async def extract_icons_via_regex(page: "Page", size: int) -> list[Icon]:
    logger.debug("Trying regex extraction from page content...")
    content = await page.content()
    
    id_matches = re.findall(
        r'img\.icons8\.com/?\?[^"\'>\s]*id=([A-Za-z0-9_-]+)[^"\'>\s]*', 
        content
    )
    logger.debug(f"Found {len(id_matches)} icon IDs via regex")
    
    icons = []
    seen_ids: set[str] = set()
    
    for icon_id in id_matches:
        if icon_id not in seen_ids:
            seen_ids.add(icon_id)
            icons.append(Icon(
                id=icon_id,
                name=f'icon-{icon_id}',
                url=Icons8URLs.build_icon_url(icon_id, size, fmt="svg")
            ))
    
    if icons:
        logger.info(f"Extracted {len(icons)} icons via regex")
    
    return icons


async def download_files_via_browser(
    icons: List[Icon], 
    output_dir: Any, # Path
    headless: bool = True
) -> List[str]:
    """
    Downloads files by navigating the browser directly to the resource URL.
    This mimics a user opening the image in a new tab, bypassing most API protections.
    """
    from pathlib import Path
    output_dir = Path(output_dir)
    
    logger.info(f"Starting browser navigation download for {len(icons)} items...")
    print(f"  📥 Downloading {len(icons)} icons via browser navigation...")
    
    context, playwright_instance = await launch_browser(headless)
    successful_paths = []
    
    try:
        # We process one by one to avoid overwhelming the browser/network
        for i, icon in enumerate(icons, 1):
            name = icon.name
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_') or f"icon_{i}"
            file_path = output_dir / f"{safe_name}.png"
            
            print(f"  [{i}/{len(icons)}] {name}...", end=" ", flush=True)
            
            page = None
            try:
                page = await context.new_page()
                
                # Random delay
                await asyncio.sleep(random.uniform(1.0, 2.5))
                
                # Navigate directly to the image URL
                response = await page.goto(icon.url, wait_until="commit", timeout=30000)
                
                if response and response.ok:
                    # Get the body of the response (the file content)
                    content = await response.body()
                    
                    # PNG Signature check
                    if content.startswith(b'\x89PNG'):
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        successful_paths.append(str(file_path))
                        print("✓")
                    else:
                        print("✗ (Not a valid PNG)")
                        logger.warning(f"Invalid PNG content for {name}")
                else:
                    status = response.status if response else "No Response"
                    print(f"✗ ({status})")
                    logger.warning(f"Failed to load {name}: {status}")
                    
            except Exception as e:
                print(f"✗ ({type(e).__name__})")
                logger.error(f"Error downloading {name}: {e}")
            finally:
                if page:
                    await page.close()
                
    finally:
        await context.close()
        await playwright_instance.stop()
        
    return successful_paths


async def scrape_collection(
    url: str,
    size: int = DEFAULT_SIZE,
    email: Optional[str] = None,
    password: Optional[str] = None,
    headless: bool = True
) -> list[Icon]:
    # Validate inputs using centralized client validation
    Icons8Client.validate_collection_url_static(url)
    validate_size(size)
    validate_credentials(email, password)
    
    context, playwright_instance = await launch_browser(headless)
    
    try:
        page = await context.new_page()
        
        logger.info(f"Opening collection page: {url}")
        print(f"  🔗 Opening collection page...")
        
        # Human-like: Random delay before navigation
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        response = await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        if response is None or not response.ok:
            raise ScrapingError(
                f"Failed to load collection page. Status: {response.status if response else 'No response'}"
            )
        
        # Human-like: Random wait after load
        await asyncio.sleep(random.uniform(2.0, 4.0))
        
        # Check login status
        is_logged_in = await check_login_status(page)
        logger.debug(f"Icons already visible: {is_logged_in}")
        
        if is_logged_in:
            logger.info("Already logged in - skipping login process")
            print("  ✓ Already logged in!")
        elif email and password:
            logger.info("Not logged in - attempting login...")
            print("  🔐 Logging in...")
            await perform_login(page, email, password)
            
            logger.debug("Reloading collection page...")
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(3.0, 5.0))
            
            # Verify login worked
            if not await check_login_status(page):
                raise AuthenticationError(
                    "Login appeared to succeed but icons are still not visible. "
                    "Please verify your credentials are correct."
                )
            
            logger.info("Login completed!")
            print("  ✓ Login successful!")
        else:
            raise AuthenticationError(
                "No icons visible and no credentials provided. "
                "Please provide --email and --password arguments or configure your credentials via environment variables."
            )
        
        logger.debug("Loading collection page...")
        
        # Human-like: Move mouse to center
        try:
            await page.mouse.move(500, 400, steps=10)
        except Exception:
            pass

        # Scroll to load all icons (Human-like)
        await human_scroll(page)
        
        # Extract icons
        print("  🔍 Extracting icons...")
        icons = await extract_icons_robust(page, size)
        
        # Fallback to regex if DOM extraction failed
        if not icons:
            icons = await extract_icons_via_regex(page, size)
        
        logger.info(f"Total unique icons found: {len(icons)}")
        
        if not icons:
            raise ScrapingError(
                "No icons found in the collection. "
                "The page structure may have changed or the collection may be empty."
            )
        
        # Capture session data for download
        cookies = await context.cookies()
        user_agent = await page.evaluate("navigator.userAgent")
        
        return icons, cookies, user_agent
        
    finally:
        await context.close()
        await playwright_instance.stop()


def get_collection_icons(
    url: str,
    size: int = DEFAULT_SIZE,
    email: Optional[str] = None,
    password: Optional[str] = None,
    headless: bool = True
) -> list[Icon]:
    # Returns only icons for backward compatibility
    icons, _, _ = asyncio.run(scrape_collection(url, size, email, password, headless))
    return icons
