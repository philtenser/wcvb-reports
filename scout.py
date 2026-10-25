import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import time

AUTHOR_PAGE_URL = "https://www.wcvb.com/news-team/36aab4e9-2df6-4970-8bac-c1139192e0ca"

def verify_byline(url, headers):
    """Strictly verify that Phil Tenser is listed as an author in metadata or byline elements."""
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Check JSON-LD Structured Data
        for script in soup.find_all('script', type='application/ld+json'):
            if script.string and "phil tenser" in script.string.lower():
                return True

        # 2. Check explicit article author meta tags
        for meta in soup.find_all('meta'):
            prop = meta.get('property', '').lower()
            name = meta.get('name', '').lower()
            content = meta.get('content', '').lower()
            
            if ('author' in prop or 'author' in name) and 'phil tenser' in content:
                return True

        # 3. Check specific byline DOM containers
        byline_elements = soup.select('[class*="byline"], [class*="author"], [class*="contributor"], [data-testid*="author"]')
        for element in byline_elements:
            if "phil tenser" in element.get_text().lower():
                return True

        return False
    except Exception as e:
        print(f"  [Error verifying byline] Skipping {url}: {e}")
        return False

def fetch_recent_from_author_page(headers):
    """Fetch potential article URLs from your station author page feed."""
    print(f"Checking author feed: {AUTHOR_PAGE_URL}")
    try:
        response = requests.get(AUTHOR_PAGE_URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        found_urls = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if '/article/' in href:
                full_url = href if href.startswith('http') else f"https://www.wcvb.com{href}"
                if full_url not in found_urls:
                    found_urls.append(full_url)
                    
        return found_urls[:15]
    except Exception as e:
        print(f"Error fetching author page: {e}")
        return []

def sync_author_ledger():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
    # Load existing archive
    existing_articles = []
    if os.path.exists('articles.json'):
        try:
            with open('articles.json', 'r') as f:
                existing_articles = json.load(f)
        except Exception:
            pass

    article_map = {art['url']: art for art in existing_articles}
    
    # -------------------------------------------------------------
    # RETROACTIVE CLEANUP PASS: Audit existing archive items
    # -------------------------------------------------------------
    print(f"Auditing existing archive ({len(article_map)} items) for non-bylined stories...")
    purged_count = 0
    cleaned_article_map = {}

    for url, art in article_map.items():
        # Test existing item against strict verification
        if verify_byline(url, headers):
            cleaned_article_map[url] = art
        else:
            print(f"  🗑️ Removing non-bylined item: {art.get('title', url)[:50]}...")
            purged_count += 1
        time.sleep(0.3)

    print(f"Audit complete. Removed {purged_count} non-bylined articles.\n")
    article_map = cleaned_article_map

    # -------------------------------------------------------------
    # NEW FEED DISCOVERY PASS
    # -------------------------------------------------------------
    candidate_urls = fetch_recent_from_author_page(headers)
    newly_added = 0

    for url in candidate_urls:
        if url in article_map:
            continue
            
        print(f"Evaluating candidate URL: {url}")
        
        if not verify_byline(url, headers):
            print(f"  ❌ Skipped (Byline verification failed)")
            continue

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            title = "Verified Article"
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
                
            pub_date = datetime.now().strftime('%Y-%m-%d')
            for meta_name in ['article:published_time', 'pubdate', 'publish-date', 'date']:
                meta = soup.find('meta', property=meta_name) or soup.find('meta', attrs={'name': meta_name})
                if meta and meta.get('content'):
                    try:
                        pub_date = meta['content'][:10]
                        break
                    except Exception:
                        pass
            
            article_map[url] = {
                "title": title,
                "url": url,
                "date": pub_date,
                "scraped_at": datetime.now().isoformat()
            }
            newly_added += 1
            print(f"  ✅ Verified & Logged: {title} ({pub_date})")
            time.sleep(0.5)
        except Exception as ex:
            print(f"  [Error parsing item]: {ex}")

    # Sort globally descending by date (newest first)
    all_articles = list(article_map.values())
    all_articles.sort(key=lambda x: x.get('date', '1900-01-01'), reverse=True)

    with open('articles.json', 'w') as f:
        json.dump(all_articles, f, indent=4)
        
    print(f"\nSync complete. Purged: {purged_count} | Added: {newly_added} | Total archive size: {len(all_articles)}")

if __name__ == "__main__":
    sync_author_ledger()
