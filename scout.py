import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

def scrape_phil_articles():
    # Searching specifically for your name
    base_url = "https://www.wcvb.com/search?q=Phil+Tenser&page="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    all_articles = []
    seen_urls = set()

    for page in range(1, 4): # Checking 3 pages for the backfill
        print(f"Scouting page {page}...")
        try:
            response = requests.get(f"{base_url}{page}", headers=headers, timeout=10)
            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # BROAD SEARCH: Look for all links that might be articles
            links = soup.find_all('a', href=True)

            for link in links:
                url = link['href']
                # Filter for typical WCVB article patterns (usually starts with /article/)
                if "/article/" in url and url not in seen_urls:
                    title = link.get_text(strip=True)
                    
                    # If the link text is long enough to be a headline, grab it
                    if len(title) > 20:
                        full_url = "https://www.wcvb.com" + url if url.startswith('/') else url
                        
                        all_articles.append({
                            "title": title,
                            "url": full_url,
                            "date": "Recently Published", # WCVB dates are tricky to scrape broadly
                            "scraped_at": datetime.now().isoformat()
                        })
                        seen_urls.add(url)

        except Exception as e:
            print(f"Error on page {page}: {e}")
        
        time.sleep(1)

    # Save findings
    with open('articles.json', 'w') as f:
        json.dump(all_articles, f, indent=4)
    
    print(f"Deep Scan complete. Found {len(all_articles)} items.")

if __name__ == "__main__":
    scrape_phil_articles()
