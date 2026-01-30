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
        self.jobs_url = "https://www.olx.pl/praca/wroclaw/"  # Фільтр по Вроцлаву
    
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
            # Знаходимо посилання на вакансію (шукаємо лінк що містить '/oferta/')
            links = element.find_all('a', href=True)
            link_elem = None
            for link in links:
                if '/oferta/' in link['href'] or '/d/' in link['href']:
                    link_elem = link
                    break
            
            if not link_elem:
                return None
            
            url = link_elem['href']
            if not url.startswith('http'):
                url = self.base_url + url
            
            # Заголовок - текст з того ж лінка
            title = link_elem.get_text(strip=True) if link_elem else ""
            
            # Отримуємо весь текст з картки для пошуку інфо
            card_text = element.get_text('\n', strip=True)
            text_lines = [line.strip() for line in card_text.split('\n') if line.strip()]
            
            # Шукаємо зарплату (містить 'zł')
            salary = ""
            for line in text_lines:
                if 'zł' in line.lower():
                    salary = line
                    break
            
            # Шукаємо локацію (зазвичай містить назву міста)
            location = ""
            for line in text_lines:
                # Пропускаємо зарплату і заголовок
                if line == title or line == salary:
                    continue
                # Шукаємо рядок що схожий на локацію (містить велику літеру на початку)
                if line and line[0].isupper() and len(line) < 50:
                    # Перевіряємо чи не дата це
                    if not any(word in line.lower() for word in ['dzisiaj', 'wczoraj', 'odświeżono', 'dodane']):
                        location = line
                        break
            
            return {
                'source_id': url.split('/')[-1].replace('.html', ''),
                'title': title,
                'location': location,
                'salary': salary,
                'url': url,
                'published_date': None,
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
            
            # Знаходимо опис - використовуємо різні селектори
            desc_elem = (
                soup.find('div', class_='css-1i3492') or  # Основний селектор для опису
                soup.find('div', {'data-cy': 'ad_description'}) or
                soup.find('div', class_=lambda x: x and 'description' in x.lower())
            )
            
            if desc_elem:
                job_data['description'] = desc_elem.get_text(strip=True)
            
            # Також можемо додати інформацію з інших секцій
            benefits_elem = soup.find('div', {'data-testid': 'benefits-content'})
            if benefits_elem and not job_data.get('description'):
                job_data['description'] = benefits_elem.get_text(strip=True)
            
            # Знаходимо компанію (якщо є)
            company_elem = (
                soup.find('div', {'data-testid': 'ad-contact'}) or
                soup.find('h4', class_=lambda x: x and 'seller' in x.lower())
            )
            
            if company_elem:
                company_text = company_elem.get_text(strip=True)
                job_data['company'] = company_text.split('\n')[0] if company_text else ""
        
        return self.normalize_data(job_data)
