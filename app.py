import streamlit as st

st.title("🚀 Tech Quiz Challenge")
st.subheader("Can you crack these AWS & DevOps questions?")

questions = [
    {
        "q": "Which AWS service is used for object storage?",
        "options": ["EC2", "Lambda", "S3", "RDS"],
        "answer": "S3"
    },
    {
        "q": "Which tool is best for Infrastructure as Code?",
        "options": ["Ansible", "Terraform", "Jenkins", "Docker"],
        "answer": "Terraform"
    },
    {
        "q": "Which command initializes a new Git repo?",
        "options": ["git init", "git start", "git create", "git push"],
        "answer": "git init"
    },
]

score = 0
for i, item in enumerate(questions):
    st.markdown(f"**Q{i+1}: {item['q']}**")
    answer = st.radio("Choose one:", item['options'], key=f"q{i}")
    if st.button(f"Submit Q{i+1}", key=f"btn{i}"):
        if answer == item['answer']:
            st.success("Correct!")
            score += 1
        else:
            st.error("Oops! That's not right.")

st.markdown(f"### ✅ Your Score: {score}/{len(questions)}")
