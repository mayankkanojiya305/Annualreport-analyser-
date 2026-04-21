import streamlit as st
import pandas as pd
import google.generativeai as genai
import PyPDF2
import json
import re

# API Key setup
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("API Key not found in Secrets!")

st.set_page_config(page_title="Fin-Analyzer + AI Chat", layout="wide", page_icon="🤖")
st.title("🧠 Smart Financial Dashboard + AI Chat")

# Session State (Taaki page hilne par ya chat karne par PDF baar-baar upload na karni pade)
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "dashboard_data" not in st.session_state:
    st.session_state.dashboard_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_file" not in st.session_state:
    st.session_state.current_file = ""

def get_best_model():
    # Large PDFs ke liye 'flash' model sabse best aur fast hota hai
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
            return m.name
    return "gemini-pro"

uploaded_file = st.file_uploader("Upload Annual Report (PDF)", type=['pdf'])

if uploaded_file is not None:
    # Nayi file aayi hai toh sirf ek baar process karo
    if st.session_state.current_file != uploaded_file.name:
        st.session_state.current_file = uploaded_file.name
        st.session_state.chat_history = [] # Nayi report daalne par purani chat clear ho jayegi
        
        with st.spinner("AI puri report apne dimaag mein save kar raha hai... ⏳"):
            try:
                # Text nikalna
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in range(len(pdf_reader.pages)): 
                    text += pdf_reader.pages[page].extract_text() + "\n"
                st.session_state.pdf_text = text
                
                # Upar ke dashboard ke liye basic summary nikalna
                model = genai.GenerativeModel(get_best_model())
                prompt = f"""
                Extract basic financial metrics from this report. Return ONLY a valid JSON.
                Format: {{"Total Revenue": 0, "Total Expenses": 0, "EBITDA": 0, "Net Profit/Loss": 0}}
                Text: {text[:100000]} 
                """
                response = model.generate_content(prompt)
                match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if match:
                    st.session_state.dashboard_data = json.loads(match.group(0))
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # --- PART 1: Top Dashboard ---
    if st.session_state.dashboard_data:
        st.write("### 📊 Quick Overview")
        d = st.session_state.dashboard_data
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"{d.get('Total Revenue', 0)}")
        col2.metric("Total Expenses", f"{d.get('Total Expenses', 0)}")
        col3.metric("EBITDA", f"{d.get('EBITDA', 0)}")
        col4.metric("Net Profit/Loss", f"{d.get('Net Profit/Loss', 0)}")
        st.divider()

    # --- PART 2: AI Chat Interface ---
    st.write("### 💬 Chat with the Report")
    st.caption("Pucho report ki deep details: 'Blinkit ka AOV kya tha?', 'Total kitne dark stores open huye?', ya 'CM1 margins batao'")

    # Purani chat screen par dikhane ke liye
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Naya sawal type karne ka box
    if user_q := st.chat_input("Ask any deep detail from the report..."):
        # User ka sawal screen par dikhao
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.markdown(user_q)
        
        # AI ka jawab nikalo
        with st.chat_message("assistant"):
            with st.spinner("Report ke 300+ pages me dhoondh raha hu..."):
                try:
                    chat_model = genai.GenerativeModel(get_best_model())
                    full_prompt = f"""
                    You are a financial analyst. Use the provided annual report text to answer the user's question accurately. 
                    If the exact numbers are not in the text, say you cannot find them. Do not make up numbers.
                    
                    Report Text: {st.session_state.pdf_text}
                    
                    User Question: {user_q}
                    """
                    ans = chat_model.generate_content(full_prompt)
                    st.markdown(ans.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": ans.text})
                except Exception as e:
                    st.error("Jawab dhoondhne mein error aayi. Please try again.")
                    
