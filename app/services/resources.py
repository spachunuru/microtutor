import xml.etree.ElementTree as ET

import httpx

_ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch_arxiv_papers(topic: str, max_results: int = 3) -> list[dict]:
    """Query the arXiv API and return up to max_results relevant papers."""
    try:
        resp = httpx.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": f'ti:"{topic}" OR abs:"{topic}"',
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            },
            timeout=8.0,
        )
        root = ET.fromstring(resp.text)
        papers = []
        for entry in root.findall("atom:entry", _ARXIV_NS):
            title = entry.findtext("atom:title", "", _ARXIV_NS).strip().replace("\n", " ")
            link = entry.findtext("atom:id", "", _ARXIV_NS).strip()
            abstract = entry.findtext("atom:summary", "", _ARXIV_NS).strip().replace("\n", " ")
            # Trim abstract to ~250 chars for a readable 2-line summary
            if len(abstract) > 250:
                abstract = abstract[:247] + "..."
            if title and link:
                papers.append({"title": title, "url": link, "summary": abstract})
        return papers
    except Exception as e:
        print(f"arXiv fetch failed: {e}")
        return []
