import asyncio
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from .exceptions import AuthenticationError, ConfigurationError


def validate_credentials(email: Optional[str], password: Optional[str]) -> None:
    if (email and not password) or (password and not email):
        raise ConfigurationError(
            "Both email and password must be provided together. "
            "Provide both --email and --password arguments."
        )


async def check_login_status(page: "Page") -> bool:
    """
    Determines if the user is logged in by checking for specific UI elements.
    Returns True if logged in, False otherwise.
    """
    # Check for definitive "Not Logged In" indicators (Login buttons)
    is_guest = await page.evaluate('''() => {
        const btns = Array.from(document.querySelectorAll('a, button'));
        return btns.some(el => {
            const text = (el.innerText || '').trim().toLowerCase();
            return (text === 'sign in' || text === 'log in') && el.offsetParent !== null; // visible
        });
    }''')
    
    if is_guest:
        return False

    # Check for definitive "Logged In" indicators (Avatar, Account link)
    is_user = await page.evaluate('''() => {
        // Check for common avatar/profile classes or links
        if (document.querySelector('.user-avatar, .profile-icon, a[href*="/account"]')) return true;
        
        // Check for "My Collections" or similar user-specific text
        const bodyText = document.body.innerText;
        return bodyText.includes('My collections') || bodyText.includes('Account');
    }''')
    
    if is_user:
        return True

    # Fallback: If we see icons, we assume we have access (might be public collection, but effective "login" for scraping)
    # Using generic robust selector similar to scraper.py
    icons_count = await page.locator('img[src*="icons8.com"]').count()
    return icons_count > 0


def _mask_email(email: str) -> str:
    if '@' not in email:
        return email[:2] + '***'
    local, domain = email.rsplit('@', 1)
    masked_local = local[:2] + '***' if len(local) > 2 else local[0] + '***'
    return f"{masked_local}@{domain}"


async def perform_login(page: "Page", email: str, password: str) -> None:
    print(f"Attempting login with email: {_mask_email(email)}")
    
    # Try to find and click the Sign in button
    btn_found = await page.evaluate('''() => {
        const btns = document.querySelectorAll('.login-button, [class*="login"], button');
        for (const btn of btns) {
            if (btn.textContent.includes('Sign in') || btn.classList.contains('login-button')) {
                return true;
            }
        }
        return false;
    }''')
    
    if btn_found:
        await _login_via_button(page, email, password)
    else:
        await _login_via_page(page, email, password)


async def _login_via_button(page: "Page", email: str, password: str) -> None:
    print("Clicking Sign in button...")
    
    clicked = await page.evaluate('''() => {
        const btns = document.querySelectorAll('.login-button, [class*="login"], button');
        for (const btn of btns) {
            if (btn.textContent.includes('Sign in') || btn.classList.contains('login-button')) {
                btn.click();
                return true;
            }
        }
        return false;
    }''')
    
    if not clicked:
        raise AuthenticationError("Failed to click Sign in button")
    
    await asyncio.sleep(4)
    await _fill_login_form(page, email, password)


async def _login_via_page(page: "Page", email: str, password: str) -> None:
    print("No Sign in button found - navigating to login page...")
    
    response = await page.goto("https://icons8.com/login", timeout=60000)
    if response is None or not response.ok:
        raise AuthenticationError(
            f"Failed to navigate to login page. Status: {response.status if response else 'No response'}"
        )
    
    await asyncio.sleep(5)
    await _fill_login_form(page, email, password)


async def _fill_login_form(page: "Page", email: str, password: str) -> None:
    print("Waiting for login form...")
    
    email_selector = 'input[type="email"], input[placeholder*="mail"], input[placeholder="Email"]'
    
    try:
        await page.wait_for_selector(email_selector, timeout=20000)
    except Exception as e:
        raise AuthenticationError(f"Login form not found: {e}") from e
    
    await asyncio.sleep(2)
    
    print(f"Filling email: {_mask_email(email)}")
    email_input = page.locator(email_selector).first
    await email_input.fill(email)
    await asyncio.sleep(1)
    
    print("Filling password...")
    password_input = page.locator('input[type="password"]').first
    await password_input.fill(password)
    await asyncio.sleep(2)
    
    print("Waiting for captcha verification (if any)...")
    await asyncio.sleep(5)
    
    print("Submitting login form...")
    submitted = await page.evaluate('''() => {
        const btns = document.querySelectorAll('button');
        for (const btn of btns) {
            if (btn.textContent.trim() === 'Log in' || btn.classList.contains('i8-login-form__submit')) {
                btn.click();
                return true;
            }
        }
        const form = document.querySelector('form');
        if (form) {
            form.submit();
            return true;
        }
        return false;
    }''')
    
    if not submitted:
        raise AuthenticationError("Failed to submit login form - no submit button found")
    
    print("Waiting for login to complete...")
    await asyncio.sleep(8)
    print("Login submitted successfully")
