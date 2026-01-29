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
    Fetches web content and returns a structured Reality Object.
    """
    try:
        browser = get_browser()
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            content_html = page.content()
            final_url = page.url
        finally:
            page.close()
        
        if content_html:
            clean_text = trafilatura.extract(content_html, include_comments=False, output_format="markdown")
            
            if not clean_text:
                return {"status": "error", "error": "Extraction failure (Trafilatura)", "url": url}

            if len(clean_text) > max_chars:
                 clean_text = clean_text[:max_chars] + f"\n\n... [Truncated] ..."
            
            return {
                "status": "success",
                "url": final_url,
                "content": clean_text,
                "length": len(clean_text),
                "signal": f"WEB_READ_CONFIRMED_{datetime.datetime.now().timestamp()}"
            }
            
        return {"status": "error", "error": "Empty HTML", "url": url}

    except Exception as e:
        return {"status": "error", "error": str(e), "url": url}

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
