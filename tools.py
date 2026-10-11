from langchain.tools import tool 
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os 
from dotenv import load_dotenv
from rich import print
load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic . Returns Titles , URLs and snippets."""
    results = tavily.search(query = query, max_results=5)
    out = []

    for r in results['results']:
        out.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n"
        )

    return "\n--------------\n".join(out)

# print(web_search.invoke("what is recent news about AI in healthcare?"))



@tool
def scrape_url(url: str) -> str:
    """Fetch a webpage and extract its readable text.
    Returns page text or a clear error if the page cannot be accessed.
    """
    try:
        url = url.strip()

        # Validate the URL
        from urllib.parse import urlparse
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return f"Invalid URL: {url}"

        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/130.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
            }
        )

        # Raise an error for HTTP 403, 404, 500, etc.
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()
        if "html" not in content_type and "text/plain" not in content_type:
            return f"Unsupported content type: {content_type}"

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup([
            "script", "style", "nav", "footer",
            "header", "noscript", "iframe"
        ]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        if not text:
            return f"No readable text found at: {url}"

        return text[:4000]

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return f"HTTP error {status} while accessing {url}: {e}"

    except requests.exceptions.Timeout:
        return f"Request timed out while accessing: {url}"

    except requests.exceptions.RequestException as e:
        return f"Network error while accessing {url}: {e}"


