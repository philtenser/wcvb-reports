import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def scrape_phil_articles():
    # The search URL for your byline on WCVB
    search_url = "https://www.wcvb.com/search?q=Phil+Tenser"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []

    # Targeting WCVB's specific search result structure
    # Note: These selectors may need a 'vibe check' if the site layout changes
    for item in soup.select('.search-results-item'):
        title_tag = item.select_one('.search-results-item-title')
        link_tag = item.select_one('a')
        date_tag = item.select_one('.search-results-item-date')
        
        if title_tag and link_tag:
            articles.append({
                "title": title_tag.get_text(strip=True),
                "url": "https://www.wcvb.com" + link_tag['href'] if not link_tag['href'].startswith('http') else link_tag['href'],
                "date": date_tag.get_text(strip=True) if date_tag else "Recently",
                "scraped_at": datetime.now().isoformat()
            })

    # Save to a JSON file that our website will read
    with open('articles.json', 'w') as f:
        json.dump(articles, f, indent=4)
    print(f"Successfully tracked {len(articles)} articles.")

if __name__ == "__main__":
    scrape_phil_articles()
