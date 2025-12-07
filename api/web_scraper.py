import requests
from bs4 import BeautifulSoup
import pandas as pd

class NewScraper:
    def __init__(self, page_url="https://www.adaderana.lk/hot-news/?pageno={}"):
        self.page_url = page_url
        self.all_news = []

    def scrape_page(self, limit):
        """Scrape the first `limit` news items across multiple pages."""
        # Safeguard limit
        limit = min(1000,limit)
        print(f"Scraping up to {limit} news items...")
        # Clear previous data before new scrape
        self.all_news = []
        
        page_no = 1  # Adaderana starts at page 1
        collected = 0

        while collected < limit:
            print(f"Scraping page {page_no}...")
            url = self.page_url.format(page_no)
            res = requests.get(url)

            if res.status_code != 200:
                print("Error loading page!")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            stories = soup.find_all("div", class_="news-story")

            if not stories:
                print("No more stories found, stopping.")
                break

            for s in stories:
                if collected >= limit:
                    break

                # Get headline + link
                h = s.find("h2")
                a = h.find("a") if h else None
                headline = a.text.strip() if a else ""
                link = a["href"] if a else ""

                # Get date + time
                comments = s.find("div", class_="comments")
                date_time_text = ""
                if comments:
                    span = comments.find("span")
                    if span:
                        date_time_text = span.text.strip().lstrip("|").strip()

                # Save entry
                self.all_news.append({
                    "ID": collected + 1,
                    "date_time": date_time_text,
                    "headline": headline,
                    "url": link
                })

                collected += 1

            page_no += 1

        return self.all_news

    def save_to_excel(self):
        df = pd.DataFrame(self.all_news)
        df.to_excel("adaderana_news_test.xlsx", index=False)
        print("Done! Saved as adaderana_news_test.xlsx")


if __name__ == "__main__":
    scraper = NewScraper()
    news = scraper.scrape_page(1500)
    print(news)
