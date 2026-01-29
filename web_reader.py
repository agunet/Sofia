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
        # Launch browser
        _BROWSER = _PLAYWRIGHT.chromium.launch(headless=True)
    return _BROWSER

def get_context(browser):
    """Creates a context with a real User Agent."""
    return browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

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

def search_via_browser(query, max_results=5, verbose=True):
    """
    Performs a search using the DuckDuckGo Search (DDGS) library.
    Strategy: 'Guerrilla Mode' - Uses ddgs library with random delays to avoid rate limits.
    """
    import time
    import random
    from ddgs import DDGS

    try:
        # Guerrilla Tactic: Human Delay
        # Sleep between 2 to 5 seconds to avoid robotic patterns
        delay = random.uniform(2, 5)
        if verbose:
            print(f"🕵️ [Web Reader] Guerrilla Mode: Waiting {delay:.2f}s before search...")
        time.sleep(delay)

        # Modifying query to target reliable, bot-friendly sources
        # "site:wikipedia.org OR site:plato.stanford.edu OR site:philpapers.org"
        # Or simply append "encyclopedia wiki" to guide the search engine naturally
        enhanced_query = f"{query} site:wikipedia.org OR site:plato.stanford.edu OR site:britannica.com OR site:scholar.google.com"
        # If that's too restrictive, just generic terms:
        # enhanced_query = f"{query} (encyclopedia OR wiki OR paper)"
        
        # User explicitly requested safer sources
        # We append 'wikipedia' or 'education' to bias results towards open knowledge
        # and avoid commercial sites that block bots aggressively.
        safe_query = f"{query} site:wikipedia.org OR site:plato.stanford.edu OR site:philpapers.org OR site:britannica.com"
        
        results = []
        try:
            with DDGS() as ddgs:
                # Use the safe query
                ddgs_gen = ddgs.text(safe_query, max_results=max_results)
                if ddgs_gen:
                    for r in ddgs_gen:
                        results.append({
                            'title': r.get('title'),
                            'url': r.get('href'),
                            'snippet': r.get('body')
                        })
        except Exception as e:
            print(f"❌ [Web Reader] DDGS Error: {e}")
            return []

        if not results:
             print(f"⚠️ [Web Reader] Search returned 0 results for: {query}")
        else:
             print(f"✅ [Web Reader] Found {len(results)} results.")
            
        return results

    except Exception as e:
        print(f"Error in search module: {e}")
        return []

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
