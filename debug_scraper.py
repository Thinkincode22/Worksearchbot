from scraper.scrapers.olx_scraper import OLXScraper
import logging

logging.basicConfig(level=logging.INFO)

def test_scraper():
    print("Testing OLX Scraper...")
    scraper = OLXScraper()
    
    # 1. Test fetching a single page
    print(f"Fetching {scraper.jobs_url}...")
    html = scraper.fetch_page(scraper.jobs_url)
    
    if not html:
        print("❌ Failed to fetch page. Blocked or network issue.")
        return
    
    print(f"✅ Page fetched. Length: {len(html)} chars")
    
    # 2. Test parsing
    print("Parsing HTML...")
    soup = scraper.parse_html(html)
    job_elements = soup.find_all('div', {'data-cy': 'l-card'})
    
    print(f"Found {len(job_elements)} job cards with data-cy='l-card'")
    
    if len(job_elements) == 0:
        print("⚠️ No jobs found. Selectors might be outdated.")
        # Try to print some other elements to see what we got
        print("Debug: Title of page:", soup.title.string if soup.title else "No title")
    else:
        print("✅ Selectors seem to work.")
        # Try to extract one
        first_job = scraper._extract_job_data(job_elements[0])
        print("First job data (List view):", first_job)
        
        # 3. Test parsing details
        print(f"Fetching details for {first_job['url']}...")
        detailed_job = scraper.parse_job(first_job)
        print("Detailed job data:", detailed_job)
        
        if not detailed_job.get('description'):
             print("❌ Description missing! Selector might be wrong.")
        else:
             print(f"✅ Description found: {detailed_job['description'][:50]}...")

if __name__ == "__main__":
    test_scraper()
