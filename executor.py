"""
executor.py: Minimal Execution Layer for AIVA
- Handles automation actions like search, filter, add to cart
- Uses perception.py to get product candidates, then automates the selection/purchase
- For demo: Flipkart automation
"""
import logging
from typing import Dict, List, Optional
from perception import get_flipkart_candidates, create_edge_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def execute_flipkart_search(product: str, price_limit: Optional[int] = None) -> List[Dict]:
    """Execute search on Flipkart and return candidates."""
    logging.info(f"Executing Flipkart search for: {product}, price limit: {price_limit}")
    candidates = get_flipkart_candidates(product, price_limit, max_items=5)
    return candidates

def execute_add_to_cart(product: str, price_limit: Optional[int] = None) -> str:
    """Execute add to cart action on Flipkart."""
    try:
        driver = create_edge_driver()
    except Exception as e:
        return f"❌ Could not start browser: {e}"
    
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
        search_box.send_keys("\n")
        
        # Wait for results and click first item
        wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "_1AtVbE")]')))
        time.sleep(2)
        
        # Find first product within price limit
        cards = driver.find_elements(By.XPATH, '//div[contains(@class, "_1AtVbE")]')
        for card in cards:
            try:
                price_el = card.find_element(By.XPATH, './/div[contains(@class, "_30jeq3")]')
                price_str = price_el.text.replace('₹', '').replace(',', '').strip()
                price = int(price_str)
                
                if price_limit and price > price_limit:
                    continue
                
                # Click on the product
                title_el = card.find_element(By.XPATH, './/div[contains(@class, "_4rR01T") or contains(@class, "s1Q9rs")]')
                title_el.click()
                break
            except Exception:
                continue
        
        # Try to add to cart
        try:
            add_to_cart_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "_2KpZ6l") and contains(text(), "ADD TO CART")]')))
            add_to_cart_btn.click()
            time.sleep(2)
            return "✅ Item successfully added to cart!"
        except Exception:
            return "❌ Could not find 'Add to Cart' button."
    
    except Exception as e:
        return f"❌ Error during execution: {e}"
    finally:
        driver.quit()

def execute_plan(plan: Dict) -> str:
    """Execute a plan from the agentic core."""
    action = plan.get("action")
    platform = plan.get("platform")
    product = plan.get("product")
    price = plan.get("price")
    
    logging.info(f"Executing plan: {plan}")
    
    if action == "search" and platform == "flipkart":
        candidates = execute_flipkart_search(product, price)
        if candidates:
            result = f"Found {len(candidates)} items:\n"
            for item in candidates[:3]:  # Show top 3
                result += f"- {item['title']} | ₹{item['price']}\n"
            return result
        else:
            return "❌ No items found matching your criteria."
    
    elif action == "add_to_cart" and platform == "flipkart":
        return execute_add_to_cart(product, price)
    
    else:
        return f"❌ Unknown action: {action} on {platform}"

if __name__ == "__main__":
    print("AIVA Executor Demo")
    action = input("Action (search/add_to_cart): ")
    product = input("Product: ")
    price = input("Max price (optional): ")
    price_limit = int(price) if price.strip().isdigit() else None
    
    plan = {
        "action": action,
        "platform": "flipkart",
        "product": product,
        "price": price_limit
    }
    
    result = execute_plan(plan)
    print("Result:", result)