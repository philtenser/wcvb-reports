import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import time

def verify_byline(url, headers):
    """The most aggressive possible scan for Phil Tenser in both visible and hidden data."""
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        html_content = response.text
        
        if "phil tenser" in html_content.lower():
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check all meta tags first
            for meta in soup.find_all('meta'):
                content = meta.get('content', '')
                if "Phil Tenser" in content:
                    return True
            
            # Check for JSON-LD (Structured data used for SEO)
            for script in soup.find_all('script', type='application/ld+json'):
                if script.string and "Phil Tenser" in script.string:
                    return True

            # Check specific byline containers
            byline_area = soup.select('[class*="byline"], [class*="author"], [class*="contributor"]')
            for area in byline_area:
                if "Phil Tenser" in area.get_text():
                    return True

        return False
    except Exception as e:
        print(f"  [Error] Skipping {url}: {e}")
        return False

def extract_article_date(soup):
    """Try to find the actual publication date from meta tags or structured data."""
    # Try meta tags common in news sites (OpenGraph, article:published_time, etc.)
    for meta_name in ['article:published_time', 'pubdate', 'publish-date', 'date']:
        meta = soup.find('meta', property=meta_name) or soup.find('meta', attrs={'name': meta_name})
        if meta and meta.get('content'):
            try:
                return meta['content'][:10] # Grab YYYY-MM-DD
            except Exception:
                pass
    return datetime.now().strftime('%Y-%m-%d')

def scrape_phil_articles():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
    base_url = "https://www.wcvb.com/search?q=Phil+Tenser&page="
    
    # 1. Load existing articles from disk so we preserve history
    existing_articles = []
    if os.path.exists('articles.json'):
        try:
            with open('articles.json', 'r') as f:
                existing_articles = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load existing articles.json: {e}")

    # Map existing articles by URL for quick lookup and deduplication
    article_map = {art['url']: art for art in existing_articles}

    newly_scraped_count = 0

    for page in range(1, 15):
        print(f"Searching WCVB Results Page {page}...")
        try:
            response = requests.get(f"{base_url}{page}", headers=headers, timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                url = link['href']
                if "/article/" in url:
                    full_url = "https://www.wcvb.com" + url if url.startswith('/') else url
                    title = link.get_text(strip=True)
                    
                    if len(title) > 20:
                        # If we already have this URL in our historical JSON, skip expensive re-scraping
                        if full_url in article_map:
                            continue
                            
                        print(f"Analyzing new article: {title[:50]}...")
                        try:
                            art_resp = requests.get(full_url, headers=headers, timeout=15)
                            art_soup = BeautifulSoup(art_resp.text, 'html.parser')
                            
                            if verify_byline(full_url, headers):
                                pub_date = extract_article_date(art_soup)
                                article_map[full_url] = {
                                    "title": title,
                                    "url": full_url,
                                    "date": pub_date,
                                    "scraped_at": datetime.now().isoformat()
                                }
                                newly_scraped_count += 1
                                print("  ✅ NEW MATCH ADDED")
                        except Exception as ex:
                            print(f"  [Error fetching article] {ex}")
                            
            time.sleep(1)
        except Exception as e:
            print(f"Search error: {e}")
            break

    # Combine back into a list and sort globally by date descending (newest first)
    all_articles = list(article_map.values())
    all_articles.sort(key=lambda x: x.get('date', '1900-01-01'), reverse=True)

    # Save cleanly back to JSON
    with open('articles.json', 'w') as f:
        json.dump(all_articles, f, indent=4)
        
    print(f"\nSuccess! Added {newly_scraped_count} new articles. Total Archive Size: {len(all_articles)}")

if __name__ == "__main__":
    scrape_phil_articles()
