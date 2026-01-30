from scraper.scrapers.pracuj_scraper import PracujScraper
import logging

logging.basicConfig(level=logging.INFO)

def test_pracuj():
    print("Testing Pracuj.pl Scraper...")
    scraper = PracujScraper()
    
    # 1. Test fetching first page
    print(f"Fetching {scraper.jobs_url}...")
    jobs = scraper.fetch_jobs(max_pages=1)
    
    print(f"Found {len(jobs)} jobs")
    
    if jobs:
        print("\nFirst 3 jobs:")
        for i, job in enumerate(jobs[:3], 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Salary: {job['salary']}")
            print(f"   URL: {job['url']}")
        
        # Test parsing details
        print("\n\nTesting detail parsing for first job...")
        detailed = scraper.parse_job(jobs[0])
        if detailed.get('description'):
            print(f"✅ Description found: {detailed['description'][:100]}...")
        else:
            print("❌ No description found")
    else:
        print("❌ No jobs found. Might be blocked by Cloudflare.")

if __name__ == "__main__":
    test_pracuj()
