import logging
from playwright.sync_api import sync_playwright
import trafilatura

# Singleton Storage
_PLAYWRIGHT = None
_BROWSER = None

def get_browser():
    """
    Singleton Pattern: Returns the existing browser capability or launches a new one.
    Keeps the browser open to save 2-5s per request.
    """
    global _PLAYWRIGHT, _BROWSER
    if _BROWSER is None:
        print("🚀 [Web Reader] Launching Headless Browser (Singleton)...")
        _PLAYWRIGHT = sync_playwright().start()
        _BROWSER = _PLAYWRIGHT.chromium.launch(headless=True)
    return _BROWSER

def fetch_and_clean(url, max_chars=12000):
    """
    Fetches web content using a Persistent Headless Browser + Trafilatura Extraction.
    
    Improvements V3:
    1. Singleton Browser (Speedup).
    2. Trafilatura (Noise Filter: Ads, Menus, Cookies).
    """
    try:
        browser = get_browser()
        
        # Create a fresh context/page for this request
        page = browser.new_page()
        
        try:
            # Go to URL with timeout
            # 'domcontentloaded' is faster than 'load' (wait for external resources)
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            
            # Get raw HTML after JS execution
            content_html = page.content()
            
        finally:
            # IMPORTANT: Close only the page, NOT the browser
            page.close()
        
        if content_html:
            # Extract Main Content (Filter Noise)
            # include_comments=False gets rid of social garbage
            clean_text = trafilatura.extract(content_html, include_comments=False, output_format="markdown")
            
            if not clean_text:
                return "⚠️ Error: Trafilatura could not extract main content (Site might be empty or blocked)."

            # Truncate
            if len(clean_text) > max_chars:
                 return clean_text[:max_chars] + f"\n\n... [Content Truncated at {max_chars} chars] ..."
            return clean_text
            
        return "Error: Empty HTML retrieved."

    except Exception as e:
        return f"Error fetching content: {str(e)}"

def close_browser():
    """Call this on system shutdown to clean up resources."""
    global _BROWSER, _PLAYWRIGHT
    if _BROWSER:
        _BROWSER.close()
        _BROWSER = None
    if _PLAYWRIGHT:
        _PLAYWRIGHT.stop()
        _PLAYWRIGHT = None

if __name__ == "__main__":
    # Test
    print(fetch_and_clean("https://example.com"))
    close_browser()
