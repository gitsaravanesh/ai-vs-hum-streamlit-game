import streamlit as st
import boto3
import json
import re

# -------------------------------
# Page configuration
# -------------------------------
st.set_page_config(page_title="Who Said It: AI or Human?", page_icon="🧠")

st.title("🧠 Who Said It: AI or Human?")
st.subheader("Pick your style and guess whether the quote is written by AI or a Human!")

# -------------------------------
# Initialize session state
# -------------------------------
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "score" not in st.session_state:
    st.session_state.score = 0
if "total" not in st.session_state:
    st.session_state.total = 0
if "quote" not in st.session_state:
    st.session_state.quote = ""
if "source" not in st.session_state:
    st.session_state.source = ""
if "answered" not in st.session_state:
    st.session_state.answered = False
if "load_new_quote" not in st.session_state:
    st.session_state.load_new_quote = False
if "previous_quote" not in st.session_state:
    st.session_state.previous_quote = ""

# -------------------------------
# User input for personalization
# -------------------------------
age_group = st.selectbox("Select your age group", ["Under 18", "18-25", "26-40", "41-60", "60+"])
preference = st.selectbox("Pick your quote preference", ["Technology", "Motivational", "Humor", "Philosophy", "Life Advice"])

# -------------------------------
# Start game button
# -------------------------------
if not st.session_state.game_started:
    if st.button("Start Game"):
        st.session_state.game_started = True
        st.session_state.load_new_quote = True
    st.stop()

# -------------------------------
# Bedrock client (from secrets)
# -------------------------------
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=st.secrets["AWS_REGION"],
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
)

# -------------------------------
# Extract JSON from LLM output
# -------------------------------
def extract_json_from_text(text):
    try:
        json_str = re.search(r"\{.*?\}", text, re.DOTALL).group(0)
        parsed = json.loads(json_str)
        if "quote" in parsed and "source" in parsed:
            return parsed
    except Exception:
        pass
    return {"quote": "", "source": ""}

# -------------------------------
# Get quote from Bedrock with retries and uniqueness check
# -------------------------------
def get_custom_quote(age_group, preference, max_retries=5):
    prompt = (
        f"You are an assistant that generates short quotes for a guessing game. "
        f"Randomly choose to either write your own quote as an AI, "
        f"or select a real quote from a known human. Do not say who wrote it. "
        f"Respond strictly in this JSON format:\n"
        f'{{\n  "quote": "The quote text",\n  "source": "AI" or "Human"\n}}\n\n'
        f"Topic: {preference}\nAge group: {age_group}"
    )

    body = {
        "prompt": prompt,
        "max_gen_len": 300,
        "temperature": 0.9,
        "top_p": 0.9
    }

    for _ in range(max_retries):
        try:
            response = bedrock.invoke_model(
                modelId="meta.llama3-8b-instruct-v1:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            response_body = json.loads(response['body'].read())
            generation = response_body.get("generation", "")
            parsed = extract_json_from_text(generation)

            quote = parsed.get("quote", "").strip()
            source = parsed.get("source", "")

            if quote and source in ["AI", "Human"] and quote != st.session_state.previous_quote:
                st.session_state.previous_quote = quote
                return quote, source
        except Exception:
            continue

    return "When circuits dream, wisdom awakens.", "AI"

# -------------------------------
# Load a new quote if needed
# -------------------------------
if st.session_state.load_new_quote:
    with st.spinner("💡 Generating a mysterious quote..."):
        quote, source = get_custom_quote(age_group, preference)
        st.session_state.quote = quote
        st.session_state.source = source
        st.session_state.load_new_quote = False
        st.session_state.answered = False

# -------------------------------
# Display quote
# -------------------------------
if st.session_state.quote:
    st.markdown(f"### 📝 \"{st.session_state.quote}\"")
else:
    st.warning("⚠️ No quote available. Try clicking 'Next Quote' again.")
    st.stop()

# -------------------------------
# User guess input
# -------------------------------
choice = st.radio("Who said it?", ["AI", "Human"], key=f"guess_{st.session_state.total}")

# -------------------------------
# Submit answer
# -------------------------------
if st.button("Submit Answer") and not st.session_state.answered:
    st.session_state.total += 1
    st.session_state.answered = True
    if choice == st.session_state.source:
        st.success("✅ Correct!")
        st.session_state.score += 1
    else:
        st.error(f"❌ Nope! It was actually {st.session_state.source}")
    st.markdown(f"### 🎯 Score: {st.session_state.score}/{st.session_state.total}")

# -------------------------------
# Next quote
# -------------------------------
if st.session_state.answered:
    if st.button("Next Quote"):
        st.session_state.load_new_quote = True
        st.rerun()