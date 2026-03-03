import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

def verify_byline(url, headers):
    """Deep scan using invisible metadata - the most reliable way to find authors."""
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. THE GOLD STANDARD: Meta Tags
        # This is where Hearst/WCVB stores the 'real' author for Google News
        meta_tags = [
            {'name': 'author'},
            {'property': 'article:author'},
            {'name': 'byl'},
            {'property': 'og:author'}
        ]
        
        for tag in meta_tags:
            found = soup.find('meta', attrs=tag)
            if found and "Phil Tenser" in found.get('content', ''):
                print(f"  [Meta Match] Found in {tag}")
                return True

        # 2. THE BACKUP: Structured Data (JSON-LD)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            if script.string and "Phil Tenser" in script.string:
                print("  [Data Match] Found in JSON-LD")
                return True

        # 3. THE HAIL MARY: Broad Text Search
        # We check the first 5000 chars to be safe
        if "Phil Tenser" in soup.get_text()[:5000]:
            print("  [Text Match] Found in page body")
            return True
            
        return False
    except Exception as e:
        print(f"  [Error] Could not verify {url}: {e}")
        return False

def scrape_phil_articles():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    
    # Checking 5 pages to ensure we catch everything during the backfill
    base_url = "https://www.wcvb.com/search?q=Phil+Tenser&page="
    all_articles = []
    seen_urls = set()

    for page in range(1, 6):
        print(f"Scouting search results page {page}...")
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
                        print(f"Investigating: {title[:40]}...")
                        if verify_byline(full_url, headers):
                            all_articles.append({
                                "title": title,
                                "url": full_url,
                                "date": "Verified Report",
                                "scraped_at": datetime.now().isoformat()
                            })
                        seen_urls.add(url)
            time.sleep(1) # Be polite to the servers
        except Exception as e:
            print(f"Search Page Error: {e}")
            break

    # Final save
    with open('articles.json', 'w') as f:
        json.dump(all_articles, f, indent=4)
    print(f"Complete! Found {len(all_articles)} verified articles.")

if __name__ == "__main__":
    scrape_phil_articles()
