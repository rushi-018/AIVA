from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import time
import os


def create_edge_driver(use_system_profile: bool = True):
    def _system_profile_options():
        opts = EdgeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-notifications")
        opts.add_argument("--disable-infobars")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        opts.add_argument("--remote-allow-origins=*")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--remote-debugging-port=9222")
        edge_user_data = os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\User Data")
        opts.add_argument(f"user-data-dir={edge_user_data}")
        opts.add_argument("profile-directory=Default")
        return opts

    def _local_profile_options():
        opts = EdgeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-notifications")
        opts.add_argument("--disable-infobars")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        opts.add_argument("--remote-allow-origins=*")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--remote-debugging-port=9222")
        project_dir = os.path.dirname(os.path.abspath(__file__))
        edge_profile_path = os.path.join(project_dir, "edge_profile")
        os.makedirs(edge_profile_path, exist_ok=True)
        opts.add_argument(f"user-data-dir={edge_profile_path}")
        return opts

    if use_system_profile:
        try:
            return webdriver.Edge(options=_system_profile_options())
        except WebDriverException:
            pass

    return webdriver.Edge(options=_local_profile_options())


def _find_and_click_affordable_item(driver, wait, price_limit):
    try:
        # Try to locate menu items with price and Add buttons
        item_cards = driver.find_elements(By.XPATH, '//div[contains(@class, "sc-") and .//button[contains(., "Add")]]')
        for item in item_cards:
            try:
                price_el = item.find_element(By.XPATH, './/*[contains(text(), "₹")]')
                text = price_el.text
                digits = ''.join(ch for ch in text if ch.isdigit())
                if not digits:
                    continue
                price = int(digits)
                if price_limit is None or price <= int(price_limit):
                    add_btn = item.find_element(By.XPATH, './/button[contains(., "Add")]')
                    add_btn.click()
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _extract_rating_from_card(card):
    try:
        rating_el = card.find_element(By.XPATH, './/*[contains(@class, "rating") or contains(., "★")]')
        digits = ''.join(ch for ch in rating_el.text if (ch.isdigit() or ch == '.'))
        return float(digits) if digits else None
    except Exception:
        return None


def _scrape_menu_items(driver, price_limit=None, max_items=10):
    items = []
    try:
        cards = driver.find_elements(By.XPATH, '//div[contains(@class, "sc-") and .//button[contains(., "Add")]]')
        for card in cards:
            try:
                name_el = None
                for xp in ['.//h2', './/h3', './/h4', './/span', './/p']:
                    els = card.find_elements(By.XPATH, xp)
                    if els:
                        name_el = els[0]
                        break
                if not name_el:
                    continue
                name = name_el.text.strip()

                price = None
                try:
                    price_el = card.find_element(By.XPATH, './/*[contains(text(), "₹")]')
                    digits = ''.join(ch for ch in price_el.text if ch.isdigit())
                    price = int(digits) if digits else None
                except Exception:
                    pass

                if price_limit is not None and price is not None and price > int(price_limit):
                    continue

                items.append({
                    'item_name': name,
                    'price': price
                })
                if len(items) >= max_items:
                    break
            except Exception:
                continue
    except Exception:
        pass
    return items


