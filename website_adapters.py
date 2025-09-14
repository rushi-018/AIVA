"""
website_adapters.py: Modular website adapters for different e-commerce platforms
Provides a common interface for different shopping websites.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class WebsiteAdapter(ABC):
    """Abstract base class for e-commerce website adapters."""
    
    def __init__(self, driver: webdriver.Chrome, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait
        self.name = self.__class__.__name__.replace('Adapter', '')
    
    @abstractmethod
    def get_base_url(self) -> str:
        """Get the base URL of the website."""
        pass
    
    @abstractmethod
    def get_login_url(self) -> str:
        """Get the login page URL."""
        pass
    
    @abstractmethod
    def search_products(self, query: str, max_price: float = None) -> List[Dict]:
        """Search for products and return list of product info."""
        pass
    
    @abstractmethod
    def add_to_cart(self, product_element) -> bool:
        """Add a product to cart."""
        pass
    
    @abstractmethod
    def remove_from_cart(self, product_title: str) -> bool:
        """Remove product from cart."""
        pass
    
    @abstractmethod
    def go_to_cart(self) -> bool:
        """Navigate to cart page."""
        pass
    
    @abstractmethod
    def check_login_status(self) -> str:
        """Check if user is logged in."""
        pass
    
    @abstractmethod
    def get_login_instructions(self) -> str:
        """Get platform-specific login instructions."""
        pass

class FlipkartAdapter(WebsiteAdapter):
    """Flipkart website adapter."""
    
    def get_base_url(self) -> str:
        return "https://www.flipkart.com"
    
    def get_login_url(self) -> str:
        return "https://www.flipkart.com/account/login"
    
    def search_products(self, query: str, max_price: float = None) -> List[Dict]:
        """Search products on Flipkart."""
        try:
            # Navigate to Flipkart and search
            self.driver.get(self.get_base_url())
            time.sleep(2)
            
            # Find search box
            search_selectors = [
                "input[name='q']",
                "input[placeholder*='Search']",
                "input[title='Search for products, brands and more']"
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not search_box:
                print("❌ Could not find search box")
                return []
            
            # Search for products
            search_box.clear()
            search_box.send_keys(query)
            search_box.submit()
            time.sleep(3)
            
            # Extract products
            products = []
            price_elements = self.driver.find_elements(By.XPATH, "//span[contains(text(), '₹')]")
            
            for price_elem in price_elements[:10]:  # Limit to first 10
                try:
                    price_text = price_elem.text.replace('₹', '').replace(',', '')
                    price = float(price_text.split()[0])
                    
                    if max_price and price > max_price:
                        continue
                    
                    # Get product title (parent elements)
                    product_container = price_elem.find_element(By.XPATH, "./ancestor::div[contains(@class, '_1AtVbE') or contains(@class, '_4rR01T')]")
                    title_element = product_container.find_element(By.XPATH, ".//a[contains(@class, 'IRpwTa')]")
                    title = title_element.text[:50] + "..." if len(title_element.text) > 50 else title_element.text
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'element': price_elem,
                        'link': title_element.get_attribute('href')
                    })
                    
                except Exception:
                    continue
            
            return products
            
        except Exception as e:
            print(f"❌ Error searching products: {e}")
            return []
    
    def add_to_cart(self, product_element) -> bool:
        """Add product to cart on Flipkart."""
        try:
            # Implementation from existing interactive_session.py
            # This would use the tab-aware add to cart logic
            return True  # Placeholder
        except Exception as e:
            print(f"❌ Error adding to cart: {e}")
            return False
    
    def remove_from_cart(self, product_title: str) -> bool:
        """Remove product from cart on Flipkart."""
        try:
            # Navigate to cart
            self.driver.get("https://www.flipkart.com/viewcart")
            time.sleep(3)
            
            # Use improved removal logic from interactive_session.py
            remove_selectors = [
                '//div[contains(@class, "_3dsJAO")]//span[contains(text(), "Remove")]',
                '//button[contains(text(), "Remove")]',
                '//span[contains(text(), "Remove")]'
            ]
            
            for selector in remove_selectors:
                try:
                    remove_elements = self.driver.find_elements(By.XPATH, selector)
                    if remove_elements:
                        remove_btn = remove_elements[0]
                        if remove_btn.is_displayed() and remove_btn.is_enabled():
                            self.driver.execute_script("arguments[0].click();", remove_btn)
                            time.sleep(2)
                            
                            # Handle confirmation
                            confirmation_selectors = [
                                '//div[contains(@class, "_2AkmmA")]//div[contains(text(), "Remove")]',
                                '//button[contains(text(), "Remove")]'
                            ]
                            
                            for conf_selector in confirmation_selectors:
                                try:
                                    confirm_elements = self.driver.find_elements(By.XPATH, conf_selector)
                                    for confirm_btn in confirm_elements:
                                        if confirm_btn.is_displayed():
                                            self.driver.execute_script("arguments[0].click();", confirm_btn)
                                            time.sleep(3)
                                            return True
                                except:
                                    continue
                            return True
                except:
                    continue
            return False
            
        except Exception as e:
            print(f"❌ Error removing from cart: {e}")
            return False
    
    def go_to_cart(self) -> bool:
        """Navigate to cart page."""
        try:
            self.driver.get("https://www.flipkart.com/viewcart")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Error navigating to cart: {e}")
            return False
    
    def check_login_status(self) -> str:
        """Check Flipkart login status."""
        try:
            # Check for login indicators
            page_source = self.driver.page_source.lower()
            
            if any(indicator in page_source for indicator in ["my account", "logout", "my orders"]):
                return "logged_in"
            elif any(indicator in page_source for indicator in ["login", "sign in", "sign up"]):
                return "not_logged_in"
            else:
                return "unknown"
                
        except Exception:
            return "unknown"
    
    def get_login_instructions(self) -> str:
        """Get Flipkart-specific login instructions."""
        return """
