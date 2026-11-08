from ddgs import DDGS
from bs4 import BeautifulSoup
import requests
class WebSearch:
    def web_fetch(self, url: str):
        response = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for element in soup(["script", "style", "nav", "footer"]):
            element.decompose()

        return {
            "url": url,
            "title": soup.title.get_text(strip=True) if soup.title else "",
            "content": soup.get_text(" ", strip=True)[:12000]
        }
    def web_search(self, query: str, max_results: int = 5):
        results = DDGS().text(
            query,
            max_results=max_results
        )

        return [
            {
                "title": result.get("title"),
                "url": result.get("href"),
                "snippet": result.get("body")
            }
            for result in results
        ]