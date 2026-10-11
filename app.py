import streamlit as st
import fitz  # PyMuPDF
import json
import random
import google.generativeai as genai
from PIL import Image
import io

st.set_page_config(page_title="Petrobangla Exam Prep", layout="wide")

if "question_bank" not in st.session_state:
    st.session_state.question_bank = []

subjects = ["বাংলা", "English", "Math", "General Knowledge"]

st.title("🔥 পেট্রোবাংলা জব প্রিপারেশন ও এআই কোশ্চেন ব্যাংক")

st.sidebar.header("⚙️ এআই সেটআপ")
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.sidebar.text_input("Gemini API Key দিন", type="password", value=st.session_state.api_key)
if api_key_input:
    st.session_state.api_key = api_key_input

menu = st.sidebar.radio("মেনু সিলেক্ট করুন", ["পিডিএফ আপলোড ও প্রশ্ন তৈরি", "প্রশ্ন ব্যাংক", "পরীক্ষা দিন"])

def generate_questions_from_pdf_images(pdf_file, subject, topic, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        pdf_file.seek(0)
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        images = []
        
        # বড় পিডিএফ থেকে বেশি প্রশ্ন পেতে পেজ লিমিট বাড়িয়ে ১৫ পর্যন্ত করা হলো
        for page_num in range(min(len(doc), 15)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("jpeg")
            image = Image.open(io.BytesIO(img_bytes))
            images.append(image)
            
        prompt = f"""
        You are an expert exam question generator for Petrobangla job preparation.
        Analyze the provided book/PDF pages thoroughly and generate 15 multiple-choice questions (MCQs) for the subject "{subject}" and topic "{topic}".
        
        Strictly respond with ONLY a valid JSON array of objects. Do not include markdown code block formatting like ```json ... ```. Just raw JSON text.
        
        Each JSON object must have these exact keys:
        - "question": string (the MCQ question in Bengali or English based on text context)
        - "options": list of 4 strings (options A, B, C, D)
        - "answer": string (must exactly match one of the items in options)
        - "explanation": string (short explanation for the correct answer)
        """
        
        content_payload = [prompt] + images
        response = model.generate_content(content_payload)
        
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        questions = json.loads(cleaned_response)
        
        for q in questions:
            q["subject"] = subject
            q["topic"] = topic
            
        return questions, None
    except Exception as e:
        return None, str(e)

# ----------------- ১. পিডিএফ আপলোড ও প্রশ্ন তৈরি -----------------
if menu == "পিডিএফ আপলোড ও প্রশ্ন তৈরি":
    st.header("📄 বই বা স্ক্যান করা পিডিএফ আপলোড করুন")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_subject = st.selectbox("সাবজেক্ট বেছে নিন", subjects)
    with col2:
        topic_name = st.text_input("টপিকের নাম লিখুন (যেমন: Vocabulary, কারেন্ট অ্যাফেয়ার্স)")
        
    uploaded_file = st.file_uploader("পিডিএফ (PDF) ফাইল আপলোড করুন", type=["pdf"])
    
    if uploaded_file and topic_name:
        st.success(f"ফাইল লোড হয়েছে: {uploaded_file.name}")
        
        if st.button("🤖 Gemini AI দিয়ে ছবি/টেキスト থেকে প্রশ্ন তৈরি করুন"):
            if not st.session_state.api_key:
                st.error("⚠️ বামপাশের সাইডবারে আপনার Gemini API Key প্রদান করুন!")
            else:
                with st.spinner("Gemini AI বইয়ের পৃষ্ঠাগুলো স্ক্যান করে এক সাথে অনেকগুলো প্রশ্ন তৈরি করছে... একটু সময় লাগতে পারে..."):
                    qs, err = generate_questions_from_pdf_images(uploaded_file, selected_subject, topic_name, st.session_state.api_key)
                    if err:
                        st.error(f"প্রশ্ন জেনারেট করতে ত্রুটি ঘটেছে: {err}")
                    else:
                        st.session_state.question_bank.extend(qs)
                        st.success(f"🎉 সফলভাবে Gemini AI থেকে {len(qs)} টি নতুন প্রশ্ন ব্যাংক-এ জমা হয়েছে!")

# ----------------- ২. প্রশ্ন ব্যাংক -----------------
elif menu == "প্রশ্ন ব্যাংক":
    st.header("📚 প্রশ্ন ব্যাংক (Question Bank)")
    
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        sub_filter = st.selectbox("সাবজেক্ট ফিল্টার করুন", ["সব"] + subjects)
    with col_f2:
        if st.button("🗑️ সকল প্রশ্ন মুছে ফেলুন", type="primary"):
            st.session_state.question_bank = []
            st.rerun()
            
    filtered_qs = [
        (idx, q) for idx, q in enumerate(st.session_state.question_bank)
        if sub_filter == "সব" or q["subject"] == sub_filter
    ]
    
    st.write(f"মোট প্রশ্ন আছে: **{len(filtered_qs)}** টি")
    
    for idx, q in filtered_qs:
        with st.expander(f"প্রশ্ন {idx+1}: [{q['subject']} - {q['topic']}] {q['question']}"):
            c1, c2 = st.columns([4, 1])
            with c1:
                for opt in q['options']:
                    st.write(f"- {opt}")
                st.write(f"**সঠিক উত্তর:** {q['answer']}")
                st.caption(f"💡 ব্যাখ্যা: {q.get('explanation', 'কোন ব্যাখ্যা নেই')}")
            with c2:
                if st.button("🗑️ প্রশ্নটি মুছুন", key=f"del_{idx}"):
                    st.session_state.question_bank.pop(idx)
                    st.success("প্রশ্নটি মুছে ফেলা হয়েছে!")
                    st.rerun()

# ----------------- ৩. পরীক্ষা দিন -----------------
elif menu == "পরীক্ষা দিন":
    st.header("📝 মডেল টেস্ট / পরীক্ষা দিন")
    
    if not st.session_state.question_bank:
        st.warning("প্রশ্ন ব্যাংকে কোনো প্রশ্ন নেই! আগে পিডিএফ আপলোড করে প্রশ্ন জেনারেট করুন।")
    else:
        exam_sub = st.selectbox("কোন সাবজেক্টের ওপর পরীক্ষা দিবেন?", ["সকল সাবজেক্ট (মডেল টেস্ট)"] + subjects)
        
        available_pool = st.session_state.question_bank
        if exam_sub != "সকল সাবজেক্ট (মডেল টেস্ট)":
            available_pool = [q for q in available_pool if q["subject"] == exam_sub]
            
        max_q = max(1, len(available_pool))
        num_q = st.number_input("কতটি প্রশ্ন নিয়ে পরীক্ষা দিতে চান?", min_value=1, max_value=max_q, value=min(10, max_q))
        
        if st.button("পরীক্ষা শুরু করুন"):
            if len(available_pool) == 0:
                st.error("এই সাবজেক্টে এখনো কোনো প্রশ্ন যোগ করা হয়নি!")
            else:
                exam_questions = random.sample(available_pool, min(num_q, len(available_pool)))
                st.session_state["current_exam"] = exam_questions
                st.session_state["user_answers"] = {}
                
        if "current_exam" in st.session_state and st.session_state["current_exam"]:
            st.subheader("আপনার প্রশ্নপত্র:")
            with st.form("exam_form"):
                for idx, q in enumerate(st.session_state["current_exam"]):
                    st.write(f"**প্রশ্ন {idx+1}:** {q['question']} *(বিষয়: {q['subject']} | টপিক: {q['topic']})*")
                    st.session_state["user_answers"][idx] = st.radio(
                        f"উত্তর বেছে নিন ({idx+1}):", 
                        q['options'], 
                        key=f"q_{idx}"
                    )
                    st.markdown("---")
                
                submitted = st.form_submit_button("পরীক্ষা জমা দিন (Submit)")
                
            if submitted:
                score = 0
                st.subheader("📊 পরীক্ষার ফলাফল:")
                for idx, q in enumerate(st.session_state["current_exam"]):
                    user_ans = st.session_state["user_answers"].get(idx)
                    if user_ans == q['answer']:
                        score += 1
                        st.success(f"প্রশ্ন {idx+1}: সঠিক হয়েছে! ({user_ans})")
                    else:
                        st.error(f"প্রশ্ন {idx+1}: ভুল হয়েছে! আপনার উত্তর: {user_ans} | সঠিক উত্তর: {q['answer']}")
                    st.info(f"💡 ব্যাখ্যা: {q.get('explanation', 'কোন ব্যাখ্যা নেই')}")
                    
                st.balloons()
                st.metric("আপনার স্কোর", f"{score} / {len(st.session_state['current_exam'])}")
