import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime
import os

# 1. Password Protection Logic
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Please enter the app password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Please enter the app password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    return True

if check_password():
    # App Configuration
    st.set_page_config(page_title="MS Symptom Tracker", layout="wide")
    FILENAME = "ms_health_data.csv"

    # Initialize CSV if it doesn't exist
    if not os.path.isfile(FILENAME):
        df_init = pd.DataFrame(columns=["Date", "Event", "Type", "Severity", "Notes"])
        df_init.to_csv(FILENAME, index=False)

    df = pd.read_csv(FILENAME)

    st.title("🎗️ MS Symptom & Trigger Tracker")

    # --- SIDEBAR: NEW ENTRY ---
    st.sidebar.header("Log New Entry")
    
    symptom_options = ["Fatigue", "Optic Neuritis", "Tingling", "MS Hug (Chest Tightness)", "Incontinence"]
    trigger_options = ["Cold Exposure", "Heat", "Stress", "Lack of Sleep"]
    all_options = symptom_options + trigger_options + ["Other"]

    event_name = st.sidebar.selectbox("Select Symptom or Trigger", all_options)
    
    # Auto-categorize
    if event_name in symptom_options:
        event_type = "Symptom"
    elif event_name in trigger_options:
        event_type = "Trigger"
    else:
        event_type = "Other"
        event_name = st.sidebar.text_input("Specify Name")

    severity = st.sidebar.slider("Severity/Intensity", 1, 10, 5)
    notes = st.sidebar.text_area("Notes")

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
    tab1, tab2, tab3 = st.tabs(["📈 Trends", "📋 History & Edit", "📄 Export"])

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
            st.info("No data recorded yet.")

    with tab2:
        st.subheader("Manage Entries")
        if not df.empty:
            st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
            
            st.write("---")
            df['Selection'] = df['Date'].astype(str) + " - " + df['Event']
            selected_event = st.selectbox("Select an entry to modify/delete:", df['Selection'])
            idx = df[df['Selection'] == selected_event].index[0]
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🗑️ Delete Entry", type="primary"):
                    df = df.drop(idx).drop(columns=['Selection'])
                    df.to_csv(FILENAME, index=False)
                    st.success("Deleted.")
                    st.rerun()
            with c2:
                if st.checkbox("📝 Edit Details"):
                    new_sev = st.slider("Update Severity", 1, 10, int(df.at[idx, 'Severity']))
                    new_notes = st.text_area("Update Notes", value=df.at[idx, 'Notes'])
                    if st.button("Save Changes"):
                        df.at[idx, 'Severity'] = new_sev
                        df.at[idx, 'Notes'] = new_notes
                        df = df.drop(columns=['Selection'])
                        df.to_csv(FILENAME, index=False)
                        st.success("Updated.")
                        st.rerun()

    with tab3:
        st.subheader("Generate Report")
        if st.button("Create PDF Report"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="MS Symptom Report", ln=True, align='C')
            pdf.set_font("Arial", size=10)
            for i, row in df.iterrows():
                pdf.ln(5)
                pdf.cell(0, 10, f"{row['Date']} - {row['Event']} (Severity: {row['Severity']})", ln=True)
                pdf.multi_cell(0, 10, f"Notes: {row['Notes']}")
            
            pdf_path = "MS_Report.pdf"
            pdf.output(pdf_path)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="MS_Symptom_Report.pdf")
