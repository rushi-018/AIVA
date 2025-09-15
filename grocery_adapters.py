"""
Grocery Website Adapters for Indian Grocery Delivery Services
Supports Blinkit, BigBasket, Zepto and other major grocery platforms
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re

class GroceryWebsiteAdapter(ABC):
    """Abstract base class for grocery delivery website adapters."""
    
    def __init__(self, driver: webdriver.Chrome, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait
        self.name = self.__class__.__name__.replace('Adapter', '').lower()
        self.location_set = False
    
    @abstractmethod
    def get_base_url(self) -> str:
        """Get the base URL of the grocery website."""
        pass
    
    @abstractmethod
    def setup_location(self, pincode: str, area: str = None) -> bool:
        """Setup delivery location for grocery orders."""
        pass
    
    @abstractmethod
    def search_product(self, product_name: str) -> List[Dict]:
        """Search for a specific grocery product."""
        pass
    
    @abstractmethod
    def add_to_cart(self, product_element, quantity: int = 1) -> bool:
        """Add a product to cart with specified quantity."""
        pass
    
    @abstractmethod
    def view_cart(self) -> List[Dict]:
        """View current cart contents."""
        pass


class BlinkitAdapter(GroceryWebsiteAdapter):
    """Blinkit (formerly Grofers) grocery delivery adapter with enhanced location detection."""
    
    def get_base_url(self) -> str:
        """Get Blinkit base URL."""
        return "https://blinkit.com"
    
    def setup_location(self, pincode: str = None, area: str = None) -> bool:
        """Enhanced location setup with automatic detection and fallback options."""
        try:
            print(f"🏠 Setting up Blinkit location (Auto-detect + fallback)")
            
            if self.location_set:
                print("   ✅ Location already set")
                return True
            
            # Navigate to Blinkit
            print("   📱 Loading Blinkit homepage...")
            self.driver.get(self.get_base_url())
            time.sleep(5)
            
            # Wait for page to fully load
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except:
                pass
            
            time.sleep(3)
            
            # Step 1: Try to detect current location automatically
            print("   🌍 Step 1: Attempting automatic location detection...")
            auto_detect_success = self._attempt_auto_location_detection()
            
            if auto_detect_success:
                print("   ✅ Auto-location detection successful!")
                self.location_set = True
                return True
            
            # Step 2: If auto-detection fails, try manual location input
            if pincode:
                print(f"   📍 Step 2: Trying manual location setup with pincode: {pincode}")
                manual_success = self._attempt_manual_location_setup(pincode, area)
                
                if manual_success:
                    print("   ✅ Manual location setup successful!")
                    self.location_set = True
                    return True
            
            # Step 3: Fallback - accept any location that's already set
            print("   🔄 Step 3: Checking if any location is already available...")
            if self._check_existing_location():
                print("   ✅ Using existing location setup")
                self.location_set = True
                return True
            
            # Step 4: Final fallback - assume location is set and proceed
            print("   ⚠️ Location setup unclear, proceeding with assumption of success")
            self.location_set = True
            return True
            
        except Exception as e:
            print(f"   ❌ Location setup failed: {e}")
            # Even if setup fails, mark as set to allow search to proceed
            self.location_set = True
            return False
    
    def _attempt_auto_location_detection(self) -> bool:
        """Attempt automatic location detection using various strategies."""
        try:
            # Strategy 1: Look for detect location buttons
            detect_location_selectors = [
                "button[data-testid='detect-location']",
                "button[data-testid*='detect']",
                "button[aria-label*='detect' i]",
                "button[aria-label*='location' i]",
                "button[class*='detect' i]",
                "button[class*='location' i]",
                "[data-cy='detect-location']",
                ".detect-location-btn",
                "#detect-location",
                "button:contains('Detect')",
                "button:contains('Use Current')",
                "button:contains('GPS')"
            ]
            
            for selector in detect_location_selectors:
                try:
                    # Handle CSS selectors vs XPath
                    if ':contains(' in selector:
                        # Convert to XPath for text search
                        text = selector.split(':contains(')[1].split(')')[0].strip("'\"")
                        xpath = f"//button[contains(text(), '{text}')]"
                        buttons = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"      🎯 Found detect button: {button.text[:30]}...")
                            
                            # Scroll to button and click
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            time.sleep(1)
                            button.click()
                            
                            # Wait for location detection
                            print("      ⏳ Waiting for location detection...")
                            time.sleep(8)
                            
                            # Check if location was detected successfully
                            if self._verify_location_success():
                                return True
                            
                except Exception as e:
                    continue
            
            # Strategy 2: Look for text-based location buttons
            print("      🔍 Scanning for text-based location buttons...")
            location_keywords = [
                "detect", "detect location", "current location", "my location", 
                "use gps", "auto detect", "find location", "get location",
                "allow location", "enable location"
            ]
            
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in all_buttons:
                try:
                    if button.is_displayed() and button.text:
                        button_text = button.text.strip().lower()
                        if any(keyword in button_text for keyword in location_keywords):
                            print(f"      🎯 Found text-based button: {button.text[:30]}...")
                            button.click()
                            time.sleep(8)
                            
                            if self._verify_location_success():
                                return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"      ❌ Auto-detection failed: {e}")
            return False
    
    def _attempt_manual_location_setup(self, pincode: str, area: str = None) -> bool:
        """Attempt manual location setup using pincode."""
        try:
            print(f"      📍 Trying manual location input...")
            
            # Look for location input fields
            location_input_selectors = [
                "input[placeholder*='pincode' i]",
                "input[placeholder*='location' i]",
                "input[placeholder*='area' i]",
                "input[name*='pincode' i]",
                "input[name*='location' i]",
                "input[id*='pincode' i]",
                "input[id*='location' i]",
                "[data-testid*='location'] input",
                "[data-testid*='pincode'] input"
            ]
            
            for selector in location_input_selectors:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for input_field in inputs:
                        if input_field.is_displayed() and input_field.is_enabled():
                            print(f"      ✏️ Found location input field")
                            
                            # Clear and enter pincode
                            input_field.clear()
                            input_field.send_keys(pincode)
                            time.sleep(2)
                            
                            # Try to submit by pressing Enter or finding submit button
                            input_field.send_keys(Keys.ENTER)
                            time.sleep(5)
                            
                            if self._verify_location_success():
                                return True
                                
                            # If Enter didn't work, look for submit button
                            submit_selectors = [
                                "button[type='submit']",
                                "button:contains('Submit')",
                                "button:contains('Set')",
                                "button:contains('Confirm')"
                            ]
                            
                            for submit_selector in submit_selectors:
                                try:
                                    if ':contains(' in submit_selector:
                                        text = submit_selector.split(':contains(')[1].split(')')[0].strip("'\"")
                                        submit_buttons = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                                    else:
                                        submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, submit_selector)
                                    
                                    for submit_btn in submit_buttons:
                                        if submit_btn.is_displayed():
                                            submit_btn.click()
                                            time.sleep(5)
                                            
                                            if self._verify_location_success():
                                                return True
                                except:
                                    continue
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"      ❌ Manual location setup failed: {e}")
            return False
    
    def _check_existing_location(self) -> bool:
        """Check if any location is already set and products are visible."""
        try:
            # Check for location indicators
            location_indicators = [
                "[data-testid*='location']",
                "[class*='location']",
                ".location-display",
                "#current-location"
            ]
            
            for indicator in location_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    if elements:
                        for elem in elements:
                            if elem.is_displayed() and elem.text.strip():
                                print(f"      ✅ Found location indicator: {elem.text[:30]}...")
                                return True
                except:
                    continue
            
            # Check if products are already visible (main success indicator)
            return self._verify_location_success()
            
        except:
            return False
    
    def _verify_location_success(self) -> bool:
        """Verify that location setup was successful by checking for products."""
        try:
            # Look for product indicators
            product_indicators = [
                "[data-testid*='product']",
                "[class*='product']",
                ".product",
                ".product-card",
                "[data-cy*='product']",
                ".item-card",
                ".grocery-item"
            ]
            
            for indicator in product_indicators:
                try:
                    products = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    if len(products) > 3:  # Need multiple products to confirm
                        print(f"      ✅ Location verified - {len(products)} products visible")
                        return True
                except:
                    continue
            
            # Alternative: Check if search bar is available
            search_selectors = [
                "input[placeholder*='Search' i]",
                "input[type='search']",
                "[data-testid*='search'] input"
            ]
            
            for selector in search_selectors:
                try:
                    search_inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if search_inputs:
                        for search_input in search_inputs:
                            if search_input.is_displayed() and search_input.is_enabled():
                                print("      ✅ Location verified - search functionality available")
                                return True
                except:
                    continue
            
            return False
            
        except:
            return False

    def search_product(self, product_name: str) -> List[Dict]:
        """Enhanced search for products using Blinkit search bar with improved reliability."""
        try:
            print(f"🔍 Searching for: {product_name}")
            
            # Ensure location is set first with enhanced setup
            if not self.location_set:
                print("   📍 Location not set, setting up location first...")
                if not self.setup_location():
                    print("   ⚠️ Location setup uncertain, but continuing with search...")
            
            # Give extra time for page to stabilize after location setup
            time.sleep(3)
            
            # Enhanced search bar selectors for Blinkit
            search_selectors = [
                "input[placeholder*='Search']",
                "input[placeholder*='search']", 
                "input[placeholder*='product' i]",
                "input[placeholder*='grocery' i]",
                "input[type='search']",
                "input[name*='search']",
                "input[id*='search']",
                "[data-testid*='search'] input",
                "[data-testid*='query'] input",
                "[class*='search'] input",
                "[class*='search-input']",
                ".search-input",
                "#search-input",
                ".search-box input",
                "[aria-label*='search' i]"
            ]
            
            search_input = None
            print("   🔍 Looking for search bar...")
            
            for selector in search_selectors:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for inp in inputs:
                        if inp.is_displayed() and inp.is_enabled():
                            search_input = inp
                            print(f"   ✅ Found search bar: {selector}")
                            break
                    if search_input:
                        break
                except:
                    continue
            
            if not search_input:
                print("   ❌ Search input not found, trying alternative methods...")
                # Fallback: look for any visible input that might be search
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                for inp in all_inputs:
                    try:
                        if inp.is_displayed() and inp.is_enabled():
                            placeholder = inp.get_attribute("placeholder") or ""
                            if any(word in placeholder.lower() for word in ["search", "find", "product", "item"]):
                                search_input = inp
                                print(f"   🎯 Found fallback search input: {placeholder}")
                                break
                    except:
                        continue
            
            if not search_input:
                print("   ❌ Could not find search bar")
                return []
            
            # Scroll to search input and focus
            self.driver.execute_script("arguments[0].scrollIntoView(true);", search_input)
            time.sleep(1)
            search_input.click()
            time.sleep(1)
            
            # Clear and type search query with better handling
            try:
                search_input.clear()
                time.sleep(1)
                
                # Type search query character by character for better reliability
                for char in product_name:
                    search_input.send_keys(char)
                    time.sleep(0.05)  # Faster typing
                
                print(f"   ✅ Typed search query: {product_name}")
                time.sleep(2)
                
                # Submit search with multiple methods
                search_submitted = False
                
                # Method 1: Press Enter
                try:
                    search_input.send_keys(Keys.ENTER)
                    print("   ✅ Submitted search with Enter")
                    search_submitted = True
                except Exception as e:
                    print(f"   ⚠️ Enter key failed: {e}")
                
                # Method 2: Look for search button if Enter failed
                if not search_submitted:
                    search_button_selectors = [
                        "button[type='submit']",
                        "button[aria-label*='search' i]",
                        "[data-testid*='search'] button",
                        ".search-button",
                        "#search-button",
                        "button[class*='search']"
                    ]
                    
                    for btn_selector in search_button_selectors:
                        try:
                            buttons = self.driver.find_elements(By.CSS_SELECTOR, btn_selector)
                            for btn in buttons:
                                if btn.is_displayed() and btn.is_enabled():
                                    btn.click()
                                    print(f"   ✅ Clicked search button: {btn_selector}")
                                    search_submitted = True
                                    break
                            if search_submitted:
                                break
                        except:
                            continue
                    
                    # Method 3: Text-based button search
                    if not search_submitted:
                        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        for btn in all_buttons:
                            try:
                                if btn.is_displayed() and btn.text:
                                    btn_text = btn.text.lower().strip()
                                    if any(word in btn_text for word in ["search", "find", "go"]):
                                        btn.click()
                                        print(f"   ✅ Clicked text-based search button: {btn.text}")
                                        search_submitted = True
                                        break
                            except:
                                continue
                
                if not search_submitted:
                    print("   ⚠️ Could not submit search, but query was typed")
                
                # Wait for search results with progressive loading
                print("   ⏳ Waiting for search results...")
                for wait_time in [3, 5, 8]:  # Progressive waiting
                    time.sleep(wait_time)
                    
                    # Check if results are loading
                    if self._check_search_results_loading():
                        print(f"      📊 Results detected after {wait_time}s")
                        break
                
                # Extract search results with enhanced parsing
                found_products = self._extract_search_results()
                
                print(f"   ✅ Found {len(found_products)} search results")
                
                # If no products found, try a more lenient extraction
                if not found_products:
                    print("   🔍 No products found with strict parsing, trying lenient extraction...")
                    found_products = self._extract_search_results_lenient()
                    print(f"   📊 Lenient extraction found {len(found_products)} products")
                
                return found_products
                
            except Exception as e:
                print(f"   ❌ Search execution failed: {e}")
                return []
                
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
            return []
    
    def _check_search_results_loading(self) -> bool:
        """Check if search results are loading or loaded."""
        try:
            # Look for result indicators
            result_indicators = [
                "[data-testid*='product']",
                "[class*='product']", 
                ".product",
                ".product-card",
                ".item-card",
                ".grocery-item",
                "[data-cy*='product']",
                ".search-result",
                "[class*='SearchResultItem']",
                "[class*='search-result']"
            ]
            
            for indicator in result_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    visible_elements = [e for e in elements if e.is_displayed()]
                    if len(visible_elements) > 0:
                        return True
                except:
                    continue
            
            return False
            
        except:
            return False
    
    def _extract_search_results(self) -> List[Dict]:
        """Extract search results with enhanced parsing."""
        found_products = []
        
        # Enhanced search result selectors
        result_selectors = [
            "[class*='product']",
            "[class*='item']", 
            "[data-testid*='product']",
            ".product",
            ".item",
            ".product-card",
            ".item-card",
            ".grocery-item",
            "[class*='SearchResultItem']",
            "[class*='search-result']",
            "[data-cy*='product']"
        ]
        
        for selector in result_selectors:
            try:
                products = self.driver.find_elements(By.CSS_SELECTOR, selector)
                visible_products = [p for p in products if p.is_displayed()]
                
                if visible_products:
                    print(f"      📊 Found {len(visible_products)} products with selector: {selector}")
                    
                    for i, product in enumerate(visible_products[:10]):  # Limit to 10 results
                        try:
                            product_text = product.text.strip()
                            
                            if product_text and len(product_text) > 5:  # Valid product text
                                product_info = {
                                    'name': product_text[:100],
                                    'element': product,
                                    'index': i,
                                    'source': 'search_results',
                                    'selector_used': selector
                                }
                                
                                # Enhanced price extraction
                                try:
                                    price_selectors = [
                                        "[class*='price']", 
                                        ".price", 
                                        "[class*='cost']",
                                        "[data-testid*='price']",
                                        "[class*='amount']",
                                        ".amount"
                                    ]
                                    for price_sel in price_selectors:
                                        price_elements = product.find_elements(By.CSS_SELECTOR, price_sel)
                                        for price_elem in price_elements:
                                            price_text = price_elem.text.strip()
                                            if price_text and ('₹' in price_text or 'Rs' in price_text or price_text.isdigit()):
                                                product_info['price'] = price_text
                                                break
                                        if 'price' in product_info:
                                            break
                                except:
                                    pass
                                
                                # Enhanced add button detection
                                try:
                                    button_selectors = [
                                        "button",
                                        "[role='button']",
                                        ".add-button",
                                        "[class*='add']",
                                        "[data-testid*='add']"
                                    ]
                                    
                                    for btn_sel in button_selectors:
                                        buttons = product.find_elements(By.CSS_SELECTOR, btn_sel)
                                        for btn in buttons:
                                            if btn.is_displayed() and btn.text:
                                                btn_text = btn.text.lower().strip()
                                                if any(word in btn_text for word in ["add", "cart", "buy"]):
                                                    product_info['add_button'] = btn
                                                    break
                                        if 'add_button' in product_info:
                                            break
                                except:
                                    pass
                                
                                found_products.append(product_info)
                                
                        except Exception as e:
                            print(f"         ⚠️ Error processing product {i}: {e}")
                            continue
                    
                    # If we found products with this selector, return them
                    if found_products:
                        return found_products
                        
            except Exception as e:
                print(f"      ⚠️ Error with selector {selector}: {e}")
                continue
        
        return found_products
    
    def _extract_search_results_lenient(self) -> List[Dict]:
        """Lenient extraction for search results when strict parsing fails."""
        found_products = []
        
        try:
            # Look for any clickable elements that might be products
            all_elements = self.driver.find_elements(By.CSS_SELECTOR, "*")
            
            for i, element in enumerate(all_elements):
                try:
                    if not element.is_displayed():
                        continue
                        
                    element_text = element.text.strip()
                    
                    # Check if element looks like a product
                    if (element_text and 
                        len(element_text) > 10 and 
                        len(element_text) < 200 and
                        ('₹' in element_text or 'Rs' in element_text or 
                         any(word in element_text.lower() for word in ['gram', 'kg', 'liter', 'piece', 'pack']))):
                        
                        # Check if it has clickable buttons
                        buttons = element.find_elements(By.CSS_SELECTOR, "button, [role='button']")
                        if buttons:
                            product_info = {
                                'name': element_text[:100],
                                'element': element,
                                'index': len(found_products),
                                'source': 'lenient_extraction'
                            }
                            
                            # Try to find add button
                            for btn in buttons:
                                if btn.is_displayed() and btn.text:
                                    btn_text = btn.text.lower()
                                    if any(word in btn_text for word in ["add", "cart", "buy"]):
                                        product_info['add_button'] = btn
                                        break
                            
                            found_products.append(product_info)
                            
                            if len(found_products) >= 5:  # Limit lenient extraction
                                break
                                
                except:
                    continue
            
        except Exception as e:
            print(f"      ⚠️ Lenient extraction failed: {e}")
        
        return found_products

    def add_to_cart(self, product_element, quantity: int = 1) -> bool:
        """Add a Blinkit product to cart."""
        try:
            print(f"🛒 Adding product to Blinkit cart (quantity: {quantity})")
            
            # Scroll to product element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", product_element)
            time.sleep(1)
            
            # Look for add to cart button
            add_button_selectors = [
                "button[class*='add']",
                "button[data-testid*='add']",
                "[class*='add-to-cart']",
                ".add-button",
                "button:contains('Add')",
                "button:contains('+')"
            ]
            
            add_button = None
            for selector in add_button_selectors:
                try:
                    if ":contains" in selector:
                        # Handle text-based selectors
                        buttons = product_element.find_elements(By.TAG_NAME, "button")
                        for btn in buttons:
                            if btn.is_displayed() and "add" in btn.text.lower():
                                add_button = btn
                                break
                    else:
                        buttons = product_element.find_elements(By.CSS_SELECTOR, selector)
                        for btn in buttons:
                            if btn.is_displayed():
                                add_button = btn
                                break
                    
                    if add_button:
                        break
                except:
                    continue
            
            if not add_button:
                print("   ❌ Add to cart button not found")
                return False
            
            # Click add to cart button
            try:
                add_button.click()
                print("   ✅ Clicked add to cart button")
                time.sleep(2)
                
                # Handle quantity if needed
                if quantity > 1:
                    for _ in range(quantity - 1):
                        try:
                            # Look for quantity increase button
                            plus_buttons = product_element.find_elements(By.CSS_SELECTOR, 
                                "button:contains('+'), [class*='plus'], [class*='increase']")
                            if plus_buttons:
                                plus_buttons[0].click()
                                time.sleep(1)
                        except:
                            break
                
                return True
                
            except Exception as e:
                print(f"   ❌ Failed to click add button: {e}")
                return False
                
        except Exception as e:
            print(f"   ❌ Add to cart failed: {e}")
            return False
    
    def view_cart(self) -> List[Dict]:
        """View Blinkit cart contents."""
        try:
            print("🛒 Viewing Blinkit cart")
            
            # Look for cart button/icon
            cart_selectors = [
                "[class*='cart']",
                "[data-testid*='cart']",
                ".cart-icon",
                "#cart",
                "button[aria-label*='cart' i]"
            ]
            
            cart_button = None
            for selector in cart_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed():
                            cart_button = btn
                            break
                    if cart_button:
                        break
                except:
                    continue
            
            if cart_button:
                cart_button.click()
                time.sleep(3)
            
            # Extract cart items
            cart_items = []
            item_selectors = [
                "[class*='cart-item']",
                "[class*='item']",
                ".cart-product"
            ]
            
            for selector in item_selectors:
                try:
                    items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for item in items:
                        if item.is_displayed():
                            item_text = item.text.strip()
                            if item_text:
                                cart_items.append({
                                    'name': item_text,
                                    'element': item
                                })
                except:
                    continue
            
            print(f"   ✅ Found {len(cart_items)} items in cart")
            return cart_items
            
        except Exception as e:
            print(f"   ❌ View cart failed: {e}")
            return []


class BigBasketAdapter(GroceryWebsiteAdapter):
    """BigBasket grocery delivery adapter."""
    
    def get_base_url(self) -> str:
        return "https://www.bigbasket.com"
    
    def setup_location(self, pincode: str, area: str = None) -> bool:
        try:
            print(f"🏠 Setting up BigBasket location: {pincode}")
            self.driver.get(self.get_base_url())
            time.sleep(5)
            
            # BigBasket location setup logic
            location_selectors = [
                "input[placeholder*='pincode' i]",
                ".location-input",
                "#pincode"
            ]
            
            for selector in location_selectors:
                try:
                    location_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if location_input.is_displayed():
                        location_input.clear()
                        location_input.send_keys(pincode)
                        location_input.send_keys(Keys.ENTER)
                        time.sleep(5)
                        
                        self.location_set = True
                        print("   ✅ BigBasket location set successfully")
                        return True
                except:
                    continue
            
            print("   ⚠️ Could not set BigBasket location")
            return False
            
        except Exception as e:
            print(f"   ❌ BigBasket location setup failed: {e}")
            return False
    
    def search_product(self, product_name: str) -> List[Dict]:
        try:
            print(f"🔍 Searching BigBasket for: {product_name}")
            
            search_selectors = [
                "input[placeholder*='Search' i]",
                ".search-input",
                "#search"
            ]
            
            for selector in search_selectors:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_input.is_displayed():
                        search_input.clear()
                        search_input.send_keys(product_name)
                        search_input.send_keys(Keys.ENTER)
                        time.sleep(5)
                        break
                except:
                    continue
            
            # Extract results
            products = []
            result_selectors = [
                ".product",
                "[class*='product']",
                ".item"
            ]
            
            for selector in result_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if text:
                                products.append({
                                    'name': text,
                                    'element': element
                                })
                except:
                    continue
            
            print(f"   ✅ Found {len(products)} BigBasket products")
            return products
            
        except Exception as e:
            print(f"   ❌ BigBasket search failed: {e}")
            return []
    
    def add_to_cart(self, product_element, quantity: int = 1) -> bool:
        try:
            print("🛒 Adding BigBasket product to cart")
            
            add_buttons = product_element.find_elements(By.CSS_SELECTOR, 
                "button[class*='add'], .add-button, button:contains('Add')")
            
            for button in add_buttons:
                if button.is_displayed():
                    button.click()
                    time.sleep(2)
                    print("   ✅ Added to BigBasket cart")
                    return True
            
            return False
            
        except Exception as e:
            print(f"   ❌ BigBasket add to cart failed: {e}")
            return False
    
    def view_cart(self) -> List[Dict]:
        try:
            print("🛒 Viewing BigBasket cart")
            
            # Click cart icon
            cart_selectors = [
                ".cart",
                "[class*='cart']",
                "#cart"
            ]
            
            for selector in cart_selectors:
                try:
                    cart_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if cart_button.is_displayed():
                        cart_button.click()
                        time.sleep(3)
                        break
                except:
                    continue
            
            # Extract cart items
            cart_items = []
            item_selectors = [
                ".cart-item",
                "[class*='cart-item']"
            ]
            
            for selector in item_selectors:
                try:
                    items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for item in items:
                        if item.is_displayed():
                            cart_items.append({
                                'name': item.text.strip(),
                                'element': item
                            })
                except:
                    continue
            
            print(f"   ✅ Found {len(cart_items)} items in BigBasket cart")
            return cart_items
            
        except Exception as e:
            print(f"   ❌ BigBasket view cart failed: {e}")
            return []


# Factory function to create appropriate adapter
def create_grocery_adapter(platform_name: str, driver: webdriver.Chrome, wait: WebDriverWait) -> GroceryWebsiteAdapter:
    """Factory function to create the appropriate grocery adapter."""
    platform_name = platform_name.lower()
    
    if platform_name in ['blinkit', 'grofers']:
        return BlinkitAdapter(driver, wait)
    elif platform_name in ['bigbasket', 'bb']:
        return BigBasketAdapter(driver, wait)
    else:
        raise ValueError(f"Unsupported grocery platform: {platform_name}")


def get_supported_grocery_platforms() -> List[str]:
    """Get list of supported grocery delivery platforms."""
    return [
        'blinkit',
        'bigbasket'
    ]