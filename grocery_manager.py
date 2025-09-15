"""
Grocery List Management System
Manages default grocery lists, custom lists, quantities, and ordering preferences
"""

import json
import os
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class GroceryItem:
    """Represents a grocery item with details."""
    name: str
    category: str
    default_quantity: int = 1
    unit: str = "piece"  # piece, kg, liter, pack, etc.
    estimated_price: float = 0.0
    brand_preference: str = ""
    notes: str = ""

@dataclass
class GroceryList:
    """Represents a grocery list."""
    name: str
    items: List[Dict]  # List of {item_name, quantity, notes}
    list_type: str = "custom"  # default, monthly, weekly, custom
    created_date: str = ""
    last_used: str = ""

class GroceryListManager:
    """Manages grocery lists and items."""
    
    def __init__(self, data_file: str = "grocery_data.json"):
        self.data_file = data_file
        self.items_db = {}  # Database of all known items
        self.lists = {}     # All grocery lists
        self.user_preferences = {}
        self.load_data()
        self._initialize_default_items()
        self._initialize_default_lists()
    
    def _initialize_default_items(self):
        """Initialize database with common Indian grocery items."""
        default_items = [
            # Staples
            GroceryItem("Rice", "Staples", 5, "kg", 200, "", "Basmati or regular"),
            GroceryItem("Wheat Flour", "Staples", 5, "kg", 150, "", "Atta"),
            GroceryItem("Dal (Toor)", "Staples", 1, "kg", 120, "", "Arhar dal"),
            GroceryItem("Dal (Moong)", "Staples", 500, "gm", 80, "", ""),
            GroceryItem("Oil", "Staples", 1, "liter", 180, "", "Cooking oil"),
            GroceryItem("Sugar", "Staples", 1, "kg", 50, "", ""),
            GroceryItem("Salt", "Staples", 1, "kg", 25, "", ""),
            
            # Dairy
            GroceryItem("Milk", "Dairy", 1, "liter", 65, "", "Full cream"),
            GroceryItem("Curd", "Dairy", 400, "gm", 30, "", ""),
            GroceryItem("Paneer", "Dairy", 200, "gm", 80, "", ""),
            GroceryItem("Butter", "Dairy", 100, "gm", 50, "", ""),
            GroceryItem("Cheese", "Dairy", 200, "gm", 120, "", ""),
            
            # Vegetables
            GroceryItem("Onions", "Vegetables", 2, "kg", 40, "", ""),
            GroceryItem("Potatoes", "Vegetables", 2, "kg", 35, "", ""),
            GroceryItem("Tomatoes", "Vegetables", 1, "kg", 50, "", ""),
            GroceryItem("Ginger", "Vegetables", 100, "gm", 40, "", ""),
            GroceryItem("Garlic", "Vegetables", 200, "gm", 60, "", ""),
            GroceryItem("Green Chilies", "Vegetables", 100, "gm", 20, "", ""),
            GroceryItem("Coriander", "Vegetables", 1, "bunch", 15, "", "Fresh"),
            GroceryItem("Mint", "Vegetables", 1, "bunch", 15, "", "Fresh"),
            
            # Fruits
            GroceryItem("Bananas", "Fruits", 1, "dozen", 60, "", ""),
            GroceryItem("Apples", "Fruits", 1, "kg", 150, "", ""),
            GroceryItem("Oranges", "Fruits", 1, "kg", 80, "", ""),
            
            # Spices
            GroceryItem("Turmeric Powder", "Spices", 100, "gm", 30, "", ""),
            GroceryItem("Red Chili Powder", "Spices", 100, "gm", 40, "", ""),
            GroceryItem("Coriander Powder", "Spices", 100, "gm", 35, "", ""),
            GroceryItem("Cumin Powder", "Spices", 50, "gm", 25, "", ""),
            GroceryItem("Garam Masala", "Spices", 50, "gm", 40, "", ""),
            
            # Household
            GroceryItem("Toothpaste", "Household", 1, "piece", 50, "", ""),
            GroceryItem("Soap", "Household", 3, "piece", 90, "", "Bathing soap"),
            GroceryItem("Detergent", "Household", 1, "kg", 120, "", "Washing powder"),
            GroceryItem("Toilet Paper", "Household", 4, "rolls", 80, "", ""),
            
            # Beverages
            GroceryItem("Tea", "Beverages", 250, "gm", 120, "", ""),
            GroceryItem("Coffee", "Beverages", 200, "gm", 200, "", ""),
            
            # Snacks
            GroceryItem("Biscuits", "Snacks", 2, "pack", 60, "", ""),
            GroceryItem("Namkeen", "Snacks", 200, "gm", 40, "", ""),
        ]
        
        for item in default_items:
            if item.name not in self.items_db:
                self.items_db[item.name] = asdict(item)
    
    def _initialize_default_lists(self):
        """Initialize default grocery lists."""
        
        # Essential items list
        essentials = [
            {"item_name": "Rice", "quantity": 5, "notes": ""},
            {"item_name": "Dal (Toor)", "quantity": 1, "notes": ""},
            {"item_name": "Oil", "quantity": 1, "notes": ""},
            {"item_name": "Milk", "quantity": 2, "notes": ""},
            {"item_name": "Onions", "quantity": 2, "notes": ""},
            {"item_name": "Potatoes", "quantity": 2, "notes": ""},
            {"item_name": "Tomatoes", "quantity": 1, "notes": ""},
            {"item_name": "Salt", "quantity": 1, "notes": ""},
            {"item_name": "Sugar", "quantity": 1, "notes": ""},
        ]
        
        # Monthly grocery list
        monthly_items = [
            {"item_name": "Rice", "quantity": 10, "notes": "Monthly stock"},
            {"item_name": "Wheat Flour", "quantity": 5, "notes": ""},
            {"item_name": "Dal (Toor)", "quantity": 2, "notes": ""},
            {"item_name": "Dal (Moong)", "quantity": 1, "notes": ""},
            {"item_name": "Oil", "quantity": 2, "notes": ""},
            {"item_name": "Sugar", "quantity": 2, "notes": ""},
            {"item_name": "Salt", "quantity": 1, "notes": ""},
            {"item_name": "Turmeric Powder", "quantity": 1, "notes": ""},
            {"item_name": "Red Chili Powder", "quantity": 1, "notes": ""},
            {"item_name": "Coriander Powder", "quantity": 1, "notes": ""},
            {"item_name": "Tea", "quantity": 1, "notes": ""},
            {"item_name": "Detergent", "quantity": 2, "notes": ""},
            {"item_name": "Soap", "quantity": 6, "notes": ""},
            {"item_name": "Toothpaste", "quantity": 2, "notes": ""},
        ]
        
        # Weekly grocery list
        weekly_items = [
            {"item_name": "Milk", "quantity": 7, "notes": "Daily 1 liter"},
            {"item_name": "Curd", "quantity": 3, "notes": ""},
            {"item_name": "Onions", "quantity": 2, "notes": ""},
            {"item_name": "Potatoes", "quantity": 2, "notes": ""},
            {"item_name": "Tomatoes", "quantity": 2, "notes": ""},
            {"item_name": "Ginger", "quantity": 1, "notes": ""},
            {"item_name": "Garlic", "quantity": 1, "notes": ""},
            {"item_name": "Green Chilies", "quantity": 1, "notes": ""},
            {"item_name": "Coriander", "quantity": 2, "notes": "Fresh"},
            {"item_name": "Bananas", "quantity": 2, "notes": "2 dozens"},
            {"item_name": "Apples", "quantity": 1, "notes": ""},
            {"item_name": "Biscuits", "quantity": 2, "notes": ""},
        ]
        
        # Create default lists if they don't exist
        if "essentials" not in self.lists:
            self.lists["essentials"] = asdict(GroceryList(
                "essentials", essentials, "default", 
                datetime.now().strftime("%Y-%m-%d"), ""
            ))
        
        if "monthly" not in self.lists:
            self.lists["monthly"] = asdict(GroceryList(
                "monthly", monthly_items, "default",
                datetime.now().strftime("%Y-%m-%d"), ""
            ))
        
        if "weekly" not in self.lists:
            self.lists["weekly"] = asdict(GroceryList(
                "weekly", weekly_items, "default",
                datetime.now().strftime("%Y-%m-%d"), ""
            ))
    
    def load_data(self):
        """Load grocery data from file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items_db = data.get('items_db', {})
                    self.lists = data.get('lists', {})
                    self.user_preferences = data.get('preferences', {})
                    print("✅ Grocery data loaded successfully")
            else:
                print("📝 Creating new grocery data file")
        except Exception as e:
            print(f"⚠️ Error loading grocery data: {e}")
    
    def save_data(self):
        """Save grocery data to file."""
        try:
            data = {
                'items_db': self.items_db,
                'lists': self.lists,
                'preferences': self.user_preferences,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("✅ Grocery data saved successfully")
        except Exception as e:
            print(f"❌ Error saving grocery data: {e}")
    
    def add_item_to_database(self, item: GroceryItem):
        """Add new item to the database."""
        self.items_db[item.name] = asdict(item)
        self.save_data()
        print(f"✅ Added {item.name} to database")
    
    def create_list(self, name: str, items: List[Dict] = None) -> bool:
        """Create a new grocery list."""
        try:
            if items is None:
                items = []
            
            new_list = GroceryList(
                name=name,
                items=items,
                list_type="custom",
                created_date=datetime.now().strftime("%Y-%m-%d"),
                last_used=""
            )
            
            self.lists[name] = asdict(new_list)
            self.save_data()
            print(f"✅ Created grocery list: {name}")
            return True
        except Exception as e:
            print(f"❌ Error creating list: {e}")
            return False
    
    def add_item_to_list(self, list_name: str, item_name: str, quantity: int = 1, notes: str = "") -> bool:
        """Add item to a grocery list."""
        try:
            if list_name not in self.lists:
                print(f"❌ List '{list_name}' not found")
                return False
            
            # Check if item exists in database
            if item_name not in self.items_db:
                print(f"⚠️ Item '{item_name}' not in database. Adding as custom item.")
                custom_item = GroceryItem(item_name, "Custom", quantity)
                self.add_item_to_database(custom_item)
            
            # Check if item already in list
            items = self.lists[list_name]['items']
            for item in items:
                if item['item_name'] == item_name:
                    item['quantity'] += quantity
                    print(f"✅ Updated {item_name} quantity to {item['quantity']} in {list_name}")
                    self.save_data()
                    return True
            
            # Add new item to list
            items.append({
                'item_name': item_name,
                'quantity': quantity,
                'notes': notes
            })
            
            self.save_data()
            print(f"✅ Added {quantity}x {item_name} to {list_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding item to list: {e}")
            return False
    
    def remove_item_from_list(self, list_name: str, item_name: str) -> bool:
        """Remove item from a grocery list."""
        try:
            if list_name not in self.lists:
                print(f"❌ List '{list_name}' not found")
                return False
            
            items = self.lists[list_name]['items']
            original_length = len(items)
            items[:] = [item for item in items if item['item_name'] != item_name]
            
            if len(items) < original_length:
                self.save_data()
                print(f"✅ Removed {item_name} from {list_name}")
                return True
            else:
                print(f"⚠️ {item_name} not found in {list_name}")
                return False
                
        except Exception as e:
            print(f"❌ Error removing item: {e}")
            return False
    
    def get_list(self, list_name: str) -> Optional[Dict]:
        """Get a grocery list."""
        return self.lists.get(list_name)
    
    def get_all_lists(self) -> Dict:
        """Get all grocery lists."""
        return self.lists
    
    def update_list_usage(self, list_name: str):
        """Update the last used date for a list."""
        if list_name in self.lists:
            self.lists[list_name]['last_used'] = datetime.now().strftime("%Y-%m-%d")
            self.save_data()
    
    def get_estimated_cost(self, list_name: str) -> float:
        """Calculate estimated cost for a grocery list."""
        try:
            if list_name not in self.lists:
                return 0.0
            
            total_cost = 0.0
            items = self.lists[list_name]['items']
            
            for item in items:
                item_name = item['item_name']
                quantity = item['quantity']
                
                if item_name in self.items_db:
                    unit_price = self.items_db[item_name]['estimated_price']
                    total_cost += unit_price * quantity
            
            return total_cost
            
        except Exception as e:
            print(f"❌ Error calculating cost: {e}")
            return 0.0
    
    def display_list(self, list_name: str):
        """Display a grocery list in a formatted way."""
        try:
            if list_name not in self.lists:
                print(f"❌ List '{list_name}' not found")
                return
            
            grocery_list = self.lists[list_name]
            items = grocery_list['items']
            
            print(f"\n🛒 GROCERY LIST: {list_name.upper()}")
            print("=" * 50)
            print(f"📅 Created: {grocery_list['created_date']}")
            print(f"🏷️ Type: {grocery_list['list_type']}")
            print(f"📊 Items: {len(items)}")
            
            if grocery_list['last_used']:
                print(f"🕒 Last Used: {grocery_list['last_used']}")
            
            estimated_cost = self.get_estimated_cost(list_name)
            print(f"💰 Estimated Cost: ₹{estimated_cost:.2f}")
            
            print("\n📋 ITEMS:")
            print("-" * 50)
            
            for i, item in enumerate(items, 1):
                item_name = item['item_name']
                quantity = item['quantity']
                notes = item['notes']
                
                # Get item details from database
                if item_name in self.items_db:
                    item_data = self.items_db[item_name]
                    unit = item_data['unit']
                    unit_price = item_data['estimated_price']
                    category = item_data['category']
                    
                    line_total = unit_price * quantity
                    
                    print(f"{i:2d}. {item_name}")
                    print(f"    📦 Quantity: {quantity} {unit}")
                    print(f"    🏷️ Category: {category}")
                    print(f"    💰 Price: ₹{unit_price} x {quantity} = ₹{line_total:.2f}")
                    if notes:
                        print(f"    📝 Notes: {notes}")
                else:
                    print(f"{i:2d}. {item_name} - {quantity} (Custom item)")
                    if notes:
                        print(f"    📝 Notes: {notes}")
                
                print()
            
        except Exception as e:
            print(f"❌ Error displaying list: {e}")

# Example usage and helper functions
def demo_grocery_system():
    """Demonstrate the grocery list management system."""
    print("🛒 GROCERY LIST MANAGEMENT SYSTEM DEMO")
    print("=" * 60)
    
    # Initialize manager
    manager = GroceryListManager()
    
    # Display default lists
    print("\n📋 DEFAULT LISTS:")
    for list_name in ["essentials", "weekly", "monthly"]:
        manager.display_list(list_name)
    
    # Create a custom list
    print("\n🎯 Creating custom weekend list...")
    manager.create_list("weekend_special")
    manager.add_item_to_list("weekend_special", "Chicken", 1, "For biryani")
    manager.add_item_to_list("weekend_special", "Basmati Rice", 2, "Special variety")
    manager.add_item_to_list("weekend_special", "Ice Cream", 2, "Family pack")
    
    manager.display_list("weekend_special")
    
    print("\n✅ Grocery system demo completed!")

if __name__ == "__main__":
    demo_grocery_system()