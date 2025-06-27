import streamlit as st
import boto3
import json

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
# Function to fetch quote from Bedrock using Llama 3
# -------------------------------
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
        data = json.loads(response_body["generation"])
        return data["quote"], data["source"]
    except Exception as e:
        st.error("⚠️ LLM response format issue. Showing fallback quote.")
        print("Error parsing model output:", e)
        return "Technology shapes the mind, but humanity shapes the purpose.", "AI"

# -------------------------------
# Streamlit session state setup
# -------------------------------
if "score" not in st.session_state:
    st.session_state.score = 0
    st.session_state.total = 0
if "quote" not in st.session_state:
    quote, source = get_custom_quote(age_group, preference)
    st.session_state.quote = quote
    st.session_state.source = source
    st.session_state.answered = False

# -------------------------------
# Display quote and get user guess
# -------------------------------
st.markdown(f"### 📝 \"{st.session_state.quote}\"")
choice = st.radio("Who said it?", ["AI", "Human"], key="guess")

# -------------------------------
# Submit and evaluate
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
        quote, source = get_custom_quote(age_group, preference)
        st.session_state.quote = quote
        st.session_state.source = source
        st.session_state.answered = False
        st.rerun()
