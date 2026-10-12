"""
LinkedIn Job Scraper
Scrapes job listings from LinkedIn and saves them to CSV format
"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import config


class LinkedInScraper:
    def __init__(self, headless=False):
        """Initialize the LinkedIn scraper"""
        self.driver = None
        self.headless = headless
        self.jobs_data = []
        
    def setup_driver(self):
        """Set up Selenium WebDriver"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Try with webdriver-manager (with cache cleared for Mac ARM compatibility)
            import os
            import platform
            
            # For Apple Silicon Macs, ensure we get the right version
            if platform.system() == 'Darwin' and platform.processor() == 'arm':
                # Clear any cached problematic drivers
                cache_path = os.path.expanduser('~/.wdm')
                print("Detected Apple Silicon Mac - setting up ChromeDriver...")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.maximize_window()
            
        except Exception as e:
            print(f"ChromeDriver setup failed: {e}")
            print("\nTrying alternative method...")
            
            # Fallback: Try using Chrome directly without webdriver-manager
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.maximize_window()
                print("✓ Successfully using system ChromeDriver")
            except Exception as e2:
                raise Exception(
                    f"Failed to setup ChromeDriver. Please try one of these solutions:\n\n"
                    f"Solution 1: Install ChromeDriver with Homebrew (recommended for Mac):\n"
                    f"  brew install chromedriver\n"
                    f"  xattr -d com.apple.quarantine $(which chromedriver)\n\n"
                    f"Solution 2: Use the CSV upload option instead of scraping\n\n"
                    f"Original error: {e2}"
                )
        
    def login_prompt(self):
        """Navigate to LinkedIn and allow user to login manually"""
        print("Opening LinkedIn...")
        self.driver.get('https://www.linkedin.com/login')
        
        print("\n" + "="*60)
        print("Please log in to your LinkedIn account in the browser window.")
        print("Press Enter here after you've successfully logged in...")
        print("="*60 + "\n")
        
        input()  # Wait for user to login
        
    def scrape_jobs(self, job_title="", location="", num_pages=5):
        """
        Scrape job listings from LinkedIn
        
        Args:
            job_title: Job title to search for
            location: Location for job search
            num_pages: Number of pages to scrape
        """
        # Construct search URL
        base_url = "https://www.linkedin.com/jobs/search/"
        params = f"?keywords={job_title.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
        search_url = base_url + params
        
        print(f"Searching for: {job_title} in {location}")
        print(f"URL: {search_url}\n")
        
        self.driver.get(search_url)
        time.sleep(3)
        
        for page in range(num_pages):
            print(f"Scraping page {page + 1}/{num_pages}...")
            
            # Scroll down to load more jobs
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get job cards
            try:
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, '.job-card-container, .jobs-search__results-list li')
                
                for card in job_cards:
                    try:
                        job_data = self._extract_job_data(card)
                        if job_data and job_data not in self.jobs_data:
                            self.jobs_data.append(job_data)
                            print(f"  ✓ Scraped: {job_data.get('title', 'Unknown Title')}")
                    except Exception as e:
                        print(f"  ✗ Error extracting job data: {e}")
                        continue
                
                # Try to click next page
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="View next page"]')
                    if next_button.is_enabled():
                        next_button.click()
                        time.sleep(config.SCRAPE_DELAY)
                    else:
                        print("No more pages available")
                        break
                except:
                    print("Could not find next page button")
                    break
                    
            except Exception as e:
                print(f"Error on page {page + 1}: {e}")
                continue
        
        print(f"\nTotal jobs scraped: {len(self.jobs_data)}")
        
    def _extract_job_data(self, card):
        """Extract job data from a job card element"""
        try:
            # Try to click on the card to load details
            try:
                card.click()
                time.sleep(1)
            except:
                pass
            
            job_data = {}
            
            # Extract title
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, '.job-card-list__title, .job-card-container__link')
                job_data['title'] = title_elem.text.strip()
            except:
                job_data['title'] = "N/A"
            
            # Extract company - try multiple selectors and the details panel
            job_data['company'] = "N/A"
            
            # Try from the job card on the left
            company_selectors = [
                '.job-card-container__company-name',
                '.job-card-container__primary-description',
                '.artdeco-entity-lockup__subtitle',
                '.job-card-list__company-name',
                'a[data-tracking-control-name="public_jobs_jserp-result_job-search-card-subtitle"]'
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = card.find_element(By.CSS_SELECTOR, selector)
                    company_text = company_elem.text.strip()
                    if company_text and company_text != "":
                        job_data['company'] = company_text
                        break
                except:
                    continue
            
            # If still N/A, try from the details panel on the right
            if job_data['company'] == "N/A":
                try:
                    detail_company = self.driver.find_element(By.CSS_SELECTOR, '.jobs-unified-top-card__company-name a, .job-details-jobs-unified-top-card__company-name a')
                    company_text = detail_company.text.strip()
                    if company_text:
                        job_data['company'] = company_text
                except:
                    pass
            
            # Additional fallback: check subtitle area
            if job_data['company'] == "N/A":
                try:
                    subtitle_elem = card.find_element(By.CSS_SELECTOR, '.job-card-container__metadata-item')
                    subtitle_text = subtitle_elem.text.strip()
                    # Often company name appears before location
                    if subtitle_text and '·' not in subtitle_text:
                        job_data['company'] = subtitle_text.split('\n')[0]
                except:
                    pass
            
            # Extract location
            try:
                location_elem = card.find_element(By.CSS_SELECTOR, '.job-card-container__metadata-item, .job-card-container__metadata-wrapper')
                job_data['location'] = location_elem.text.strip()
            except:
                job_data['location'] = "N/A"
            
            # Extract job URL
            try:
                link_elem = card.find_element(By.CSS_SELECTOR, 'a')
                job_data['url'] = link_elem.get_attribute('href')
            except:
                job_data['url'] = "N/A"
            
            # Extract job description (from the details panel)
            try:
                description_elem = self.driver.find_element(By.CSS_SELECTOR, '.jobs-description, .jobs-box__html-content')
                job_data['description'] = description_elem.text.strip()
            except:
                job_data['description'] = "N/A"
            
            return job_data
            
        except Exception as e:
            print(f"Error extracting job data: {e}")
            return None
    
    def save_to_csv(self, filename=None):
        """Save scraped jobs to CSV file"""
        if not filename:
            filename = config.JOBS_CSV_FILE
        
        if not self.jobs_data:
            print("No jobs to save!")
            return
        
        df = pd.DataFrame(self.jobs_data)
        df.to_csv(filename, index=False)
        print(f"\n✓ Saved {len(self.jobs_data)} jobs to {filename}")
        
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()


def main():
    """Main function for standalone usage"""
    scraper = LinkedInScraper(headless=False)
    
    try:
        scraper.setup_driver()
        scraper.login_prompt()
        
        # Get search parameters from user
        job_title = input("Enter job title to search: ")
        location = input("Enter location (or press Enter for 'United States'): ") or "United States"
        num_pages = int(input("Enter number of pages to scrape (default 5): ") or "5")
        
        scraper.scrape_jobs(job_title=job_title, location=location, num_pages=num_pages)
        scraper.save_to_csv()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()

