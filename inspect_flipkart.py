#!/usr/bin/env python3
"""
Flipkart Selector Inspector - Find current add to cart selectors
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

def inspect_flipkart_selectors():
    """Inspect current Flipkart selectors"""
    print("🔍 Inspecting Flipkart Add-to-Cart Selectors")
    print("=" * 50)
    
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Search for a product
        print("🔍 Searching for test product...")
        driver.get("https://www.flipkart.com")
        time.sleep(3)
        
        # Handle popup
        try:
            popup = driver.find_element(By.CSS_SELECTOR, "button[class*='_2KpZ6l _2doB4z']")
            popup.click()
        except:
            pass
        
        # Search
        search_box = driver.find_element(By.CSS_SELECTOR, "input[name='q']")
        search_box.send_keys("shoes")
        search_box.submit()
        time.sleep(5)
        
        # Click first product
        first_product = driver.find_element(By.CSS_SELECTOR, "[data-id] a")
        first_product.click()
        time.sleep(5)
        
        print("📍 Looking for add to cart buttons...")
        
        # Try to find all potential add to cart buttons
        potential_selectors = [
            "button[class*='_2KpZ6l']",  # Flipkart button base class
            "button[class*='_2AkmmA']",  # Another common class
            "button:contains('Add')",    # Contains "Add"
            "li[class*='_1rH2Jg']",     # List item buttons
            "div[class*='_1gUKSk'] button",  # Buttons in action containers
            "button[class*='_3v1-ww']",  # Primary buttons
            "[class*='ADD'] button",     # Classes containing ADD
            "button[class*='cart']",     # Classes containing cart
            "button:contains('Cart')",   # Contains "Cart"
            "button[role='button']",     # Button role
        ]
        
        found_buttons = []
        for selector in potential_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    text = button.text.strip().upper()
                    if 'ADD' in text or 'CART' in text or 'BUY' in text:
                        classes = button.get_attribute('class')
                        found_buttons.append({
                            'text': text,
                            'classes': classes,
                            'selector': selector,
                            'tag': button.tag_name
                        })
                        print(f"   ✅ Found: {text} | Classes: {classes}")
            except Exception as e:
                continue
        
        if found_buttons:
            print(f"\n🎯 Found {len(found_buttons)} potential add-to-cart buttons!")
            
            # Try clicking the most likely one
            for button_info in found_buttons:
                if 'ADD TO CART' in button_info['text']:
                    print(f"🎯 Best match: {button_info['text']} | {button_info['classes']}")
                    break
        else:
            print("❌ No add-to-cart buttons found")
            
            # Fallback: show all buttons
            print("\n📍 All buttons on page:")
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            for i, btn in enumerate(all_buttons[:10]):
                text = btn.text.strip()
                classes = btn.get_attribute('class')
                if text:
                    print(f"   {i+1}. {text} | {classes}")
        
        print(f"\n📄 Current URL: {driver.current_url}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    inspect_flipkart_selectors()
    input("Press Enter to exit...")