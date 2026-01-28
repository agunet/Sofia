import requests

def fetch_and_clean(url, max_chars=8000):
    """
    Fetches web content and converts it to clean Markdown using Jina Reader.
    Args:
        url: The target URL to read.
        max_chars: Safety limit to prevent context flooding (default 8k).
    Returns:
        Clean markdown string or error message.
    """
    try:
        # Jina Reader API: https://r.jina.ai/<URL>
        # It returns standard markdown.
        reader_url = f"https://r.jina.ai/{url}"
        
        # Determine if we need to request JSON or text. 
        # Standard GET usually returns text/markdown for Jina.
        response = requests.get(reader_url, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Basic cleanup if needed, but Jina is usually good.
            # Truncate if too long (keeping the head is usually more important for summary)
            if len(content) > max_chars:
                return content[:max_chars] + f"\n\n... [Content Truncated at {max_chars} chars] ..."
            return content
            
        else:
            return f"Error reading content: HTTP {response.status_code}"
            
    except Exception as e:
        return f"Error fetching content: {str(e)}"

if __name__ == "__main__":
    # Quick Test
    test_url = "https://example.com"
    print(f"Fetching {test_url}...")
    print(fetch_and_clean(test_url))
