"""
interactive_session.py: Interactive AIVA session with persistent browser and user confirmations
- Keeps browser open throughout the session
- Handles login flow with credential management
- Smart AI-powered product selection with semantic recommendations
- User confirmations for cart and payment
"""
import logging
import time
import re
from typing import Dict, List, Optional
from perception import create_edge_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from smart_recommendations import SmartProductRecommender
from credential_manager import CredentialManager

class InteractiveAIVA:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.logged_in = False
        self.recommender = SmartProductRecommender()  # AI recommendation system
        self.credential_manager = CredentialManager()  # Credential management
        
    def start_session(self, platform: str = "flipkart"):
        """Start browser session and navigate to platform."""
        print("🚀 Starting AIVA Interactive Session...")
        try:
            self.driver = create_edge_driver()
            self.wait = WebDriverWait(self.driver, 20)
            
            if platform.lower() == "flipkart":
                self.driver.get("https://www.flipkart.com/")
                print("✅ Opened Flipkart")
            else:
                print(f"❌ Platform {platform} not supported yet")
                return False
                
            return True
        except Exception as e:
            print(f"❌ Failed to start session: {e}")
            return False
    
    def smart_login_handler(self, action_context: str = "shopping") -> bool:
        """Smart login handling based on action context."""
        print(f"\n🔐 Login Check for {action_context}...")
        
        # Check current login status
        login_status = self.check_login_status()
        
        if login_status == "logged_in":
            print("✅ You're already logged in!")
            self.logged_in = True
            return True
        elif login_status == "not_logged_in":
            return self.prompt_for_login(action_context)
        else:
            print("⚠️ Could not determine login status, continuing...")
            return True
    
    def check_login_status(self) -> str:
        """Check if user is currently logged in."""
        try:
            # Method 1: Look for login/signup buttons (indicates not logged in)
            login_indicators = [
                '//span[contains(text(), "Login")]',
                '//span[contains(text(), "Sign Up")]',
                '//a[contains(@href, "account/login")]',
                '//button[contains(text(), "Login")]'
            ]
            
            for indicator in login_indicators:
                elements = self.driver.find_elements(By.XPATH, indicator)
                if elements and any(el.is_displayed() for el in elements):
                    return "not_logged_in"
            
            # Method 2: Look for user account indicators (indicates logged in)
            account_indicators = [
                '//span[contains(@class, "namePed")]',  # Flipkart user name
                '//div[contains(@class, "_1psGji")]',   # Account dropdown
                '//span[contains(text(), "My Account")]',
                '//div[contains(@title, "Account")]'
            ]
            
            for indicator in account_indicators:
                elements = self.driver.find_elements(By.XPATH, indicator)
                if elements and any(el.is_displayed() for el in elements):
                    return "logged_in"
            
            return "unknown"
            
        except Exception as e:
            print(f"⚠️ Login status check failed: {e}")
            return "unknown"
    
    def prompt_for_login(self, action_context: str) -> bool:
        """Prompt user for login with context-aware messaging."""
        print("\n" + "="*50)
        print("🔒 LOGIN REQUIRED")
        print("="*50)
        
        if action_context == "cart":
            print("🛒 To add items to cart and checkout, you need to be logged in.")
            print("💡 This ensures your items are saved and you can complete purchase.")
        elif action_context == "shopping":
            print("🛍️ For the best shopping experience, please log in.")
            print("💡 This enables cart management, order history, and personalized recommendations.")
        else:
            print(f"🔐 Login is recommended for {action_context}.")
        
        print("\nOptions:")
        print("1. 🔐 Login now (Recommended)")
        print("2. 🕶️ Continue as guest (Limited functionality)")
        print("3. ❌ Cancel and exit")
        
        while True:
            choice = input("\nSelect option (1/2/3): ").strip()
            
            if choice == "1":
                return self.interactive_login()
            elif choice == "2":
                print("⚠️ Continuing as guest - some features may not work")
                return True
            elif choice == "3":
                print("👋 Goodbye!")
                return False
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    def interactive_login(self) -> bool:
        """Interactive login process with credential management."""
        print("\n🔐 LOGIN PROCESS")
        print("-" * 30)
        
        # Get user choice for credentials
        choice = self.credential_manager.get_credential_choice()
        
        if choice == "1" and self.credential_manager.has_saved_credentials():
            # Use saved credentials
            return self.auto_login_with_saved_credentials()
        elif choice == "1" or choice == "2":
            # Manual login (new credentials or no saved ones)
            return self.manual_login_process()
        elif choice == "3":
            # Guest mode
            print("🕶️ Continuing as guest")
            return True
        elif choice == "4":
            # Delete credentials
            self.credential_manager.delete_credentials()
            return self.interactive_login()  # Restart the process
        else:
            return True
    
    def auto_login_with_saved_credentials(self) -> bool:
        """Assisted login using saved credentials (Flipkart requires OTP)."""
        print("🔑 Using saved credentials for assisted login...")
        
        creds = self.credential_manager.load_credentials()
        if not creds:
            print("❌ Could not load saved credentials")
            return self.manual_login_process()
        
        try:
            # Navigate to login page
            self.driver.get("https://www.flipkart.com/account/login")
            time.sleep(3)
            
            print("🤖 Assisted login in progress...")
            print(f"📧 Using saved email/mobile: {creds['username']}")
            
            # Find and fill email/mobile field
            email_selectors = [
                '//input[@class="_2IX_2- VJZDxU"]',
                '//input[contains(@class, "email")]',
                '//input[contains(@class, "mobile")]',
                '//input[@type="text"]',
                '//input[@name="username"]'
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = self.driver.find_element(By.XPATH, selector)
                    if email_field.is_displayed():
                        break
                except:
                    continue
            
            if email_field:
                email_field.clear()
                email_field.send_keys(creds["username"])
                print("✅ Email/mobile entered automatically")
                time.sleep(1)
                
                # Try to proceed to OTP step
                proceed_selectors = [
                    '//button[contains(text(), "Request OTP")]',
                    '//button[contains(text(), "Continue")]',
                    '//button[contains(text(), "Next")]',
                    '//button[@class="_2KpZ6l _2HKlqd _3AWRsL"]'
                ]
                
                proceed_button = None
                for selector in proceed_selectors:
                    try:
                        proceed_button = self.driver.find_element(By.XPATH, selector)
                        if proceed_button.is_displayed() and proceed_button.is_enabled():
                            break
                    except:
                        continue
                
                if proceed_button:
                    proceed_button.click()
                    print("✅ Proceeding to OTP verification...")
                    time.sleep(3)
                    
                    # Now handle OTP
                    return self.handle_otp_verification()
                else:
                    print("❌ Could not find proceed button")
                    return self.manual_otp_login(creds["username"])
            else:
                print("❌ Could not find email field")
                return self.manual_login_process()
                
        except Exception as e:
            print(f"❌ Assisted login failed: {e}")
            print("🔄 Falling back to manual login...")
            return self.manual_login_process()
    
    def handle_otp_verification(self) -> bool:
        """Handle OTP verification step."""
        print("\n📱 OTP VERIFICATION")
        print("-" * 30)
        print("🔐 Flipkart has sent an OTP to your registered mobile number")
        print("📲 Please check your SMS/WhatsApp for the OTP")
        
        # Wait for OTP input
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                otp = input(f"\n🔢 Enter OTP (Attempt {attempt + 1}/{max_attempts}): ").strip()
                
                if not otp or not otp.isdigit():
                    print("❌ Please enter a valid numeric OTP")
                    continue
                
                # Find OTP input field
                otp_selectors = [
                    '//input[@type="text" and @maxlength="6"]',
                    '//input[contains(@class, "otp")]',
                    '//input[@class="_2IX_2- VJZDxU"]',
                    '//input[@placeholder="Enter OTP"]'
                ]
                
                otp_field = None
                for selector in otp_selectors:
                    try:
                        otp_field = self.driver.find_element(By.XPATH, selector)
                        if otp_field.is_displayed():
                            break
                    except:
                        continue
                
                if otp_field:
                    otp_field.clear()
                    otp_field.send_keys(otp)
                    print("✅ OTP entered")
                    time.sleep(1)
                    
                    # Find and click verify button
                    verify_selectors = [
                        '//button[contains(text(), "Verify")]',
                        '//button[contains(text(), "Login")]',
                        '//button[contains(text(), "Continue")]',
                        '//button[@class="_2KpZ6l _2HKlqd _3AWRsL"]'
                    ]
                    
                    verify_button = None
                    for selector in verify_selectors:
                        try:
                            verify_button = self.driver.find_element(By.XPATH, selector)
                            if verify_button.is_displayed() and verify_button.is_enabled():
                                break
                        except:
                            continue
                    
                    if verify_button:
                        verify_button.click()
                        print("🔐 Verifying OTP...")
                        time.sleep(5)
                        
                        # Check for login success
                        login_status = self.check_login_status()
                        if login_status == "logged_in":
                            print("🎉 OTP verification successful!")
                            self.logged_in = True
                            self.driver.get("https://www.flipkart.com/")
                            time.sleep(2)
                            return True
                        else:
                            # Check if still on OTP page (wrong OTP)
                            current_url = self.driver.current_url
                            if "verify" in current_url.lower() or "otp" in current_url.lower():
                                print("❌ Invalid OTP. Please try again.")
                                continue
                            else:
                                print("⚠️ OTP verification completed, but login status unclear")
                                return True
                    else:
                        print("❌ Could not find verify button")
                        break
                else:
                    print("❌ Could not find OTP input field")
                    break
                    
            except Exception as e:
                print(f"❌ OTP verification error: {e}")
                continue
        
        print("❌ OTP verification failed after multiple attempts")
        print("💡 Please try manual login")
        return False
    
    def manual_otp_login(self, email: str = None) -> bool:
        """Manual OTP-based login process."""
        print("\n🔐 MANUAL LOGIN WITH OTP")
        print("-" * 30)
        
        try:
            if not email:
                self.driver.get("https://www.flipkart.com/account/login")
                time.sleep(3)
                
                print("📋 Manual Login Steps:")
                print("1. 📱 Enter your mobile number/email")
                print("2. 🔢 Click 'Request OTP' or 'Continue'")
                print("3. 📲 Check your SMS/WhatsApp for OTP")
                print("4. 🔐 Enter the OTP when prompted")
                print("5. ✅ Click 'Verify' or 'Login'")
            else:
                print(f"📧 Email/mobile: {email} (already entered)")
                print("📋 Remaining Steps:")
                print("1. 📲 Check your SMS/WhatsApp for OTP")
                print("2. 🔐 Enter the OTP in the browser")
                print("3. ✅ Click 'Verify' or 'Login'")
            
            print("\n⚠️  IMPORTANT: Flipkart requires OTP verification for security")
            print("📱 Make sure you have access to your registered mobile number")
            print("\n⏰ Take your time - I'll wait for you to complete the process...")
            
            # Wait for user to complete login
            input("\n⏸️  Press Enter AFTER you have successfully logged in...")
            
            # Verify login
            time.sleep(2)
            login_status = self.check_login_status()
            
            if login_status == "logged_in":
                print("🎉 Login successful! Welcome!")
                self.logged_in = True
                
                # Ask if user wants to save email for future assisted login
                if not email and not self.credential_manager.has_saved_credentials():
                    save_email = input("\n💾 Save email/mobile for faster login next time? (y/n): ").lower().strip()
                    if save_email == 'y':
                        user_email = input("📧 Enter your email/mobile: ").strip()
                        if user_email:
                            # Save with placeholder password (OTP will still be required)
                            self.credential_manager.save_credentials(user_email, "otp_required")
                            print("💾 Email saved for assisted login (OTP will still be required)")
                
                # Navigate back to main page
                self.driver.get("https://www.flipkart.com/")
                time.sleep(2)
                return True
            else:
                print("⚠️ Login verification failed, but continuing...")
                print("💡 You may need to manually verify your login status")
                return True
                
        except Exception as e:
            print(f"❌ Login process error: {e}")
            print("� Please try refreshing the page and logging in again")
            return True
    
    def manual_login_process(self) -> bool:
        """Manual login process optimized for OTP-based authentication."""
        print("🌐 Opening Flipkart login page...")
        
        try:
            # Navigate to login page
            self.driver.get("https://www.flipkart.com/account/login")
            time.sleep(3)
            
            print("\n📋 Flipkart Login Instructions (OTP Required):")
            print("� Flipkart uses OTP-based login for security")
            print("📱 Make sure you have access to your registered mobile number")
            print()
            print("Steps:")
            print("1. � Enter your mobile number/email in the browser")
            print("2. 🔢 Click 'Request OTP' or 'Continue'")
            print("3. � Check your SMS/WhatsApp for the OTP")
            print("4. 🔐 Enter the OTP when prompted")
            print("5. ✅ Click 'Verify' or 'Login'")
            print("\n⏰ Take your time - I'll wait for you to complete the process...")
            
            # Ask if user wants to save email for future assisted login
            save_email = input("\n💾 Would you like to save your email/mobile for faster login next time? (y/n): ").lower().strip()
            
            saved_email = None
            if save_email == 'y':
                email = input("� Enter email/mobile to save: ").strip()
                if email:
                    print("💾 Email will be saved after successful login")
                    saved_email = email
                else:
                    print("⚠️ Skipping email save (empty field)")
            
            # Wait for user to complete login
            input("\n⏸️  Press Enter AFTER you have successfully logged in with OTP...")
            
            # Verify login
            time.sleep(2)
            login_status = self.check_login_status()
            
            if login_status == "logged_in":
                print("🎉 Login successful! Welcome!")
                self.logged_in = True
                
                # Save email if requested and login was successful
                if saved_email:
                    # Save as OTP account since Flipkart requires OTP
                    self.credential_manager.save_otp_account(saved_email)
                    print("💾 Email saved for assisted OTP login")
                
                # Navigate back to main page
                self.driver.get("https://www.flipkart.com/")
                time.sleep(2)
                return True
            else:
                print("⚠️ Login verification failed, but continuing...")
                print("💡 You may need to manually verify your login status")
                return True
                
        except Exception as e:
            print(f"❌ Login process error: {e}")
            print("💡 Please try refreshing the page and logging in again")
            return True
    
    def handle_login(self):
        """Legacy login handler - replaced by smart_login_handler."""
        return self.smart_login_handler("shopping")
    
    def search_products(self, product: str, price_limit: Optional[int] = None) -> List[Dict]:
        """Universal product search that works for any product type on Flipkart."""
        print(f"\n🔍 Searching for: {product}")
        if price_limit:
            print(f"💰 Price limit: ₹{price_limit}")
        
        try:
            # Close any popups
            try:
                close_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "✕")]')))
                close_btn.click()
            except Exception:
                pass
            
            # Search
            search_box = self.wait.until(EC.presence_of_element_located((By.NAME, "q")))
            search_box.clear()
            search_box.send_keys(product)
            search_box.send_keys(Keys.ENTER)
            
            time.sleep(5)  # Wait longer for results to load
            
            print("🔍 Analyzing search results...")
            
            # Universal approach: Find all elements with price symbols
            price_elements = self.driver.find_elements(By.XPATH, '//*[contains(text(), "₹")]')
            print(f"Found {len(price_elements)} elements with prices")
            
            products = []
            processed_containers = set()  # Avoid duplicates
            
            for price_el in price_elements[:20]:  # Check first 20 price elements
                try:
                    # Navigate up the DOM to find the product container
                    container = None
                    current = price_el
                    
                    # Go up the DOM tree to find a substantial container
                    for level in range(1, 6):  # Check up to 5 levels up
                        try:
                            current = current.find_element(By.XPATH, '..')
                            text_content = current.text.strip()
                            
                            # Check if this looks like a product container
                            if (len(text_content) > 50 and 
                                "₹" in text_content and 
                                current not in processed_containers):
                                container = current
                                processed_containers.add(container)
                                break
                        except Exception:
                            break
                    
                    if not container:
                        continue
                    
                    # Extract product information
                    container_text = container.text.strip()
                    lines = [line.strip() for line in container_text.split('\n') if line.strip()]
                    
                    # Find title (usually one of the longer lines without just price)
                    title = None
                    for line in lines:
                        if (len(line) > 10 and 
                            "₹" not in line and 
                            not line.isdigit() and
                            "%" not in line and
                            "rating" not in line.lower() and
                            "free delivery" not in line.lower()):
                            title = line
                            break
                    
                    if not title:
                        # Fallback: use first substantial line
                        for line in lines:
                            if len(line) > 15:
                                title = line
                                break
                    
                    # Extract price
                    price = None
                    for line in lines:
                        if "₹" in line:
                            import re
                            # Extract number after ₹
                            price_match = re.search(r'₹\s*([0-9,]+)', line)
                            if price_match:
                                price_str = price_match.group(1).replace(',', '')
                                try:
                                    price = int(price_str)
                                    break
                                except ValueError:
                                    continue
                    
                    # Extract rating if available
                    rating = None
                    for line in lines:
                        if "★" in line or "star" in line.lower():
                            rating_match = re.search(r'([0-9.]+)', line)
                            if rating_match:
                                try:
                                    rating = float(rating_match.group(1))
                                    break
                                except ValueError:
                                    continue
                    
                    # Validate the extracted data
                    if not title or not price:
                        continue
                    
                    # Check price limit
                    if price_limit and price > price_limit:
                        continue
                    
                    # Try to find a clickable element within this container
                    clickable_el = None
                    try:
                        # Look for links or clickable elements
                        clickable_candidates = container.find_elements(By.XPATH, './/a[@href]')
                        if clickable_candidates:
                            clickable_el = clickable_candidates[0]
                        else:
                            # Fallback to the container itself
                            clickable_el = container
                    except Exception:
                        clickable_el = container
                    
                    products.append({
                        "index": len(products) + 1,
                        "title": title,
                        "price": price,
                        "rating": rating,
                        "element": clickable_el,
                        "card": container,
                        "raw_text": container_text[:200]  # For debugging
                    })
                    
                    # Limit results
                    if len(products) >= 10:
                        break
                        
                except Exception as e:
                    continue
            
            # Sort by price (ascending) for best value first
            products.sort(key=lambda x: x['price'])
            
            # Re-index after sorting
            for i, product in enumerate(products):
                product['index'] = i + 1
            
            print(f"✅ Found {len(products)} products")
            
            # Debug: show what we found
            if products:
                print("📋 Products found:")
                for p in products[:5]:
                    rating_str = f" | ⭐ {p['rating']}" if p['rating'] else ""
                    print(f"  {p['index']}. {p['title'][:50]}... | ₹{p['price']}{rating_str}")
            
            return products
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def select_best_product(self, products: List[Dict], criteria: str = "smart", auto_select: bool = True, user_query: str = "") -> Optional[Dict]:
        """AI-powered product selection with semantic recommendations."""
        if not products:
            return None
        
        print(f"\n🤖 AI Product Selection (criteria: {criteria}):")
        
        # Get smart recommendations
        recommended_products = self.recommender.recommend_products(
            products, user_query, criteria=criteria, top_k=len(products)
        )
        
        # Display options with AI explanations
        for i, product in enumerate(recommended_products[:5], 1):  # Show top 5
            rating_str = f" | ⭐ {product['rating']}" if product['rating'] else ""
            score_str = f" | AI Score: {product.get('final_score', 0):.2f}" if criteria == "smart" else ""
            
            print(f"{i}. {product['title']}")
            print(f"   💰 ₹{product['price']}{rating_str}{score_str}")
            
            if criteria == "smart":
                explanation = self.recommender.explain_recommendation(product)
                print(f"   🔍 {explanation}")
            print()
        
        # Select best product
        selected = recommended_products[0] if recommended_products else products[0]
        
        if criteria == "smart":
            print(f"🎯 AI Selected: {selected['title']} (₹{selected['price']})")
            print(f"🔍 {self.recommender.explain_recommendation(selected)}")
        elif criteria == "price":
            print(f"🎯 AI Selected: Best value - {selected['title']} (₹{selected['price']})")
        elif criteria == "rating":
            rating_text = f" (⭐ {selected['rating']})" if selected['rating'] else " (no ratings)"
            print(f"🎯 AI Selected: Highest rated - {selected['title']}{rating_text}")
        
        if auto_select:
            print(f"🤖 Adding to cart automatically for review...")
            return selected
        else:
            # Ask for user confirmation
            choice = input(f"\n❓ Do you want to add '{selected['title']}' to cart? (y/n/choose): ").lower().strip()
            
            if choice == 'y' or choice == 'yes':
                return selected
            elif choice == 'n' or choice == 'no':
                print("❌ Product selection cancelled.")
                return None
            elif choice == 'choose':
                try:
                    idx = int(input("Enter product number (1-5): ")) - 1
                    if 0 <= idx < len(recommended_products):
                        return recommended_products[idx]
                    else:
                        print("❌ Invalid choice, using AI selection.")
                        return selected
                except ValueError:
                    print("❌ Invalid input, using AI selection.")
                    return selected
            else:
                print("❌ Invalid choice, using AI selection.")
                return selected
    
    def add_to_cart(self, product: Dict) -> bool:
        """Add selected product to cart with robust navigation and tab management."""
        print(f"\n🛒 Adding to cart: {product['title']}")
        
        # Check if login is needed for cart operations
        if not self.logged_in:
            print("🔐 Login check for cart operations...")
            if not self.smart_login_handler("cart"):
                print("❌ Login cancelled or failed")
                return False
        
        try:
            # Store the original window handle
            original_window = self.driver.current_window_handle
            original_windows = set(self.driver.window_handles)
            
            # Method 1: Try to refresh and find the product element again
            print("🔍 Method 1: Re-finding product element...")
            try:
                # Use title to find the product again (more reliable)
                product_title = product['title']
                
                # Search for elements containing the product title
                title_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{product_title[:30]}')]")
                
                fresh_product_element = None
                for element in title_elements:
                    try:
                        # Find the parent container that might be clickable
                        parent = element
                        for _ in range(5):  # Check up to 5 levels up
                            if parent.tag_name in ['a', 'div'] and parent.is_displayed():
                                # Check if this parent contains price info (indicating it's a product card)
                                parent_text = parent.text
                                if '₹' in parent_text and product_title[:20] in parent_text:
                                    fresh_product_element = parent
                                    break
                            parent = parent.find_element(By.XPATH, "..")
                        if fresh_product_element:
                            break
                    except:
                        continue
                
                if fresh_product_element:
                    print("✅ Found fresh product element")
                    
                    # Try clicking it
                    self.driver.execute_script("arguments[0].click();", fresh_product_element)
                    time.sleep(3)
                    
                    # Check for new windows/tabs
                    new_windows = set(self.driver.window_handles) - original_windows
                    if new_windows:
                        # Switch to the new tab
                        new_window = new_windows.pop()
                        self.driver.switch_to.window(new_window)
                        print("✅ Switched to new product tab")
                        time.sleep(2)
                        return self._find_and_click_add_to_cart_with_tab_cleanup(original_window)
                    
                    # Check if we navigated to a product page in same tab
                    current_url = self.driver.current_url
                    if '/p/' in current_url or 'product' in current_url.lower():
                        print("✅ Navigated to product detail page (same tab)")
                        return self._find_and_click_add_to_cart()
                    else:
                        print("⚠️ Still on search page, trying method 2...")
                
            except Exception as e:
                print(f"⚠️ Method 1 failed: {e}")
            
            # Method 2: Try to find any link containing the product name
            print("🔍 Method 2: Looking for product links by title...")
            try:
                # Look for links containing parts of the product title
                title_parts = product['title'].split()[:3]  # Use first 3 words
                
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    try:
                        href = link.get_attribute('href')
                        link_text = link.text
                        
                        if href and ('/p/' in href or 'product' in href.lower()):
                            # Check if link text matches our product
                            if any(part in link_text for part in title_parts):
                                print(f"✅ Found matching product link")
                                
                                # Store windows before clicking
                                windows_before = set(self.driver.window_handles)
                                link.click()
                                time.sleep(3)
                                
                                # Check for new windows/tabs
                                windows_after = set(self.driver.window_handles)
                                new_windows = windows_after - windows_before
                                
                                if new_windows:
                                    # Switch to the new tab
                                    new_window = new_windows.pop()
                                    self.driver.switch_to.window(new_window)
                                    print("✅ Switched to new product tab")
                                    time.sleep(2)
                                    return self._find_and_click_add_to_cart_with_tab_cleanup(original_window)
                                else:
                                    # Same tab navigation
                                    return self._find_and_click_add_to_cart()
                    except:
                        continue
                        
            except Exception as e:
                print(f"⚠️ Method 2 failed: {e}")
            
            # Method 3: Direct navigation using URL
            print("🔍 Method 3: Direct URL navigation...")
            try:
                # Look for any product URL and navigate directly
                title_parts = product['title'].split()[:2]  # Use first 2 words
                
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    try:
                        href = link.get_attribute('href')
                        if href and ('/p/' in href or 'product' in href.lower()):
                            # Navigate directly instead of clicking
                            print(f"✅ Direct navigation to: {href}")
                            self.driver.get(href)
                            time.sleep(3)
                            return self._find_and_click_add_to_cart()
                    except:
                        continue
                        
            except Exception as e:
                print(f"⚠️ Method 3 failed: {e}")
            
            print("❌ All methods failed to navigate to product page")
            return False
            
        except Exception as e:
            print(f"❌ Failed to add to cart: {e}")
            return False
    
    def _find_and_click_add_to_cart(self) -> bool:
        """Find and click the Add to Cart button on product detail page."""
        print("🔍 Looking for Add to Cart button on product page...")
        
        # Wait for page to load
        time.sleep(2)
        
        # Comprehensive list of Add to Cart selectors
        add_to_cart_selectors = [
            # Text-based selectors (most reliable)
            '//button[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "add to cart")]',
            '//span[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "add to cart")]',
            '//div[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "add to cart")]',
            
            # Exact text matches
            '//button[text()="ADD TO CART"]',
            '//button[text()="Add to Cart"]',
            '//span[text()="ADD TO CART"]',
            '//span[text()="Add to Cart"]',
            
            # Common Flipkart class patterns
            '//button[contains(@class, "_2KpZ6l")]',
            '//button[contains(@class, "_2AkmmA")]',
            '//button[contains(@class, "_1k9lOr")]',
            '//button[contains(@class, "btn-cart")]',
            
            # Generic approaches
            '//button[contains(., "cart") or contains(., "Cart") or contains(., "ADD")]',
            '//*[@role="button" and (contains(text(), "cart") or contains(text(), "Cart"))]',
            
            # Fallback selectors
            '//*[contains(text(), "ADD TO CART") and (local-name()="button" or local-name()="span" or local-name()="div")]'
        ]
        
        # Try each selector
        for i, selector in enumerate(add_to_cart_selectors):
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element_text = element.text.strip()
                        print(f"✅ Found Add to Cart button: '{element_text}' (selector {i+1})")
                        element.click()
                        time.sleep(2)
                        print("✅ Added to cart successfully!")
                        return True
            except Exception:
                continue
        
        # If no specific Add to Cart button found, try any button with cart-related text
        print("⚠️ Specific Add to Cart button not found, trying any cart-related button...")
        
        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        cart_keywords = ['cart', 'add', 'buy', 'purchase']
        
        for btn in all_buttons:
            try:
                text = btn.text.lower().strip()
                if any(keyword in text for keyword in cart_keywords) and len(text) > 0:
                    if btn.is_displayed() and btn.is_enabled():
                        print(f"✅ Trying button: '{btn.text}'")
                        btn.click()
                        time.sleep(2)
                        
                        # Check if we were successful (simple check)
                        page_text = self.driver.page_source.lower()
                        if 'added to cart' in page_text or 'cart' in self.driver.title.lower():
                            print("✅ Successfully added to cart!")
                            return True
            except Exception:
                continue
        
        print("❌ Could not find any working Add to Cart button")
        return False
    
    def _find_and_click_add_to_cart_with_tab_cleanup(self, original_window: str) -> bool:
        """Find and click Add to Cart button with proper tab management."""
        try:
            result = self._find_and_click_add_to_cart()
            
            # After attempting to add to cart, close the product tab and return to original
            try:
                current_handles = self.driver.window_handles
                if len(current_handles) > 1:
                    # Close current tab
                    self.driver.close()
                    # Switch back to original window
                    self.driver.switch_to.window(original_window)
                    print("✅ Closed product tab and returned to search")
            except Exception as e:
                print(f"⚠️ Tab cleanup warning: {e}")
                # Try to switch back to original window anyway
                try:
                    self.driver.switch_to.window(original_window)
                except:
                    pass
            
            return result
            
        except Exception as e:
            print(f"❌ Error in tab-aware add to cart: {e}")
            # Ensure we return to original tab
            try:
                self.driver.switch_to.window(original_window)
            except:
                pass
            return False
    
    def remove_from_cart(self, product_title: str) -> bool:
        """Remove item from cart."""
        print(f"\n�️ Removing '{product_title}' from cart...")
        
        try:
            # Go to cart
            self.driver.get("https://www.flipkart.com/viewcart")
            time.sleep(3)
            
            # Look for remove buttons with multiple selectors
            remove_selectors = [
                '//div[contains(@class, "_3dsJAO")]//span[contains(text(), "Remove")]',
                '//button[contains(text(), "Remove")]',
                '//span[contains(text(), "Remove")]',
                '//div[contains(@class, "_3cc_Qe")]//span[text()="Remove"]',
                '//button[@class="_23FHuj"]'  # Common Flipkart remove button class
            ]
            
            removed = False
            for selector in remove_selectors:
                try:
                    # Find and click the first remove button
                    remove_elements = self.driver.find_elements(By.XPATH, selector)
                    if remove_elements:
                        remove_btn = remove_elements[0]
                        if remove_btn.is_displayed() and remove_btn.is_enabled():
                            self.driver.execute_script("arguments[0].click();", remove_btn)
                            print("🔄 Clicked first remove button...")
                            time.sleep(2)
                            
                            # Handle confirmation dialog - try multiple selectors
                            confirmation_selectors = [
                                '//div[contains(@class, "_2AkmmA")]//div[contains(text(), "Remove")]',
                                '//button[contains(text(), "Remove")]',
                                '//div[contains(@class, "_3dsJAO")]//button[contains(text(), "Remove")]',
                                '//span[text()="Remove"]',
                                '//button[@class="_2AkmmA _29YdH8"]'  # Flipkart confirmation button
                            ]
                            
                            confirmation_clicked = False
                            for conf_selector in confirmation_selectors:
                                try:
                                    confirm_elements = self.driver.find_elements(By.XPATH, conf_selector)
                                    for confirm_btn in confirm_elements:
                                        if confirm_btn.is_displayed() and confirm_btn.is_enabled():
                                            self.driver.execute_script("arguments[0].click();", confirm_btn)
                                            print("✅ Clicked confirmation remove button")
                                            time.sleep(3)
                                            confirmation_clicked = True
                                            break
                                    if confirmation_clicked:
                                        break
                                except Exception:
                                    continue
                            
                            if not confirmation_clicked:
                                print("⚠️ Could not find confirmation button, item might be removed")
                            
                            # Check if cart is empty or item is removed
                            time.sleep(2)
                            page_source = self.driver.page_source.lower()
                            if "your cart is empty" in page_source or "missing cart items" in page_source:
                                print("✅ Item removed from cart (cart is now empty)")
                                removed = True
                                break
                            else:
                                print("✅ Item removed from cart")
                                removed = True
                                break
                except Exception as e:
                    continue
            
            if not removed:
                print("⚠️ Could not remove item (might already be empty or removed)")
            
            return removed
            
        except Exception as e:
            print(f"❌ Error removing from cart: {e}")
            return False
    
    def review_cart(self) -> bool:
        """Review items in cart and get user approval."""
        print(f"\n📋 Reviewing cart...")
        
        try:
            # Go to cart
            self.driver.get("https://www.flipkart.com/viewcart")
            time.sleep(3)
            
            # Check if cart is empty
            empty_indicators = self.driver.find_elements(By.XPATH, '//*[contains(text(), "Your cart is empty") or contains(text(), "Missing Cart items")]')
            if empty_indicators:
                print("🛒 Cart is empty")
                return False
            
            # Get cart items
            cart_items = []
            item_elements = self.driver.find_elements(By.XPATH, '//div[contains(@class, "_1kp8KI") or contains(@class, "_1AtVbE")]')
            
            for item in item_elements[:3]:  # Show max 3 items
                try:
                    # Get item name
                    name_el = item.find_element(By.XPATH, './/a[contains(@class, "_2rpwqI")] | .//div[contains(@class, "_4rR01T")]')
                    name = name_el.text.strip()
                    
                    # Get price
                    price_el = item.find_element(By.XPATH, './/*[contains(text(), "₹")]')
                    price = price_el.text.strip()
                    
                    cart_items.append({"name": name, "price": price})
                except Exception:
                    continue
            
            if not cart_items:
                print("⚠️ Could not read cart items, but cart appears to have items")
                
            print("🛒 Current cart contents:")
            for i, item in enumerate(cart_items, 1):
                print(f"{i}. {item['name']} - {item['price']}")
            
            # Ask for approval
            approval = input(f"\n❓ Are you satisfied with this item in your cart? (y/n): ").lower().strip()
            
            if approval == 'y' or approval == 'yes':
                print("✅ Cart approved!")
                return True
            else:
                print("❌ Item not approved, will find alternative")
                return False
                
        except Exception as e:
            print(f"❌ Error reviewing cart: {e}")
            return False
    
    def intelligent_shopping_loop(self, product: str, price_limit: Optional[int] = None, max_attempts: int = 3):
        """Intelligent shopping loop: find → add → review → repeat if not satisfied."""
        print(f"\n🛍️ Starting Intelligent Shopping Loop")
        print(f"🎯 Looking for: {product}")
        if price_limit:
            print(f"💰 Price limit: ₹{price_limit}")
        print(f"🔄 Max attempts: {max_attempts}")
        
        attempts = 0
        tried_products = []  # Keep track of what we've tried
        
        while attempts < max_attempts:
            attempts += 1
            print(f"\n--- Attempt {attempts}/{max_attempts} ---")
            
            # Search for products
            products = self.search_products(product, price_limit)
            
            if not products:
                print("❌ No more products found matching criteria")
                break
            
            # Filter out already tried products
            available_products = [p for p in products if p['title'] not in tried_products]
            
            if not available_products:
                print("❌ All available products have been tried")
                break
            
            # Select best available product with AI
            selected = self.select_best_product(available_products, criteria="smart", auto_select=True, user_query=product)
            
            if not selected:
                print("❌ No product selected")
                break
            
            # Add to tried list
            tried_products.append(selected['title'])
            
            # Add to cart
            if self.add_to_cart(selected):
                
                # Review cart
                if self.review_cart():
                    print("🎉 Perfect! Shopping completed successfully!")
                    return True
                else:
                    # Remove from cart and try next option
                    print("🔄 Trying next best option...")
                    self.remove_from_cart(selected['title'])
            else:
                print("❌ Failed to add to cart, trying next option...")
        
    def proceed_to_checkout(self):
        """Navigate to cart and ask for payment confirmation."""
        print("\n� Proceeding to checkout...")
        
        try:
            # Go to cart
            self.driver.get("https://www.flipkart.com/viewcart")
            time.sleep(3)
            
            print("✅ Cart opened. Please review your items.")
            
            # Ask for payment confirmation
            proceed = input("\n❓ Do you want to proceed to payment? (y/n): ").lower().strip()
            
            if proceed == 'y' or proceed == 'yes':
                # Look for checkout button but don't click it automatically
                try:
                    checkout_selectors = [
                        '//button[contains(text(), "PLACE ORDER")]',
                        '//span[contains(text(), "CONTINUE")]',
                        '//button[contains(text(), "Proceed")]'
                    ]
                    
                    for selector in checkout_selectors:
                        try:
                            checkout_btn = self.driver.find_element(By.XPATH, selector)
                            print(f"✅ Found checkout button: '{checkout_btn.text}'")
                            print("🔒 For security, please complete the checkout manually in the browser.")
                            print("⏸️  I'll keep the browser open for you to complete the purchase.")
                            return True
                        except Exception:
                            continue
                    
                    print("⚠️  Checkout button not found. Please proceed manually in the browser.")
                    return True
                    
                except Exception as e:
                    print(f"⚠️  Could not locate checkout button: {e}")
                    print("Please proceed manually in the browser.")
                    return True
            else:
                print("❌ Checkout cancelled. Items remain in cart.")
                return False
                
        except Exception as e:
            print(f"❌ Error during checkout: {e}")
            return False
    
    def keep_session_alive(self):
        """Keep browser open for user interaction."""
        print("\n🔄 Session active. Browser will remain open.")
        print("You can:")
        print("1. Complete your purchase manually")
        print("2. Continue browsing")
        print("3. Close when done")
        
        input("\n⏸️  Press Enter when you're done...")
    
    def end_session(self):
        """Close browser and end session."""
        if self.driver:
            print("\n👋 Ending AIVA session...")
            self.driver.quit()
            print("✅ Browser closed. Session ended.")

if __name__ == "__main__":
    aiva = InteractiveAIVA()
    
    try:
        # Start session
        if not aiva.start_session("flipkart"):
            exit(1)
        
        # Handle login
        aiva.handle_login()
        
        # Get user input
        product = input("\n🛍️  What product are you looking for? ")
        price_input = input("💰 Maximum price (optional, press Enter to skip): ")
        price_limit = int(price_input) if price_input.strip().isdigit() else None
        
        # Start intelligent shopping loop
        if aiva.intelligent_shopping_loop(product, price_limit, max_attempts=3):
            # If successful, proceed to checkout
            aiva.proceed_to_checkout()
        else:
            print("😔 Shopping unsuccessful. You can continue browsing manually.")
        
        # Keep session alive
        aiva.keep_session_alive()
        
    except KeyboardInterrupt:
        print("\n⚠️  Session interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        aiva.end_session()