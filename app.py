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
# User input for personalization
# -------------------------------
age_group = st.selectbox("Select your age group", ["Under 18", "18-25", "26-40", "41-60", "60+"])
preference = st.selectbox("Pick your quote preference", ["Technology", "Motivational", "Humor", "Philosophy", "Life Advice"])

# -------------------------------
# Initialize Bedrock client using secrets
# -------------------------------
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=st.secrets["AWS_REGION"],
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
)

# -------------------------------
# Utility: Extract JSON from messy output
# -------------------------------
def extract_json_from_text(text):
    try:
        json_str = re.search(r"\{.*?\}", text, re.DOTALL).group(0)
        return json.loads(json_str)
    except Exception as e:
        st.error("⚠️ Could not extract valid JSON from model output.")
        st.write("🧨 JSON parsing error:", str(e))
        st.write("📝 Full model response:", text)
        return {"quote": "The mind dreams. The machine delivers.", "source": "AI"}

# -------------------------------
# Function to fetch quote from Llama 3
# -------------------------------
def get_custom_quote(age_group, preference):
    prompt = (
        f"You are an assistant that only generates short quotes for a game. "
        f"Generate ONE quote for a user aged {age_group} who prefers {preference}. "
        f"Respond strictly in JSON like this:\n"
        f'{{\n  "quote": "The quote text",\n  "source": "AI" or "Human"\n}}'
    )

    body = {
        "prompt": prompt,
        "max_gen_len": 300,
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
        generation = response_body.get("generation")

        if not generation:
            raise ValueError("Missing 'generation' key in response")

        parsed = extract_json_from_text(generation)
        return parsed["quote"], parsed["source"]

    except Exception as e:
        st.error("⚠️ Failed to get or parse quote from LLM.")
        st.write("🧨 Exception:", str(e))
        return "Fallback: The future belongs to those who dare to guess.", "AI"

# -------------------------------
# Session state initialization
# -------------------------------
if "score" not in st.session_state:
    st.session_state.score = 0
    st.session_state.total = 0
if "quote" not in st.session_state:
    st.session_state.quote = ""
    st.session_state.source = ""
if "answered" not in st.session_state:
    st.session_state.answered = False
if "load_new_quote" not in st.session_state:
    st.session_state.load_new_quote = True

# -------------------------------
# Load a new quote if needed
# -------------------------------
if st.session_state.load_new_quote:
    quote, source = get_custom_quote(age_group, preference)
    st.session_state.quote = quote
    st.session_state.source = source
    st.session_state.load_new_quote = False
    st.session_state.answered = False

# -------------------------------
# Display quote and user input
# -------------------------------
st.markdown(f"### 📝 \"{st.session_state.quote}\"")
choice = st.radio("Who said it?", ["AI", "Human"], key="guess")

# -------------------------------
# Evaluate guess
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
# Next quote button
# -------------------------------
if st.session_state.answered:
    if st.button("Next Quote"):
        st.session_state.load_new_quote = True
        st.rerun()
