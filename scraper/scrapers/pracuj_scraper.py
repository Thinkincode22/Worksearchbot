"""Скрапер для Pracuj.pl"""
from typing import Dict, List
from scraper.base_scraper import BaseScraper
import json
import re
from loguru import logger


class PracujScraper(BaseScraper):
    """Скрапер для Pracuj.pl"""
    
    def __init__(self):
        super().__init__(
            source_name="pracuj",
            base_url="https://www.pracuj.pl"
        )
        self.jobs_url = "https://www.pracuj.pl/praca/wroclaw"  # Фільтр по Вроцлаву
    
    def fetch_jobs(self, max_pages: int = 3) -> List[Dict]:
        """Отримує список вакансій з Pracuj.pl"""
        all_jobs = []
        
        for page in range(1, max_pages + 1):
            # Pracuj.pl використовує параметр pn для пагінації
            url = f"{self.jobs_url}?pn={page}" if page > 1 else self.jobs_url
            
            logger.info(f"Отримання сторінки {page}: {url}")
            html = self.fetch_page(url)
            
            if not html:
                logger.warning(f"Не вдалося отримати сторінку {page}")
                break
            
            # Шукаємо JSON дані Next.js
            jobs = self._extract_jobs_from_nextjs(html)
            
            if not jobs:
                logger.warning(f"Не знайдено вакансій на сторінці {page}")
                break
            
            all_jobs.extend(jobs)
            logger.info(f"Знайдено {len(jobs)} вакансій на сторінці {page}")
        
        return all_jobs
    
    def _extract_jobs_from_nextjs(self, html: str) -> List[Dict]:
        """Витягує вакансії з Next.js JSON"""
        try:
            # Шукаємо скрипт з __NEXT_DATA__
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html, re.DOTALL)
            
            if not match:
                logger.warning("Не знайдено __NEXT_DATA__ в HTML")
                return self._extract_jobs_from_html(html)  # Fallback до HTML парсингу
            
            data = json.loads(match.group(1))
            
            # Структура може відрізнятися, шукаємо offers
            jobs_data = self._find_offers_in_json(data)
            
            if not jobs_data:
                logger.warning("Не знайдено offers в JSON")
                return []
            
            jobs = []
            for job in jobs_data:
                try:
                    # Отримуємо дані з вкладених offers
                    nested_offers = job.get('offers', [])
                    
                    # Якщо є вкладені offers, беремо перший
                    if nested_offers and isinstance(nested_offers, list):
                        offer_id = nested_offers[0].get('partitionId', '')
                        # Будуємо URL з jobTitle та offer_id
                        job_title_slug = job.get('jobTitle', '').lower().replace(' ', '-').replace('/', '-')
                        # Видаляємо спеціальні символи
                        job_title_slug = ''.join(c for c in job_title_slug if c.isalnum() or c == '-')
                        url = f"{self.base_url}/praca/{job_title_slug},oferta,{offer_id}"
                    else:
                        # Fallback
                        url = self.base_url
                    
                    # Локація - беремо з displayWorkplace або будуємо з workplaces
                    location = job.get('displayWorkplace', '')
                    if not location and 'workplaces' in job:
                        workplaces = job.get('workplaces', [])
                        if workplaces and isinstance(workplaces, list):
                            location = workplaces[0].get('city', 'Wrocław')
                    if not location:
                        location = 'Wrocław'
                    
                    # Опис (короткий)
                    description = job.get('jobDescription', '')
                    
                    job_dict = {
                        'source_id': str(job.get('groupId', job.get('jobOfferId', ''))),
                        'title': job.get('jobTitle', ''),
                        'company': job.get('companyName', ''),
                        'location': location,
                        'salary': job.get('salaryDisplayText', ''),
                        'url': url,
                        'published_date': None,
                        'description': description,  # Додаємо короткий опис
                    }
                    jobs.append(job_dict)
                except Exception as e:
                    logger.error(f"Помилка при обробці вакансії: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Помилка при парсингу JSON: {e}")
            return []
    
    def _find_offers_in_json(self, data: dict) -> List:
        """Рекурсивно шукає offers в JSON структурі"""
        if isinstance(data, dict):
            if 'offers' in data and isinstance(data['offers'], list):
                return data['offers']
            if 'groupedOffers' in data:
                return data['groupedOffers']
            for value in data.values():
                result = self._find_offers_in_json(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_offers_in_json(item)
                if result:
                    return result
        return []
    
    def _extract_salary(self, job: dict) -> str:
        """Витягує зарплату з даних вакансії"""
        try:
            if 'salaryDisplayText' in job:
                return job['salaryDisplayText']
            if 'typicalEarningsFrom' in job or 'typicalEarningsTo' in job:
                from_sal = job.get('typicalEarningsFrom', '')
                to_sal = job.get('typicalEarningsTo', '')
                if from_sal and to_sal:
                    return f"{from_sal} - {to_sal} PLN"
                elif from_sal:
                    return f"від {from_sal} PLN"
                elif to_sal:
                    return f"до {to_sal} PLN"
        except:
            pass
        return ""
    
    def _extract_jobs_from_html(self, html: str) -> List[Dict]:
        """Fallback: витягує вакансії з HTML якщо JSON не спрацював"""
        soup = self.parse_html(html)
        jobs = []
        
        # Шукаємо всі h2 (заголовки вакансій)
        job_titles = soup.find_all('h2')
        
        for title_elem in job_titles:
            try:
                link_elem = title_elem.find_parent('a')
                if not link_elem or not link_elem.get('href'):
                    continue
                
                url = link_elem['href']
                if not url.startswith('http'):
                    url = self.base_url + url
                
                # Шукаємо компанію (h3)
                card = title_elem.find_parent('div')
                company_elem = card.find('h3') if card else None
                
                jobs.append({
                    'source_id': url.split(',')[-1] if ',' in url else '',
                    'title': title_elem.get_text(strip=True),
                    'company': company_elem.get_text(strip=True) if company_elem else '',
                    'location': 'Wrocław',  # За замовчуванням, бо ми фільтруємо по Вроцлаву
                    'salary': '',
                    'url': url,
                    'published_date': None,
                })
            except Exception as e:
                logger.error(f"Помилка при парсингу HTML вакансії: {e}")
                continue
        
        return jobs
    
    def parse_job(self, job_data: Dict) -> Dict:
        """Парсить деталі вакансії"""
        # Отримуємо детальну сторінку
        html = self.fetch_page(job_data['url'])
        
        if html:
            # Спробуємо витягнути з JSON
            try:
                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    # Шукаємо опис в JSON
                    description = self._find_description_in_json(data)
                    if description:
                        job_data['description'] = description
            except:
                pass
            
            # Якщо JSON не спрацював, пробуємо HTML
            if not job_data.get('description'):
                soup = self.parse_html(html)
                desc_elem = soup.find('div', class_=lambda x: x and 'description' in x.lower())
                if desc_elem:
                    job_data['description'] = desc_elem.get_text(strip=True)
        
        return self.normalize_data(job_data)
    
    def _find_description_in_json(self, data: dict) -> str:
        """Шукає опис вакансії в JSON"""
        if isinstance(data, dict):
            if 'sections' in data:
                for section in data['sections']:
                    if isinstance(section, dict) and section.get('sectionName') == 'description':
                        return section.get('textContent', '')
            for value in data.values():
                result = self._find_description_in_json(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_description_in_json(item)
                if result:
                    return result
        return ""
