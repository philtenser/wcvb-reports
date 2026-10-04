import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

AUTHOR_PAGE_URL = "https://www.wcvb.com/news-team/36aab4e9-2df6-4970-8bac-c1139192e0ca"

def fetch_recent_from_author_page():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
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
                    
        return found_urls[:10]
    except Exception as e:
        print(f"Error fetching author page: {e}")
        return []

def sync_author_ledger():
    existing_articles = []
    if os.path.exists('articles.json'):
        try:
            with open('articles.json', 'r') as f:
                existing_articles = json.load(f)
        except Exception:
            pass

    article_map = {art['url']: art for art in existing_articles}
    recent_urls = fetch_recent_from_author_page()
    
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    newly_added = 0

    for url in recent_urls:
        if url in article_map:
            continue
            
        print(f"New item detected from feed: {url}")
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            title = "Verified Article"
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
                
            pub_date = datetime.now().strftime('%Y-%m-%d')
            for meta_name in ['article:published_time', 'pubdate', 'date']:
                meta = soup.find('meta', property=meta_name) or soup.find('meta', attrs={'name': meta_name})
                if meta and meta.get('content'):
                    pub_date = meta['content'][:10]
                    break
            
            article_map[url] = {
                "title": title,
                "url": url,
                "date": pub_date,
                "scraped_at": datetime.now().isoformat()
            }
            newly_added += 1
            print(f"  ✅ Logged: {title} ({pub_date})")
        except Exception as ex:
            print(f"  [Error parsing item]: {ex}")

    all_articles = list(article_map.values())
    all_articles.sort(key=lambda x: x.get('date', '1900-01-01'), reverse=True)

    with open('articles.json', 'w') as f:
        json.dump(all_articles, f, indent=4)
        
    print(f"Sync complete. Added {newly_added} new items from your feed.")

if __name__ == "__main__":
    sync_author_ledger()
