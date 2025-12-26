import os
import re
import asyncio
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page, BrowserContext

from .exceptions import ScrapingError, BrowserError, AuthenticationError, ValidationError
from .auth import check_login_status, perform_login, validate_credentials
from .client import Icon, Icons8URLs, Icons8Client

logger = logging.getLogger(__name__)


# Default configuration
DEFAULT_SIZE = 256
BROWSER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.browser_data')

# Validation constants
VALID_SIZES = [16, 24, 32, 48, 64, 96, 128, 256, 512]


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
    
    # Try Chrome first, fall back to Chromium
    try:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            headless=headless,
            channel="chrome"
        )
        logger.debug("Using Chrome browser")
    except Exception as chrome_error:
        logger.debug(f"Chrome not available: {chrome_error}")
        print(f"  ℹ Chrome not available, using Chromium...")
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_DATA_DIR,
                headless=headless
            )
        except Exception as chromium_error:
            await p.stop()
            raise BrowserError(
                "Failed to launch browser. Ensure Playwright browsers are installed: "
                "Run 'python -m playwright install chromium'",
                browser_type="chromium",
                original_error=chromium_error
            )
    
    return context, p


async def scroll_to_load_icons(page: "Page", max_scrolls: int = 20) -> int:
    logger.debug("Scrolling to load icons...")
    print("  📜 Scrolling to load all icons...")
    prev_count = 0
    
    for i in range(max_scrolls):
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1.5)
        
        icon_count = await page.locator('div.app-grid-icon__image img').count()
        if icon_count == 0:
            icon_count = await page.locator('img[srcset*="icons8.com"]').count()
        
        logger.debug(f"Scroll {i + 1}: Found {icon_count} icon elements")
        
        # Stop if count hasn't changed after several scrolls
        if icon_count == prev_count and i > 5 and icon_count > 0:
            break
        prev_count = icon_count
    
    return prev_count


async def extract_icons_from_dom(page: "Page", size: int) -> list[Icon]:
    icon_imgs = page.locator('div.app-grid-icon__image img')
    count = await icon_imgs.count()
    
    if count == 0:
        logger.debug("Trying alternative selector: img[srcset*='icons8']")
        icon_imgs = page.locator('img[srcset*="icons8.com"]')
        count = await icon_imgs.count()
    
    if count == 0:
        return []
    
    logger.info(f"Found {count} icon images via DOM")
    
    icons = []
    seen_ids: set[str] = set()
    
    for i in range(count):
        img = icon_imgs.nth(i)
        srcset = await img.get_attribute('srcset')
        alt = await img.get_attribute('alt') or f'icon_{i}'
        
        if srcset:
            id_match = re.search(r'id=([A-Za-z0-9_-]+)', srcset)
            if id_match:
                icon_id = id_match.group(1)
                if icon_id not in seen_ids:
                    seen_ids.add(icon_id)
                    name = alt.replace(' icon', '').strip()
                    
                    icons.append(Icon(
                        id=icon_id,
                        name=name,
                        url=Icons8URLs.build_icon_url(icon_id, size)
                    ))
                    logger.debug(f"Found: {name} (ID: {icon_id})")
    
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
                url=Icons8URLs.build_icon_url(icon_id, size)
            ))
    
    if icons:
        logger.info(f"Extracted {len(icons)} icons via regex")
    
    return icons


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
        response = await page.goto(url, timeout=60000)
        if response is None or not response.ok:
            raise ScrapingError(
                f"Failed to load collection page. Status: {response.status if response else 'No response'}"
            )
        
        await asyncio.sleep(5)
        logger.debug("Waiting for page to fully load...")
        await asyncio.sleep(3)
        
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
            await page.goto(url, timeout=60000)
            await asyncio.sleep(5)
            
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
        await asyncio.sleep(2)
        
        logger.debug("Waiting for icons to load...")
        try:
            await page.wait_for_selector(
                '.app-grid-icon__image, .collection-icon, img[srcset*="icons8"]',
                timeout=15000
            )
        except asyncio.TimeoutError:
            logger.warning("Timed out waiting for icon elements with standard selectors")
        except Exception as selector_error:
            logger.warning(f"Could not find icon elements: {type(selector_error).__name__}")
        
        await asyncio.sleep(2)
        
        title = await page.title()
        logger.debug(f"Page title: {title}")
        
        # Scroll to load all icons
        await scroll_to_load_icons(page)
        
        # Extract icons
        logger.info("Extracting icons from page...")
        print("  🔍 Extracting icons from page...")
        icons = await extract_icons_from_dom(page, size)
        
        # Fallback to regex if DOM extraction failed
        if not icons:
            icons = await extract_icons_via_regex(page, size)
        
        logger.info(f"Total unique icons found: {len(icons)}")
        
        if not icons:
            raise ScrapingError(
                "No icons found in the collection. "
                "The page structure may have changed or the collection may be empty."
            )
        
        return icons
        
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
    return asyncio.run(scrape_collection(url, size, email, password, headless))