def find_candidates(food_type, price_limit=None, driver=None, use_system_profile=True, max_restaurants=3, max_items_per_restaurant=6):
    local_driver = driver or create_edge_driver(use_system_profile=use_system_profile)
    local_driver.get("https://www.zomato.com/pune/delivery")
    wait = WebDriverWait(local_driver, 20)

    # Search
    search_box = wait.until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search for dishes, restaurants, or cuisines" or @placeholder="Search for restaurant, cuisine or a dish"]'))
    )
    search_box.clear()
    search_box.send_keys(food_type)
    search_box.send_keys(Keys.ENTER)

    # Collect top restaurant links
    wait.until(EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/pune/")]')))
    restaurant_links = local_driver.find_elements(By.XPATH, '//a[contains(@href, "/pune/") and not(contains(@href, "cart"))]')
    results = []
    visited = 0
    for link in restaurant_links:
        try:
            href = link.get_attribute('href')
            if not href:
                continue
            # Open restaurant
            local_driver.get(href)
            wait.until(EC.presence_of_element_located((By.XPATH, '//button[contains(., "Add")]')))

            # Restaurant name and rating
            restaurant_name = None
            try:
                restaurant_name_el = local_driver.find_element(By.XPATH, '//h1 | //h2')
                restaurant_name = restaurant_name_el.text.strip()
            except Exception:
                pass
            rating = None
            try:
                rating_el = local_driver.find_element(By.XPATH, '//*[contains(@class, "rating") or contains(., "★")]')
                digits = ''.join(ch for ch in rating_el.text if (ch.isdigit() or ch == '.'))
                rating = float(digits) if digits else None
            except Exception:
                pass

            # Scrape items
            items = _scrape_menu_items(local_driver, price_limit=price_limit, max_items=max_items_per_restaurant)
            for it in items:
                it.update({
                    'restaurant_name': restaurant_name,
                    'rating': rating,
                    'restaurant_url': href
                })
                # Prefer those matching keyword
                it['score'] = (1 if (food_type.lower() in (it['item_name'] or '').lower()) else 0)
                results.append(it)

            visited += 1
            if visited >= max_restaurants:
                break
        except Exception:
            continue

    # Sort by keyword match, then rating desc, then price asc
    results.sort(key=lambda x: (-x.get('score', 0), -(x.get('rating') or 0), x.get('price') or 10**9))
    return results


def add_selected_item(item_name, candidates, driver=None, go_to_payment=True, use_system_profile=True):
    if not candidates:
        return "❌ No candidates to select from."
    # Choose best rated candidate with given item name (case-insensitive contains)
    filtered = [c for c in candidates if item_name.lower() in (c.get('item_name') or '').lower()]
    if not filtered:
        # fallback: use first candidate
        filtered = candidates
    filtered.sort(key=lambda x: -(x.get('rating') or 0))
    chosen = filtered[0]

    local_driver = driver or create_edge_driver(use_system_profile=use_system_profile)
    wait = WebDriverWait(local_driver, 20)
    local_driver.get(chosen['restaurant_url'])

    # Try to find the specific item by name and click Add
    try:
        xpath = f'//div[contains(@class, "sc-")][.//button[contains(., "Add")]]//*[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{item_name.lower()}")]/ancestor::div[contains(@class, "sc-")][.//button[contains(., "Add")]][1]//button[contains(., "Add")]'
        add_btns = local_driver.find_elements(By.XPATH, xpath)
        if add_btns:
            local_driver.execute_script("arguments[0].click();", add_btns[0])
        else:
            # Fallback: first affordable
            _find_and_click_affordable_item(local_driver, wait, chosen.get('price'))
    except Exception:
        _find_and_click_affordable_item(local_driver, wait, chosen.get('price'))

    time.sleep(1)
    if go_to_payment:
        local_driver.get("https://www.zomato.com/cart")
        try:
            for xpath in [
                '//button[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "checkout")]',
                '//a[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "checkout")]',
                '//button[contains(., "Proceed") or contains(., "Continue")]',
                '//a[contains(., "Proceed") or contains(., "Continue")]']:
                btns = local_driver.find_elements(By.XPATH, xpath)
                if btns:
                    local_driver.execute_script("arguments[0].click();", btns[0])
                    break
        except Exception:
            pass
        return "✅ Proceeding to checkout/payment with selected item."
    else:
        local_driver.get("https://www.zomato.com/cart")
        return "✅ Selected item added to cart."

def automate_zomato(food_type, price_limit=None, driver=None, go_to_payment=False, use_system_profile=True):
    try:
        local_driver = driver or create_edge_driver(use_system_profile=use_system_profile)

        # Open Delivery section directly to avoid Dining Out
        local_driver.get("https://www.zomato.com/pune/delivery")
        wait = WebDriverWait(local_driver, 20)

        # Search for food_type (delivery search bar variants)
        search_box = wait.until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search for dishes, restaurants, or cuisines" or @placeholder="Search for restaurant, cuisine or a dish"]'))
        )
        search_box.clear()
        search_box.send_keys(food_type)
        search_box.send_keys(Keys.ENTER)

        # Wait for restaurant results and click the first one
        wait.until(EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/pune/")]')))
        links = local_driver.find_elements(By.XPATH, '//a[contains(@href, "/pune/") and not(contains(@href, "cart"))]')
        if not links:
            return "❌ No restaurants found."
        links[0].click()

        # Wait for menu to load
        wait.until(EC.presence_of_element_located((By.XPATH, '//button[contains(., "Add")]')))

        # If price_limit given, try to pick an affordable item
        clicked = _find_and_click_affordable_item(local_driver, wait, price_limit)
        if not clicked:
            # Fallback to first Add button
            add_buttons = local_driver.find_elements(By.XPATH, '//button[contains(., "Add")]')
            if not add_buttons:
                return "❌ No items available."
            add_buttons[0].click()

        time.sleep(2)
        if go_to_payment:
            # Try to navigate to cart and proceed
            local_driver.get("https://www.zomato.com/cart")
            try:
                for xpath in [
                    '//button[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "checkout")]',
                    '//a[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "checkout")]',
                    '//button[contains(., "Proceed") or contains(., "Continue")]',
                    '//a[contains(., "Proceed") or contains(., "Continue")]']:
                    btns = local_driver.find_elements(By.XPATH, xpath)
                    if btns:
                        local_driver.execute_script("arguments[0].click();", btns[0])
                        break
                time.sleep(1)
            except Exception:
                pass
            return "✅ Item added to cart and proceeding to checkout/payment."
        else:
            local_driver.get("https://www.zomato.com/cart")
            return "✅ Item added to cart!"
    except Exception as e:
        return f"❌ Error: {e}"
