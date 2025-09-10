import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or "AIzaSyB939h9BOGiigZRmg_FagAI_Yjkx9_Sv6w"
genai.configure(api_key=api_key)

def parse_command_with_gemini(command):
    prompt = f"""
    You are a strict JSON generator. 
    From the following command, extract:
    - action: string (like "search_zomato")
    - food_type: string
    - price_limit: integer

    Return ONLY valid JSON. No extra text, no explanations, no markdown.

    Example:
    {{"action": "search_zomato", "food_type": "spicy", "price_limit": 200}}

    Command: {command}
    """
    def _local_fallback_parse(cmd: str) -> str:
        # price: detect numbers near 'under/below/less than' or any ₹/rs amounts
        price = None
        m = re.search(r"(?:under|below|less than|upto|up to)\s*₹?\s*(\d+)", cmd, re.I)
        if not m:
            m = re.search(r"₹\s*(\d+)", cmd)
        if not m:
            m = re.search(r"\b(\d{2,4})\b\s*(?:rs|rupees)?", cmd, re.I)
        if m:
            try:
                price = int(m.group(1))
            except Exception:
                price = None

        # food_type: remove common stopwords and platforms
        cleaned = re.sub(r"zomato|order|orders?|food|delivery|from|please|want|i\s*want|need|get|for|under|below|less than|upto|up to|rs|rupees|₹|\d+", " ", cmd, flags=re.I)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        food_type = cleaned if cleaned else "food"

        data = {"action": "search_zomato", "food_type": food_type, "price_limit": price}
        return json.dumps(data)

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # On rate limit or any error, fallback to local parser
        return _local_fallback_parse(command)
