import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

def scrape_phil_articles():
    # We will check the first 5 pages of results to backfill
    base_url = "https://www.wcvb.com/search?q=Phil+Tenser&page="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    all_articles = []

    for page in range(1, 6): # Checks pages 1 through 5
        print(f"Scouting page {page}...")
        response = requests.get(f"{base_url}{page}", headers=headers)
        
        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('.search-results-item')
        
        if not items:
            break # Stop if no more results found

        for item in items:
            title_tag = item.select_one('.search-results-item-title')
            link_tag = item.select_one('a')
            date_tag = item.select_one('.search-results-item-date')
            
            if title_tag and link_tag:
                all_articles.append({
                    "title": title_tag.get_text(strip=True),
                    "url": "https://www.wcvb.com" + link_tag['href'] if not link_tag['href'].startswith('http') else link_tag['href'],
                    "date": date_tag.get_text(strip=True) if date_tag else "Recently",
                    "scraped_at": datetime.now().isoformat()
                })
        
        time.sleep(1) # Be a "polite" bot to avoid being blocked

    # Save the expanded list
    with open('articles.json', 'w') as f:
        json.dump(all_articles, f, indent=4)
    print(f"Backfill complete. Found {len(all_articles)} articles.")

if __name__ == "__main__":
    scrape_phil_articles()
