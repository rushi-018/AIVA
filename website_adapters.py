"""
fixed_website_adapters.py: Fixed website adapters with proper selectors
Updated adapters that handle current website layouts and popups.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import re

class WebsiteAdapter(ABC):
    """Abstract base class for e-commerce website adapters."""
    
    def __init__(self, driver: webdriver.Chrome, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait
        self.name = self.__class__.__name__.replace('Adapter', '').lower()
    
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
    """Fixed Flipkart website adapter."""
    
    def get_base_url(self) -> str:
        return "https://www.flipkart.com"
    
    def get_login_url(self) -> str:
        return "https://www.flipkart.com/account/login"
    
    def _handle_popups(self):
        """Handle Flipkart popups and dialogs."""
        try:
            # Handle login popup
            popup_selectors = [
                "button[class*='_2KpZ6l _2doB4z']",
                "button[class*='_2AkmmA _29YdH8']",
                "span[role='button'][class*='_30XB9F']"
            ]
            
            for selector in popup_selectors:
                try:
                    popup = self.driver.find_element(By.CSS_SELECTOR, selector)
                    popup.click()
                    time.sleep(1)
                    print("   ✅ Closed Flipkart popup")
                    break
                except:
                    continue
        except:
            pass
    
    def search_products(self, query: str, max_price: float = None) -> List[Dict]:
        """Search products on Flipkart with improved selectors."""
        try:
            print(f"🔍 Searching Flipkart for: {query}")
            
            # Navigate to Flipkart
            self.driver.get(self.get_base_url())
            time.sleep(3)
            
            # Handle popups
            self._handle_popups()
            
            # Find and use search box
            search_selectors = [
                "input[name='q']",
                "input[placeholder*='Search']",
                "input[title*='Search']",
                "input._3704LK"
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not search_box:
                print("❌ Could not find search box on Flipkart")
                return []
            
            # Perform search
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.ENTER)
            time.sleep(5)  # Wait for results
            
            # Extract products using improved selectors
            products = []
            
            # Get product containers
            product_containers = self.driver.find_elements(By.CSS_SELECTOR, "[data-id]")
            
            if not product_containers:
                print("❌ No products found on Flipkart results page")
                return []
            
            print(f"📦 Found {len(product_containers)} product containers")
            
            for container in product_containers[:10]:  # Limit to first 10
                try:
                    # Extract title
                    title_selectors = [
                        ".KzDlHZ",  # Updated title class
                        ".IRpwTa",  # Alternative title class
                        "a[title]",  # Title attribute
                        ".s1Q9rs"   # Another title class
                    ]
                    
                    title = "Unknown Product"
                    for selector in title_selectors:
                        try:
                            title_elem = container.find_element(By.CSS_SELECTOR, selector)
                            title = title_elem.text or title_elem.get_attribute('title')
                            if title:
                                title = title[:60] + "..." if len(title) > 60 else title
                                break
                        except:
                            continue
                    
                    # Extract price
                    price_selectors = [
                        ".Nx9bqj",      # Current price class
                        "._25b18c",     # Alternative price
                        "._30jeq3",     # Another price class
                        "[class*='price']"
                    ]
                    
                    price = 0
                    for selector in price_selectors:
                        try:
                            price_elem = container.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.replace('₹', '').replace(',', '').strip()
                            # Extract numbers only
                            price_match = re.search(r'(\d+)', price_text)
                            if price_match:
                                price = float(price_match.group(1))
                                break
                        except:
                            continue
                    
                    # Skip if no price found or price filter
                    if price == 0:
                        continue
                    if max_price and price > max_price:
                        continue
                    
                    # Get product link
                    link = ""
                    try:
                        link_elem = container.find_element(By.CSS_SELECTOR, "a")
                        link = link_elem.get_attribute('href')
                    except:
                        pass
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'element': container,
                        'link': link,
                        'platform': 'flipkart'
                    })
                    
                except Exception as e:
                    print(f"   ⚠️ Error extracting product: {e}")
                    continue
            
            print(f"✅ Extracted {len(products)} products from Flipkart")
            return products
            
        except Exception as e:
            print(f"❌ Error searching Flipkart: {e}")
            return []
    
    def add_to_cart(self, product_element) -> bool:
        """Add product to cart on Flipkart."""
        try:
            print("🛒 Attempting to add product to cart...")
            
            # Click on product to go to product page
            try:
                product_link = product_element.find_element(By.CSS_SELECTOR, "a")
                product_url = product_link.get_attribute('href')
                print(f"   📍 Navigating to product page...")
                self.driver.get(product_url)  # Direct navigation is more reliable
                time.sleep(5)  # Wait for page to load
            except Exception as e:
                print(f"   ❌ Failed to navigate to product page: {e}")
                return False
            
            # Wait for page to load and handle any popups
            self._handle_popups()
            time.sleep(2)
            
            # Modern Flipkart add-to-cart selectors (updated for 2025)
            add_to_cart_selectors = [
                # Updated button selectors based on current Flipkart layout
                "button[class*='QqFHMw']",                    # Primary add to cart button 2025
                "button[class*='_2KpZ6l'][class*='_2U9uOA']", # Classic add to cart
                "button[class*='_2KpZ6l'][class*='_3v1-ww']", # Primary button variant
                "button[class*='_2AkmmA'][class*='_29YdH8']", # Secondary button style
                "li[class*='_1rH2Jg'] button",               # List item button
                "div[class*='_30jeq3'] button",              # Price section button
                "button:contains('ADD TO CART')",             # Text-based fallback
                "button:contains('Add to Cart')",             # Case variation
                "[data-testid='add-to-cart']",                # Data attribute
                "button[aria-label*='cart']",                 # Accessibility attribute
                "button[title*='cart']",                      # Title attribute
                ".add-to-cart button",                        # Class-based
                "[class*='addToCart'] button",               # CamelCase variation
                "button[class*='btn-primary']",               # Bootstrap-style
                "button[class*='primary-btn']"                # Alternative primary
            ]
            
            print("   🔍 Searching for add to cart button...")
            
            for i, selector in enumerate(add_to_cart_selectors, 1):
                try:
                    print(f"      Trying selector {i}/{len(add_to_cart_selectors)}: {selector}")
                    
                    # Use WebDriverWait for better reliability
                    add_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    # Verify it's actually an add to cart button
                    button_text = add_btn.text.upper()
                    print(f"      Found button with text: '{button_text}'")
                    
                    if any(keyword in button_text for keyword in ['ADD', 'CART', 'BUY']):
                        # Scroll to button and click
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", add_btn)
                        time.sleep(1)
                        add_btn.click()
                        time.sleep(3)
                        
                        print("   ✅ Successfully clicked add to cart button")
                        
                        # Check if we were redirected to cart or got confirmation
                        current_url = self.driver.current_url.lower()
                        if 'cart' in current_url or 'checkout' in current_url:
                            print("   ✅ Redirected to cart page - item added!")
                            return True
                        else:
                            # Look for success indicators on the same page
                            success_indicators = [
                                "added to cart",
                                "view cart",
                                "go to cart",
                                "item added",
                                "cart-success",
                                "successfully added",
                                "_2AkmmA",  # Flipkart success button class
                                "_3dsJAO"   # Flipkart cart indicator
                            ]
                            
                            page_text = self.driver.page_source.lower()
                            if any(indicator in page_text for indicator in success_indicators):
                                print("   ✅ Success indicator found - item likely added!")
                                return True
                            
                            # Additional check for cart count increase
                            try:
                                cart_count_selectors = [
                                    "._1ksD7M",     # Flipkart cart count
                                    "[data-cy='cart-count']",
                                    ".cart-count"
                                ]
                                
                                for selector in cart_count_selectors:
                                    cart_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                                    if cart_element and cart_element.text.strip():
                                        print("   ✅ Cart count detected - item likely added!")
                                        return True
                            except:
                                pass
                        
                        print("   ⚠️ Button clicked but no clear success indication")
                        return True  # Assume success if we got this far
                    
                except Exception as e:
                    print(f"      ❌ Selector {i} failed: {e}")
                    continue
            
            # If no specific button found, try to find any clickable element with cart-related text
            print("   🔄 Trying text-based search as fallback...")
            try:
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in all_buttons:
                    text = button.text.upper()
                    if any(keyword in text for keyword in ['ADD TO CART', 'ADD CART', 'BUY NOW']):
                        print(f"   🎯 Found text-based button: {text}")
                        button.click()
                        time.sleep(2)
                        print("   ✅ Clicked text-based add to cart button")
                        return True
            except Exception as e:
                print(f"   ❌ Text-based search failed: {e}")
            
            print("   ❌ Could not find any add to cart button")
            return False
            
        except Exception as e:
            print(f"   ❌ Error in add_to_cart: {e}")
            return False
            return False
    
    def remove_from_cart(self, product_title: str) -> bool:
        """Remove product from cart on Flipkart."""
        try:
            # Navigate to cart
            self.driver.get("https://www.flipkart.com/viewcart")
            time.sleep(3)
            
            # Find remove buttons
            remove_selectors = [
                "div[class*='_3dsJAO _24d-qY FhkMJZ'] div[class*='_2d-qUv']",  # Remove button
                "button[class*='_2AkmmA _29YdH8']",  # Alternative remove
                ".zZ4QVo",  # Remove link
                "div:contains('Remove')"
            ]
            
            for selector in remove_selectors:
                try:
                    remove_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if remove_buttons:
                        remove_buttons[0].click()
                        time.sleep(1)
                        
                        # Handle confirmation dialog
                        try:
                            confirm_btn = self.driver.find_element(By.CSS_SELECTOR, "div[class*='_2AkmmA _29YdH8']")
                            confirm_btn.click()
                            time.sleep(1)
                        except:
                            pass
                        
                        print("✅ Removed from cart on Flipkart")
                        return True
                except:
                    continue
            
            print("❌ Could not find remove button")
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
        except:
            return False
    
    def check_login_status(self) -> str:
        """Check Flipkart login status."""
        try:
            page_source = self.driver.page_source.lower()
            
            if any(indicator in page_source for indicator in ["my account", "logout", "my orders"]):
                return "logged_in"
            elif any(indicator in page_source for indicator in ["login", "sign in"]):
                return "not_logged_in"
            else:
                return "unknown"
        except:
            return "unknown"
    
    def get_login_instructions(self) -> str:
        """Get Flipkart login instructions."""
        return """
