import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

def verify_byline(url, headers):
    """The most aggressive possible scan for Phil Tenser in both visible and hidden data."""
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        html_content = response.text
        
        # 1. THE BRUTE FORCE CHECK: Raw HTML
        # If 'Phil Tenser' appears anywhere in the raw code (case-insensitive)
        if "phil tenser" in html_content.lower():
            # We still want to be careful not to match 'Phil Tenser' in a 'Recommended' sidebar
            # So we check if it's near author-related keywords
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check all meta tags first
            for meta in soup.find_all('meta'):
                content = meta.get('content', '')
                if "Phil Tenser" in content:
                    print(f"  [Meta Match] Found in: {meta.attrs}")
                    return True
            
            # Check for JSON-LD (Structured data used for SEO)
            for script in soup.find_all('script', type='application/ld+json'):
                if script.string and "Phil Tenser" in script.string:
                    print("  [JSON-LD Match] Found in structured data")
                    return True

            # Check specific byline containers for co-authors
            # Hearst often uses classes like 'm-article-header__byline'
            byline_area = soup.select('[class*="byline"], [class*="author"], [class*="contributor"]')
            for area in byline_area:
                if "Phil Tenser" in area.get_text():
                    print("  [Byline Area Match] Found in CSS-selected area")
                    return True

        return False
    except Exception as e:
        print(f"  [Error] Skipping {url}: {e}")
        return False

def scrape_phil_articles():
    # We use a very modern User-Agent to ensure we get the full page content
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
    # Check 5 pages of search results to ensure full history capture
    base_url = "https://www.wcvb.com/search?q=Phil+Tenser&page="
    all_articles = []
    seen_urls = set()

    for page in range(1, 6):
        print(f"Searching WCVB Results Page {page}...")
        try:
            response = requests.get(f"{base_url}{page}", headers=headers, timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links to articles
            for link in soup.find_all('a', href=True):
                url = link['href']
                if "/article/" in url and url not in seen_urls:
                    full_url = "https://www.wcvb.com" + url if url.startswith('/') else url
                    title = link.get_text(strip=True)
                    
                    if len(title) > 20: # Filter out short menu links
                        print(f"Analyzing: {title[:50]}...")
                        if verify_byline(full_url, headers):
                            all_articles.append({
                                "title": title,
                                "url": full_url,
                                "date": "Verified Work",
                                "scraped_at": datetime.now().isoformat()
                            })
                            print("  ✅ MATCH ADDED")
                        seen_urls.add(url)
            time.sleep(1) # Be a good bot
        except Exception as e:
            print(f"Search error: {e}")
            break

    # Save to JSON
    with open('articles.json', 'w') as f:
        json.dump(all_articles, f, indent=4)
    print(f"\nSuccess! Total Verified Articles: {len(all_articles)}")

if __name__ == "__main__":
    scrape_phil_articles()
