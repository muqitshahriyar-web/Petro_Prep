import streamlit as st
import fitz  # PyMuPDF
import json
import os
import random
import google.generativeai as genai
from PIL import Image
import io

st.set_page_config(page_title="Petrobangla Exam Prep", layout="wide")

# Persistent storage file name
DB_FILE = "question_bank.json"

# Load question bank from local file if exists
if "question_bank" not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                st.session_state.question_bank = json.load(f)
        except:
            st.session_state.question_bank = []
    else:
        st.session_state.question_bank = []

def save_question_bank():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.question_bank, f, ensure_ascii=False, indent=4)

subjects = ["বাংলা", "English", "Math", "General Knowledge"]

st.title("🔥 পেট্রোবাংলা জব প্রিপারেশন ও এআই কোশ্চেন ব্যাংক")

st.sidebar.header("⚙️ এআই সেটআপ")
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.sidebar.text_input("Gemini API Key দিন", type="password", value=st.session_state.api_key)
if api_key_input:
    st.session_state.api_key = api_key_input

menu = st.sidebar.radio("মেনু সিলেক্ট করুন", ["পিডিএফ আপলোড ও প্রশ্ন তৈরি", "প্রশ্ন ব্যাংক", "পরীক্ষা দিন"])

def generate_questions_from_pdf_images(pdf_file, subject, topic, api_key, existing_questions):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3.8-flash')
        
        pdf_file.seek(0)
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        images = []
        
        for page_num in range(min(len(doc), 20)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("jpeg")
            image = Image.open(io.BytesIO(img_bytes))
            images.append(image)
            
        existing_q_texts = [q["question"] for q in existing_questions if q.get("topic") == topic]
        avoid_text = ""
        if existing_q_texts:
            avoid_text = f"Do NOT repeat these already generated questions: {json.dumps(existing_q_texts[-30:], ensure_ascii=False)}"

        prompt = f"""
        You are an expert exam question generator for Petrobangla job preparation.
        Analyze the provided book/PDF pages thoroughly and generate up to 50 unique multiple-choice questions (MCQs) for the subject "{subject}" and topic "{topic}".
        {avoid_text}
        
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
    st.markdown("## 📄 বই বা স্ক্যান করা পিডিএফ আপলোড করুন")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_subject = st.selectbox("সাবজেক্ট বেছে নিন", subjects)
    with col2:
        topic_name = st.text_input("টপিকের নাম লিখুন (যেমন: শব্দার্থ, Vocabulary)")
        
    uploaded_file = st.file_uploader("পিডিএফ (PDF) ফাইল আপলোড করুন", type=["pdf"])
    
    if uploaded_file and topic_name:
        st.success(f"ফাইল লোড হয়েছে: {uploaded_file.name}")
        
        if st.button("🤖 Gemini AI দিয়ে সর্বোচ্চ ৫০টি পর্যন্ত নতুন প্রশ্ন তৈরি করুন"):
            if not st.session_state.api_key:
                st.error("⚠️ বামপাশের সাইডবারে আপনার Gemini API Key প্রদান করুন!")
            else:
                with st.spinner("Gemini 3.8 Flash বইয়ের পৃষ্ঠা স্ক্যান করে নতুন ও ইউনিক প্রশ্ন তৈরি করছে... একটু সময় লাগতে পারে..."):
                    qs, err = generate_questions_from_pdf_images(uploaded_file, selected_subject, topic_name, st.session_state.api_key, st.session_state.question_bank)
                    if err:
                        st.error(f"প্রশ্ন জেনারেট করতে ত্রুটি ঘটেছে: {err}")
                    else:
                        existing_questions_set = {q["question"].strip() for q in st.session_state.question_bank}
                        new_added = 0
                        for q in qs:
                            if q["question"].strip() not in existing_questions_set:
                                st.session_state.question_bank.append(q)
                                existing_questions_set.add(q["question"].strip())
                                new_added += 1
                        
                        save_question_bank()
                        st.success(f"🎉 সফলভাবে Gemini AI থেকে নতুন {new_added} টি প্রশ্ন ব্যাংক-এ জমা হয়েছে এবং সেভ করা হয়েছে!")

# ----------------- ২. প্রশ্ন ব্যাংক -----------------
elif menu == "প্রশ্ন ব্যাংক":
    st.markdown("## 📚 প্রশ্ন ব্যাংক (Question Bank)")
    
    available_topics = list(set([q.get("topic", "অন্যান্য") for q in st.session_state.question_bank]))
    
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        sub_filter = st.selectbox("সাবজেক্ট ফিল্টার", ["সব"] + subjects)
    with col_f2:
        topic_filter = st.selectbox("টপিক ফিল্টার", ["সব"] + available_topics)
    with col_f3:
        if st.button("🗑️ সব মুছুন", type="primary"):
            st.session_state.question_bank = []
            save_question_bank()
            st.rerun()
            
    filtered_qs = [
        (idx, q) for idx, q in enumerate(st.session_state.question_bank)
        if (sub_filter == "সব" or q["subject"] == sub_filter) and (topic_filter == "সব" or q.get("topic") == topic_filter)
    ]
    
    st.write(f"মোট প্রশ্ন আছে: **{len(filtered_qs)}** টি")
    
    for idx, q in filtered_qs:
        with st.expander(f"প্রশ্ন {idx+1}: [{q['subject']} - {q.get('topic', 'জেনারেল')}] {q['question']}"):
            c1, c2 = st.columns([4, 1])
            with c1:
                for opt in q['options']:
                    st.write(f"- {opt}")
                st.write(f"**সঠিক উত্তর:** {q['answer']}")
                st.caption(f"💡 ব্যাখ্যা: {q.get('explanation', 'কোন ব্যাখ্যা নেই')}")
            with c2:
                if st.button("🗑️ মুছুন", key=f"del_{idx}"):
                    st.session_state.question_bank.pop(idx)
                    save_question_bank()
                    st.success("প্রশ্নটি মুছে ফেলা হয়েছে!")
                    st.rerun()

# ----------------- ৩. পরীক্ষা দিন -----------------
elif menu == "পরীক্ষা দিন":
    st.markdown("## 📝 মডেল টেস্ট / পরীক্ষা দিন")
    
    if not st.session_state.question_bank:
        st.warning("প্রশ্ন ব্যাংকে কোনো প্রশ্ন নেই! আগে পিডিএফ আপলোড করে প্রশ্ন জেনারেট করুন।")
    else:
        all_topics = list(set([q.get("topic", "অন্যান্য") for q in st.session_state.question_bank]))
        
        exam_mode = st.radio("পরীক্ষার ধরণ নির্বাচন করুন:", ["সাবজেক্ট ভিত্তিক", "নির্দিষ্ট টপিক ভিত্তিক"])
        
        available_pool = st.session_state.question_bank
        
        if exam_mode == "সাবজেক্ট ভিত্তিক":
            exam_sub = st.selectbox("কোন সাবজেক্টের ওপর পরীক্ষা দিবেন?", ["সকল সাবজেক্ট"] + subjects)
            if exam_sub != "সকল সাবজেক্ট":
                available_pool = [q for q in available_pool if q["subject"] == exam_sub]
        else:
            if not all_topics:
                st.warning("কোনো টপিক পাওয়া যায়নি।")
            else:
                selected_topic = st.selectbox("কোন টপিকের ওপর পরীক্ষা দিতে চান?", all_topics)
                available_pool = [q for q in available_pool if q.get("topic") == selected_topic]
            
        max_q = max(1, len(available_pool))
        
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            num_q = st.number_input("কতটি প্রশ্ন নিয়ে পরীক্ষা দিতে চান?", min_value=1, max_value=max_q, value=min(15, max_q))
        with col_e2:
            exam_duration = st.number_input("পরীক্ষার সময় (মিনিট):", min_value=1, max_value=120, value=10)
        
        if st.button("পরীক্ষা শুরু করুন"):
            if len(available_pool) == 0:
                st.error("এই ক্যাটাগরিতে এখনো কোনো প্রশ্ন যোগ করা হয়নি!")
            else:
                exam_questions = random.sample(available_pool, min(num_q, len(available_pool)))
                st.session_state["current_exam"] = exam_questions
                st.session_state["user_answers"] = {}
                st.session_state["exam_duration"] = exam_duration
                
        if "current_exam" in st.session_state and st.session_state["current_exam"]:
            st.info(f"⏱️ নির্ধারিত সময়: **{st.session_state.get('exam_duration', 10)} মিনিট** | মোট প্রশ্ন: **{len(st.session_state['current_exam'])}** টি")
            st.markdown("---")
            
            with st.form("exam_form"):
                for idx, q in enumerate(st.session_state["current_exam"]):
                    st.write(f"**প্রশ্ন {idx+1}:** {q['question']}")
                    
                    # রেডিও বাটনে আগে থেকে টিক থাকা রোধ করতে প্লেসহোল্ডার যোগ করা হয়েছে
                    radio_options = ["--- উত্তর নির্বাচন করুন ---"] + q['options']
                    
                    user_selection = st.radio(
                        f"উত্তর বেছে নিন ({idx+1}):", 
                        radio_options, 
                        key=f"q_{idx}"
                    )
                    
                    st.session_state["user_answers"][idx] = user_selection
                    st.markdown("---")
                
                submitted = st.form_submit_button("পরীক্ষা জমা দিন (Submit)")
                
            if submitted:
                score = 0
                correct_count = 0
                wrong_count = 0
                unanswered_count = 0
                
                st.subheader("📊 পরীক্ষার ফলাফল:")
                for idx, q in enumerate(st.session_state["current_exam"]):
                    user_ans = st.session_state["user_answers"].get(idx)
                    
                    if user_ans == "--- উত্তর নির্বাচন করুন ---":
                        unanswered_count += 1
                        st.warning(f"প্রশ্ন {idx+1}: উত্তর দেননি! সঠিক উত্তর ছিল: **{q['answer']}**")
                    elif user_ans == q['answer']:
                        score += 1
                        correct_count += 1
                        st.success(f"প্রশ্ন {idx+1}: সঠিক হয়েছে! ({user_ans})")
                    else:
                        wrong_count += 1
                        st.error(f"প্রশ্ন {idx+1}: ভুল হয়েছে! আপনার উত্তর: {user_ans} | সঠিক উত্তর: {q['answer']}")
                    
                    st.info(f"💡 ব্যাখ্যা: {q.get('explanation', 'কোন ব্যাখ্যা নেই')}")
                    st.markdown("---")
                    
                st.balloons()
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("প্রাপ্ত স্কোর", f"{score} / {len(st.session_state['current_exam'])}")
                col_m2.metric("সঠিক উত্তর", correct_count)
                col_m3.metric("ভুল / উত্তরহীন", wrong_count + unanswered_count)
