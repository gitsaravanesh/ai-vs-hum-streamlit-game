import streamlit as st
import random

st.set_page_config(page_title="Who Said It: AI or Human?", page_icon="🧠")

st.title("🧠 Who Said It: AI or Human?")
st.subheader("Guess whether the quote is written by an AI or a Human!")

# Sample quotes
quotes = [
    {
        "text": "The greatest glory in living lies not in never falling, but in rising every time we fall.",
        "source": "Human",
        "by": "Nelson Mandela"
    },
    {
        "text": "As an intelligent machine, I aim to replicate human creativity but lack genuine emotion.",
        "source": "AI",
        "by": "GPT-3"
    },
    {
        "text": "Sometimes, silence is the loudest scream.",
        "source": "Human",
        "by": "Anonymous Poet"
    },
    {
        "text": "Dreams are not bound by physical laws or limited by logic; they are the blueprints of possibility.",
        "source": "AI",
        "by": "ChatGPT"
    },
    {
        "text": "If I could feel, I imagine curiosity would be my favorite emotion.",
        "source": "AI",
        "by": "Claude AI"
    },
    {
        "text": "To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.",
        "source": "Human",
        "by": "Ralph Waldo Emerson"
    }
]

# Initialize session state
if "score" not in st.session_state:
    st.session_state.score = 0
    st.session_state.total = 0
if "current_quote" not in st.session_state:
    st.session_state.current_quote = random.choice(quotes)
if "answered" not in st.session_state:
    st.session_state.answered = False

quote = st.session_state.current_quote
st.markdown(f"### 📝 \"{quote['text']}\"")
choice = st.radio("Who said it?", ["AI", "Human"])

if st.button("Submit Answer") and not st.session_state.answered:
    st.session_state.total += 1
    st.session_state.answered = True
    if choice == quote["source"]:
        st.success(f"✅ Correct! It was {quote['source']} - {quote['by']}")
        st.session_state.score += 1
    else:
        st.error(f"❌ Oops! It was actually {quote['source']} - {quote['by']}")

    st.markdown(f"### 🎯 Score: {st.session_state.score}/{st.session_state.total}")

if st.session_state.answered:
    if st.button("Try Another"):
        st.session_state.current_quote = random.choice(quotes)
        st.session_state.answered = False
        st.experimental_rerun()
