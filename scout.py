def verify_byline(url, headers):
    """Strictly verify that Phil Tenser is listed as an author in metadata."""
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Check JSON-LD Structured Data (Most reliable for news CMS author fields)
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

        # 3. Check specific byline DOM containers (avoiding random body mentions)
        byline_elements = soup.select('[class*="byline"], [class*="author"], [class*="contributor"], [data-testid*="author"]')
        for element in byline_elements:
            if "phil tenser" in element.get_text().lower():
                return True

        return False
    except Exception as e:
        print(f"  [Error verifying byline] Skipping {url}: {e}")
        return False
