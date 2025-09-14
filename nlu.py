"""
nlu.py: Minimal NLU (Natural Language Understanding) module for AIVA
- Extracts intent and entities from text command
- Uses regex fallback (no external API)
- Provides parse_command() function
"""
import re
import logging
from typing import Dict, Any

def parse_command(command: str) -> Dict[str, Any]:
    """Extracts intent and entities from a user command string."""
    # Example: "Find budget smartphones under 20k on Flipkart."
    # Intent: search_product, Entities: product_name, price_range, platform
    intent = "search_product"
    product_name = None
    price_range = None
    platform = None

    # Price extraction (e.g., under 20k, below 15000, less than 10,000)
    price_match = re.search(r"(?:under|below|less than|upto|up to)\s*₹?\s*([\d,]+[kK]?)", command, re.I)
    if price_match:
        price_str = price_match.group(1).replace(",", "").lower()
        if price_str.endswith("k"):
            price_range = int(float(price_str[:-1]) * 1000)
        else:
            try:
                price_range = int(price_str)
            except Exception:
                price_range = None

    # Platform extraction (Flipkart, Amazon, etc.)
    plat_match = re.search(r"(flipkart|amazon|myntra|zomato|swiggy)", command, re.I)
    if plat_match:
        platform = plat_match.group(1).lower()

    # Product/entity extraction (remove stopwords and platform)
    cleaned = re.sub(r"\b(?:find|search|show|for|under|below|less than|upto|up to|on|in|buy|order|please|want|need|get|rs|rupees|₹|[\d,]+[kK]?|flipkart|amazon|myntra|zomato|swiggy)\b", "", command, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    product_name = cleaned if cleaned else None

    result = {
        "intent": intent,
        "product_name": product_name,
        "price_range": price_range,
        "platform": platform
    }
    logging.info(f"NLU parsed: {result}")
    return result

if __name__ == "__main__":
    print("AIVA NLU Demo: Type a command (e.g., 'Find budget smartphones under 20k on Flipkart.')")
    cmd = input("Command: ")
    parsed = parse_command(cmd)
    print(f"Parsed: {parsed}")
