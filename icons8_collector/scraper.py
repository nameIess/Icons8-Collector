import os
import re
import asyncio
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from playwright.async_api import Page, BrowserContext

from .exceptions import ScrapingError, BrowserError, AuthenticationError, ValidationError
from .auth import check_login_status, perform_login, validate_credentials


# Default configuration
DEFAULT_SIZE = 256
BROWSER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.browser_data')

# Security constants
ALLOWED_COLLECTION_DOMAINS = ['icons8.com']
ALLOWED_SCHEMES = ['https']
VALID_SIZES = [16, 24, 32, 48, 64, 96, 128, 256, 512]


@dataclass
class Icon:
    id: str
    name: str
    url: str


def validate_collection_url(url: str) -> None:
    if not url or not isinstance(url, str):
        raise ValidationError(
            "Collection URL must be a non-empty string",
            field_name="url"
        )
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(
            f"Invalid URL format",
            field_name="url",
            original_error=e
        )
    
    # Check scheme
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValidationError(
            f"Only HTTPS URLs are allowed. Got: {parsed.scheme}",
            field_name="url"
        )
    
    # Check domain
    domain = parsed.netloc.lower()
    if not any(domain == allowed or domain.endswith('.' + allowed) for allowed in ALLOWED_COLLECTION_DOMAINS):
        raise ValidationError(
            f"URL domain not allowed: {domain}. Only Icons8 domains are permitted.",
            field_name="url"
        )
    
    # Check for collection path
    if '/collection/' not in parsed.path and '/collections/' not in parsed.path:
        raise ValidationError(
            "URL does not appear to be a valid Icons8 collection URL. "
            "Expected path to contain '/collection/' or '/collections/'",
            field_name="url"
        )


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
    print(f"Launching browser ({mode_str})...")
    
    p = await async_playwright().start()
    
    # Try Chrome first, fall back to Chromium
    try:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            headless=headless,
            channel="chrome"
        )
    except Exception as chrome_error:
        print(f"Chrome not available, using Chromium...")
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
    print("Scrolling to load icons...")
    prev_count = 0
    
    for i in range(max_scrolls):
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1.5)
        
        icon_count = await page.locator('div.app-grid-icon__image img').count()
        if icon_count == 0:
            icon_count = await page.locator('img[srcset*="icons8.com"]').count()
        
        print(f"  Scroll {i + 1}: Found {icon_count} icon elements...")
        
        # Stop if count hasn't changed after several scrolls
        if icon_count == prev_count and i > 5 and icon_count > 0:
            break
        prev_count = icon_count
    
    return prev_count


async def extract_icons_from_dom(page: "Page", size: int) -> list[Icon]:
    icon_imgs = page.locator('div.app-grid-icon__image img')
    count = await icon_imgs.count()
    
    if count == 0:
        print("Trying alternative selector: img[srcset*='icons8']")
        icon_imgs = page.locator('img[srcset*="icons8.com"]')
        count = await icon_imgs.count()
    
    if count == 0:
        return []
    
    print(f"Found {count} icon images via DOM")
    
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
                        url=f"https://img.icons8.com/?size={size}&id={icon_id}&format=png"
                    ))
                    print(f"  Found: {name} (ID: {icon_id})")
    
    return icons


async def extract_icons_via_regex(page: "Page", size: int) -> list[Icon]:
    print("Trying regex extraction from page content...")
    content = await page.content()
    
    id_matches = re.findall(
        r'img\.icons8\.com/?\?[^"\'>\s]*id=([A-Za-z0-9_-]+)[^"\'>\s]*', 
        content
    )
    print(f"Found {len(id_matches)} icon IDs via regex")
    
    icons = []
    seen_ids: set[str] = set()
    
    for icon_id in id_matches:
        if icon_id not in seen_ids:
            seen_ids.add(icon_id)
            icons.append(Icon(
                id=icon_id,
                name=f'icon-{icon_id}',
                url=f"https://img.icons8.com/?size={size}&id={icon_id}&format=png"
            ))
    
    if icons:
        print(f"Extracted {len(icons)} icons via regex")
    
    return icons


async def scrape_collection(
    url: str,
    size: int = DEFAULT_SIZE,
    email: Optional[str] = None,
    password: Optional[str] = None,
    headless: bool = True
) -> list[Icon]:
    # Validate inputs
    validate_collection_url(url)
    validate_size(size)
    validate_credentials(email, password)
    
    context, playwright_instance = await launch_browser(headless)
    
    try:
        page = await context.new_page()
        
        print(f"Opening collection page: {url}")
        response = await page.goto(url, timeout=60000)
        if response is None or not response.ok:
            raise ScrapingError(
                f"Failed to load collection page. Status: {response.status if response else 'No response'}"
            )
        
        await asyncio.sleep(5)
        print("Waiting for page to fully load...")
        await asyncio.sleep(3)
        
        # Check login status
        is_logged_in = await check_login_status(page)
        print(f"Icons already visible: {is_logged_in}")
        
        if is_logged_in:
            print("Already logged in! Skipping login process...")
        elif email and password:
            print("Not logged in - attempting login...")
            await perform_login(page, email, password)
            
            print(f"Reloading collection page...")
            await page.goto(url, timeout=60000)
            await asyncio.sleep(5)
            
            # Verify login worked
            if not await check_login_status(page):
                raise AuthenticationError(
                    "Login appeared to succeed but icons are still not visible. "
                    "Please verify your credentials are correct."
                )
            
            print("Login completed!")
        else:
            raise AuthenticationError(
                "No icons visible and no credentials provided. "
                "Please provide ICONS8_EMAIL and ICONS8_PASSWORD environment variables, "
                "or use --email and --password arguments."
            )
        
        print("Loading collection page...")
        await asyncio.sleep(2)
        
        print("Waiting for icons to load...")
        try:
            await page.wait_for_selector(
                '.app-grid-icon__image, .collection-icon, img[srcset*="icons8"]',
                timeout=15000
            )
        except asyncio.TimeoutError:
            print("Warning: Timed out waiting for icon elements with standard selectors")
        except Exception as selector_error:
            # Log but don't fail - we'll try alternative methods
            print(f"Warning: Could not find icon elements: {type(selector_error).__name__}")
        
        await asyncio.sleep(2)
        
        title = await page.title()
        print(f"Page title: {title}")
        
        # Scroll to load all icons
        await scroll_to_load_icons(page)
        
        # Extract icons
        print("\nExtracting icons from page...")
        icons = await extract_icons_from_dom(page, size)
        
        # Fallback to regex if DOM extraction failed
        if not icons:
            icons = await extract_icons_via_regex(page, size)
        
        print(f"\nTotal unique icons found: {len(icons)}")
        
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
