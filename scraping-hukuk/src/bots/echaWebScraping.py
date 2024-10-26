import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Tuple
from src.utils.baseScrapper import BaseScraper
from urllib.parse import urljoin



class EchaWebScraper(BaseScraper):
    def __init__(self, key_words: List[str], base_url: str, limited_pages: int, driver):
        """
        Initializes the EchaWebScraper class with keywords for searching and Selenium WebDriver.
        """
        super().__init__(key_words, base_url, limited_pages, driver, site_name="ECHA")
        self.driver.get(self.base_url)

    def search_for_keyword(self, keyword: str):
        """
        ECHA web sitesinde anahtar kelimeyle arama yapar.
        """
        self.logger.info(f"Searching for keyword: {keyword}")
        search_box = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "SimpleSearchText"))
        )
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)

    def select_date(self, year: int, month: int, day: int):
        """
        Arama sonucunu tarih filtresi ile sınırlar.
        """
        self.logger.info(f"Selecting date: {year}-{month}-{day}")
        from_date_picker = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//input[contains(@id, '_echasearch_WAR_echaportlet_updatedFrom')]"))
        )
        from_date_picker.click()

        year_select_element = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//select[contains(@class, 'ui-datepicker-year')]"))
        )

        year_select = Select(year_select_element)
        year_select.select_by_value(str(year))

        month_select_element = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//select[contains(@class, 'ui-datepicker-month')]"))
        )
        month_select = Select(month_select_element)
        month_select.select_by_value(str(month - 1))

        day_element = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH,
                                        f"//td[@data-handler='selectDay' and @data-month='{month - 1}' and @data-year='{year}']/a[text()='{day}']"))
        )
        day_element.click()

    def sort_by_last_modified(self):
        """
        Arama sonuçlarını "Son Düzenlenme" tarihine göre sıralar.
        """
        self.logger.info("Sorting by last modified date.")
        sort_by_select = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//select[contains(@id, '_echasearch_WAR_echaportlet_sortingType')]"))
        )
        sort_by_select.click()
        last_modified_option = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//option[@value='modified']"))
        )
        last_modified_option.click()

    def get_urls(self, keyword: str, limited_page: int) -> Tuple[List[Tuple[str, str, str, str]], List[Tuple[str, str, str, str]]]:
        """
        Arama sonuçlarından PDF ve PDF olmayan URL'leri toplar.
        """
        pdf_urls = []
        non_pdf_urls = []
        matching_links = []


        self.driver.get(self.base_url)

        try:
            self.logger.info(f"Retrieving URLs for keyword: {keyword}")
            self.search_for_keyword(keyword)
            self.select_date(2012, 8, 9)
            self.sort_by_last_modified()
            time.sleep(3)
            page_number = 1

            while True:
                self.logger.info(f"Processing page number: {page_number}")
                results = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[contains(@class, 'search-result-title')]//a[@href]"))
                )
                dates = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH,
                         "//div[contains(@class, 'search-result-title')]//a[@href]/../../following-sibling::td"))
                )
                descriptions = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'search-result-content')]"))
                )

                for result, date, description in zip(results, dates, descriptions):
                    link = result.get_attribute("href")
                    name = result.text.strip()
                    # Linke gidip içerikten veri çekme
                    description_text = self.get_description_from_link(link, keyword)


                    if link.startswith('/'):
                        link = 'https://echa.europa.eu' + link
                    formatted_date = date.text.strip().replace('/', '-')
                    day, month, year = formatted_date.split('-')
                    year = '20' + year
                    formatted_date = f"{year}-{month}-{day}"

                    unique_name = f"{formatted_date}-{name}".replace('/', '_').replace(':', '').replace(' ', '_').replace('\n',
                                                                                                                '_')

                    # Ensure the name is unique
                    counter = 1
                    base_name = unique_name
                    while any(unique_name in item for item in matching_links):
                        unique_name = f"{base_name}-{counter}"
                        counter += 1

                    if link.split('/')[-2].endswith('.pdf'):
                        pdf_urls.append((link, formatted_date, unique_name, description_text))
                    else:
                        non_pdf_urls.append((link, formatted_date, unique_name, description_text))

                self.logger.info(f"Found {len(pdf_urls)} PDF URLs and {len(non_pdf_urls)} non-PDF URLs.")

                if limited_page == 0:
                    limited_page = float('inf')

                if page_number < limited_page:
                    page_number += 1
                    # 'Next' butonunu bulun
                    next_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Next')]")
                    if next_buttons:
                        next_button = next_buttons[0]
                        # 'Next' butonunun etkin olup olmadığını kontrol edin
                        if next_button.is_enabled() and next_button.get_attribute('href') != "javascript:;":
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                                next_button.click()
                                time.sleep(2)
                            except Exception as e:
                                self.logger.info("Cannot click on 'Next' button. Ending the scraping process.")
                                self.log_error(e, self.driver.current_url)
                                break  # 'Next' butonuna tıklanamazsa döngüden çıkın
                        else:
                            self.logger.info(
                                "'Next' button is not enabled or points to 'javascript:;'. Ending the scraping process.")
                            break  # 'Next' butonu etkin değilse döngüden çıkın
                    else:
                        self.logger.info("No 'Next' button found. Ending the scraping process.")
                        break  # 'Next' butonu bulunamazsa döngüden çıkın
                else:
                    break  # Sayfa limitine ulaşıldıysa döngüden çıkın

        except Exception as e:
            self.log_error(e, self.driver.current_url)

        return pdf_urls, non_pdf_urls

    def get_description_from_link(self, link: str, keyword: str) -> str:
        self.logger.info(f"Visiting link: {link}")

        # PDF linklerini kontrol edin
        if link.split('/')[-2].endswith('.pdf'):
            self.logger.info(f"Link is a PDF, setting description accordingly: {link}")
            return 'this is a pdf link'

        try:
            # Mevcut pencereyi kaydedin ve yeni bir sekme açın
            current_window = self.driver.current_window_handle
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(link)

            # Sayfanın yüklenmesini bekleyin
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )

            # Sayfa kaynağını alın ve BeautifulSoup ile parse edin
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # script, style ve diğer istenmeyen etiketleri kaldırın
            for element in soup(['script', 'style', 'noscript', 'iframe', 'header', 'footer', 'nav']):
                element.decompose()

            # 'journal-content-article' sınıfına odaklanın
            content_divs = soup.find_all('div', class_='journal-content-article')

            description_texts = []

            if content_divs:
                for div in content_divs:
                    # Div içindeki tüm metni alın
                    text = div.get_text(separator=' ', strip=True)
                    description_texts.append(text)
            else:
                self.logger.info('No content found in journal-content-article class.')

            # Tekrarlayan metinleri kaldırın
            description_texts = list(set(description_texts))

            # Metinleri birleştirin
            description_text = '\n'.join(description_texts)

            # Sekmeyi kapatın ve ana pencereye dönün
            self.driver.close()
            self.driver.switch_to.window(current_window)

            return description_text

        except Exception as e:
            self.log_error(e, link)
            # Sekmeyi kapatın ve ana pencereye dönün
            self.driver.close()
            self.driver.switch_to.window(current_window)
            return ''







