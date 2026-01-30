import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime
import os

# App Configuration
st.set_page_config(page_title="MS Symptom Tracker", layout="wide")
FILENAME = "ms_health_data.csv"

# Load or Initialize Data
if not os.path.isfile(FILENAME):
    df = pd.DataFrame(columns=["Date", "Event", "Type", "Severity", "Notes"])
    df.to_csv(FILENAME, index=False)

df = pd.read_csv(FILENAME)

st.title("🎗️ MS Symptom & Trigger Tracker")

# --- SIDEBAR: NEW ENTRY ---
st.sidebar.header("Log New Event")
event_type = st.sidebar.radio("Type", ["Symptom", "Trigger"])
event_list = {
    "Symptom": ["Fatigue", "Optic Neuritis", "Tingling", "MS Hug (Chest Tightness)", "Incontinence", "Other"],
    "Trigger": ["Cold Exposure", "Heat", "Stress", "Lack of Sleep", "Other"]
}

event_name = st.sidebar.selectbox("Event Name", event_list[event_type])
if event_name == "Other":
    event_name = st.sidebar.text_input("Specify Other")

severity = st.sidebar.slider("Severity/Intensity", 1, 10, 5)
notes = st.sidebar.text_area("Notes (Triggers, duration, etc.)")

if st.sidebar.button("Save Entry"):
    new_row = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Event": event_name,
        "Type": event_type,
        "Severity": severity,
        "Notes": notes
    }])
    new_row.to_csv(FILENAME, mode='a', header=False, index=False)
    st.sidebar.success("Logged!")
    st.rerun()

# --- MAIN DASHBOARD ---
tab1, tab2, tab3 = st.tabs(["📈 Trends", "📋 History", "📄 Export"])

with tab1:
    st.subheader("Severity Over Time")
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        fig, ax = plt.subplots(figsize=(10, 4))
        for label, grp in df.groupby('Event'):
            grp.sort_values('Date').plot(x='Date', y='Severity', ax=ax, label=label, marker='o')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        st.pyplot(fig)
    else:
        st.info("No data yet. Log your first symptom in the sidebar!")

with tab2:
    st.subheader("Recent Logs")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)

with tab3:
    st.subheader("Doctor's Report")
    if st.button("Generate PDF Report"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="MS Health Report", ln=True, align='C')
        # ... (PDF generation logic same as previous step)
        pdf_output = "MS_Health_Report.pdf"
        pdf.output(pdf_output)
        with open(pdf_output, "rb") as f:
            st.download_button("Download PDF for Neurologist", f, file_name=pdf_output)
