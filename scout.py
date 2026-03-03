import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

def verify_byline(url, headers):
    """Deep scan for Phil Tenser in text, meta tags, and script data."""
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Check Meta Tags (The 'Invisible' Byline)
        # News sites use these for SEO/Google News
        meta_authors = soup.find_all('meta', attrs={'name': ['author', 'byl', 'creator']})
        meta_authors += soup.find_all('meta', attrs={'property': ['article:author', 'og:author']})
        
        for meta in meta_authors:
            if "Phil Tenser" in meta.get('content', ''):
                return True

        # 2. Check JSON-LD (Structured Data)
        # This is where most modern sites hide the 'real' author data
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            if "Phil Tenser" in script.string:
                return True

        # 3. Last Resort: Broad Text Search
        page_text = soup.get_text()
        if "Phil Tenser" in page_text:
            return True
            
        return False
    except Exception as e:
        print(f"Skipping {url}: {e}")
        return False

def scrape_phil_articles():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    
    # Checking 5 pages to be absolutely sure we backfill everything
    base_url = "https://www.wcvb.com/search?q=Phil+Tenser&page="
    all_articles = []
    seen_urls = set()

    for page in range(1, 6):
        print(f"Scouting page {page}...")
        try:
            response = requests.get(f"{base_url}{page}", headers=headers, timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)

            for link in links:
                url = link['href']
                if "/article/" in url and url not in seen_urls:
                    full_url = "https://www.wcvb.com" + url if url.startswith('/') else url
                    title = link.get_text(strip=True)
                    
                    if len(title) > 20:
                        print(f"Checking: {title[:30]}...")
                        if verify_byline(full_url, headers):
                            print("Match found!")
                            all_articles.append({
                                "title": title,
                                "url": full_url,
                                "date": "Verified Report",
                                "scraped_at": datetime.now().isoformat()
                            })
                        seen_urls.add(url)
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            break

    with open('articles.json', 'w') as f:
        json.dump(all_articles, f, indent=4)
    print(f"Finished! Found {len(all_articles)} articles.")

if __name__ == "__main__":
    scrape_phil_articles()
