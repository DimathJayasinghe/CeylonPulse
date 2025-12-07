import json
import requests
from bs4 import BeautifulSoup


def scrape_news(limit: int):
    page_url = "https://www.adaderana.lk/hot-news/?pageno={}"
    all_news = []
    page_no = 1
    collected = 0

    while collected < limit:
        url = page_url.format(page_no)
        res = requests.get(url, timeout=15)
        if res.status_code != 200:
            break

        soup = BeautifulSoup(res.text, "html.parser")
        stories = soup.find_all("div", class_="news-story")
        if not stories:
            break

        for s in stories:
            if collected >= limit:
                break

            h = s.find("h2")
            a = h.find("a") if h else None
            headline = a.text.strip() if a else ""
            link = a["href"] if a else ""

            comments = s.find("div", class_="comments")
            date_time_text = ""
            if comments:
                span = comments.find("span")
                if span:
                    date_time_text = span.text.strip().lstrip("|").strip()

            all_news.append({
                "id": collected + 1,
                "date_time": date_time_text,
                "headline": headline,
                "url": link,
            })
            collected += 1

        page_no += 1

    return all_news


def handler(request):
    """Vercel Python Function entrypoint."""
    try:
        qs = request.get("query", {}) or {}
        raw_limit = qs.get("limit", "10")
        limit = int(raw_limit)
        limit = max(1, min(limit, 50))

        data = scrape_news(limit)
        body = json.dumps({"count": len(data), "items": data})

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": body,
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)}),
        }