📋 Flipkart Login Instructions (OTP Required):
🔐 Flipkart uses OTP-based login for security
📱 Make sure you have access to your registered mobile number

Steps:
1. 📧 Enter your mobile number/email in the browser
2. 🔢 Click 'Request OTP' or 'Continue'
3. 📲 Check your SMS/WhatsApp for the OTP
4. 🔐 Enter the OTP when prompted
5. ✅ Click 'Verify' or 'Login'
"""

class AmazonAdapter(WebsiteAdapter):
    """Amazon website adapter."""
    
    def get_base_url(self) -> str:
        return "https://www.amazon.in"
    
    def get_login_url(self) -> str:
        return "https://www.amazon.in/ap/signin"
    
    def search_products(self, query: str, max_price: float = None) -> List[Dict]:
        """Search products on Amazon."""
        try:
            # Navigate to Amazon and search
            self.driver.get(self.get_base_url())
            time.sleep(2)
            
            # Find search box
            search_box = self.driver.find_element(By.ID, "twotabsearchtextbox")
            search_box.clear()
            search_box.send_keys(query)
            
            # Click search button
            search_btn = self.driver.find_element(By.ID, "nav-search-submit-button")
            search_btn.click()
            time.sleep(3)
            
            # Extract products
            products = []
            product_containers = self.driver.find_elements(By.CSS_SELECTOR, "[data-component-type='s-search-result']")
            
            for container in product_containers[:10]:
                try:
                    # Get title
                    title_elem = container.find_element(By.CSS_SELECTOR, "h2 a span")
                    title = title_elem.text[:50] + "..." if len(title_elem.text) > 50 else title_elem.text
                    
                    # Get price
                    price_elem = container.find_element(By.CSS_SELECTOR, ".a-price-whole")
                    price_text = price_elem.text.replace(',', '')
                    price = float(price_text)
                    
                    if max_price and price > max_price:
                        continue
                    
                    # Get link
                    link_elem = container.find_element(By.CSS_SELECTOR, "h2 a")
                    link = link_elem.get_attribute('href')
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'element': container,
                        'link': link
                    })
                    
                except Exception:
                    continue
            
            return products
            
        except Exception as e:
            print(f"❌ Error searching Amazon products: {e}")
            return []
    
    def add_to_cart(self, product_element) -> bool:
        """Add product to cart on Amazon."""
        try:
            # Amazon-specific add to cart logic
            return True  # Placeholder
        except Exception as e:
            print(f"❌ Error adding to cart: {e}")
            return False
    
    def remove_from_cart(self, product_title: str) -> bool:
        """Remove product from cart on Amazon."""
        try:
            # Amazon-specific removal logic
            return True  # Placeholder
        except Exception as e:
            print(f"❌ Error removing from cart: {e}")
            return False
    
    def go_to_cart(self) -> bool:
        """Navigate to Amazon cart."""
        try:
            self.driver.get("https://www.amazon.in/gp/cart/view.html")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Error navigating to cart: {e}")
            return False
    
    def check_login_status(self) -> str:
        """Check Amazon login status."""
        try:
            # Check for Amazon login indicators
            page_source = self.driver.page_source.lower()
            
            if "hello," in page_source or "your account" in page_source:
                return "logged_in"
            elif "sign in" in page_source:
                return "not_logged_in"
            else:
                return "unknown"
                
        except Exception:
            return "unknown"
    
    def get_login_instructions(self) -> str:
        """Get Amazon-specific login instructions."""
        return """
📋 Amazon Login Instructions:
🔐 Amazon uses email/mobile and password authentication

Steps:
1. 📧 Enter your email/mobile number
2. 🔐 Enter your password
3. ✅ Click 'Sign In'
4. 📱 Complete 2FA if prompted
"""

class WebsiteAdapterFactory:
    """Factory to create website adapters."""
    
    ADAPTERS = {
        'flipkart': FlipkartAdapter,
        'amazon': AmazonAdapter,
    }
    
    @classmethod
    def create_adapter(cls, website: str, driver: webdriver.Chrome, wait: WebDriverWait) -> WebsiteAdapter:
        """Create an adapter for the specified website."""
        website = website.lower()
        if website not in cls.ADAPTERS:
            raise ValueError(f"Unsupported website: {website}. Supported: {list(cls.ADAPTERS.keys())}")
        
        return cls.ADAPTERS[website](driver, wait)
    
    @classmethod
    def get_supported_websites(cls) -> List[str]:
        """Get list of supported websites."""
        return list(cls.ADAPTERS.keys())

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Website Adapters...")
    
    # Print supported websites
    supported = WebsiteAdapterFactory.get_supported_websites()
    print(f"✅ Supported websites: {supported}")
    
    # Example of how to use (without actually creating driver)
    print(f"✅ FlipkartAdapter base URL: {FlipkartAdapter(None, None).get_base_url()}")
    print(f"✅ AmazonAdapter base URL: {AmazonAdapter(None, None).get_base_url()}")
    
    print("✅ Website adapter system ready!")