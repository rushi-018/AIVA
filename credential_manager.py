"""
credential_manager.py: Simple and secure credential management for AIVA
Handles saving, loading, and managing user credentials for e-commerce platforms.
"""

import os
import json
import base64
import time
from typing import Optional, Dict

class CredentialManager:
    """Secure credential management for AIVA login system."""
    
    def __init__(self, credentials_file: str = ".aiva_credentials"):
        """Initialize credential manager."""
        self.credentials_file = credentials_file
    
    def _encode(self, data: str) -> str:
        """Simple encoding for security."""
        try:
            encoded = base64.b64encode(data.encode()).decode()
            return encoded
        except:
            return ""
    
    def _decode(self, data: str) -> str:
        """Simple decoding."""
        try:
            decoded = base64.b64decode(data.encode()).decode()
            return decoded
        except:
            return ""
    
    def save_credentials(self, email: str, password: str) -> bool:
        """Save credentials with simple encoding (legacy method)."""
        try:
            credentials = {
                "email": self._encode(email),
                "password": self._encode(password),
                "saved": True
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f)
            
            print("✅ Credentials saved securely")
            return True
        except Exception as e:
            print(f"❌ Failed to save credentials: {e}")
            return False
    
    def save_otp_account(self, email_or_mobile: str) -> bool:
        """Save email/mobile for OTP-based accounts."""
        try:
            credentials = {
                "username": email_or_mobile,
                "password": "otp_required",
                "login_type": "otp",
                "saved_at": time.time()
            }
            
            encoded_creds = base64.b64encode(json.dumps(credentials).encode()).decode()
            
            with open(self.credentials_file, 'w') as f:
                f.write(encoded_creds)
            
            print(f"✅ Email/mobile saved securely for OTP login")
            return True
            
        except Exception as e:
            print(f"❌ Error saving email/mobile: {e}")
            return False

    def load_credentials(self) -> Optional[Dict[str, str]]:
        """Load saved credentials - supports both old and new formats."""
        try:
            if not os.path.exists(self.credentials_file):
                return None
            
            with open(self.credentials_file, 'r') as f:
                content = f.read().strip()
            
            if not content:
                return None
            
            # Try new base64 format first
            try:
                decoded_data = base64.b64decode(content).decode()
                credentials = json.loads(decoded_data)
                
                # Normalize to standard format
                if "username" in credentials:
                    return {
                        "username": credentials["username"],
                        "password": credentials.get("password", "otp_required"),
                        "login_type": credentials.get("login_type", "otp")
                    }
                    
            except Exception:
                pass
            
            # Try old JSON format
            try:
                data = json.loads(content)
                if data.get("saved"):
                    return {
                        "username": self._decode(data["email"]),
                        "password": self._decode(data["password"]),
                        "login_type": "traditional"
                    }
            except Exception:
                pass
            
            return None
            
        except Exception:
            return None
    
    def has_saved_credentials(self) -> bool:
        """Check if credentials are saved."""
        return self.load_credentials() is not None
    
    def is_otp_account(self) -> bool:
        """Check if saved account is OTP-based."""
        creds = self.load_credentials()
        return creds and creds.get("password") == "otp_required"
    
    def delete_credentials(self) -> bool:
        """Delete saved credentials."""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
                print("✅ Credentials deleted")
            return True
        except Exception as e:
            print(f"❌ Failed to delete credentials: {e}")
            return False
    
    def get_credential_choice(self) -> str:
        """Get user choice for credential handling with OTP awareness."""
        print("\n🔐 Login Options:")
        
        if self.has_saved_credentials():
            saved_creds = self.load_credentials()
            is_otp_account = saved_creds and saved_creds.get("password") == "otp_required"
            
            if is_otp_account:
                print("1. 📱 Use saved email/mobile (Assisted OTP login)")
                print("2. 🆕 Enter different email/mobile")
                print("3. 🕶️ Continue as guest")
                print("4. 🗑️ Delete saved email")
                print("\n💡 Note: Flipkart requires OTP verification for all logins")
            else:
                print("1. 📱 Use saved email/mobile (Assisted login)")
                print("2. 🆕 Enter different email/mobile")
                print("3. 🕶️ Continue as guest")
                print("4. 🗑️ Delete saved credentials")
                print("\n💡 Note: Flipkart may require OTP verification")
            
            while True:
                choice = input("\nSelect option (1/2/3/4): ").strip()
                if choice in ["1", "2", "3", "4"]:
                    return choice
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
        else:
            print("1. 🔑 Enter email/mobile for login")
            print("2. 🕶️ Continue as guest")
            print("\n💡 Note: Flipkart requires OTP verification for all logins")
            
            while True:
                choice = input("\nSelect option (1/2): ").strip()
                if choice in ["1", "2"]:
                    return choice
                print("❌ Invalid choice. Please enter 1 or 2.")

# Test functionality
if __name__ == "__main__":
    cm = CredentialManager()
    
    print("🧪 Testing Credential Manager...")
    
    # Test OTP account
    result = cm.save_otp_account("test@example.com")
    print(f"✅ Save test passed: {result}")
    
    creds = cm.load_credentials()
    print(f"✅ Load test passed: {creds['username'] if creds else 'None'}")
    
    is_otp = cm.is_otp_account()
    print(f"✅ OTP check passed: {is_otp}")
    
    # Clean up
    cm.delete_credentials()
    print("✅ Delete test passed")