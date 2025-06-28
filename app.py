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
if "author" not in st.session_state:
    st.session_state.author = ""
if "answered" not in st.session_state:
    st.session_state.answered = False
if "load_new_quote" not in st.session_state:
    st.session_state.load_new_quote = False
if "recent_quotes" not in st.session_state:
    st.session_state.recent_quotes = []

# -------------------------------
# User input for personalization
# -------------------------------
age_group = st.selectbox("Select your age group", ["Under 18", "18-25", "26-40", "41-60", "60+"])
preference = st.selectbox("Pick your quote preference", ["Technology", "Motivational", "Humor", "Philosophy", "Life Advice"])

# -------------------------------
# Stop after 10 questions
# -------------------------------
if st.session_state.total >= 10:
    st.markdown("## 🎉 Thanks for participating!")
    st.markdown(f"### Your Final Score: **{st.session_state.score}/10**")
    st.stop()

# -------------------------------
# Start game
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
    return {"quote": "", "source": "", "author": ""}

# -------------------------------
# Get quote from Bedrock
# -------------------------------
def get_custom_quote(age_group, preference, max_retries=5):
    prompt = (
        f"You are playing a guessing game. Randomly choose:\n"
        f"- If AI: invent a short quote yourself.\n"
        f'- If Human: use a real quote said by a real person and return the author\'s name.\n\n'
        f"Respond strictly in this JSON format:\n"
        f'{{\n  "quote": "text here",\n  "source": "AI" or "Human",\n  "author": "name or None"\n}}\n\n'
        f"Do not include anything else in your response.\n\n"
        f"Topic: {preference}\nAudience Age Group: {age_group}"
    )

    body = {
        "prompt": prompt,
        "max_gen_len": 300,
        "temperature": 1.0,
        "top_p": 1.0
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
            author = parsed.get("author", "").strip()

            if (
                quote and
                source in ["AI", "Human"] and
                quote not in st.session_state.recent_quotes
            ):
                st.session_state.recent_quotes.append(quote)
                if len(st.session_state.recent_quotes) > 10:
                    st.session_state.recent_quotes.pop(0)
                return quote, source, author
        except Exception:
            continue

    # fallback
    return "When circuits dream, wisdom awakens.", "AI", "None"

# -------------------------------
# Load new quote
# -------------------------------
if st.session_state.load_new_quote:
    with st.spinner("💡 Generating a mysterious quote..."):
        quote, source, author = get_custom_quote(age_group, preference)
        st.session_state.quote = quote
        st.session_state.source = source
        st.session_state.author = author
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

    if st.session_state.source == "Human" and st.session_state.author and st.session_state.author.lower() != "none":
        st.info(f"👤 Quote by: **{st.session_state.author}**")

    st.markdown(f"### 🎯 Score: {st.session_state.score}/{st.session_state.total}")

# -------------------------------
# Next quote
# -------------------------------
if st.session_state.answered:
    if st.button("Next Quote"):
        st.session_state.load_new_quote = True
        st.rerun()
