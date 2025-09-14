"""
main.py: Main entry point for AIVA - Agentic Intelligent Voice Assistant
"""
from interactive_session import InteractiveAIVA
import sys

def main():
    """Main entry point for AIVA."""
    print("🚀 AIVA - Agentic Intelligent Voice Assistant")
    print("🤖 AI-Powered Shopping Assistant")
    print("=" * 50)
    
    # Initialize AIVA
    aiva = InteractiveAIVA()
    
    if not aiva.start_session():
        print("❌ Failed to start AIVA session")
        return
    
    try:
        print("\n🎤 Welcome to AIVA!")
        print("I can help you find and purchase products with AI-powered recommendations.")
        print("\nExamples:")
        print("- 'Find wireless earphones under 2000'")
        print("- 'Show me good gaming headsets'")
        print("- 'bluetooth speakers under 5000'")
        
        while True:
            print("\n" + "="*50)
            user_input = input("🛍️ What would you like to shop for? (or 'quit' to exit): ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Thank you for using AIVA! Goodbye!")
                break
            
            if not user_input:
                continue
            
            try:
                # Extract product and price limit from input
                product_query = user_input
                price_limit = None
                
                # Simple price extraction
                import re
                price_match = re.search(r'under (\d+)', user_input.lower())
                if price_match:
                    price_limit = int(price_match.group(1))
                
                # Run intelligent shopping loop
                print(f"\n🔍 Searching for: {product_query}")
                if price_limit:
                    print(f"💰 Price limit: ₹{price_limit}")
                
                success = aiva.intelligent_shopping_loop(
                    product=product_query,
                    price_limit=price_limit,
                    max_attempts=3
                )
                
                if success:
                    print("🎉 Shopping completed successfully!")
                    
                    choice = input("\n❓ Continue shopping? (y/n): ").lower().strip()
                    if choice in ['n', 'no']:
                        break
                else:
                    print("❌ Shopping was unsuccessful. Please try again with different criteria.")
                    
            except Exception as e:
                print(f"❌ Error during shopping: {e}")
                print("Please try again with a different query.")
                
    except KeyboardInterrupt:
        print("\n\n👋 AIVA session interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ AIVA session error: {e}")
    finally:
        if aiva.driver:
            aiva.driver.quit()

if __name__ == "__main__":
    main()