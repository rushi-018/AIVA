"""
main_voice.py: Enhanced main entry point for voice-enabled AIVA
Provides both voice and traditional text-based AIVA options.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_enabled_aiva import VoiceEnabledAIVA
from multi_website_aiva import MultiWebsiteAIVA

def display_welcome():
    """Display welcome message and options."""
    print("🤖 AIVA - AI-Powered Shopping Assistant")
    print("🎯 Enhanced with Voice & Multi-Website Support")
    print("=" * 65)
    print()
    print("🎤 VOICE-ENABLED FEATURES:")
    print("   • Speak or type your shopping queries")
    print("   • Voice responses and guidance")
    print("   • Voice commands for navigation")
    print("   • Smart product recommendations")
    print("   • Multi-website support (Flipkart, Amazon)")
    print()
    print("📋 OPTIONS:")
    print("   1. 🎤 Voice-Enabled AIVA (Recommended)")
    print("   2. 📝 Text-Only AIVA")
    print("   3. ❌ Exit")
    print()

def get_user_choice():
    """Get user's preferred AIVA mode."""
    while True:
        try:
            choice = input("Select mode (1/2/3): ").strip()
            
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("❌ Please enter 1, 2, or 3")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Input error: {e}")

def run_voice_enabled_aiva():
    """Run the voice-enabled AIVA."""
    print("\n🎤 Starting Voice-Enabled AIVA...")
    print("💡 Tip: You can speak or type your responses")
    print("-" * 50)
    
    aiva = VoiceEnabledAIVA()
    aiva.run()

def run_text_only_aiva():
    """Run the traditional text-only AIVA."""
    print("\n📝 Starting Text-Only AIVA...")
    print("💡 Traditional keyboard input mode")
    print("-" * 50)
    
    aiva = MultiWebsiteAIVA()
    aiva.run()

def main():
    """Main entry point with mode selection."""
    try:
        display_welcome()
        
        choice = get_user_choice()
        
        if choice == 1:
            run_voice_enabled_aiva()
        elif choice == 2:
            run_text_only_aiva()
        elif choice == 3:
            print("👋 Thank you for choosing AIVA! Goodbye!")
        
    except KeyboardInterrupt:
        print("\n\n👋 AIVA session interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ AIVA startup error: {e}")
        print("Please check your environment and dependencies.")
    finally:
        print("\n🤖 Thank you for using AIVA!")

if __name__ == "__main__":
    main()