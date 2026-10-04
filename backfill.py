import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import time

def backfill_archive():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
    # 1. Check if the backfill URL file exists
    if not os.path.exists('backfill_urls.txt'):
        print("Error: 'backfill_urls.txt' not found. Create it and add URLs, one per line.")
        return

    with open('backfill_urls.txt', 'r') as f:
        urls_to_process = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    if not urls_to_process:
        print("No URLs found in backfill_urls.txt.")
        return

    # 2. Load existing articles.json
    existing_articles = []
    if os.path.exists('articles.json'):
        try:
            with open('articles.json', 'r') as f:
                existing_articles = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load existing articles.json: {e}")

    article_map = {art['url']: art for art in existing_articles}
    added_count = 0

    print(f"Starting backfill for {len(urls_to_process)} URLs...")

    # 3. Process each URL
    for url in urls_to_process:
        if url in article_map:
            print(f"  Skipping (already in archive): {url}")
            continue

        print(f"Fetching metadata for: {url}")
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Extract title
            title = "Verified Article"
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)

            # Extract true publication date from meta tags
            pub_date = None
            for meta_name in ['article:published_time', 'pubdate', 'publish-date', 'date']:
                meta = soup.find('meta', property=meta_name) or soup.find('meta', attrs={'name': meta_name})
                if meta and meta.get('content'):
                    try:
                        pub_date = meta['content'][:10]
                        break
                    except Exception:
                        pass

            # Fallback date if meta tags are missing
            if not pub_date:
                pub_date = "2025-01-01" 

            article_map[url] = {
                "title": title,
                "url": url,
                "date": pub_date,
                "scraped_at": datetime.now().isoformat()
            }
            added_count += 1
            print(f"    ✅ Added: [{pub_date}] {title}")
            
            # Be polite to the server
            time.sleep(0.5)

        except Exception as ex:
            print(f"    ❌ Error processing URL: {ex}")

    # 4. Sort globally descending by date and save back out
    all_articles = list(article_map.values())
    all_articles.sort(key=lambda x: x.get('date', '1900-01-01'), reverse=True)

    with open('articles.json', 'w') as f:
        json.dump(all_articles, f, indent=4)

    print(f"\nBackfill complete! Successfully added {added_count} historical items. Total archive size: {len(all_articles)}")

if __name__ == "__main__":
    backfill_archive()
