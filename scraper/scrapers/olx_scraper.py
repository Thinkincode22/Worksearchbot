"""Скрапер для OLX.pl"""
from typing import List, Dict
from scraper.base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class OLXScraper(BaseScraper):
    """Скрапер для OLX.pl"""
    
    def __init__(self):
        super().__init__(
            source_name="olx",
            base_url="https://www.olx.pl"
        )
        self.jobs_url = "https://www.olx.pl/praca/"
    
    def fetch_jobs(self, max_pages: int = 5) -> List[Dict]:
        """Отримує список вакансій з OLX"""
        jobs = []
        
        try:
            for page in range(1, max_pages + 1):
                url = f"{self.jobs_url}?page={page}"
                html = self.fetch_page(url)
                
                if not html:
                    continue
                
                soup = self.parse_html(html)
                job_elements = soup.find_all('div', {'data-cy': 'l-card'})
                
                for element in job_elements:
                    try:
                        job_data = self._extract_job_data(element)
                        if job_data:
                            jobs.append(job_data)
                    except Exception as e:
                        logger.error(f"Помилка при парсингу вакансії: {e}")
                        continue
                
                # Затримка між сторінками
                import time
                time.sleep(2)
        
        except Exception as e:
            logger.error(f"Помилка при отриманні вакансій з OLX: {e}")
        
        return jobs
    
    def _extract_job_data(self, element) -> Dict:
        """Витягує дані вакансії з елемента"""
        try:
            # Знаходимо посилання
            link_elem = element.find('a', href=True)
            if not link_elem:
                return None
            
            url = link_elem['href']
            if not url.startswith('http'):
                url = self.base_url + url
            
            # Знаходимо заголовок
            title_elem = element.find('h6') or element.find('a')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Знаходимо локацію
            location_elem = element.find('p', {'data-testid': 'location-date'})
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Знаходимо ціну (зарплату)
            price_elem = element.find('p', {'data-testid': 'ad-price'})
            salary = price_elem.get_text(strip=True) if price_elem else ""
            
            return {
                'source_id': url.split('/')[-1],
                'title': title,
                'location': location,
                'salary': salary,
                'url': url,
                'published_date': None,  # OLX не завжди показує дату в списку
            }
        except Exception as e:
            logger.error(f"Помилка при витягуванні даних: {e}")
            return None
    
    def parse_job(self, job_data: Dict) -> Dict:
        """Парсить деталі вакансії"""
        # Отримуємо детальну сторінку
        html = self.fetch_page(job_data['url'])
        
        if html:
            soup = self.parse_html(html)
            
            # Знаходимо опис
            desc_elem = soup.find('div', {'data-cy': 'ad_description'})
            if desc_elem:
                job_data['description'] = desc_elem.get_text(strip=True)
            
            # Знаходимо компанію (якщо є)
            company_elem = soup.find('div', {'data-testid': 'ad-contact'})
            if company_elem:
                job_data['company'] = company_elem.get_text(strip=True)
        
        return self.normalize_data(job_data)
