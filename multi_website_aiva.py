"""
multi_website_aiva.py: Enhanced AIVA with multi-website support
Supports shopping across multiple e-commerce platforms.
"""

import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from website_adapters import WebsiteAdapterFactory
from smart_recommendations import SmartProductRecommender
from credential_manager import CredentialManager

class MultiWebsiteAIVA:
    """AIVA with support for multiple e-commerce websites."""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.current_adapter = None
        self.recommender = SmartProductRecommender()
        self.credential_manager = CredentialManager()
        self.logged_in = False
    
    def initialize_browser(self):
        """Initialize browser with Edge WebDriver."""
        try:
            print("🌐 Initializing browser...")
            
            # Edge WebDriver options
            options = webdriver.EdgeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Initialize Edge WebDriver
            self.driver = webdriver.Edge(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 10)
            
            print("✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize browser: {e}")
            return False
    
    def select_website(self) -> str:
        """Let user select which website to shop on."""
        supported_websites = WebsiteAdapterFactory.get_supported_websites()
        
        print("\n🛍️ WEBSITE SELECTION")
        print("=" * 40)
        print("Available shopping websites:")
        
        for i, website in enumerate(supported_websites, 1):
            print(f"{i}. {website.title()}")
        
        while True:
            try:
                choice = input(f"\nSelect website (1-{len(supported_websites)}): ").strip()
                choice_idx = int(choice) - 1
                
                if 0 <= choice_idx < len(supported_websites):
                    selected_website = supported_websites[choice_idx]
                    print(f"✅ Selected: {selected_website.title()}")
                    return selected_website
                else:
                    print(f"❌ Invalid choice. Please enter 1-{len(supported_websites)}")
                    
            except ValueError:
                print("❌ Please enter a valid number")
    
    def initialize_website(self, website: str) -> bool:
        """Initialize the selected website adapter."""
        try:
            print(f"🔄 Initializing {website.title()} adapter...")
            
            # Create adapter
            self.current_adapter = WebsiteAdapterFactory.create_adapter(website, self.driver, self.wait)
            
            # Navigate to website
            self.driver.get(self.current_adapter.get_base_url())
            time.sleep(3)
            
            print(f"✅ Successfully loaded {website.title()}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize {website}: {e}")
            return False
    
    def handle_login_rate_limiting(self) -> bool:
        """Handle login rate limiting with helpful guidance."""
        print("\n🚫 LOGIN RATE LIMITING DETECTED")
        print("=" * 50)
        print("⚠️ The website has temporarily blocked login attempts.")
        print("💡 This usually happens after multiple login attempts.")
        print()
        print("🔧 SOLUTIONS:")
        print("1. ⏰ Wait 15-30 minutes before trying again")
        print("2. 🌐 Try using a different browser manually")
        print("3. 📱 Use the mobile app instead")
        print("4. 🔄 Clear browser cache and cookies")
        print("5. 🌍 Try from a different network/location")
        print()
        print("🛍️ ALTERNATIVE OPTIONS:")
        print("• Continue as guest (limited features)")
        print("• Try a different website")
        print("• Come back later when limit is reset")
        
        while True:
            choice = input("\nChoose: (1) Wait and retry (2) Guest mode (3) Different website (4) Exit: ").strip()
            
            if choice == "1":
                print("⏰ Waiting 30 seconds before retry...")
                time.sleep(30)
                return True  # Try again
            elif choice == "2":
                print("🕶️ Continuing as guest...")
                return True  # Continue without login
            elif choice == "3":
                return False  # Switch website
            elif choice == "4":
                print("👋 Goodbye!")
                return None  # Exit
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
    
    def smart_login_process(self) -> bool:
        """Enhanced login process with rate limiting detection."""
        try:
            # Check current login status
            status = self.current_adapter.check_login_status()
            if status == "logged_in":
                print("✅ Already logged in!")
                self.logged_in = True
                return True
            
            print("\n🔐 LOGIN PROCESS")
            print("-" * 30)
            print("💡 Options:")
            print("1. 🔐 Login now")
            print("2. 🕶️ Continue as guest")
            print("3. ❌ Skip for now")
            
            choice = input("\nSelect option (1/2/3): ").strip()
            
            if choice == "1":
                # Navigate to login page
                self.driver.get(self.current_adapter.get_login_url())
                time.sleep(3)
                
                # Check for rate limiting
                page_source = self.driver.page_source.lower()
                rate_limit_indicators = [
                    "too many attempts",
                    "temporarily blocked",
                    "rate limit",
                    "try again later",
                    "account locked"
                ]
                
                if any(indicator in page_source for indicator in rate_limit_indicators):
                    return self.handle_login_rate_limiting()
                
                # Show platform-specific instructions
                print(self.current_adapter.get_login_instructions())
                
                # Get user credentials choice
                cred_choice = self.credential_manager.get_credential_choice()
                
                if cred_choice == "1" and self.credential_manager.has_saved_credentials():
                    return self.assisted_login()
                elif cred_choice in ["1", "2"]:
                    return self.manual_login()
                else:
                    print("🕶️ Continuing as guest")
                    return True
                    
            elif choice == "2":
                print("🕶️ Continuing as guest")
                return True
            else:
                print("⏰ Skipping login for now")
                return True
                
        except Exception as e:
            print(f"❌ Login process error: {e}")
            return True  # Continue anyway
    
    def assisted_login(self) -> bool:
        """Assisted login using saved credentials."""
        print("🤖 Attempting assisted login...")
        # Implementation would depend on the specific adapter
        return True  # Placeholder
    
    def manual_login(self) -> bool:
        """Manual login process."""
        print("👤 Manual login process...")
        input("⏸️ Please complete login in the browser, then press Enter...")
        
        # Check if login was successful
        status = self.current_adapter.check_login_status()
        if status == "logged_in":
            print("✅ Login successful!")
            self.logged_in = True
            
            # Offer to save credentials
            save = input("💾 Save email/mobile for faster login next time? (y/n): ").lower().strip()
            if save == 'y':
                email = input("📧 Enter email/mobile to save: ").strip()
                if email:
                    self.credential_manager.save_otp_account(email)
            
            return True
        else:
            print("⚠️ Login status unclear, continuing...")
            return True
    
    def shopping_session(self):
        """Main shopping session with multi-website support."""
        try:
            while True:
                print("\n" + "="*50)
                print("🛍️ What would you like to shop for? (or 'quit' to exit)")
                print(f"🌐 Current website: {self.current_adapter.name}")
                print("💡 Type 'switch' to change website")
                
                query = input("Search: ").strip().lower()
                
                if query == 'quit':
                    break
                elif query == 'switch':
                    new_website = self.select_website()
                    if self.initialize_website(new_website):
                        self.logged_in = False  # Reset login status
                        self.smart_login_process()
                    continue
                elif not query:
                    continue
                
                # Extract price limit from query
                max_price = self.extract_price_limit(query)
                
                print(f"\n🔍 Searching on {self.current_adapter.name} for: {query}")
                if max_price:
                    print(f"💰 Price limit: ₹{max_price}")
                
                # Search for products
                products = self.current_adapter.search_products(query, max_price)
                
                if not products:
                    print(f"❌ No products found on {self.current_adapter.name}")
                    print("💡 Try a different search term or switch websites")
                    continue
                
                # Get AI recommendations
                recommended = self.recommender.get_smart_recommendations(products, query)
                
                if recommended:
                    print(f"\n🤖 AI Recommendations from {self.current_adapter.name}:")
                    for i, product in enumerate(recommended[:3], 1):
                        print(f"{i}. {product['title']}")
                        print(f"   💰 ₹{product['price']} | 🎯 Score: {product.get('ai_score', 0):.2f}")
                        print(f"   🔍 {product.get('explanation', 'Good match')}")
                        print()
                    
                    # Option to add to cart
                    if self.logged_in or self.current_adapter.name.lower() == 'flipkart':
                        add_choice = input("🛒 Add top recommendation to cart? (y/n): ").strip().lower()
                        if add_choice == 'y':
                            success = self.current_adapter.add_to_cart(recommended[0]['element'])
                            if success:
                                print("✅ Item added to cart!")
                            else:
                                print("❌ Failed to add to cart")
                    else:
                        print("💡 Login required to add items to cart")
                else:
                    print("❌ No suitable recommendations found")
                
                # Continue shopping option
                continue_shopping = input("\n❓ Continue shopping? (y/n): ").strip().lower()
                if continue_shopping != 'y':
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Shopping session interrupted")
        except Exception as e:
            print(f"❌ Shopping session error: {e}")
    
    def extract_price_limit(self, query: str) -> Optional[float]:
        """Extract price limit from search query."""
        try:
            words = query.split()
            for i, word in enumerate(words):
                if word in ['under', 'below', 'less', 'max']:
                    if i + 1 < len(words):
                        price_text = words[i + 1].replace(',', '')
                        if price_text.isdigit():
                            return float(price_text)
            return None
        except:
            return None
    
    def run(self):
        """Main AIVA execution."""
        print("🚀 AIVA - Multi-Website Shopping Assistant")
        print("🤖 AI-Powered Shopping Across Multiple Platforms")
        print("=" * 60)
        
        try:
            # Initialize browser
            if not self.initialize_browser():
                return
            
            # Select website
            website = self.select_website()
            
            # Initialize website
            if not self.initialize_website(website):
                return
            
            # Handle login
            self.smart_login_process()
            
            # Start shopping session
            self.shopping_session()
            
        except Exception as e:
            print(f"❌ AIVA error: {e}")
        finally:
            if self.driver:
                print("🔄 Closing browser...")
                self.driver.quit()
                print("👋 Thank you for using AIVA!")

if __name__ == "__main__":
    aiva = MultiWebsiteAIVA()
    aiva.run()