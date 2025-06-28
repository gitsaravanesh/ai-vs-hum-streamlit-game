import streamlit as st
import boto3
import json
import re

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(page_title="Who Said It: AI or Human?", page_icon="🧠")
st.title("🧠 Who Said It: AI or Human?")
st.subheader("Pick your style and guess whether the quote is written by AI or a Human!")

# -------------------------------
# Session state setup
# -------------------------------
defaults = {
    "game_started": False,
    "score": 0,
    "total": 0,
    "quotes": [],
    "current_index": 0,
    "answered": False,
    "current_quote": "",
    "current_source": ""
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# -------------------------------
# User inputs
# -------------------------------
age_group = st.selectbox("Select your age group", ["Under 18", "18-25", "26-40", "41-60", "60+"])
preference = st.selectbox("Pick your quote preference", ["Technology", "Motivational", "Humor", "Philosophy", "Life Advice"])

# -------------------------------
# Bedrock client
# -------------------------------
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=st.secrets["AWS_REGION"],
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
)

# -------------------------------
# Extract array of quote JSONs from response
# -------------------------------
def extract_quotes_array(text):
    try:
        json_array = re.search(r"\s*\{.*?\}\s*", text, re.DOTALL).group(0)
        return json.loads(json_array)
    except Exception:
        return []

# -------------------------------
# Load 10 quotes using one Bedrock call
# -------------------------------
def load_quotes_batch(age_group, preference):
    prompt = (
        "You are an assistant that generates short, thought-provoking quotes for a guessing game.\n\n"
        "Please generate a list of 10 quotes. Each quote should be either:\n"
        "- an original AI-generated quote\n"
        "- or a famous quote by a known human\n\n"
        "Each item must be in JSON format like:\n"
        '{"quote": "text here", "source": "AI" or "Human"}\n\n'
        "Respond ONLY with a JSON array like:\n"
        "[\n"
        '  {"quote": "...", "source": "..."},\n'
        "  ...\n"
        "]\n\n"
        f"Topic: {preference}\n"
        f"Age group: {age_group}"
    )

    body = {
        "prompt": prompt,
        "max_gen_len": 1000,
        "temperature": 0.9,
        "top_p": 0.9
    }

    try:
        response = bedrock.invoke_model(
            modelId="meta.llama3-8b-instruct-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )
        response_body = json.loads(response['body'].read())
        generation = response_body.get("generation", "")
        quotes = extract_quotes_array(generation)

        # Validate and clean
        valid_quotes = [
            q for q in quotes
            if isinstance(q, dict)
            and "quote" in q
            and "source" in q
            and q["quote"].strip() != ""
            and q["source"] in ["AI", "Human"]
        ]
        return valid_quotes[:10]

    except Exception as e:
        st.error("❌ Failed to generate quotes from the model.")
        st.caption(f"Debug info: {e}")
        return []

# -------------------------------
# Start the game
# -------------------------------
if not st.session_state.game_started:
    if st.button("Start Game"):
        with st.spinner("🎲 Generating 10 mysterious quotes..."):
            st.session_state.quotes = load_quotes_batch(age_group, preference)
            st.session_state.current_index = 0
            st.session_state.total = 0
            st.session_state.score = 0
            st.session_state.answered = False
            st.session_state.game_started = True

        if not st.session_state.quotes:
            st.warning("⚠️ No quotes loaded. Try again.")
            st.session_state.game_started = False
        else:
            st.session_state.current_quote = st.session_state.quotes[0]["quote"]
            st.session_state.current_source = st.session_state.quotes[0]["source"]
    st.stop()

# -------------------------------
# Show current quote
# -------------------------------
st.markdown(f"### 📝 \"{st.session_state.current_quote}\"")

# -------------------------------
# Input guess
# -------------------------------
choice = st.radio("Who said it?", ["AI", "Human"], key=f"guess_{st.session_state.current_index}")

# -------------------------------
# Submit guess
# -------------------------------
if st.button("Submit Answer") and not st.session_state.answered:
    st.session_state.total += 1
    st.session_state.answered = True
    if choice == st.session_state.current_source:
        st.success("✅ Correct!")
        st.session_state.score += 1
    else:
        st.error(f"❌ Nope! It was actually {st.session_state.current_source}")
    st.markdown(f"### 🎯 Score: {st.session_state.score}/{st.session_state.total}")

# -------------------------------
# Next quote or End
# -------------------------------
if st.session_state.answered:
    if st.session_state.current_index < len(st.session_state.quotes) - 1:
        if st.button("Next Quote"):
            st.session_state.current_index += 1
            next_quote = st.session_state.quotes[st.session_state.current_index]
            st.session_state.current_quote = next_quote["quote"]
            st.session_state.current_source = next_quote["source"]
            st.session_state.answered = False
            st.rerun()
    else:
        st.markdown("---")
        st.success("🎉 You've reached the end of the game!")
        st.markdown(f"### 🏁 Final Score: {st.session_state.score}/{st.session_state.total}")
        if st.button("🔄 Play Again"):
            for key in defaults:
                st.session_state[key] = defaults[key]
            st.rerun()