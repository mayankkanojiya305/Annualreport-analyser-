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

st.set_page_config(page_title="Fin-Analyzer Pro", layout="wide")
st.title("📊 Financial Report Visualizer (Pro Mode)")
st.subheader("Upload any Detailed Annual Report (PDF)")

uploaded_file = st.file_uploader("Choose a PDF report", type=['pdf'])

if uploaded_file is not None:
    # 384 pages padhne mein time lagega, isliye spinner text change kiya hai
    with st.spinner("AI puri report (saare pages) deep scan kar raha hai... Badi PDF mein 1-2 minute lag sakte hain ⏳"):
        try:
            # 1. PDF se Text nikalna (Ab hum SAARE pages padhenge, 10 nahi)
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            total_pages = len(pdf_reader.pages)
            for page in range(total_pages): 
                text += pdf_reader.pages[page].extract_text() + "\n"
            
            # 2. Auto-Detect Available Model
            best_model = None
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    best_model = m.name
                    break
            
            if best_model is None:
                st.error("Aapki API key par koi active model nahi mila.")
            else:
                model = genai.GenerativeModel(best_model)
                
                # 3. STRICT PROMPT (Taaki kachra data na aaye)
                prompt = f"""
                You are an expert financial analyst. Read this text from an annual report.
                Extract the key financial metrics for the latest financial year. 
                I need exact numbers (in Crores or Millions as mentioned in the report).
                Give me ONLY a valid JSON format with these specific keys:
                "Total Revenue", "Cost of Goods Sold (COGS)", "Employee Cost", "Marketing & Advertising", "Other Operational Expenses", "EBITDA", "Net Profit/Loss".
                If a specific metric is not explicitly found, estimate it from available data or put 0.
                Return ONLY valid JSON. No markdown, no extra text.
                Text: {text}
                """
                
                response = model.generate_content(prompt)
                
                # 4. JSON saaf karna
                json_str = response.text.strip().replace("```json", "").replace("```", "")
                metrics = json.loads(json_str)
                
                # Table banana
                df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Amount'])
                
                st.success(f"Deep Analysis Complete! ✅ ({total_pages} pages scanned)")
                
                col1, col2 = st.columns([1, 2]) # Graph ko zyada jagah di hai
                
                with col1:
                    st.write("### 📝 Detailed Metrics")
                    st.dataframe(df)
                    
                with col2:
                    st.write("### 📊 Financial Breakdown (Bar Chart)")
                    # Pie chart hata kar Bar chart lagaya hai taaki clear dikhe
                    fig = px.bar(df, x='Metric', y='Amount', text='Amount', 
                                 title="Revenue vs Expenses vs Profit",
                                 color='Metric')
                    fig.update_traces(textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Data extract karne mein problem aayi. Error: {e}")
            
