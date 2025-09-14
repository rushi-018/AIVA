"""
perception.py: Minimal Perception Layer for AIVA
- Handles DOM parsing and candidate extraction for e-commerce platforms
- For demo: only Flipkart, using Selenium
- Provides get_flipkart_candidates() function
"""
import logging
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def create_edge_driver() -> webdriver.Edge:
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.common.service import utils
    
    opts = EdgeOptions()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--remote-allow-origins=*")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--allow-running-insecure-content")
    opts.add_argument("--disable-extensions")
    
    try:
        # Try with automatic driver management
        return webdriver.Edge(options=opts)
    except Exception as e1:
        try:
            # Try with webdriver-manager for automatic driver download
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            service = Service(EdgeChromiumDriverManager().install())
            return webdriver.Edge(service=service, options=opts)
        except Exception as e2:
            # Fallback: try Chrome if Edge fails
            try:
                from selenium.webdriver.chrome.options import Options as ChromeOptions
                chrome_opts = ChromeOptions()
                chrome_opts.add_argument("--start-maximized")
                chrome_opts.add_argument("--disable-notifications")
                chrome_opts.add_argument("--disable-infobars")
                chrome_opts.add_argument("--no-first-run")
                chrome_opts.add_argument("--no-default-browser-check")
                chrome_opts.add_argument("--remote-allow-origins=*")
                chrome_opts.add_argument("--disable-gpu")
                return webdriver.Chrome(options=chrome_opts)
            except Exception as e3:
                raise Exception(f"Could not create webdriver. Edge error: {e1}, WebDriver Manager error: {e2}, Chrome error: {e3}")

def get_flipkart_candidates(product: str, price_limit: Optional[int] = None, max_items: int = 5) -> List[Dict]:
    """Searches Flipkart for a product and extracts item titles and prices."""
    try:
        driver = create_edge_driver()
    except Exception as e:
        logging.error(f"Could not create driver: {e}")
        return []
    
    driver.get("https://www.flipkart.com/")
    wait = WebDriverWait(driver, 15)
    try:
        # Close login popup if present
        try:
            close_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "✕")]')))
            close_btn.click()
        except Exception:
            pass
        
        # Search for product
        search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        search_box.clear()
        search_box.send_keys(product)
        search_box.send_keys(Keys.ENTER)
        
        # Wait for results with multiple possible selectors
        time.sleep(3)  # Give page time to load
        
        # Try multiple selectors for product cards
        items = []
        possible_selectors = [
            '//div[contains(@class, "_1AtVbE")]',
            '//div[contains(@class, "_2kHMtA")]',
            '//div[contains(@class, "_1YokD2")]',
            '//div[contains(@class, "col-12")]',
            '//div[contains(@data-id, "")]',
            '//a[contains(@class, "_1fQZEK")]'
        ]
        
        cards = []
        for selector in possible_selectors:
            try:
                cards = driver.find_elements(By.XPATH, selector)
                if cards:
                    logging.info(f"Found {len(cards)} elements with selector: {selector}")
                    break
            except Exception:
                continue
        
        if not cards:
            logging.warning("No product cards found, trying generic approach")
            # Try to find any clickable elements with text that might be products
            cards = driver.find_elements(By.XPATH, '//div[contains(text(), "₹") or contains(text(), "Price")]/..')
        
        for card in cards[:max_items * 2]:  # Get more than needed in case some fail
            try:
                # Try multiple ways to get title
                title = None
                title_selectors = [
                    './/div[contains(@class, "_4rR01T")]',
                    './/div[contains(@class, "s1Q9rs")]',
                    './/a[contains(@class, "IRpwTa")]',
                    './/span[contains(@class, "_35KyD6")]',
                    './/h3',
                    './/h4',
                    './/div[@class="KzDlHZ"]',
                    './/span[@class="_35KyD6"]'
                ]
                
                for sel in title_selectors:
                    try:
                        title_el = card.find_element(By.XPATH, sel)
                        title = title_el.text.strip()
                        if title and len(title) > 5:  # Basic validation
                            break
                    except Exception:
                        continue
                
                if not title:
                    continue
                
                # Try multiple ways to get price
                price = None
                price_selectors = [
                    './/div[contains(@class, "_30jeq3")]',
                    './/div[contains(@class, "_1_TelR")]',
                    './/span[contains(@class, "_1_TelR")]',
                    './/*[contains(text(), "₹")]',
                    './/div[contains(text(), "₹")]'
                ]
                
                for sel in price_selectors:
                    try:
                        price_el = card.find_element(By.XPATH, sel)
                        price_text = price_el.text.replace('₹', '').replace(',', '').strip()
                        # Extract just the numbers
                        import re
                        price_match = re.search(r'\d+', price_text)
                        if price_match:
                            price = int(price_match.group())
                            break
                    except Exception:
                        continue
                
                if price_limit and price and price > price_limit:
                    continue
                
                if title and price:
                    items.append({"title": title, "price": price})
                    if len(items) >= max_items:
                        break
                        
            except Exception as e:
                logging.debug(f"Error processing card: {e}")
                continue
        
        logging.info(f"Found {len(items)} items on Flipkart.")
        return items
        
    except Exception as e:
        logging.error(f"Error during Flipkart search: {e}")
        return []
    finally:
        driver.quit()

if __name__ == "__main__":
    print("AIVA Perception Demo: Search Flipkart for a product.")
    prod = input("Product name: ")
    price = input("Max price (optional): ")
    price_limit = int(price) if price.strip().isdigit() else None
    results = get_flipkart_candidates(prod, price_limit)
    print("Results:")
    for item in results:
        print(f"- {item['title']} | ₹{item['price']}")
