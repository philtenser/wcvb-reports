import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import sys

def verify_byline(url, headers):
    """Visits the article and checks for Phil Tenser anywhere in the byline area."""
    try:
        # Added a slightly longer timeout for multi-page articles
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Search specific byline/author tags and classes
        # This handles cases where multiple authors are listed in separate spans/links
        potential_containers = soup.find_all(['span', 'div', 'a', 'p', 'address'])
        for container in potential_containers:
            # Get class list as a string to check for author keywords
            classes = str(container.get('class', [])).lower()
            if any(key in classes for key in ['author', 'byline', 'writer', 'contributor']):
                if "Phil Tenser" in container.get_text():
                    return True

        # 2. Fallback: Scan the first 3000 characters of the page text
        # (This is a safety net for any layout changes or co-author lists)
        page_start = soup.get_text()[:3000]
        if "Phil Tenser" in page_start:
            return True
            
        return False
    except Exception as e:
        print(f"Skipping verification for {url}: {e}")
        return False

def scrape_phil_articles():
    # Modern headers to look like a standard Mac/Chrome browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    # We check 3 pages of search results to ensure we catch recent co-authored work
    base_url = "https://www.wcvb.com/search?q=Phil+Tenser&page="
    all_articles = []
    seen_urls = set()

    print(f"Starting Scout at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for page in range(1, 4):
        print(f"Scouting search page {page}...")
        try:
            response = requests.get(f"{base_url}{page}", headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            if not links:
                print("No links found on this page.")
                break

            for link in links:
                url = link['href']
                # Standard WCVB article pattern
                if "/article/" in url and url not in seen_urls:
                    full_url = "https://www.wcvb.com" + url if url.startswith('/') else url
                    title = link.get_text(strip=True)
                    
                    # Only verify links that look like actual headlines (over 20 chars)
                    if len(title) > 20:
                        print(f"Verifying byline: {title[:40]}...")
                        if verify_byline(full_url, headers):
                            print("Match found! Adding to list.")
                            all_articles.append({
                                "title": title,
                                "url": full_url,
                                "date": "Recently Published",
                                "scraped_at": datetime.now().isoformat()
                            })
                        seen_urls.add(url)
            
            # Brief pause to be respectful to the server
            time.sleep(1.5)

        except Exception as e:
            print(f"Error on search page {page}: {e}")
            break

    # Save the final list (even if empty to prevent front-end errors)
    try:
        with open('articles.json', 'w') as f:
            json.dump(all_articles, f, indent=4)
        print(f"Successfully saved {len(all_articles)} verified articles.")
    except Exception as e:
        print(f"Failed to save JSON: {e}")

if __name__ == "__main__":
    scrape_phil_articles()
