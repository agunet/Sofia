import asyncio
from playwright.sync_api import sync_playwright
from markdownify import markdownify as md

def fetch_and_clean(url, max_chars=8000):
    """
    Fetches web content using Playwright (Headless Browser) and converts to Markdown.
    Args:
        url: The target URL to read.
        max_chars: Safety limit to prevent context flooding.
    Returns:
        Clean markdown string or error message.
    """
    try:
        content_html = ""
        
        with sync_playwright() as p:
            # Launch browser (chromium by default)
            # We assume browsers are installed or system browser is available.
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Go to URL with timeout
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            
            # Simple heuristic: wait a bit for JS to render if needed
            # page.wait_for_timeout(1000) 
            
            # Get content
            content_html = page.content()
            browser.close()
        
        if content_html:
            # Convert to Markdown
            markdown_text = md(content_html)
            
            # Basic cleanup: Remove excessive newlines
            clean_text = "\n".join([line.strip() for line in markdown_text.splitlines() if line.strip()])
            
            # Truncate
            if len(clean_text) > max_chars:
                return clean_text[:max_chars] + f"\n\n... [Content Truncated at {max_chars} chars] ..."
            return clean_text
            
        return "Error: Empty content retrieved."

    except Exception as e:
        return f"Error fetching content (Playwright): {str(e)}"

if __name__ == "__main__":
    # Test
    print(fetch_and_clean("https://example.com"))
