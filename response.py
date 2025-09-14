"""
response.py: Minimal Response Layer for AIVA
- Summarizes execution results into user-friendly text
- For demo: formats search results and action confirmations
- Can be extended to include speech synthesis (TTS)
"""
import logging
from typing import List, Dict, Any

def format_search_results(candidates: List[Dict]) -> str:
    """Format search results into a user-friendly summary."""
    if not candidates:
        return "❌ No products found matching your criteria."
    
    response = f"✅ Found {len(candidates)} products:\n\n"
    for i, item in enumerate(candidates, 1):
        title = item.get('title', 'Unknown Product')
        price = item.get('price', 'Price not available')
        response += f"{i}. {title}\n   Price: ₹{price}\n\n"
    
    return response

def format_action_result(action: str, result: str) -> str:
    """Format action execution results."""
    action_name = {
        'search': 'Search',
        'add_to_cart': 'Add to Cart',
        'checkout': 'Checkout'
    }.get(action, action.title())
    
    return f"[{action_name}] {result}"

def generate_response(execution_result: str, candidates: List[Dict] = None) -> str:
    """Generate a comprehensive response from execution results."""
    response = "🤖 AIVA Response:\n"
    response += "=" * 40 + "\n\n"
    
    if candidates:
        response += format_search_results(candidates)
    else:
        response += execution_result
    
    response += "\n" + "=" * 40
    return response

def speak_response(text: str) -> str:
    """Placeholder for text-to-speech functionality."""
    # For now, just return the text
    # In future: use pyttsx3 or similar TTS library
    logging.info("TTS: Would speak the response here")
    return f"[SPEECH] {text}"

if __name__ == "__main__":
    print("AIVA Response Demo")
    
    # Test with sample candidates
    sample_candidates = [
        {"title": "Samsung Galaxy A14 (Black, 128 GB)", "price": 16999},
        {"title": "Redmi Note 12 5G (Frosted Blue, 128 GB)", "price": 18999},
        {"title": "POCO X5 5G (Jaguar Black, 128 GB)", "price": 19999}
    ]
    
    print("Sample search response:")
    print(generate_response("", sample_candidates))
    
    print("\nSample action response:")
    print(generate_response("✅ Item successfully added to cart!"))