📋 Flipkart Login Instructions:
🔐 Flipkart uses OTP-based login
📱 Have your registered mobile number ready

Steps:
1. 📧 Enter mobile number/email
2. 🔢 Click 'Request OTP'
3. 📲 Check SMS/WhatsApp for OTP
4. 🔐 Enter OTP and verify
"""

class AmazonAdapter(WebsiteAdapter):
    """Fixed Amazon website adapter."""
    
    def get_base_url(self) -> str:
        return "https://www.amazon.in"
    
    def get_login_url(self) -> str:
        return "https://www.amazon.in/ap/signin"
    
    def _handle_popups(self):
        """Handle Amazon popups and modals including initial continue page."""
        try:
            print("   Checking for Amazon popups and continue buttons...")
            
            # First, handle the initial "Continue" page that appears before main page loads
            continue_selectors = [
                "//span[text()='Continue']",
                "//button[contains(text(), 'Continue')]",
                "//input[@value='Continue']",
                "//a[contains(text(), 'Continue')]",
                "[data-action='continue']"
            ]
            
            for selector in continue_selectors:
                try:
                    if selector.startswith("//"):
                        continue_btn = self.driver.find_element(By.XPATH, selector)
                    else:
                        continue_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if continue_btn.is_displayed() and continue_btn.is_enabled():
                        continue_btn.click()
                        print("   ✅ Clicked Amazon continue button")
                        
                        # Wait for the main page to load after clicking continue
                        time.sleep(3)
                        
                        # Wait for the main Amazon page elements to appear
                        try:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "#nav-logo"))
                            )
                            print("   ✅ Main Amazon page loaded")
                        except:
                            print("   ⚠️ Main page elements not detected, continuing anyway")
                        
                        break
                except:
                    continue
            
            # Handle other common Amazon popups
            popup_selectors = [
                "[data-action-type='DISMISS']",
                ".a-button-close",
                "input[aria-label='Dismiss']",
                "[aria-label*='Close']",
                ".a-popover-close"
            ]
            
            for selector in popup_selectors:
                try:
                    popup = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if popup.is_displayed():
                        popup.click()
                        time.sleep(1)
                        print("   ✅ Dismissed Amazon popup")
                        break
                except:
                    continue
                    
            # Handle location/delivery popup specifically
            try:
                location_popup = self.driver.find_element(By.CSS_SELECTOR, "#GLUXZipUpdateApi")
                if location_popup.is_displayed():
                    dismiss_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-action-type='DISMISS']")
                    dismiss_btn.click()
                    time.sleep(1)
                    print("   ✅ Dismissed location popup")
            except:
                pass
                
        except Exception as e:
            print(f"   ⚠️ Error handling popups: {e}")
            pass
    
    def search_products(self, query: str, max_price: float = None) -> List[Dict]:
        """Search products on Amazon with improved timing and popup handling."""
        try:
            print(f"🔍 Searching Amazon for: {query}")
            
            # Navigate to Amazon
            self.driver.get(self.get_base_url())
            
            # Wait longer for initial page load
            print("   Waiting for Amazon page to load...")
            WebDriverWait(self.driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)
            
            # Handle popups and continue buttons
            self._handle_popups()
            
            # After handling popups, wait a bit more for the main page to stabilize
            time.sleep(2)
            
            # Find search box with improved waiting and selectors
            print("   Looking for search box...")
            search_box = None
            search_selectors = [
                "#twotabsearchtextbox",  # Primary search box
                "input[name='field-keywords']",
                "input[type='text'][placeholder*='Search']",
                "#nav-search-bar-form input",
                ".nav-search-field input"
            ]
            
            for selector in search_selectors:
                try:
                    # Wait for each selector to be clickable
                    search_box = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"   ✅ Found search box: {selector}")
                    break
                except:
                    continue
            
            if not search_box:
                print("❌ Could not find search box on Amazon")
                return []
            
            # Clear and enter search query
            search_box.clear()
            search_box.send_keys(query)
            
            # Find and click search button
            search_button_found = False
            search_btn_selectors = [
                "#nav-search-submit-button",
                "input[type='submit'][value='Go']",
                ".nav-input[type='submit']",
                ".nav-search-submit input"
            ]
            
            for selector in search_btn_selectors:
                try:
                    search_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    search_btn.click()
                    print("   ✅ Search button clicked")
                    search_button_found = True
                    break
                except:
                    continue
            
            if not search_button_found:
                print("   ⚠️ Search button not found, using Enter key")
                search_box.send_keys(Keys.ENTER)
            
            # Wait for search results to load
            print("   Waiting for search results...")
            time.sleep(5)
            
            # Extract products
            products = []
            
            # Updated product container selectors
            container_selectors = [
                "[data-component-type='s-search-result']",
                ".s-result-item",
                ".sg-col-inner .s-widget-container",
                "[data-asin]"
            ]
            
            product_containers = []
            for selector in container_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        product_containers = containers
                        break
                except:
                    continue
            
            if not product_containers:
                print("❌ No products found on Amazon results page")
                return []
            
            print(f"📦 Found {len(product_containers)} product containers on Amazon")
            
            for container in product_containers[:10]:  # Limit to first 10
                try:
                    # Extract title with comprehensive selectors
                    title_selectors = [
                        "h2 a span",  # Primary title location
                        "h2 span",    # Alternative title
                        "[data-cy='title-recipe-title'] span",  # Recipe title
                        ".a-size-medium span",  # Medium size title
                        ".a-size-base-plus",    # Base plus title
                        "h2 a",       # Direct title link
                        ".a-link-normal span",  # Normal link title
                        ".s-size-mini span",    # Mini size title
                        "[aria-label]"          # Aria label fallback
                    ]
                    
                    title = "Unknown Product"
                    for selector in title_selectors:
                        try:
                            title_elem = container.find_element(By.CSS_SELECTOR, selector)
                            title_text = title_elem.text.strip()
                            
                            # Also try aria-label if text is empty
                            if not title_text:
                                title_text = title_elem.get_attribute('aria-label') or ""
                            
                            # Also try title attribute
                            if not title_text:
                                title_text = title_elem.get_attribute('title') or ""
                            
                            if title_text and len(title_text) > 3:  # Ensure meaningful title
                                title = title_text[:60] + "..." if len(title_text) > 60 else title_text
                                break
                        except:
                            continue
                    
                    # If still no title found, try getting text from any child elements
                    if title == "Unknown Product":
                        try:
                            # Try to find any text within h2 elements
                            h2_elements = container.find_elements(By.CSS_SELECTOR, "h2")
                            for h2 in h2_elements:
                                h2_text = h2.text.strip()
                                if h2_text and len(h2_text) > 3:
                                    title = h2_text[:60] + "..." if len(h2_text) > 60 else h2_text
                                    break
                        except:
                            pass
                    
                    # Extract price
                    price_selectors = [
                        ".a-price-whole",
                        ".a-price .a-offscreen",
                        ".a-price-range .a-price .a-offscreen",
                        ".a-price-symbol"
                    ]
                    
                    price = 0
                    for selector in price_selectors:
                        try:
                            price_elem = container.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.replace('₹', '').replace(',', '').strip()
                            # Extract numbers only
                            price_match = re.search(r'(\d+)', price_text)
                            if price_match:
                                price = float(price_match.group(1))
                                break
                        except:
                            continue
                    
                    # Skip if no price or price filter
                    if price == 0:
                        continue
                    if max_price and price > max_price:
                        continue
                    
                    # Get product link
                    link = ""
                    try:
                        link_elem = container.find_element(By.CSS_SELECTOR, "h2 a")
                        link = link_elem.get_attribute('href')
                    except:
                        pass
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'element': container,
                        'link': link,
                        'platform': 'amazon'
                    })
                    
                except Exception as e:
                    print(f"   ⚠️ Error extracting Amazon product: {e}")
                    continue
            
            print(f"✅ Extracted {len(products)} products from Amazon")
            return products
            
        except Exception as e:
            print(f"❌ Error searching Amazon: {e}")
            return []
    
    def add_to_cart(self, product_element) -> bool:
        """Add product to cart on Amazon with enhanced functionality."""
        try:
            print("🛒 Attempting to add product to Amazon cart...")
            
            # Navigate to product page
            try:
                # Try multiple ways to get the product link
                product_link = None
                link_selectors = [
                    "h2 a",                    # Standard product title link
                    "a[data-cy='title-recipe-ATF']",  # Amazon specific
                    ".a-link-normal",          # Amazon link class
                    "a:first-child",           # First link in container
                    "[data-testid='product-title'] a"  # Data attribute
                ]
                
                for selector in link_selectors:
                    try:
                        product_link = product_element.find_element(By.CSS_SELECTOR, selector)
                        if product_link:
                            break
                    except:
                        continue
                
                if not product_link:
                    print("   ❌ Could not find product link")
                    return False
                
                product_url = product_link.get_attribute('href')
                print(f"   📍 Navigating to Amazon product page...")
                self.driver.get(product_url)  # Direct navigation is more reliable
                time.sleep(5)  # Wait for page to load
                
            except Exception as e:
                print(f"   ❌ Failed to navigate to product page: {e}")
                return False
            
            # Handle Amazon popups on product page
            self._handle_popups()
            time.sleep(2)
            
            # Modern Amazon add-to-cart selectors (updated for 2025)
            add_to_cart_selectors = [
                # Primary Amazon add to cart selectors
                "#add-to-cart-button",                        # Classic Amazon add to cart
                "input[name='submit.add-to-cart']",           # Form input version
                "#add-to-cart-button-ubb",                    # Updated button ID
                "[data-testid='add-to-cart-button']",         # Data attribute
                "input[aria-labelledby='submit.add-to-cart-announce']", # Accessibility
                "#freshAddToCartButton",                      # Amazon Fresh
                ".a-button-primary input[name*='cart']",      # Primary button with cart
                "#oneClickSignIn",                            # One-click purchase (fallback)
                "input[title*='Add to Cart']",               # Title attribute
                "input[value*='Add to Cart']",               # Value attribute
                "button[aria-label*='Add to Cart']",         # ARIA label
                ".a-button-input[aria-labelledby*='cart']",  # Button input with cart
                "[name='submit.addToCart']",                 # Alternative form name
                "#attach-sidesheet-addtocart-button",        # Sidesheet add to cart
                "input[data-action='add-to-cart']",          # Data action
                ".a-button-primary[name*='add']",            # Primary button with add
                "button[data-cy='add-to-cart']",             # Cypress test attribute
                "[id*='addToCart'] input",                   # ID containing addToCart
                ".buybox input[name*='cart']",               # Buybox cart input
                "#buy-now-button",                           # Buy now as fallback
            ]
            
            print("   🔍 Searching for Amazon add to cart button...")
            
            for i, selector in enumerate(add_to_cart_selectors, 1):
                try:
                    print(f"      Trying selector {i}/{len(add_to_cart_selectors)}: {selector}")
                    
                    # Use WebDriverWait for better reliability
                    add_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    # Verify it's actually an add to cart button
                    button_text = add_btn.get_attribute('value') or add_btn.text or add_btn.get_attribute('aria-label') or ""
                    button_text = button_text.upper()
                    print(f"      Found button with text/value: '{button_text}'")
                    
                    # Check if it's a cart-related button
                    cart_keywords = ['ADD TO CART', 'ADD CART', 'CART', 'BUY NOW', 'ADD TO BASKET']
                    if any(keyword in button_text for keyword in cart_keywords) or 'cart' in selector.lower():
                        # Scroll to button and click
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", add_btn)
                        time.sleep(1)
                        
                        # Try clicking with JavaScript if regular click fails
                        try:
                            add_btn.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", add_btn)
                        
                        time.sleep(3)
                        print("   ✅ Successfully clicked Amazon add to cart button")
                        
                        # Check for success indicators
                        current_url = self.driver.current_url.lower()
                        
                        # Check if redirected to cart
                        if 'cart' in current_url or 'checkout' in current_url or 'gp/cart' in current_url:
                            print("   ✅ Redirected to cart page - item added!")
                            return True
                        
                        # Check for success messages or indicators
                        success_indicators = [
                            "added to cart",
                            "added to your cart", 
                            "item added",
                            "successfully added",
                            "in your cart",
                            "proceed to checkout",
                            "cart-success",
                            "sw-atc-details-single-container",  # Amazon success container
                            "a-alert-success",                   # Amazon success alert
                            "attachDisplayAddBaseAlert"          # Amazon add to cart alert
                        ]
                        
                        page_text = self.driver.page_source.lower()
                        if any(indicator in page_text for indicator in success_indicators):
                            print("   ✅ Success indicator found - item added to Amazon cart!")
                            return True
                        
                        # Check for cart count increase
                        try:
                            cart_count_selectors = [
                                "#nav-cart-count",              # Main cart count
                                ".nav-cart-count",             # Cart count class
                                "#nav-cart .nav-cart-count",   # Nested cart count
                                "[data-cy='cart-count']"       # Data attribute
                            ]
                            
                            for count_selector in cart_count_selectors:
                                cart_element = self.driver.find_element(By.CSS_SELECTOR, count_selector)
                                if cart_element and cart_element.text.strip() and cart_element.text.strip() != '0':
                                    print("   ✅ Cart count detected - item added to Amazon cart!")
                                    return True
                        except:
                            pass
                        
                        # Check for Amazon-specific success elements
                        try:
                            success_elements = [
                                "[data-feature-name='addToCart']",
                                ".a-alert-success",
                                "#sw-atc-details-single-container",
                                "#attachDisplayAddBaseAlert"
                            ]
                            
                            for elem_selector in success_elements:
                                success_elem = self.driver.find_element(By.CSS_SELECTOR, elem_selector)
                                if success_elem and success_elem.is_displayed():
                                    print("   ✅ Amazon success element found - item added!")
                                    return True
                        except:
                            pass
                        
                        print("   ⚠️ Button clicked but no clear success indication")
                        return True  # Assume success if we got this far
                    
                except Exception as e:
                    print(f"      ❌ Selector {i} failed: {e}")
                    continue
            
            # Fallback: Try to find any button with cart-related text
            print("   🔄 Trying text-based search as fallback...")
            try:
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                
                for element in all_inputs + all_buttons:
                    text = (element.get_attribute('value') or element.text or 
                           element.get_attribute('aria-label') or element.get_attribute('title') or "").upper()
                    
                    if any(keyword in text for keyword in ['ADD TO CART', 'ADD CART', 'BUY NOW']):
                        print(f"   🎯 Found text-based button: {text}")
                        try:
                            element.click()
                            time.sleep(2)
                            print("   ✅ Clicked text-based add to cart button")
                            return True
                        except:
                            continue
            except Exception as e:
                print(f"   ❌ Text-based search failed: {e}")
            
            print("   ❌ Could not find any add to cart button on Amazon")
            return False
            
        except Exception as e:
            print(f"   ❌ Error in Amazon add_to_cart: {e}")
            return False
    
    def remove_from_cart(self, product_title: str) -> bool:
        """Remove product from cart on Amazon."""
        try:
            # Navigate to cart
            self.driver.get("https://www.amazon.in/gp/cart/view.html")
            time.sleep(3)
            
            # Find remove buttons
            remove_selectors = [
                "input[value='Delete']",
                ".sc-action-delete input",
                "[data-action='delete'] input"
            ]
            
            for selector in remove_selectors:
                try:
                    remove_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if remove_buttons:
                        remove_buttons[0].click()
                        time.sleep(1)
                        print("✅ Removed from cart on Amazon")
                        return True
                except:
                    continue
            
            print("❌ Could not find remove button on Amazon")
            return False
            
        except Exception as e:
            print(f"❌ Error removing from Amazon cart: {e}")
            return False
    
    def go_to_cart(self) -> bool:
        """Navigate to cart page."""
        try:
            self.driver.get("https://www.amazon.in/gp/cart/view.html")
            time.sleep(2)
            return True
        except:
            return False
    
    def check_login_status(self) -> str:
        """Check Amazon login status."""
        try:
            page_source = self.driver.page_source.lower()
            
            if any(indicator in page_source for indicator in ["your account", "sign out", "your orders"]):
                return "logged_in"
            elif any(indicator in page_source for indicator in ["sign in", "create account"]):
                return "not_logged_in"
            else:
                return "unknown"
        except:
            return "unknown"
    
    def get_login_instructions(self) -> str:
        """Get Amazon login instructions."""
        return """
📋 Amazon Login Instructions:
🔐 Amazon supports email/phone login

Steps:
1. 📧 Enter email or mobile number
2. 🔐 Enter password
3. ✅ Click 'Sign In'
4. 🔢 Handle 2FA if enabled
"""

class WebsiteAdapterFactory:
    """Factory to create website adapters."""
    
    @staticmethod
    def create_adapter(website: str, driver: webdriver.Chrome, wait: WebDriverWait) -> WebsiteAdapter:
        """Create appropriate adapter for website."""
        if website.lower() == 'flipkart':
            return FlipkartAdapter(driver, wait)
        elif website.lower() == 'amazon':
            return AmazonAdapter(driver, wait)
        else:
            raise ValueError(f"Unsupported website: {website}")
    
    @staticmethod
    def get_supported_websites() -> List[str]:
        """Get list of supported websites."""
        return ['flipkart', 'amazon']