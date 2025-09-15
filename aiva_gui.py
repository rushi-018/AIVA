"""
AIVA - AI Voice Assistant with GUI
Unified interface for e-commerce, grocery ordering, and voice commands
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import sys
import os
import time
import re
from datetime import datetime
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
try:
    from grocery_manager import GroceryListManager
    # Try enhanced adapters first, fallback to original
    try:
        from enhanced_adapters import FlipkartAdapter, AmazonAdapter
        print("✅ Using enhanced adapters")
    except ImportError:
        from website_adapters import FlipkartAdapter, AmazonAdapter
        print("⚠️ Using original adapters")
    
    from grocery_adapters import BlinkitAdapter
    from requirement_fulfillment import RequirementAnalyzer, ProductRecommendationEngine, SatisfactionChecker
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
    SELENIUM_AVAILABLE = True
    GROCERY_AVAILABLE = True
    AI_FEATURES_AVAILABLE = True
except ImportError as e:
    VOICE_AVAILABLE = False
    SELENIUM_AVAILABLE = False
    GROCERY_AVAILABLE = False
    AI_FEATURES_AVAILABLE = False
    print(f"Some modules not available: {e}")
    
# Additional imports for GUI
try:
    import tkinter.simpledialog
except ImportError:
    pass

class AIVAGui:
    """Main GUI for AIVA Voice Assistant."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AIVA - AI Voice Assistant")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize components
        self.grocery_manager = GroceryListManager()
        self.current_service = None
        self.driver = None
        self.voice_enabled = VOICE_AVAILABLE
        
        # Initialize AI components
        if AI_FEATURES_AVAILABLE:
            self.requirement_analyzer = RequirementAnalyzer()
            self.recommendation_engine = ProductRecommendationEngine(self.requirement_analyzer)
            self.satisfaction_checker = SatisfactionChecker(self.requirement_analyzer)
        else:
            self.requirement_analyzer = None
            self.recommendation_engine = None
            self.satisfaction_checker = None
        
        # Shopping session state
        self.current_products = []
        self.current_requirements = None
        self.cart_items = []
        self.shopping_session_active = False
        
        # Initialize voice components if available
        if self.voice_enabled:
            try:
                # Enhanced voice recognition setup
                self.recognizer = sr.Recognizer()
                
                # Improved microphone initialization with device selection
                self.microphone = self._initialize_microphone()
                
                # Enhanced TTS engine setup
                self.tts_engine = self._initialize_tts_engine()
                
                # Voice recognition settings
                self._configure_voice_recognition()
                
                # Voice state management
                self.is_listening = False
                self.voice_active = False
                self.last_command_time = 0
                
                print("✅ Voice system initialized successfully")
                
            except Exception as e:
                self.voice_enabled = False
                print(f"❌ Voice initialization failed: {e}")
                print("   Install: pip install speechrecognition pyttsx3 pyaudio")
        
        # Message queue for thread communication
        self.message_queue = queue.Queue()
        
        # Setup GUI
        self.setup_gui()
        
        # Start message processor
        self.process_messages()
        
        # Load user settings
        self.load_settings()
    
    def setup_gui(self):
        """Setup the main GUI interface."""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = tk.Label(main_frame, text="🤖 AIVA - AI Voice Assistant", 
                              font=("Arial", 20, "bold"), bg='#f0f0f0', fg='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Service Selection Frame
        service_frame = ttk.LabelFrame(main_frame, text="Select Service", padding="10")
        service_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Service buttons
        self.setup_service_buttons(service_frame)
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=0)  # Control panel - fixed width
        content_frame.columnconfigure(1, weight=1)  # Output panel - expandable
        content_frame.rowconfigure(0, weight=1)
        
        # Left panel - Controls
        self.setup_control_panel(content_frame)
        
        # Right panel - Output
        self.setup_output_panel(content_frame)
        
        # Status bar
        self.setup_status_bar(main_frame)
    
    def setup_service_buttons(self, parent):
        """Setup service selection buttons."""
        
        # E-commerce section
        ecom_frame = ttk.LabelFrame(parent, text="🛒 E-commerce", padding="5")
        ecom_frame.grid(row=0, column=0, padx=(0, 10), sticky=(tk.W, tk.E, tk.N))
        
        ttk.Button(ecom_frame, text="🏪 Flipkart", 
                  command=lambda: self.select_service('flipkart')).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(ecom_frame, text="📦 Amazon", 
                  command=lambda: self.select_service('amazon')).grid(row=0, column=1, padx=5, pady=2)
        
        # Grocery section
        grocery_frame = ttk.LabelFrame(parent, text="🥬 Grocery", padding="5")
        grocery_frame.grid(row=0, column=1, padx=10, sticky=(tk.W, tk.E, tk.N))
        
        ttk.Button(grocery_frame, text="🛍️ Blinkit", 
                  command=lambda: self.select_service('blinkit')).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(grocery_frame, text="📋 Manage Lists", 
                  command=self.show_grocery_manager).grid(row=0, column=1, padx=5, pady=2)
        
        # Voice section
        voice_frame = ttk.LabelFrame(parent, text="🎤 Voice Commands", padding="5")
        voice_frame.grid(row=0, column=2, padx=(10, 0), sticky=(tk.W, tk.E, tk.N))
        
        voice_status = "🎤 Voice Mode" if self.voice_enabled else "❌ Voice Disabled"
        self.voice_btn = ttk.Button(voice_frame, text=voice_status, 
                                   command=self.toggle_voice_mode)
        self.voice_btn.grid(row=0, column=0, padx=5, pady=2)
        
        ttk.Button(voice_frame, text="🎓 Tutorial", 
                  command=self.start_voice_tutorial).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Button(voice_frame, text="❓ Help", 
                  command=self.show_help).grid(row=0, column=2, padx=5, pady=2)
    
    def setup_control_panel(self, parent):
        """Setup the left control panel with scrollable content."""
        
        # Create main control frame
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="5")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        control_frame.columnconfigure(0, weight=1)
        control_frame.rowconfigure(0, weight=1)
        
        # Create canvas and scrollbar for scrollable content
        canvas = tk.Canvas(control_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(control_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Grid the canvas and scrollbar
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure column weights
        scrollable_frame.columnconfigure(0, weight=1)
        
        # Add mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # Service status
        self.service_label = ttk.Label(scrollable_frame, text="No service selected", 
                                      font=("Arial", 12, "bold"))
        self.service_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Quick actions frame
        actions_frame = ttk.LabelFrame(scrollable_frame, text="Quick Actions", padding="5")
        actions_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        actions_frame.columnconfigure(0, weight=1)  # Allow content to expand
        
        # Search section
        ttk.Label(actions_frame, text="Search Query:").grid(row=0, column=0, sticky=tk.W)
        self.search_entry = ttk.Entry(actions_frame, width=30)
        self.search_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        self.search_entry.bind('<Return>', lambda e: self.start_search())
        
        # Requirements section
        ttk.Label(actions_frame, text="Budget (₹):").grid(row=2, column=0, sticky=tk.W)
        budget_frame = ttk.Frame(actions_frame)
        budget_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.budget_min_entry = ttk.Entry(budget_frame, width=12)
        self.budget_min_entry.grid(row=0, column=0, padx=(0, 5))
        self.budget_min_entry.insert(0, "Min")
        self.budget_min_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.budget_min_entry, "Min"))
        
        ttk.Label(budget_frame, text="to").grid(row=0, column=1, padx=5)
        
        self.budget_max_entry = ttk.Entry(budget_frame, width=12)
        self.budget_max_entry.grid(row=0, column=2, padx=(5, 0))
        self.budget_max_entry.insert(0, "Max")
        self.budget_max_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.budget_max_entry, "Max"))
        
        button_frame1 = ttk.Frame(actions_frame)
        button_frame1.grid(row=4, column=0, columnspan=2, pady=5)
        
        ttk.Button(button_frame1, text="🔍 Smart Search", 
                  command=self.start_smart_search).grid(row=0, column=0, padx=(0, 5), pady=2)
        ttk.Button(button_frame1, text="🛒 View Cart", 
                  command=self.view_cart).grid(row=0, column=1, padx=5, pady=2)
        
        # Shopping session controls
        session_frame = ttk.LabelFrame(scrollable_frame, text="Shopping Session", padding="5")
        session_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        session_frame.columnconfigure(0, weight=1)  # Allow content to expand
        
        # Session explanation label
        session_help = ttk.Label(session_frame, text="Sessions track your search results and cart items", 
                                font=("Arial", 8), foreground="gray")
        session_help.grid(row=0, column=0, columnspan=2, pady=(0, 2))
        
        self.session_status_label = ttk.Label(session_frame, text="No active session")
        self.session_status_label.grid(row=1, column=0, columnspan=2, pady=(0, 5))
        
        button_frame2 = ttk.Frame(session_frame)
        button_frame2.grid(row=2, column=0, columnspan=2)
        
        ttk.Button(button_frame2, text="🎯 Add to Cart", 
                  command=self.add_selected_to_cart).grid(row=0, column=0, padx=(0, 5), pady=2)
        ttk.Button(button_frame2, text="🔄 Refine Search", 
                  command=self.refine_search).grid(row=0, column=1, padx=5, pady=2)
        
        # Product selection
        ttk.Label(session_frame, text="Select Product:").grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        self.product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(session_frame, textvariable=self.product_var, width=40)
        self.product_combo.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Grocery specific controls
        self.grocery_frame = ttk.LabelFrame(scrollable_frame, text="Grocery Lists", padding="5")
        self.grocery_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # List selection
        ttk.Label(self.grocery_frame, text="Select List:").grid(row=0, column=0, sticky=tk.W)
        self.list_var = tk.StringVar()
        self.list_combo = ttk.Combobox(self.grocery_frame, textvariable=self.list_var, 
                                      values=list(self.grocery_manager.get_all_lists().keys()))
        self.list_combo.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(self.grocery_frame, text="📋 Show List", 
                  command=self.show_selected_list).grid(row=2, column=0, padx=(0, 5), pady=5)
        ttk.Button(self.grocery_frame, text="🛍️ Order List", 
                  command=self.order_selected_list).grid(row=2, column=1, padx=5, pady=5)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(scrollable_frame, text="Settings", padding="5")
        settings_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Location setting
        ttk.Label(settings_frame, text="Location (Pincode):").grid(row=0, column=0, sticky=tk.W)
        self.location_entry = ttk.Entry(settings_frame, width=20)
        self.location_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(settings_frame, text="📍 Set Location", 
                  command=self.set_location).grid(row=2, column=0, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="🔄 Refresh", 
                  command=self.refresh_interface).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="🧹 Clear Output", 
                  command=self.clear_output).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="💾 Save Settings", 
                  command=self.save_settings).grid(row=0, column=2, padx=5)
    
    def setup_output_panel(self, parent):
        """Setup the right output panel."""
        
        output_frame = ttk.LabelFrame(parent, text="Output", padding="10")
        output_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Output text area with scrollbar
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, 
                                                    height=25, width=60, 
                                                    font=("Consolas", 10))
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for colored output
        self.output_text.tag_configure("success", foreground="green")
        self.output_text.tag_configure("error", foreground="red")
        self.output_text.tag_configure("warning", foreground="orange")
        self.output_text.tag_configure("info", foreground="blue")
        self.output_text.tag_configure("header", font=("Consolas", 10, "bold"))
        
        # Initial welcome message
        self.add_output("🤖 Welcome to AIVA - AI Voice Assistant!", "header")
        self.add_output("📋 Select a service to get started.", "info")
        if not self.voice_enabled:
            self.add_output("⚠️ Voice features disabled. Install speech_recognition and pyttsx3 for voice control.", "warning")
    
    def setup_status_bar(self, parent):
        """Setup the status bar."""
        
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=0, column=1, padx=(10, 0))
    
    def select_service(self, service):
        """Select and initialize a service."""
        
        self.current_service = service
        self.service_label.config(text=f"Selected: {service.title()}")
        
        if service in ['flipkart', 'amazon']:
            self.add_output(f"🛒 Selected {service.title()} for e-commerce shopping.", "info")
            self.add_output("💡 Enter a search query and click Search to find products.", "info")
        elif service == 'blinkit':
            self.add_output("🥬 Selected Blinkit for grocery delivery.", "info")
            self.add_output("📍 Set your location first, then search for groceries.", "info")
        
        self.update_status(f"{service.title()} selected")
    
    def start_search(self):
        """Enhanced start basic product search with voice guidance."""
        
        query = self.search_entry.get().strip()
        if not query:
            message = "Please enter a search query."
            messagebox.showwarning("Warning", message)
            if self.voice_active:
                self.speak("Please enter what you'd like to search for")
            return
        
        if not self.current_service:
            message = "Please select a service first."
            messagebox.showwarning("Warning", message)
            if self.voice_active:
                self.speak("Please select a platform like Amazon or Flipkart first")
            return
        
        # Voice guidance for search start
        if self.voice_active:
            self.speak(f"Starting search for {query} on {self.current_service}")
        
        # Start search in thread to prevent GUI freezing
        thread = threading.Thread(target=self.perform_search, args=(query,))
        thread.daemon = True
        thread.start()
    
    def start_smart_search(self):
        """Enhanced start intelligent product search with voice guidance and requirement analysis."""
        
        query = self.search_entry.get().strip()
        if not query:
            message = "Please enter a search query."
            messagebox.showwarning("Warning", message)
            if self.voice_active:
                self.speak("Please enter what you'd like to search for")
            return
        
        if not self.current_service:
            message = "Please select a service first."
            messagebox.showwarning("Warning", message)
            if self.voice_active:
                self.speak("Please select a platform first")
            return
        
        # Voice guidance for smart search
        if self.voice_active:
            self.speak(f"Starting intelligent search for {query}. I'll analyze your requirements and find the best options.")
        
        # Start smart search in thread
        thread = threading.Thread(target=self.perform_smart_search, args=(query,))
        thread.daemon = True
        thread.start()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search query.")
            return
        
        if not self.current_service:
            messagebox.showwarning("Warning", "Please select a service first.")
            return
        
        if not AI_FEATURES_AVAILABLE:
            messagebox.showwarning("Warning", "AI features not available. Using basic search.")
            self.start_search()
            return
        
        # Start smart search in thread
        thread = threading.Thread(target=self.perform_smart_search, args=(query,))
        thread.daemon = True
        thread.start()
    
    def perform_smart_search(self, query):
        """Perform intelligent search with requirement analysis."""
        
        try:
            self.message_queue.put(("status", "Analyzing requirements..."))
            self.message_queue.put(("progress", "start"))
            self.message_queue.put(("output", f"🧠 Analyzing your requirements for '{query}'...", "info"))
            
            # Analyze user requirements
            budget_min = self._parse_budget(self.budget_min_entry.get())
            budget_max = self._parse_budget(self.budget_max_entry.get())
            
            # Create enhanced query with budget info
            enhanced_query = query
            if budget_max > 0:
                enhanced_query += f" under {budget_max}"
            
            requirements = self.requirement_analyzer.analyze_query(enhanced_query)
            # Ensure budget values are properly set
            if budget_min > 0:
                requirements.budget_min = budget_min
            elif not requirements.budget_min:
                requirements.budget_min = 0
                
            if budget_max > 0:
                requirements.budget_max = budget_max
            elif not requirements.budget_max:
                requirements.budget_max = 999999
            
            self.current_requirements = requirements
            
            self.message_queue.put(("output", f"📊 Requirements detected:", "info"))
            self.message_queue.put(("output", f"   Category: {requirements.category}", ""))
            self.message_queue.put(("output", f"   Budget: ₹{requirements.budget_min} - ₹{requirements.budget_max}", ""))
            if requirements.features:
                self.message_queue.put(("output", f"   Features: {', '.join(requirements.features)}", ""))
            if requirements.brand_preference:
                self.message_queue.put(("output", f"   Brands: {', '.join(requirements.brand_preference)}", ""))
            
            # Initialize browser if needed
            if not self.driver:
                self.init_browser()
            
            # Perform search
            self.message_queue.put(("output", f"🔍 Searching for products...", "info"))
            products = self._search_products(query)
            
            if products:
                # Rank products using AI
                self.message_queue.put(("output", f"🎯 Analyzing {len(products)} products...", "info"))
                ranked_products = self.recommendation_engine.rank_products(products, requirements)
                self.current_products = ranked_products
                
                # Check satisfaction
                satisfaction = self.satisfaction_checker.check_satisfaction(ranked_products, requirements)
                
                # Display results
                self._display_smart_results(ranked_products, satisfaction)
                
                # Update product selection dropdown
                self._update_product_selection(ranked_products)
                
                # Update session status
                self.shopping_session_active = True
                self.message_queue.put(("session_status", f"Active: {len(ranked_products)} products analyzed"))
                
            else:
                self.message_queue.put(("output", f"❌ No products found for '{query}'", "error"))
                
        except Exception as e:
            self.message_queue.put(("output", f"❌ Smart search failed: {str(e)}", "error"))
        
        finally:
            self.message_queue.put(("progress", "stop"))
            self.message_queue.put(("status", "Ready"))
    
    def _parse_budget(self, budget_str):
        """Parse budget string to integer."""
        try:
            return int(budget_str.strip()) if budget_str.strip() else 0
        except:
            return 0
    
    def _search_products(self, query):
        """Search products based on current service."""
        if self.current_service == 'flipkart':
            return self.search_flipkart(query)
        elif self.current_service == 'amazon':
            return self.search_amazon(query)
        elif self.current_service == 'blinkit':
            return self.search_blinkit(query)
        else:
            return []
    
    def _display_smart_results(self, products, satisfaction):
        """Display smart search results with analysis."""
        
        if satisfaction['satisfied']:
            self.message_queue.put(("output", f"✅ {satisfaction['reason']}", "success"))
            best_product = satisfaction['best_product']
            self.message_queue.put(("output", f"🏆 TOP RECOMMENDATION:", "header"))
            self._display_product_details(best_product, 1)
            
            if satisfaction.get('alternatives'):
                self.message_queue.put(("output", f"🔄 ALTERNATIVES:", "info"))
                for i, product in enumerate(satisfaction['alternatives'], 2):
                    self._display_product_details(product, i)
        else:
            self.message_queue.put(("output", f"⚠️ {satisfaction['reason']}", "warning"))
            
            if satisfaction.get('suggestions'):
                self.message_queue.put(("output", f"💡 SUGGESTIONS:", "info"))
                for suggestion in satisfaction['suggestions']:
                    self.message_queue.put(("output", f"   • {suggestion}", ""))
            
            if satisfaction.get('partial_matches'):
                self.message_queue.put(("output", f"🔍 BEST AVAILABLE OPTIONS:", "info"))
                for i, product in enumerate(satisfaction['partial_matches'], 1):
                    self._display_product_details(product, i)
    
    def _display_product_details(self, product, rank):
        """Display detailed product information."""
        title = product.get('title', 'Unknown')
        price = product.get('price', 0)
        score = product.get('match_score', 0)
        reasons = product.get('match_reasons', [])
        rating = product.get('rating')
        
        price_text = f"₹{price}" if price > 0 else "Price not available"
        rating_text = f" ({rating}⭐)" if rating else ""
        
        self.message_queue.put(("output", f"  {rank}. {title[:70]}...", ""))
        self.message_queue.put(("output", f"     💰 {price_text} | 🎯 {score:.1f}% match{rating_text}", ""))
        
        if reasons:
            self.message_queue.put(("output", f"     ✨ {', '.join(reasons[:2])}", ""))
    
    def _update_product_selection(self, products):
        """Update product selection dropdown."""
        product_options = []
        for i, product in enumerate(products[:10], 1):
            title = product.get('title', 'Unknown')[:50]
            price = product.get('price', 0)
            score = product.get('match_score', 0)
            option = f"{i}. {title}... - ₹{price} ({score:.1f}%)"
            product_options.append(option)
        
        self.message_queue.put(("update_products", product_options))
    
    def add_selected_to_cart(self):
        """Add selected product to cart."""
        
        if not self.shopping_session_active or not self.current_products:
            messagebox.showwarning("Warning", "No active shopping session. Please search for products first.")
            return
        
        selection = self.product_var.get()
        if not selection:
            messagebox.showwarning("Warning", "Please select a product from the dropdown.")
            return
        
        # Extract product index from selection
        try:
            product_index = int(selection.split('.')[0]) - 1
            selected_product = self.current_products[product_index]
            
            # Start cart operation in thread
            thread = threading.Thread(target=self.perform_add_to_cart, args=(selected_product,))
            thread.daemon = True
            thread.start()
            
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Invalid product selection.")
    
    def perform_add_to_cart(self, product):
        """Add product to cart with enhanced adapter."""
        
        try:
            self.message_queue.put(("status", "Adding to cart..."))
            self.message_queue.put(("progress", "start"))
            
            # Get the selenium element from the product dictionary
            product_element = product.get('element')
            if not product_element:
                self.message_queue.put(("output", f"❌ Product element not found for cart operation", "error"))
                return
            
            if self.current_service == 'flipkart':
                adapter = FlipkartAdapter(self.driver, WebDriverWait(self.driver, 10))
                success = adapter.add_to_cart(product_element)  # Pass the selenium element
            elif self.current_service == 'amazon':
                adapter = AmazonAdapter(self.driver, WebDriverWait(self.driver, 10))
                success = adapter.add_to_cart(product_element)  # Pass the selenium element
            else:
                success = False
                self.message_queue.put(("output", f"❌ Service '{self.current_service}' not supported for cart operations", "error"))
            
            if success:
                self.cart_items.append(product)
                self.message_queue.put(("output", f"✅ Added to cart: {product['title'][:50]}...", "success"))
                self.message_queue.put(("session_status", f"Cart: {len(self.cart_items)} items"))
                
                # Check if requirements are satisfied
                self._check_requirement_satisfaction()
            else:
                self.message_queue.put(("output", f"❌ Failed to add product to cart", "error"))
                
        except Exception as e:
            self.message_queue.put(("output", f"❌ Cart operation failed: {str(e)}", "error"))
        
        finally:
            self.message_queue.put(("progress", "stop"))
            self.message_queue.put(("status", "Ready"))
    
    def _check_requirement_satisfaction(self):
        """Check if current cart satisfies user requirements."""
        
        if not self.current_requirements or not AI_FEATURES_AVAILABLE:
            return
        
        # Analyze cart contents
        total_value = sum(item.get('price', 0) for item in self.cart_items)
        
        self.message_queue.put(("output", f"📊 CART ANALYSIS:", "header"))
        self.message_queue.put(("output", f"   Items: {len(self.cart_items)}", ""))
        self.message_queue.put(("output", f"   Total: ₹{total_value}", ""))
        
        if total_value <= self.current_requirements.budget_max:
            self.message_queue.put(("output", f"✅ Cart fits within budget!", "success"))
        else:
            excess = total_value - self.current_requirements.budget_max
            self.message_queue.put(("output", f"⚠️ Cart exceeds budget by ₹{excess}", "warning"))
        
        # Ask for satisfaction
        self.message_queue.put(("output", f"❓ Are you satisfied with current selection?", "info"))
        self.message_queue.put(("output", f"💡 Use 'Refine Search' to find alternatives or 'View Cart' to proceed", "info"))
    
    def refine_search(self):
        """Refine search based on current requirements."""
        
        if not self.shopping_session_active:
            messagebox.showwarning("Warning", "No active shopping session.")
            return
        
        # Ask for refinement criteria
        refinement = tk.simpledialog.askstring(
            "Refine Search", 
            "What would you like to change?\n(e.g., 'lower price', 'different brand', 'better rating')"
        )
        
        if refinement:
            self.message_queue.put(("output", f"🔄 Refining search: {refinement}", "info"))
            # This could be enhanced with more sophisticated refinement logic
            self.start_smart_search()
    
    def perform_search(self, query):
        """Enhanced perform product search with voice guidance."""
        
        try:
            self.message_queue.put(("status", "Searching..."))
            self.message_queue.put(("progress", "start"))
            self.message_queue.put(("output", f"🔍 Searching for '{query}' on {self.current_service.title()}...", "info"))
            
            # Voice guidance for search start
            if self.voice_active:
                self.speak(f"Searching for {query} on {self.current_service}")
            
            # Initialize browser if needed
            if not self.driver:
                if self.voice_active:
                    self.speak("Initializing browser, please wait")
                self.init_browser()
            
            # Perform search based on service
            if self.current_service == 'flipkart':
                products = self.search_flipkart(query)
            elif self.current_service == 'amazon':
                products = self.search_amazon(query)
            elif self.current_service == 'blinkit':
                products = self.search_blinkit(query)
            else:
                products = []
            
            # Display results with voice feedback
            if products:
                self.current_products = products
                self.shopping_session_active = True
                success_msg = f"Found {len(products)} products"
                self.message_queue.put(("output", f"✅ {success_msg}:", "success"))
                self.message_queue.put(("session_status", f"Active: {len(products)} products found"))
                
                # Voice feedback for successful search
                if self.voice_active:
                    if len(products) == 1:
                        self.speak("Found 1 product for you")
                    else:
                        self.speak(f"Great! I found {len(products)} products for you. You can now select one to add to cart.")
                
                # Update product selection dropdown
                self._update_product_selection(products)
                
                for i, product in enumerate(products[:10], 1):
                    price = product.get('price', 0)
                    price_text = f"₹{price}" if price > 0 else "Price not available"
                    self.message_queue.put(("output", f"  {i}. {product.get('title', 'Unknown')} - {price_text}", ""))
            else:
                error_msg = f"No products found for '{query}'"
                self.message_queue.put(("output", f"❌ {error_msg}", "error"))
                
                # Voice feedback for no results
                if self.voice_active:
                    self.speak(f"Sorry, I couldn't find any products for {query}. Try a different search term.")
            
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            self.message_queue.put(("output", f"❌ {error_msg}", "error"))
            
            # Voice feedback for search errors
            if self.voice_active:
                self.speak("Search failed due to an error. Please try again.")
        
        finally:
            self.message_queue.put(("progress", "stop"))
            self.message_queue.put(("status", "Ready"))
    
    def init_browser(self):
        """Initialize browser for web scraping."""
        
        try:
            if not SELENIUM_AVAILABLE:
                raise Exception("Selenium not available. Please install selenium and webdriver-manager.")
            
            self.message_queue.put(("output", "🌐 Initializing browser...", "info"))
            
            chrome_options = Options()
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            # Comment out headless for testing - user can see what's happening
            # chrome_options.add_argument("--headless")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.message_queue.put(("output", "✅ Browser initialized successfully.", "success"))
            
        except Exception as e:
            self.message_queue.put(("output", f"❌ Browser initialization failed: {str(e)}", "error"))
            raise
    
    def search_flipkart(self, query):
        """Search products on Flipkart."""
        
        try:
            wait = WebDriverWait(self.driver, 10)
            adapter = FlipkartAdapter(self.driver, wait)
            return adapter.search_products(query)
        except Exception as e:
            raise Exception(f"Flipkart search failed: {str(e)}")
    
    def search_amazon(self, query):
        """Search products on Amazon."""
        
        try:
            wait = WebDriverWait(self.driver, 10)
            adapter = AmazonAdapter(self.driver, wait)
            return adapter.search_products(query)
        except Exception as e:
            raise Exception(f"Amazon search failed: {str(e)}")
    
    def search_blinkit(self, query):
        """Search groceries on Blinkit."""
        
        try:
            if not GROCERY_AVAILABLE:
                raise Exception("Grocery adapter not available. Please check grocery_adapters.py file.")
            
            wait = WebDriverWait(self.driver, 10)
            adapter = BlinkitAdapter(self.driver, wait)
            
            # Setup location if provided
            location = self.location_entry.get().strip()
            if location:
                # Parse location - assume it's either pincode or "area, pincode"
                if ',' in location:
                    parts = [part.strip() for part in location.split(',')]
                    if len(parts) >= 2:
                        area = parts[0]
                        pincode = parts[1]
                    else:
                        area = None
                        pincode = location
                else:
                    area = None
                    pincode = location
                
                adapter.setup_location(pincode, area)
            
            return adapter.search_product(query)
        except Exception as e:
            raise Exception(f"Blinkit search failed: {str(e)}")
    
    def view_cart(self):
        """View shopping cart with enhanced functionality."""
        
        if not self.current_service:
            messagebox.showwarning("Warning", "Please select a service first.")
            return
        
        if not self.driver:
            messagebox.showwarning("Warning", "Browser not initialized. Please search for products first.")
            return
        
        # Start cart viewing in thread
        thread = threading.Thread(target=self.perform_view_cart)
        thread.daemon = True
        thread.start()
    
    def perform_view_cart(self):
        """Perform cart viewing operation."""
        
        try:
            self.message_queue.put(("status", "Loading cart..."))
            self.message_queue.put(("progress", "start"))
            
            # Show local cart items (more reliable than website cart)
            if self.cart_items:
                self.message_queue.put(("output", f"🛒 YOUR SHOPPING CART ({len(self.cart_items)} items):", "header"))
                
                total_value = 0
                for i, item in enumerate(self.cart_items, 1):
                    price = item.get('price', 0)
                    total_value += price
                    self.message_queue.put(("output", f"  {i}. {item.get('title', 'Unknown')[:60]}", ""))
                    self.message_queue.put(("output", f"     Price: ₹{price:,}", ""))
                
                self.message_queue.put(("output", f"", ""))
                self.message_queue.put(("output", f"💰 TOTAL VALUE: ₹{total_value:,}", "success"))
                
                # Check if requirements are satisfied
                if self.current_requirements and AI_FEATURES_AVAILABLE:
                    budget_min = self.current_requirements.budget_min or 0
                    budget_max = self.current_requirements.budget_max or 999999
                    
                    if budget_min <= total_value <= budget_max:
                        self.message_queue.put(("output", f"✅ Cart total fits your budget (₹{budget_min:,} - ₹{budget_max:,})", "success"))
                        self.message_queue.put(("output", f"🎉 THANK YOU for using AIVA! Your shopping requirements are satisfied.", "success"))
                        self.message_queue.put(("output", f"", ""))
                        self.message_queue.put(("output", f"Would you like to:", "info"))
                        self.message_queue.put(("output", f"  • Proceed to checkout on {self.current_service.title()}", ""))
                        self.message_queue.put(("output", f"  • Continue shopping for more items", ""))
                        self.message_queue.put(("output", f"  • Refine your search for better options", ""))
                    else:
                        if total_value > budget_max:
                            excess = total_value - budget_max
                            self.message_queue.put(("output", f"⚠️ Cart exceeds budget by ₹{excess:,}", "warning"))
                            self.message_queue.put(("output", f"💡 Consider removing items or increasing budget", "info"))
                        else:
                            remaining = budget_min - total_value
                            self.message_queue.put(("output", f"💡 You can add ₹{remaining:,} more to reach minimum budget", "info"))
                
                # Also try to show website cart for comparison
                self.message_queue.put(("output", f"", ""))
                self.message_queue.put(("output", f"🌐 Checking website cart...", "info"))
                
                if self.current_service == 'flipkart':
                    try:
                        adapter = FlipkartAdapter(self.driver, WebDriverWait(self.driver, 10))
                        website_cart = adapter.view_cart()
                        if website_cart:
                            self.message_queue.put(("output", f"✅ Website cart has {len(website_cart)} items", ""))
                        else:
                            self.message_queue.put(("output", f"ℹ️ Website cart appears empty (this is normal due to session management)", "info"))
                    except:
                        self.message_queue.put(("output", f"ℹ️ Could not check website cart", "info"))
                
            else:
                self.message_queue.put(("output", f"🛒 Your cart is empty", "warning"))
                self.message_queue.put(("output", f"� Search for products and add them to cart first", "info"))
                
        except Exception as e:
            self.message_queue.put(("output", f"❌ Cart viewing failed: {str(e)}", "error"))
        
        finally:
            self.message_queue.put(("progress", "stop"))
            self.message_queue.put(("status", "Ready"))
    
    def _clear_placeholder(self, entry_widget, placeholder):
        """Clear placeholder text when entry is focused."""
        if entry_widget.get() == placeholder:
            entry_widget.delete(0, tk.END)
    
    def show_grocery_manager(self):
        """Show grocery list manager window."""
        
        GroceryManagerWindow(self.root, self.grocery_manager, self.message_queue)
    
    def show_selected_list(self):
        """Show the selected grocery list."""
        
        list_name = self.list_var.get()
        if not list_name:
            messagebox.showwarning("Warning", "Please select a grocery list.")
            return
        
        grocery_list = self.grocery_manager.get_list(list_name)
        if grocery_list:
            self.add_output(f"📋 {list_name.upper()} GROCERY LIST", "header")
            items = grocery_list['items']
            cost = self.grocery_manager.get_estimated_cost(list_name)
            
            self.add_output(f"📊 Items: {len(items)} | 💰 Estimated Cost: ₹{cost:.2f}", "info")
            
            for i, item in enumerate(items, 1):
                item_name = item['item_name']
                quantity = item['quantity']
                notes = item.get('notes', '')
                notes_text = f" ({notes})" if notes else ""
                self.add_output(f"  {i}. {quantity}x {item_name}{notes_text}", "")
        else:
            self.add_output(f"❌ List '{list_name}' not found.", "error")
    
    def order_selected_list(self):
        """Order the selected grocery list."""
        
        list_name = self.list_var.get()
        if not list_name:
            messagebox.showwarning("Warning", "Please select a grocery list.")
            return
        
        if self.current_service != 'blinkit':
            messagebox.showwarning("Warning", "Please select Blinkit service for grocery ordering.")
            return
        
        # Start ordering in thread
        thread = threading.Thread(target=self.perform_grocery_order, args=(list_name,))
        thread.daemon = True
        thread.start()
    
    def perform_grocery_order(self, list_name):
        """Perform actual grocery ordering on Blinkit."""
        
        try:
            self.message_queue.put(("status", f"Ordering {list_name} list..."))
            self.message_queue.put(("progress", "start"))
            
            # Get the grocery list
            grocery_list = self.grocery_manager.get_list(list_name)
            if not grocery_list:
                self.message_queue.put(("output", f"❌ Grocery list '{list_name}' not found", "error"))
                return
                
            items = grocery_list['items']
            self.message_queue.put(("output", f"🛍️ Starting to order {len(items)} items from {list_name} list...", "info"))
            
            # Initialize browser if needed
            if not self.driver:
                self.message_queue.put(("output", "🌐 Initializing browser...", "info"))
                self.init_browser()
                time.sleep(2)
            
            # Initialize Blinkit adapter
            if not GROCERY_AVAILABLE:
                self.message_queue.put(("output", "❌ Grocery adapter not available", "error"))
                return
                
            wait = WebDriverWait(self.driver, 10)
            adapter = BlinkitAdapter(self.driver, wait)
            
            # Setup location if provided
            location = self.location_entry.get().strip()
            if location:
                self.message_queue.put(("output", f"📍 Setting up location: {location}", "info"))
                # Parse location - assume it's either pincode or "area, pincode"
                if ',' in location:
                    parts = [part.strip() for part in location.split(',')]
                    if len(parts) >= 2:
                        area = parts[0]
                        pincode = parts[1]
                    else:
                        area = None
                        pincode = location
                else:
                    area = None
                    pincode = location
                
                location_result = adapter.setup_location(pincode, area)
                if not location_result:
                    self.message_queue.put(("output", "❌ Failed to setup location", "error"))
                    return
                else:
                    self.message_queue.put(("output", "✅ Location setup successful", "success"))
            
            # Process each item in the grocery list
            ordered_items = 0
            failed_items = 0
            
            for i, item in enumerate(items, 1):
                item_name = item['item_name']
                quantity = item['quantity']
                
                self.message_queue.put(("output", f"  🔍 [{i}/{len(items)}] Searching for {quantity}x {item_name}...", ""))
                
                try:
                    # Search for the product
                    products = adapter.search_product(item_name)
                    
                    if products:
                        # Take the first product (best match)
                        product = products[0]
                        self.message_queue.put(("output", f"    ✅ Found: {product['name']} - ₹{product['price']}", ""))
                        
                        # Try to add to cart
                        if 'element' in product:
                            cart_result = adapter.add_to_cart(product['element'], quantity)
                            if cart_result:
                                self.message_queue.put(("output", f"    🛒 Added {quantity}x {product['name']} to cart", "success"))
                                ordered_items += 1
                            else:
                                self.message_queue.put(("output", f"    ⚠️ Could not add {item_name} to cart", "warning"))
                                failed_items += 1
                        else:
                            self.message_queue.put(("output", f"    ⚠️ No element available for {item_name}", "warning"))
                            failed_items += 1
                    else:
                        self.message_queue.put(("output", f"    ❌ Product '{item_name}' not found", "warning"))
                        failed_items += 1
                    
                    # Small delay between items
                    time.sleep(2)
                    
                except Exception as e:
                    self.message_queue.put(("output", f"    ❌ Error processing {item_name}: {str(e)}", "error"))
                    failed_items += 1
                    continue
            
            # Summary
            self.message_queue.put(("output", f"\n📊 ORDERING SUMMARY:", "header"))
            self.message_queue.put(("output", f"  ✅ Successfully ordered: {ordered_items} items", "success"))
            if failed_items > 0:
                self.message_queue.put(("output", f"  ❌ Failed to order: {failed_items} items", "warning"))
            
            if ordered_items > 0:
                self.message_queue.put(("output", f"🛒 Items have been added to your Blinkit cart!", "success"))
                self.message_queue.put(("output", f"💡 Click 'View Cart' to review and checkout", "info"))
            else:
                self.message_queue.put(("output", f"❌ No items were successfully added to cart", "error"))
            
        except Exception as e:
            self.message_queue.put(("output", f"❌ Ordering failed: {str(e)}", "error"))
            import traceback
            traceback.print_exc()
        
        finally:
            self.message_queue.put(("progress", "stop"))
            self.message_queue.put(("status", "Ready"))
    
    def set_location(self):
        """Set delivery location."""
        
        location = self.location_entry.get().strip()
        if location:
            self.add_output(f"📍 Location set to: {location}", "success")
            self.update_status(f"Location: {location}")
        else:
            messagebox.showwarning("Warning", "Please enter a location.")
    
    def _initialize_microphone(self):
        """Initialize microphone with best available device."""
        try:
            # Try to find the best microphone
            mic_list = sr.Microphone.list_microphone_names()
            print(f"📡 Available microphones: {len(mic_list)}")
            
            # Use default microphone with optimized settings
            microphone = sr.Microphone()
            
            # Calibrate for ambient noise
            print("🎯 Calibrating microphone for ambient noise...")
            with microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            print(f"✅ Microphone initialized with energy threshold: {self.recognizer.energy_threshold}")
            return microphone
            
        except Exception as e:
            print(f"❌ Microphone initialization failed: {e}")
            return sr.Microphone()  # Fallback to default
    
    def _initialize_tts_engine(self):
        """Initialize text-to-speech engine with optimized settings."""
        try:
            engine = pyttsx3.init()
            
            # Get available voices
            voices = engine.getProperty('voices')
            
            # Try to set a female voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            # Optimize speech settings
            engine.setProperty('rate', 160)     # Slower, clearer speech
            engine.setProperty('volume', 0.9)   # High volume
            
            # Test TTS
            print("🗣️ Testing text-to-speech...")
            engine.say("Voice system ready")
            engine.runAndWait()
            
            return engine
            
        except Exception as e:
            print(f"❌ TTS initialization failed: {e}")
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 0.8)
            return engine
    
    def _configure_voice_recognition(self):
        """Configure voice recognition parameters for better accuracy."""
        # Adjust recognition sensitivity
        self.recognizer.energy_threshold = 300      # Higher threshold for better noise filtering
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8       # Longer pause before considering speech ended
        self.recognizer.phrase_threshold = 0.3      # Minimum audio length to consider for phrase
        self.recognizer.non_speaking_duration = 0.5 # Seconds of non-speaking audio before phrase completes
        
        print(f"🎙️ Voice recognition configured:")
        print(f"   • Energy threshold: {self.recognizer.energy_threshold}")
        print(f"   • Pause threshold: {self.recognizer.pause_threshold}s")
        print(f"   • Dynamic energy: {self.recognizer.dynamic_energy_threshold}")
    
    def speak(self, text):
        """Enhanced text-to-speech with better error handling."""
        if not self.voice_enabled:
            return
            
        try:
            # Clean text for better speech
            clean_text = self._clean_text_for_speech(text)
            
            # Speak in separate thread to avoid blocking
            def speak_thread():
                try:
                    self.tts_engine.say(clean_text)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    print(f"❌ TTS error: {e}")
            
            thread = threading.Thread(target=speak_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print(f"❌ Speech synthesis failed: {e}")
    
    def _clean_text_for_speech(self, text):
        """Clean text for better speech synthesis."""
        # Remove emojis and special characters
        clean_text = re.sub(r'[🤖🎤🔍🛒🥬📍✅❌⚠️💡📊🎯]', '', text)
        
        # Replace common abbreviations
        replacements = {
            'AIVA': 'Aiva',
            'GUI': 'graphical user interface',
            'API': 'A P I',
            'URL': 'U R L',
            'TTS': 'text to speech',
            'AI': 'artificial intelligence'
        }
        
        for old, new in replacements.items():
            clean_text = clean_text.replace(old, new)
        
        return clean_text.strip()
    
    def toggle_voice_mode(self):
        """Enhanced toggle voice command mode with better feedback."""
        
        if not self.voice_enabled:
            messagebox.showinfo("Voice Disabled", 
                              "Voice features are not available.\n\nTo enable voice control:\n" +
                              "1. Install: pip install speechrecognition pyttsx3 pyaudio\n" +
                              "2. Restart AIVA")
            return
        
        if self.is_listening:
            # Stop listening
            self.is_listening = False
            self.voice_active = False
            self.add_output("🔇 Voice mode deactivated", "info")
            self.speak("Voice mode off")
            return
        
        # Start voice mode
        self.voice_active = True
        self.add_output("🎤 Voice mode activated. Say 'help' for commands or 'stop' to exit.", "info")
        self.speak("Voice mode activated. How can I help you?")
        
        # Start voice recognition in thread
        thread = threading.Thread(target=self.listen_for_voice_command)
        thread.daemon = True
        thread.start()
    
    def listen_for_voice_command(self):
        """Enhanced voice listening with improved error handling and recovery."""
        
        self.is_listening = True
        retry_count = 0
        max_retries = 3
        
        while self.voice_active and self.is_listening:
            try:
                self.message_queue.put(("status", "🎤 Listening..."))
                
                # Dynamic ambient noise adjustment
                if retry_count == 0:
                    with self.microphone as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen with timeout
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=15, phrase_time_limit=8)
                
                # Recognize speech
                command = self.recognizer.recognize_google(audio, language='en-US').lower().strip()
                
                if command:
                    self.message_queue.put(("output", f"👂 Heard: '{command}'", "info"))
                    
                    # Process command
                    self._process_enhanced_voice_command(command)
                    retry_count = 0  # Reset retry count on successful recognition
                
            except sr.WaitTimeoutError:
                error_info = self.handle_voice_errors('timeout', 'Listening timeout')
                retry_count += 1
                
            except sr.UnknownValueError:
                error_info = self.handle_voice_errors('recognition', 'Could not understand speech')
                retry_count += 1
                
            except sr.RequestError as e:
                error_info = self.handle_voice_errors('network', str(e))
                retry_count += 1
                
            except OSError as e:
                error_info = self.handle_voice_errors('microphone', str(e))
                retry_count += 1
                
            except Exception as e:
                error_info = self.handle_voice_errors('unknown', str(e))
                retry_count += 1
            
            # Check if too many retries
            if retry_count >= max_retries:
                self.message_queue.put(("output", "🔇 Too many errors, attempting recovery...", "error"))
                
                # Attempt recovery
                if self.recover_voice_session():
                    retry_count = 0  # Reset if recovery successful
                    continue
                else:
                    self.voice_active = False
                    self.is_listening = False
                    self.message_queue.put(("output", "❌ Voice mode stopped due to repeated errors", "error"))
                    break
            
            # Brief pause between listening attempts
            time.sleep(0.5)
        
        self.message_queue.put(("status", "Ready"))
        self.is_listening = False
    
    def _process_enhanced_voice_command(self, command):
        """Enhanced voice command processing with better natural language understanding."""
        
        command = command.lower().strip()
        
        # Check for stop commands first
        if any(word in command for word in ['stop', 'exit', 'quit', 'end']):
            self.voice_active = False
            self.is_listening = False
            self.add_output("🔇 Voice mode stopped", "info")
            self.speak("Voice mode stopped")
            return
        
        # Help commands
        if any(word in command for word in ['help', 'what can you do', 'commands']):
            self._provide_voice_help()
            return
        
        # Search commands with intelligent parsing
        if self._handle_search_commands(command):
            return
        
        # Shopping and e-commerce commands
        if self._handle_shopping_commands(command):
            return
        
        # Grocery commands
        if self._handle_grocery_commands(command):
            return
        
        # Settings and configuration
        if self._handle_settings_commands(command):
            return
        
        # If no command matched, provide helpful feedback
        self._handle_unknown_command(command)
    
    def _handle_search_commands(self, command):
        """Handle search-related voice commands."""
        search_triggers = ['search', 'find', 'look for', 'show me', 'get me']
        
        if any(trigger in command for trigger in search_triggers):
            # Extract search query
            query = self._extract_search_query(command)
            
            if query:
                # Set the query in the search box
                self.search_entry.delete(0, tk.END)
                self.search_entry.insert(0, query)
                
                # Start search
                self.add_output(f"🔍 Searching for: {query}", "info")
                self.speak(f"Searching for {query}")
                
                # Start search in thread
                thread = threading.Thread(target=self.start_search)
                thread.daemon = True
                thread.start()
                
                return True
            else:
                self.speak("What would you like me to search for?")
                return True
        
        return False
    
    def _handle_shopping_commands(self, command):
        """Handle shopping and e-commerce commands."""
        shopping_keywords = ['buy', 'purchase', 'order', 'cart', 'checkout', 'flipkart', 'amazon']
        
        if any(keyword in command for keyword in shopping_keywords):
            
            # Platform selection
            if 'flipkart' in command:
                self.platform_var.set('flipkart')
                self.add_output("🛒 Switched to Flipkart", "info")
                self.speak("Switched to Flipkart")
                return True
                
            elif 'amazon' in command:
                self.platform_var.set('amazon')
                self.add_output("🛒 Switched to Amazon", "info")  
                self.speak("Switched to Amazon")
                return True
            
            # Cart operations
            elif any(word in command for word in ['cart', 'basket', 'checkout']):
                self.add_output("🛒 Cart functionality via voice coming soon!", "info")
                self.speak("Cart functionality via voice will be available soon")
                return True
            
            # General purchase intent
            elif any(word in command for word in ['buy', 'purchase', 'order']):
                # Extract product name
                product = self._extract_product_from_command(command)
                if product:
                    self.search_entry.delete(0, tk.END)
                    self.search_entry.insert(0, product)
                    self.add_output(f"🛒 Ready to shop for: {product}", "info")
                    self.speak(f"Ready to shop for {product}. Say search to begin.")
                else:
                    self.speak("What would you like to buy?")
                return True
        
        return False
    
    def _handle_grocery_commands(self, command):
        """Handle grocery ordering commands."""
        grocery_keywords = ['grocery', 'groceries', 'food', 'blinkit', 'deliver', 'order food']
        
        if any(keyword in command for keyword in grocery_keywords):
            
            # Switch to grocery mode
            if 'blinkit' in command or 'grocery' in command or 'groceries' in command:
                self.add_output("🥬 Switched to grocery ordering mode", "info")
                self.speak("Switched to grocery mode. You can set your location and start ordering.")
                return True
            
            # Location setting
            elif 'location' in command or 'address' in command:
                self.speak("Please enter your location or pincode manually, or say a specific location")
                return True
            
            # Order specific items
            elif 'order' in command:
                item = self._extract_grocery_item(command)
                if item:
                    self.add_output(f"🥬 Adding {item} to grocery search", "info")
                    self.speak(f"Adding {item} to your grocery list")
                else:
                    self.speak("What grocery items would you like to order?")
                return True
        
        return False
    
    def _handle_settings_commands(self, command):
        """Handle settings and configuration commands."""
        settings_keywords = ['settings', 'config', 'setup', 'change']
        
        if any(keyword in command for keyword in settings_keywords):
            
            if 'voice' in command:
                if 'faster' in command or 'speed up' in command:
                    self._adjust_speech_rate(1.2)
                    return True
                elif 'slower' in command or 'slow down' in command:
                    self._adjust_speech_rate(0.8)
                    return True
                elif 'volume' in command:
                    if 'up' in command or 'louder' in command:
                        self._adjust_speech_volume(1.0)
                    elif 'down' in command or 'quieter' in command:
                        self._adjust_speech_volume(0.6)
                    return True
            
            self.speak("Settings can be adjusted manually in the interface")
            return True
        
        return False
    
    def _handle_unknown_command(self, command):
        """Handle unrecognized commands with helpful suggestions."""
        suggestions = [
            "Try saying 'search for laptop' to find products",
            "Say 'switch to Amazon' or 'switch to Flipkart'",
            "Say 'grocery mode' for food ordering",
            "Say 'help' to hear all available commands",
            "Say 'stop' to exit voice mode"
        ]
        
        suggestion = suggestions[len(command) % len(suggestions)]
        
        self.add_output(f"❓ Command not recognized: '{command}'", "warning")
        self.add_output(f"💡 {suggestion}", "info")
        self.speak(f"I didn't understand that. {suggestion}")
    
    def _extract_search_query(self, command):
        """Extract search query from voice command."""
        # Remove trigger words
        triggers = ['search for', 'find', 'look for', 'show me', 'get me', 'search']
        
        query = command
        for trigger in triggers:
            query = query.replace(trigger, '')
        
        # Clean up the query
        query = query.strip()
        
        # Remove common stop words at the beginning/end
        stop_words = ['a', 'an', 'the', 'some', 'any']
        words = query.split()
        
        # Remove stop words from beginning
        while words and words[0] in stop_words:
            words.pop(0)
        
        # Remove stop words from end
        while words and words[-1] in stop_words:
            words.pop()
        
        return ' '.join(words)
    
    def _extract_product_from_command(self, command):
        """Extract product name from shopping commands."""
        # Remove shopping trigger words
        triggers = ['buy', 'purchase', 'order', 'get me', 'i want', 'i need']
        
        product = command
        for trigger in triggers:
            product = product.replace(trigger, '')
        
        return product.strip()
    
    def _extract_grocery_item(self, command):
        """Extract grocery item from command."""
        # Remove grocery trigger words
        triggers = ['order', 'get', 'buy', 'add', 'i need', 'i want']
        
        item = command
        for trigger in triggers:
            item = item.replace(trigger, '')
        
        return item.strip()
    
    def _adjust_speech_rate(self, factor):
        """Adjust speech rate."""
        try:
            current_rate = self.tts_engine.getProperty('rate')
            new_rate = int(current_rate * factor)
            self.tts_engine.setProperty('rate', new_rate)
            self.speak(f"Speech rate adjusted to {new_rate}")
        except:
            self.speak("Could not adjust speech rate")
    
    def _adjust_speech_volume(self, volume):
        """Adjust speech volume."""
        try:
            self.tts_engine.setProperty('volume', volume)
            self.speak("Speech volume adjusted")
        except:
            self.speak("Could not adjust speech volume")
    
    def _provide_voice_help(self):
        """Provide comprehensive voice help with interactive tutorial."""
        help_commands = [
            "Here are available voice commands:",
            "Search: Say 'search for laptop' or 'find headphones'",
            "Shopping: Say 'switch to Amazon' or 'buy smartphone'", 
            "Grocery: Say 'grocery mode' or 'order milk and bread'",
            "Settings: Say 'speak faster' or 'volume up'",
            "Control: Say 'stop' to exit voice mode"
        ]
        
        self.add_output("🎤 Voice Commands Help:", "info")
        for cmd in help_commands:
            self.add_output(f"   • {cmd}", "info")
        
        # Interactive voice tutorial
        self.speak("Here are the main voice commands you can use.")
        time.sleep(1)
        self.speak("For searching, say search for followed by what you want to find.")
        time.sleep(1) 
        self.speak("To switch platforms, say switch to Amazon or switch to Flipkart.")
        time.sleep(1)
        self.speak("For groceries, say grocery mode or order specific items.")
        time.sleep(1)
        self.speak("Say stop anytime to exit voice mode. What would you like to do?")
    
    def start_voice_tutorial(self):
        """Start an interactive voice tutorial for new users."""
        if not self.voice_enabled:
            messagebox.showinfo("Voice Disabled", "Voice features are not available.")
            return
        
        self.add_output("🎓 Starting Voice Tutorial", "info")
        
        def tutorial_thread():
            try:
                self.speak("Welcome to AIVA voice tutorial!")
                time.sleep(2)
                
                self.speak("I'll teach you how to use voice commands. First, try saying hello to me.")
                # Wait for user response
                tutorial_step = 1
                
                while tutorial_step <= 3:
                    if tutorial_step == 1:
                        self.speak("Now try saying: search for laptop")
                        # Tutorial continues...
                    elif tutorial_step == 2:
                        self.speak("Good! Now try: switch to Amazon")
                    elif tutorial_step == 3:
                        self.speak("Excellent! Voice tutorial complete. You're ready to use AIVA!")
                        break
                    
                    tutorial_step += 1
                    time.sleep(5)  # Wait for user to try command
                    
            except Exception as e:
                self.message_queue.put(("output", f"❌ Tutorial error: {e}", "error"))
        
        thread = threading.Thread(target=tutorial_thread)
        thread.daemon = True
        thread.start()
    
    def handle_voice_errors(self, error_type, error_msg):
        """Enhanced voice error handling with recovery suggestions."""
        
        error_responses = {
            'timeout': {
                'message': "⏰ Voice timeout - I didn't hear anything",
                'speech': "I didn't hear you. Please try speaking again, or say stop to exit voice mode.",
                'suggestion': "💡 Speak clearly and ensure your microphone is working"
            },
            'recognition': {
                'message': "❓ Could not understand what you said",
                'speech': "I couldn't understand that. Please speak clearly and try again.",
                'suggestion': "💡 Try speaking slower or rephrasing your command"
            },
            'network': {
                'message': "🌐 Network error - speech recognition service unavailable",
                'speech': "Network error. Speech recognition is temporarily unavailable.",
                'suggestion': "💡 Check your internet connection and try again"
            },
            'microphone': {
                'message': "🎤 Microphone error - check your audio input",
                'speech': "Microphone error. Please check your audio settings.",
                'suggestion': "💡 Ensure your microphone is connected and not muted"
            }
        }
        
        error_info = error_responses.get(error_type, {
            'message': f"❌ Voice error: {error_msg}",
            'speech': "An error occurred with voice recognition.",
            'suggestion': "💡 Try restarting voice mode"
        })
        
        # Display error message
        self.add_output(error_info['message'], "error")
        self.add_output(error_info['suggestion'], "info")
        
        # Speak error feedback
        if self.voice_enabled and error_type != 'microphone':
            try:
                self.speak(error_info['speech'])
            except:
                pass  # Don't compound errors
        
        return error_info
    
    def recover_voice_session(self):
        """Attempt to recover from voice errors."""
        try:
            self.add_output("🔄 Attempting voice recovery...", "info")
            
            # Reinitialize microphone
            if self.voice_enabled:
                self.microphone = self._initialize_microphone()
                self.speak("Voice system recovered. You can continue using voice commands.")
                return True
                
        except Exception as e:
            self.add_output(f"❌ Voice recovery failed: {e}", "error")
            return False
    
    def process_voice_command(self, command):
        """Legacy voice command processor - keeping for compatibility."""
        
        if 'search' in command:
            # Extract search query
            query = command.replace('search', '').replace('for', '').strip()
            if query:
                self.search_entry.delete(0, tk.END)
                self.search_entry.insert(0, query)
                self.start_search()
        elif 'grocery' in command or 'order' in command:
            self.add_output("🥬 Voice grocery commands will be processed here.", "info")
        else:
            self.add_output(f"❓ Command not recognized: {command}", "warning")
    
    def show_help(self):
        """Show help dialog."""
        
        help_text = """
🤖 AIVA - AI Voice Assistant Help

🛒 E-COMMERCE:
• Select Flipkart or Amazon
• Enter search query and click Search
• View results in the output panel

🥬 GROCERY:
• Select Blinkit for delivery
• Set your location (pincode)
• Choose a grocery list or search items
• Click "Order List" to process orders

🎤 VOICE COMMANDS:
• Click "Voice Mode" to activate
• Say commands like:
  - "Search for laptop"
  - "Order monthly groceries"
  - "Show my grocery list"

💡 TIPS:
• Use the Quick Actions for common tasks
• Save your settings for future use
• Check the output panel for detailed results
• Use grocery lists for efficient shopping

❓ For issues, check the output panel for error messages.
        """
        
        messagebox.showinfo("AIVA Help", help_text)
    
    def refresh_interface(self):
        """Refresh the interface."""
        
        # Update grocery list combo
        lists = list(self.grocery_manager.get_all_lists().keys())
        self.list_combo['values'] = lists
        
        self.add_output("🔄 Interface refreshed.", "info")
    
    def clear_output(self):
        """Clear the output panel."""
        
        self.output_text.delete(1.0, tk.END)
        self.add_output("🧹 Output cleared.", "info")
    
    def save_settings(self):
        """Save user settings."""
        
        settings = {
            'location': self.location_entry.get(),
            'last_service': self.current_service,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open('aiva_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            self.add_output("💾 Settings saved successfully.", "success")
        except Exception as e:
            self.add_output(f"❌ Failed to save settings: {str(e)}", "error")
    
    def load_settings(self):
        """Load user settings."""
        
        try:
            if os.path.exists('aiva_settings.json'):
                with open('aiva_settings.json', 'r') as f:
                    settings = json.load(f)
                
                # Load location
                location = settings.get('location', '')
                self.location_entry.insert(0, location)
                
                # Load last service
                last_service = settings.get('last_service')
                if last_service:
                    self.select_service(last_service)
                
                self.add_output("📂 Settings loaded successfully.", "info")
        except Exception as e:
            self.add_output(f"⚠️ Could not load settings: {str(e)}", "warning")
    
    def add_output(self, text, tag="", speak=False):
        """Enhanced add text to output panel with optional formatting and voice feedback."""
        
        def _add():
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_text = f"[{timestamp}] {text}\n"
            
            if tag:
                self.output_text.insert(tk.END, formatted_text, tag)
            else:
                self.output_text.insert(tk.END, formatted_text)
            
            self.output_text.see(tk.END)
            
            # Auto-speak important messages if voice is active
            if self.voice_active and (speak or self._should_auto_speak(text, tag)):
                self.speak(text)
        
        if threading.current_thread() == threading.main_thread():
            _add()
        else:
            self.message_queue.put(("output", text, tag, speak))
    
    def _should_auto_speak(self, text, tag):
        """Determine if a message should be automatically spoken."""
        # Speak important status updates
        if tag in ["success", "error", "warning"]:
            return True
        
        # Speak search results and completion messages
        if any(keyword in text.lower() for keyword in 
               ["found", "completed", "ready", "failed", "error", "success"]):
            return True
        
        # Don't speak routine log messages
        if any(keyword in text.lower() for keyword in 
               ["loading", "processing", "analyzing", "waiting"]):
            return False
        
        return False
    
    def update_status(self, text):
        """Update status bar."""
        
        def _update():
            self.status_label.config(text=text)
        
        if threading.current_thread() == threading.main_thread():
            _update()
        else:
            self.message_queue.put(("status", text))
    
    def process_messages(self):
        """Process messages from worker threads."""
        
        try:
            while True:
                msg_data = self.message_queue.get_nowait()
                msg_type = msg_data[0]
                data = msg_data[1:]
                
                if msg_type == "output":
                    # Handle both old and new message formats
                    if len(data) == 2:
                        text, tag = data
                        speak = False
                    else:
                        text, tag, speak = data
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    formatted_text = f"[{timestamp}] {text}\n"
                    
                    if tag:
                        self.output_text.insert(tk.END, formatted_text, tag)
                    else:
                        self.output_text.insert(tk.END, formatted_text)
                    
                    self.output_text.see(tk.END)
                    
                    # Voice feedback for important messages
                    if self.voice_active and (speak or self._should_auto_speak(text, tag)):
                        self.speak(text)
                
                elif msg_type == "status":
                    status_text = data[0]
                    self.status_label.config(text=status_text)
                    
                    # Voice feedback for status changes during voice mode
                    if self.voice_active and any(keyword in status_text.lower() for keyword in 
                                               ["ready", "completed", "error", "failed"]):
                        self.speak(status_text)
                
                elif msg_type == "progress":
                    if data[0] == "start":
                        self.progress.start()
                    else:
                        self.progress.stop()
                
                elif msg_type == "session_status":
                    self.session_status_label.config(text=data[0])
                
                elif msg_type == "update_products":
                    self.product_combo['values'] = data[0]
                    if data[0]:  # If there are products, select the first one
                        self.product_combo.current(0)
        
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_messages)
    
    def on_closing(self):
        """Handle application closing."""
        
        if self.driver:
            self.driver.quit()
        
        self.save_settings()
        self.root.destroy()

class GroceryManagerWindow:
    """Separate window for grocery list management."""
    
    def __init__(self, parent, grocery_manager, message_queue):
        self.grocery_manager = grocery_manager
        self.message_queue = message_queue
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Grocery List Manager")
        self.window.geometry("800x600")
        self.window.configure(bg='#f0f0f0')
        
        self.setup_grocery_gui()
    
    def setup_grocery_gui(self):
        """Setup grocery management GUI."""
        
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="🛒 Grocery List Manager", 
                              font=("Arial", 16, "bold"), bg='#f0f0f0')
        title_label.pack(pady=(0, 20))
        
        # List selection
        list_frame = ttk.LabelFrame(main_frame, text="Grocery Lists", padding="10")
        list_frame.pack(fill=tk.X, pady=(0, 10))
        
        # List display
        self.list_text = scrolledtext.ScrolledText(main_frame, height=20, width=80)
        self.list_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Display all lists
        self.display_all_lists()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="🔄 Refresh", 
                  command=self.display_all_lists).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="➕ Create List", 
                  command=self.create_new_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Close", 
                  command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def display_all_lists(self):
        """Display all grocery lists."""
        
        self.list_text.delete(1.0, tk.END)
        
        all_lists = self.grocery_manager.get_all_lists()
        
        for list_name, list_data in all_lists.items():
            items = list_data['items']
            cost = self.grocery_manager.get_estimated_cost(list_name)
            
            self.list_text.insert(tk.END, f"📋 {list_name.upper()}\n", "header")
            self.list_text.insert(tk.END, f"Items: {len(items)} | Cost: ₹{cost:.2f}\n")
            self.list_text.insert(tk.END, "-" * 50 + "\n")
            
            for item in items:
                item_name = item['item_name']
                quantity = item['quantity']
                notes = item.get('notes', '')
                notes_text = f" ({notes})" if notes else ""
                self.list_text.insert(tk.END, f"  • {quantity}x {item_name}{notes_text}\n")
            
            self.list_text.insert(tk.END, "\n")
    
    def create_new_list(self):
        """Create a new grocery list."""
        
        # Simple dialog for new list name
        list_name = tk.simpledialog.askstring("New List", "Enter list name:")
        if list_name:
            if self.grocery_manager.create_list(list_name):
                messagebox.showinfo("Success", f"Created list: {list_name}")
                self.display_all_lists()
            else:
                messagebox.showerror("Error", "Failed to create list")

def main():
    """Main function to run AIVA GUI."""
    
    # Create main window
    root = tk.Tk()
    
    # Initialize AIVA GUI
    app = AIVAGui(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start GUI
    root.mainloop()

if __name__ == "__main__":
    main()