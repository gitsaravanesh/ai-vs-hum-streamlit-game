import streamlit as st import boto3 import json import re

-------------------------------

Page config

-------------------------------

st.set_page_config(page_title="Who Said It: AI or Human?", page_icon="🧠") st.title("🧠 Who Said It: AI or Human?") st.subheader("Pick your style and guess whether the quote is written by AI or a Human!")

-------------------------------

Session state setup

-------------------------------

defaults = { "game_started": False, "score": 0, "total": 0, "quotes": [], "current_index": 0, "answered": False, "current_quote": "", "current_source": "" } for key, val in defaults.items(): if key not in st.session_state: st.session_state[key] = val

-------------------------------

User inputs

-------------------------------

age_group = st.selectbox("Select your age group", ["Under 18", "18-25", "26-40", "41-60", "60+"]) preference = st.selectbox("Pick your quote preference", ["Technology", "Motivational", "Humor", "Philosophy", "Life Advice"])

-------------------------------

Bedrock client

-------------------------------

bedrock = boto3.client( service_name="bedrock-runtime", region_name=st.secrets["AWS_REGION"], aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"], aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"] )

-------------------------------

Extract array of quote JSONs from response

-------------------------------

def extract_quotes_array(text): try: match = re.search(r"", text, re.DOTALL) if not match: return [] return json.loads(match.group(0)) except Exception: return []

-------------------------------

Load quotes using one Bedrock call

-------------------------------

def load_quotes_batch(age_group, preference, max_attempts=3): prompt = f""" You are an assistant that generates short, thought-provoking quotes for a guessing game.

Please generate a JSON array of 10 unique quotes. Each quote should be either:

an original quote created by you, the AI

OR a real, famous quote written by a human


Each item in the array should follow this format exactly: {{ "quote": "The actual quote goes here.", "source": "AI" or "Human" }}

Important rules:

Do NOT include any explanation or extra text.

Only output a single JSON array.

Avoid repeating quotes.

Keep each quote under 25 words.


Audience age group: {age_group} Topic of interest: {preference} """

body = {
    "prompt": prompt,
    "max_gen_len": 2000,
    "temperature": 0.9,
    "top_p": 0.9
}

for attempt in range(max_attempts):
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

        valid_quotes = [
            q for q in quotes
            if isinstance(q, dict)
            and "quote" in q
            and "source" in q
            and q["quote"].strip() != ""
            and q["source"] in ["AI", "Human"]
        ]
        if len(valid_quotes) >= 3:
            return valid_quotes[:10]
    except Exception:
        continue

return []

-------------------------------

Start the game

-------------------------------

if not st.session_state.game_started: if st.button("Start Game"): with st.spinner("Getting your first quote..."): st.session_state.quotes = load_quotes_batch(age_group, preference) st.session_state.current_index = 0 st.session_state.total = 0 st.session_state.score = 0 st.session_state.answered = False st.session_state.game_started = True

if not st.session_state.quotes:
        st.warning("⚠️ No quotes loaded. Try again.")
        st.session_state.game_started = False
    else:
        first = st.session_state.quotes[0]
        st.session_state.current_quote = first["quote"]
        st.session_state.current_source = first["source"]
st.stop()

-------------------------------

Display current quote

-------------------------------

st.markdown(f"### 📝 "{st.session_state.current_quote}"")

-------------------------------

Input guess

-------------------------------

choice = st.radio("Who said it?", ["AI", "Human"], key=f"guess_{st.session_state.current_index}")

-------------------------------

Submit guess

-------------------------------

if st.button("Submit Answer") and not st.session

