"""
core.py: Minimal Agentic Core for AIVA
- Implements a basic ReAct loop: Reason → Act → Observe → Repeat (1 cycle for demo)
- Receives parsed NLU output, decides what to do, and calls the right module
- For now, just prints reasoning and returns a plan dict
"""
import logging
from typing import Dict, Any

def react_loop(nlu_result: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal ReAct loop: reason, act, observe (1 cycle for demo)."""
    # Reason
    intent = nlu_result.get("intent")
    product = nlu_result.get("product_name")
    price = nlu_result.get("price_range")
    platform = nlu_result.get("platform")
    reasoning = f"Intent: {intent}. Product: {product}. Price: {price}. Platform: {platform}."
    logging.info(f"Reasoning: {reasoning}")
    print(f"[REASON] {reasoning}")

    # Act (plan)
    if intent == "search_product" and platform:
        plan = {
            "action": "search",
            "platform": platform,
            "product": product,
            "price": price
        }
        print(f"[ACT] Plan: {plan}")
    else:
        plan = {"action": "unknown"}
        print("[ACT] No valid plan.")

    # Observe (for demo, just echo plan)
    print(f"[OBSERVE] Plan ready for execution.")
    return plan

if __name__ == "__main__":
    print("AIVA Core Demo: Enter parsed NLU dict (or use sample)")
    sample = {'intent': 'search_product', 'product_name': 'budget smartphones', 'price_range': 20000, 'platform': 'flipkart'}
    inp = input("Use sample? (y/n): ")
    if inp.strip().lower().startswith('y'):
        nlu_result = sample
    else:
        import ast
        nlu_result = ast.literal_eval(input("Paste NLU dict: "))
    plan = react_loop(nlu_result)
    print(f"Returned plan: {plan}")
