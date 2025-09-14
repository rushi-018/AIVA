"""
demo_multi_website.py: Quick demo of the multi-website AIVA system
Shows how to use the website adapter system without full browser automation.
"""

from website_adapters import WebsiteAdapterFactory

def demo_website_selection():
    """Demo the website selection and adapter creation."""
    print("🎭 AIVA Multi-Website Demo")
    print("=" * 40)
    
    # Show supported websites
    supported = WebsiteAdapterFactory.get_supported_websites()
    print(f"🌐 Supported websites: {supported}")
    print()
    
    # Demo each adapter
    for website in supported:
        print(f"📱 {website.title()} Adapter:")
        
        # Create adapter (without actual driver)
        try:
            adapter = WebsiteAdapterFactory.create_adapter(website, None, None)
            
            print(f"   🔗 Base URL: {adapter.get_base_url()}")
            print(f"   🔐 Login URL: {adapter.get_login_url()}")
            print(f"   📋 Login Instructions:")
            
            instructions = adapter.get_login_instructions()
            for line in instructions.split('\n')[:5]:  # Show first 5 lines
                if line.strip():
                    print(f"      {line}")
            print("      ...")
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    print("✅ Multi-website system ready!")
    print("\n💡 Usage:")
    print("• Run 'python multi_website_aiva.py' for full shopping experience")
    print("• Run 'python main.py' for original Flipkart-only version")

if __name__ == "__main__":
    demo_website_selection()