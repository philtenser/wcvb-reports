import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

def verify_byline(url, headers):
    """Visits the article page to check if Phil Tenser is in the byline."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # WCVB usually puts the byline in a span or div with 'author' or 'byline' in the class
        # This search is broad to catch different layout versions
        byline_elements = soup.find_all(lambda tag: tag.name in ['span', 'div', 'a'] and 
                                       any(cls in str(tag.get('class', [])).lower() for cls in ['author', 'byline']))
        
        for element in byline_elements:
            if "Phil Tenser" in element.get_text():
                return True
        
        # Fallback: check if your name is anywhere in a typical byline string
        page_text = soup.get_text()
        if "By Phil Tenser" in page_text or "Reporting by Phil Tenser" in page_text:
            return True
            
        return False
    except:
        return False

def scrape_phil_articles():
    base_url = "https://www.wcvb.com/search?q=Phil+Tenser&page="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    all_articles = []
    seen_urls = set()

    for page in range(1, 4):
        print(f"Scouting page {page}...")
        response = requests.get(f"{base_url}{page}", headers=headers)
        if response.status_code != 200: break

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)

        for link in links:
            url = link['href']
            if "/article/" in url and url not in seen_urls:
                full_url = "https://www.wcvb.com" + url if url.startswith('/') else url
                title = link.get_text(strip=True)
                
                if len(title) > 20:
                    print(f"Verifying byline for: {title[:30]}...")
                    if verify_byline(full_url, headers):
                        print("Match found!")
                        all_articles.append({
                            "title": title,
                            "url": full_url,
                            "date": "Recently Published",
                            "scraped_at": datetime.now().isoformat()
                        })
                    seen_urls.add(url)
        time.sleep(1)

    with open('articles.json', 'w') as f:
        json.dump(all_articles, f, indent=4)
    print(f"Verified Scan complete. Found {len(all_articles)} articles by Phil Tenser.")

if __name__ == "__main__":
    scrape_phil_articles()
