import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import PyPDF2
import json
import re

# API Key setup
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("API Key not found in Secrets!")

st.set_page_config(page_title="Fin-Analyzer Ultra", layout="wide", page_icon="📈")
st.title("📈 Advanced Financial Dashboard")
st.markdown("Upload a detailed Annual/Quarterly Report to extract deep financial metrics and insights.")

uploaded_file = st.file_uploader("Choose a PDF report", type=['pdf'])

if uploaded_file is not None:
    with st.spinner("AI puri report ka deep scan kar raha hai (Isme 1-2 minute lag sakte hain)... ⏳"):
        try:
            # 1. Extract Text
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            total_pages = len(pdf_reader.pages)
            for page in range(total_pages): 
                text += pdf_reader.pages[page].extract_text() + "\n"
            
            # 2. Find best model
            best_model = None
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
                    best_model = m.name # Use Flash model for large context
                    break
            if not best_model:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        best_model = m.name
                        break
            
            model = genai.GenerativeModel(best_model)
            
            # 3. HIGHLY DETAILED PROMPT
            prompt = f"""
            You are a top-tier Equity Research Analyst. Read this annual report carefully.
            Extract maximum possible financial details and key insights.
            Return ONLY a valid JSON object matching exactly this structure:
            {{
                "Financial_Overview": {{"Total Revenue": 0, "Total Expenses": 0, "EBITDA": 0, "Net Profit/Loss": 0}},
                "Expense_Deep_Dive": {{"COGS/Material Cost": 0, "Employee Benefits": 0, "Marketing & Promotion": 0, "Delivery/Platform Charges": 0, "Technology/Server Cost": 0, "Other Ops Expenses": 0}},
                "Key_Insights": ["Insight 1 about growth", "Insight 2 about margins", "Insight 3 about future outlook"]
            }}
            Use actual numbers (in Crores/Millions as in report). If a specific expense is not found, estimate from available data or put 0.
            Text: {text}
            """
            
            response = model.generate_content(prompt)
            
            # 4. Robust JSON Extraction
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                json_str = response.text.replace("```json", "").replace("```", "")
                
            data = json.loads(json_str)
            
            st.success(f"Deep Analysis Complete! ✅ Scanned {total_pages} pages.")
            
            # --- DASHBOARD UI ---
            
            # Top KPI Cards
            overview = data.get("Financial_Overview", {})
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Revenue", f"{overview.get('Total Revenue', 0)}")
            col2.metric("Total Expenses", f"{overview.get('Total Expenses', 0)}")
            col3.metric("EBITDA", f"{overview.get('EBITDA', 0)}")
            col4.metric("Net Profit / Loss", f"{overview.get('Net Profit/Loss', 0)}")
            
            st.markdown("---")
            
            # Tabs for detailed visualisations
            tab1, tab2, tab3 = st.tabs(["📊 Financial Breakdown", "🍩 Expense Deep Dive", "💡 Key Insights from Report"])
            
            with tab1:
                st.subheader("Revenue vs Expenses vs Profit")
                df_overview = pd.DataFrame(list(overview.items()), columns=['Metric', 'Amount'])
                fig1 = px.bar(df_overview, x='Metric', y='Amount', text='Amount', color='Metric')
                st.plotly_chart(fig1, use_container_width=True)
                
            with tab2:
                st.subheader("Where is the money going? (Expense Breakdown)")
                expenses = data.get("Expense_Deep_Dive", {})
                df_exp = pd.DataFrame(list(expenses.items()), columns=['Expense Category', 'Amount'])
                # Filtering out 0 values for cleaner chart
                df_exp = df_exp[df_exp['Amount'] > 0] 
                
                col_pie, col_table = st.columns([2, 1])
                with col_pie:
                    fig2 = px.pie(df_exp, values='Amount', names='Expense Category', hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)
                with col_table:
                    st.dataframe(df_exp, hide_index=True)
                    
            with tab3:
                st.subheader("Top Takeaways (No need to read the report)")
                insights = data.get("Key_Insights", [])
                for i, insight in enumerate(insights):
                    st.info(f"**{i+1}.** {insight}")

        except Exception as e:
            st.error(f"Data extract karne mein problem aayi. Error: {e}")
            
