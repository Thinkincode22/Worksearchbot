from scraper.scrapers.pracuj_scraper import PracujScraper
import json

scraper = PracujScraper()
html = scraper.fetch_page("https://www.pracuj.pl/praca/wroclaw")

import re
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html, re.DOTALL)

if match:
    data = json.loads(match.group(1))
    
    # Знаходимо offers
    def find_offers(d):
        if isinstance(d, dict):
            if 'offers' in d and isinstance(d['offers'], list):
                return d['offers']
            if 'groupedOffers' in d:
                return d['groupedOffers']
            for v in d.values():
                result = find_offers(v)
                if result:
                    return result
        elif isinstance(d, list):
            for item in d:
                result = find_offers(item)
                if result:
                    return result
        return []
    
    offers = find_offers(data)
    
    if offers:
        print(f"Found {len(offers)} offers")
        print("\nFirst offer keys:")
        print(json.dumps(offers[0], indent=2, ensure_ascii=False)[:1000])
