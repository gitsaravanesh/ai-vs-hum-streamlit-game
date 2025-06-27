import streamlit as st
import boto3
import json
import os

# Set page config
st.set_page_config(page_title="Who Said It: AI or Human?", page_icon="🧠")

st.title("🧠 Who Said It: AI or Human?")
st.subheader("Pick your style and guess whether the quote is written by AI or a Human!")

# Dropdowns to personalize quote
age_group = st.selectbox("Select your age group", ["Under 18", "18-25", "26-40", "41-60", "60+"])
preference = st.selectbox("Pick your quote preference", ["Technology", "Motivational", "Humor", "Philosophy", "Life Advice"])

# Initialize Bedrock client using Streamlit secrets or env vars
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", st.secrets.get("AWS_ACCESS_KEY_ID")),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", st.secrets.get("AWS_SECRET_ACCESS_KEY"))
)

# Function to get quote from Llama 3
def get_custom_quote(age_group, preference):
    prompt = f"Generate one quote for a user aged {age_group} who prefers {preference}. Respond strictly in JSON like this:\n{{\n  \"quote\": \"The quote text\",\n  \"source\": \"AI\" or \"Human\"\n}}"

    body = {
        "messages": [
            {
                "role": "system",
                "content": "You are an assistant that only generates short quotes for a guessing game called 'Who Said It: AI or Human?'."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 300,
        "temperature": 0.9,
        "top_p": 0.9
    }

    response = bedrock.invoke_model(
        modelId="meta.llama3-8b-instruct-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )

    response_body = json.loads(response['body'].read())
    try:
        # Parse only the model's reply
        result = json.loads(response_body["generation"])
        return result["quote"], result["source"]
    except Exception as e:
        print("Error parsing:", e)
        return "Unable to get a valid quote. Try again!", "AI"

# Session state init
if "score" not in st.session_state:
    st.session_state.score = 0
    st.session_state.total = 0
if "quote" not in st.session_state:
    quote, source = get_custom_quote(age_group, preference)
    st.session_state.quote = quote
    st.session_state.source = source
    st.session_state.answered = False

# Show quote
st.markdown(f"### 📝 \"{st.session_state.quote}\"")
choice = st.radio("Who said it?", ["AI", "Human"], key="guess")

# Handle answer
if st.button("Submit Answer") and not st.session_state.answered:
    st.session_state.total += 1
    st.session_state.answered = True
    if choice == st.session_state.source:
        st.success("✅ Correct!")
        st.session_state.score += 1
    else:
        st.error(f"❌ Nope! It was actually {st.session_state.source}")
    st.markdown(f"### 🎯 Score: {st.session_state.score}/{st.session_state.total}")

# Load next quote
if st.session_state.answered:
    if st.button("Next Quote"):
        quote, source = get_custom_quote(age_group, preference)
        st.session_state.quote = quote
        st.session_state.source = source
        st.session_state.answered = False
        st.rerun()
