import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import PyPDF2
import json

# API Key setup from Streamlit Secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("API Key not found in Secrets! Please add it in Streamlit settings.")

st.set_page_config(page_title="Fin-Analyzer 13R", layout="wide")
st.title("📊 Financial Report Visualizer")
st.subheader("Upload any Quarterly/Annual Report (PDF)")

uploaded_file = st.file_uploader("Choose a PDF report", type=['pdf'])

if uploaded_file is not None:
    with st.spinner("AI Report padh raha hai... Isme 10-15 seconds lag sakte hain ⏳"):
        try:
            # 1. PDF se Text nikalna
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in range(min(10, len(pdf_reader.pages))): 
                text += pdf_reader.pages[page].extract_text()
            
            # 2. Auto-Detect Available Model (Smart Jugaad)
            best_model = None
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    best_model = m.name
                    break
            
            if best_model is None:
                st.error("Aapki API key par koi active model nahi mila.")
            else:
                model = genai.GenerativeModel(best_model)
                
                # 3. Prompt for AI
                prompt = f"""
                Is financial text ko analyze karo. Mujhe sirf ek valid JSON do jisme company ke main financial metrics ho (jaise Revenue, Marketing Cost, Operations, Net Profit etc.). 
                Sirf JSON format return karna, koi extra text nahi.
                Text: {text}
                """
                
                response = model.generate_content(prompt)
                
                # 4. JSON saaf karna aur extract karna
                json_str = response.text.strip().replace("```json", "").replace("```", "")
                metrics = json.loads(json_str)
                
                # Table aur Graph banana
                df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Amount (approx)'])
                
                st.success(f"Analysis Complete! ✅ (Model used: {best_model})")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### 📝 Extracted Metrics")
                    st.dataframe(df)
                    
                with col2:
                    st.write("### 🍩 Financial Breakdown")
                    fig = px.pie(df, values='Amount (approx)', names='Metric')
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Data extract karne mein problem aayi. Error: {e}")
            
