import streamlit as st
import json
import re
from voice_input import get_voice_command
from ai_parser import parse_command_with_gemini
from zomato_bot import automate_zomato, create_edge_driver, find_candidates, add_selected_item

st.title("🎯 AI Voice Shopping Agent")

# Select input method
input_mode = st.radio("Choose input method:", ["🎙 Voice", "⌨ Text"])

command = ""

if input_mode == "🎙 Voice":
    if st.button("🎙 Speak Command"):
        with st.spinner("Listening..."):
            command = get_voice_command()
        if command:
            st.success("Captured voice command.")
            st.write("You said:", command)
        else:
            st.error("Voice input unavailable. Install SpeechRecognition and PyAudio, or use Text mode.")

elif input_mode == "⌨ Text":
    command = st.text_input("Type your command here:")
    if st.button("Submit Command"):
        st.write("You entered:", command)

# Only process if command is not empty
if command:
    parsed = parse_command_with_gemini(command)

    # Try to extract only JSON part from AI output
    json_match = re.search(r"\{.*\}", parsed, re.DOTALL)
    if json_match:
        parsed_json_str = json_match.group(0)
    else:
        st.error("No JSON found in AI response")
        st.text(parsed)
        parsed_json_str = None

    # Maintain a single persistent Edge driver in session
    if "driver" not in st.session_state:
        st.session_state["driver"] = None

    def get_driver():
        if st.session_state["driver"] is None:
            st.session_state["driver"] = create_edge_driver()
        return st.session_state["driver"]

    if parsed_json_str:
        # First validate JSON separately from automation errors
        try:
            data = json.loads(parsed_json_str)
        except Exception as e:
            st.error(f"Invalid JSON from AI: {e}")
            st.text(parsed_json_str)
            data = None

        if data:
            st.write("AI Parsed Command:", data)
            if data.get("action") == "search_zomato":
                st.write("Finding candidates...")
                try:
                    edge_driver = get_driver()
                    candidates = find_candidates(data.get("food_type"), data.get("price_limit"), driver=edge_driver)
                    if not candidates:
                        st.error("No matching items found.")
                    else:
                        # Show choices
                        display = [f"{c['item_name']} - ₹{c.get('price') or '?'} | {c.get('restaurant_name') or 'Unknown'} | ⭐ {c.get('rating') or '?'}" for c in candidates[:10]]
                        choice = st.selectbox("Select an item to add to cart:", options=display)
                        if st.button("Add Selected Item and Proceed to Payment"):
                            try:
                                # Extract item name from selection
                                selected_name = choice.split(' - ')[0]
                                result = add_selected_item(selected_name, candidates, driver=edge_driver, go_to_payment=True)
                                st.success(result)
                            except Exception as e:
                                st.error(f"Failed to add selected item: {e}")
                except Exception as auto_e:
                    st.error(f"Automation failed: {auto_e}")

    # Optional control to close browser
    if st.session_state.get("driver") is not None:
        if st.button("Close Browser"):
            try:
                st.session_state["driver"].quit()
            except Exception:
                pass
            st.session_state["driver"] = None