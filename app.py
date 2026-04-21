import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Fin-Analyzer 13R", layout="wide")

st.title("📊 Financial Report Visualizer")
st.subheader("Upload any Quarterly/Annual Report")

uploaded_file = st.file_uploader("Choose a PDF or CSV file", type=['csv', 'pdf'])

if uploaded_file is not None:
    data = {
        'Metric': ['Revenue', 'Marketing', 'Operations', 'Employee Cost', 'Net Profit'],
        'Amount': [1000, 200, 300, 150, 350]
    }
    df = pd.DataFrame(data)

    fig = px.pie(df, values='Amount', names='Metric', title='Cost Breakdown (Sample)')
    st.plotly_chart(fig, use_container_width=True)
    
    st.success("Analysis Complete!")
  
