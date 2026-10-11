import streamlit as st
import fitz  # PyMuPDF for PDF text extraction
import json
import random

st.set_page_config(page_title="Petrobangla Exam Prep", layout="wide")

# Session state initialization
if "question_bank" not in st.session_state:
    st.session_state.question_bank = []

subjects = ["বাংলা", "English", "Math", "General Knowledge"]

st.title("🔥 পেট্রোবাংলা জব প্রিপারেশন ও এআই কোশ্চেন ব্যাংক")

menu = st.sidebar.radio("মেনু সিলেক্ট করুন", ["পিডিএফ আপলোড ও প্রশ্ন তৈরি", "প্রশ্ন ব্যাংক", "পরীক্ষা দিন"])

# ----------------- ১. পিডিএফ আপলোড ও প্রশ্ন তৈরি -----------------
if menu == "পিডিএফ আপলোড ও প্রশ্ন তৈরি":
    st.header("📄 টপিক-ভিত্তিক পিডিএফ আপলোড করুন")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_subject = st.selectbox("সাবজেক্ট বেছে নিন", subjects)
    with col2:
        topic_name = st.text_input("টপিকের নাম লিখুন (যেমন: ব্যাকরণ, Algebra, কারেন্ট অ্যাফেয়ার্স)")
        
    uploaded_file = st.file_uploader("পিডিএফ (PDF) বা টেক্সট ফাইল আপলোড করুন", type=["pdf", "txt"])
    
    if uploaded_file and topic_name:
        st.success(f"ফাইল সফলতা সহকারে লোড হয়েছে: {uploaded_file.name}")
        
        # Extract text from PDF
        extracted_text = ""
        if uploaded_file.type == "application/pdf":
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            for page in doc:
                extracted_text += page.get_text()
        else:
            extracted_text = uploaded_file.read().decode("utf-8")
            
        st.subheader("নির্যাসিত টেক্সটের নমুনা:")
        st.text_area("PDF Text", extracted_text[:500] + "...", height=100)
        
        if st.button("🤖 AI দিয়ে প্রশ্ন তৈরি করুন"):
            st.info("AI টেক্সট এনালাইস করে প্রশ্ন তৈরি করছে...")
            
            # নমুনা জেনারেটেড প্রশ্ন (এখানে Gemini API কানেক্ট করে রিয়েল প্রশ্ন আসবে)
            mock_generated_questions = [
                {
                    "subject": selected_subject,
                    "topic": topic_name,
                    "question": f"[{topic_name}] সম্পর্কিত আপলোডকৃত টেক্সট থেকে সংগৃহীত নমুনা প্রশ্ন ১?",
                    "options": ["অপশন A", "অপশন B", "অপশন C", "অপশন D"],
                    "answer": "অপশন A",
                    "explanation": "এটি আপলোডকৃত টেক্সটের ৩ নং প্যারা থেকে সংগৃহীত সঠিক উত্তর।"
                },
                {
                    "subject": selected_subject,
                    "topic": topic_name,
                    "question": f"[{topic_name}] সম্পর্কিত সংগৃহীত নমুনা প্রশ্ন ২?",
                    "options": ["ক্লজ A", "ক্লজ B", "ক্লজ C", "ক্লজ D"],
                    "answer": "ক্লজ B",
                    "explanation": "পিডিএফ এর বিস্তারিত অংশে এটার সঠিক উত্তর উল্লেখ আছে।"
                }
            ]
            
            st.session_state.question_bank.extend(mock_generated_questions)
            st.success(f"সফলভাবে {len(mock_generated_questions)} টি প্রশ্ন ব্যাকএন্ডে সংরক্ষিত হয়েছে!")

# ----------------- ২. প্রশ্ন ব্যাংক -----------------
elif menu == "প্রশ্ন ব্যাংক":
    st.header("📚 প্রশ্ন ব্যাংক (Question Bank)")
    
    sub_filter = st.selectbox("সাবজেক্ট ফিল্টার করুন", ["সব"] + subjects)
    
    filtered_qs = st.session_state.question_bank
    if sub_filter != "সব":
        filtered_qs = [q for q in filtered_qs if q["subject"] == sub_filter]
        
    st.write(f"মোট প্রশ্ন আছে: **{len(filtered_qs)}** টি")
    
    for idx, q in enumerate(filtered_qs):
        with st.expander(f"প্রশ্ন {idx+1}: [{q['subject']} - {q['topic']}] {q['question']}"):
            for opt in q['options']:
                st.write(f"- {opt}")
            st.write(f"**সঠিক উত্তর:** {q['answer']}")
            st.caption(f"ব্যাখ্যা: {q['explanation']}")

# ----------------- ৩. পরীক্ষা দিন -----------------
elif menu == "পরীক্ষা দিন":
    st.header("📝 মডেল টেস্ট / পরীক্ষা দিন")
    
    if not st.session_state.question_bank:
        st.warning("প্রশ্ন ব্যাংকে কোনো প্রশ্ন নেই! আগে পিডিএফ আপলোড করে প্রশ্ন জেনারেট করুন।")
    else:
        exam_sub = st.selectbox("কোন সাবজেক্টের ওপর পরীক্ষা দিবেন?", ["সকল সাবজেক্ট (মডেল টেস্ট)"] + subjects)
        num_q = st.number_input("কতটি প্রশ্ন নিয়ে পরীক্ষা দিতে চান?", min_value=1, max_value=max(1, len(st.session_state.question_bank)), value=min(5, len(st.session_state.question_bank)))
        
        if st.button("পরীক্ষা শুরু করুন"):
            pool = st.session_state.question_bank
            if exam_sub != "সকল সাবজেক্ট (মডেল টেস্ট)":
                pool = [q for q in pool if q["subject"] == exam_sub]
                
            if len(pool) == 0:
                st.error("এই সাবজেক্টে এখনো কোনো প্রশ্ন যোগ করা হয়নি!")
            else:
                exam_questions = random.sample(pool, min(num_q, len(pool)))
                st.session_state["current_exam"] = exam_questions
                st.session_state["answers"] = {}
                
        if "current_exam" in st.session_state:
            st.subheader("আপনার প্রশ্নপত্র:")
            with st.form("exam_form"):
                for idx, q in enumerate(st.session_state["current_exam"]):
                    st.write(f"**প্রশ্ন {idx+1}:** {q['question']} *(বিষয়: {q['subject']} | টপিক: {q['topic']})*")
                    st.session_state["answers"][idx] = st.radio(f"উত্তর বেছে নিন ({idx+1}):", q['options'], key=f"q_{idx}")
                    st.markdown("---")
                
                submitted = st.form_submit_button("পরীক্ষা জমা দিন (Submit)")
                
            if submitted:
                score = 0
                st.subheader("📊 পরীক্ষার ফলাফল:")
                for idx, q in enumerate(st.session_state["current_exam"]):
                    user_ans = st.session_state["answers"].get(idx)
                    if user_ans == q['answer']:
                        score += 1
                        st.success(f"প্রশ্ন {idx+1}: সঠিক হয়েছে! ({user_ans})")
                    else:
                        st.error(f"প্রশ্ন {idx+1}: ভুল হয়েছে! আপনার উত্তর: {user_ans} | সঠিক উত্তর: {q['answer']}")
                    st.info(f"💡 ব্যাখ্যা: {q['explanation']}")
                    
                st.balloons()
                st.metric("আপনার স্কোর", f"{score} / {len(st.session_state['current_exam'])}")