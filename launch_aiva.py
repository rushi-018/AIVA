"""
AIVA Launcher - Smart dependency checker and installer
"""

import sys
import subprocess
import os
import importlib.util

def check_and_install_packages():
    """Check and install required packages."""
    
    required_packages = {
        'selenium': 'selenium',
        'webdriver_manager': 'webdriver-manager',
        'speech_recognition': 'SpeechRecognition',
        'pyttsx3': 'pyttsx3',
        'tkinter': None  # Built-in with Python
    }
    
    missing_packages = []
    
    print("🔍 Checking dependencies...")
    
    for package, pip_name in required_packages.items():
        if package == 'tkinter':
            try:
                import tkinter
                print(f"✅ {package} - OK")
            except ImportError:
                print(f"❌ {package} - Missing (install Python with tkinter support)")
                return False
        else:
            spec = importlib.util.find_spec(package)
            if spec is None:
                print(f"❌ {package} - Missing")
                if pip_name:
                    missing_packages.append(pip_name)
            else:
                print(f"✅ {package} - OK")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        
        for package in missing_packages:
            try:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package}: {e}")
                return False
    
    print("✅ All dependencies ready!")
    return True

def launch_aiva():
    """Launch the AIVA GUI application."""
    
    print("\n🚀 Starting AIVA...")
    
    try:
        # Import and run AIVA
        import aiva_gui
        aiva_gui.main()
        
    except ImportError as e:
        print(f"❌ Failed to import AIVA modules: {e}")
        print("Make sure all files are in the same directory:")
        print("  - aiva_gui.py")
        print("  - grocery_manager.py")
        print("  - website_adapters.py")
        print("  - grocery_adapters.py")
        return False
    
    except Exception as e:
        print(f"❌ AIVA startup failed: {e}")
        return False
    
    return True

def show_service_menu():
    """Show a simple console menu for service selection."""
    
    print("\n🤖 AIVA - AI Voice Assistant")
    print("=" * 40)
    print("1. 🖥️  Launch GUI Interface (Recommended)")
    print("2. 🛒 Quick Flipkart Search")
    print("3. 📦 Quick Amazon Search") 
    print("4. 🥬 Quick Grocery Search")
    print("5. 📋 View Grocery Lists")
    print("6. ❓ Help")
    print("7. 🚪 Exit")
    print("=" * 40)
    
    while True:
        choice = input("\nSelect an option (1-7): ").strip()
        
        if choice == '1':
            return launch_aiva()
        elif choice == '2':
            return quick_search('flipkart')
        elif choice == '3':
            return quick_search('amazon')
        elif choice == '4':
            return quick_search('blinkit')
        elif choice == '5':
            return show_grocery_lists()
        elif choice == '6':
            show_help()
            continue
        elif choice == '7':
            print("👋 Goodbye!")
            return True
        else:
            print("❌ Invalid choice. Please enter 1-7.")

def quick_search(service):
    """Perform a quick search without GUI."""
    
    query = input(f"\n🔍 Enter search query for {service.title()}: ").strip()
    if not query:
        print("❌ No query entered.")
        return True
    
    print(f"🔍 Searching for '{query}' on {service.title()}...")
    print("💡 For full functionality, use the GUI interface (option 1)")
    
    # This would implement actual search logic
    print(f"✅ Search simulation completed for '{query}'")
    
    return True

def show_grocery_lists():
    """Show available grocery lists."""
    
    try:
        from grocery_manager import GroceryListManager
        
        manager = GroceryListManager()
        lists = manager.get_all_lists()
        
        print("\n📋 Available Grocery Lists:")
        print("-" * 30)
        
        for list_name, list_data in lists.items():
            items = list_data['items']
            cost = manager.get_estimated_cost(list_name)
            print(f"• {list_name.title()}: {len(items)} items, ₹{cost:.2f}")
        
        print("\n💡 Use the GUI interface for full list management.")
        
    except ImportError:
        print("❌ Grocery manager not available.")
    except Exception as e:
        print(f"❌ Error loading grocery lists: {e}")
    
    return True

def show_help():
    """Show help information."""
    
    help_text = """
🤖 AIVA - AI Voice Assistant Help

🎯 GETTING STARTED:
1. Option 1: Launch GUI Interface for full functionality
2. Use Quick Search options for simple searches
3. View Grocery Lists to see available shopping lists

🛒 E-COMMERCE FEATURES:
• Flipkart product search and comparison
• Amazon product search and cart management
• Price comparison and product details

🥬 GROCERY FEATURES:
• Predefined grocery lists (essentials, weekly, monthly)
• Custom grocery list creation and management
• Blinkit integration for delivery
• Cost estimation and shopping optimization

🎤 VOICE FEATURES:
• Voice command recognition
• Text-to-speech feedback
• Natural language processing for commands

💡 REQUIREMENTS:
• Python 3.7+
• Chrome browser (for web automation)
• Internet connection
• Microphone (for voice features)

🔧 TROUBLESHOOTING:
• If dependencies are missing, this launcher will install them
• For Chrome issues, update Chrome browser
• For voice issues, check microphone permissions

📞 SUPPORT:
For issues, check the output in GUI mode for detailed error messages.
    """
    
    print(help_text)

def main():
    """Main launcher function."""
    
    print("🤖 AIVA Launcher v1.0")
    print("Checking system requirements...")
    
    # Check dependencies
    if not check_and_install_packages():
        print("\n❌ Dependency installation failed.")
        print("Please install required packages manually:")
        print("pip install selenium webdriver-manager SpeechRecognition pyttsx3")
        input("\nPress Enter to continue anyway...")
    
    # Show menu
    try:
        show_service_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Launcher error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()