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
    st.set_page_config(page_title="MS Symptom Tracker", layout="wide")
    FILENAME = "ms_health_data.csv"

    if not os.path.isfile(FILENAME):
        df_init = pd.DataFrame(columns=["Date", "Event", "Type", "Severity", "Notes"])
        df_init.to_csv(FILENAME, index=False)

    # Load and Clean Data
    df = pd.read_csv(FILENAME)
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date']) 

    st.title("🎗️ MS Symptom & Trigger Tracker")

    # --- SIDEBAR: NEW ENTRY ---
    st.sidebar.header("Log New Entry")
    
    c1, c2 = st.sidebar.columns(2)
    with c1:
        entry_date = st.sidebar.date_input("Date", datetime.now(), format="MM/DD/YYYY")
    with c2:
        entry_time = st.sidebar.time_input("Time", datetime.now().time(), step=900)

    final_timestamp = datetime.combine(entry_date, entry_time).strftime("%m/%d/%Y %I:%M %p")

    symptom_options = ["Fatigue", "Optic Neuritis", "Tingling", "MS Hug (Chest Tightness)", "Incontinence"]
    trigger_options = ["Cold Exposure", "Heat", "Stress", "Lack of Sleep"]
    all_options = symptom_options + trigger_options

    selected_events = st.sidebar.multiselect("Select Symptoms or Triggers", all_options)

    event_data = {}
    if selected_events:
        st.sidebar.write("### Set Severities")
        for event in selected_events:
            score = st.sidebar.slider(f"Intensity for {event}", 1, 10, 5, key=f"sidebar_{event}")
            event_data[event] = score

    notes = st.sidebar.text_area("General Notes")

    if st.sidebar.button("Save Entry"):
        if not selected_events:
            st.sidebar.error("Please select at least one symptom.")
        else:
            new_rows = []
            for event, sev in event_data.items():
                etype = "Symptom" if event in symptom_options else "Trigger"
                new_rows.append({
                    "Date": final_timestamp, "Event": event, "Type": etype, "Severity": sev, "Notes": notes
                })
            new_df = pd.DataFrame(new_rows)
            new_df.to_csv(FILENAME, mode='a', header=False, index=False)
            st.sidebar.success(f"Logged for {final_timestamp}!")
            st.rerun()

    # --- MAIN DASHBOARD ---
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "📋 History & Edit", "📄 Export", "🔓 Logout"])

    with tab1:
        st.subheader("Severity Over Time")
        if not df.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            for label, grp in df.groupby('Event'):
                grp.sort_values('Date').plot(x='Date', y='Severity', ax=ax, label=label, marker='o')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            st.pyplot(fig)
        else:
            st.info("No valid data to display yet.")

    with tab2:
        st.subheader("Manage Entries")
        if not df.empty:
            display_df = df.copy()
            display_df = display_df.sort_values(by="Date", ascending=False)
            display_df['Date_Str'] = display_df['Date'].dt.strftime("%m/%d/%Y %I:%M %p")
            
            st.dataframe(
                display_df[['Date_Str', 'Event', 'Severity', 'Notes']], 
                use_container_width=True
            )
            
            st.write("---")
            
            entry_options = []
            for time_group, group_data in display_df.groupby('Date_Str', sort=False):
                events_list = ", ".join(group_data['Event'].astype(str).tolist())
                entry_options.append(f"{time_group} | {events_list}")

            selected_full_line = st.selectbox("Select a log entry to manage:", ["-- Select an Entry --"] + entry_options)
            
            if selected_full_line != "-- Select an Entry --":
                selected_time_str = selected_full_line.split(" | ")[0]
                
                if st.button("🗑️ Delete All at this Time", type="primary"):
                    df_clean = pd.read_csv(FILENAME)
                    # REPAIRED LINE 128:
                    df_clean['Temp_Date'] = pd.to_datetime(df_clean['Date']).dt.strftime("%m/%d/%Y %I:%M %p")
                    df_clean = df_clean[df_clean['Temp_Date'] != selected_time_str].drop(columns=['Temp_Date'])
                    df_clean.to_csv(FILENAME, index=False)
                    st.success("Deleted.")
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
                pdf.cell(0, 10, f"{row['Date'].strftime('%m/%d/%Y %I:%M %p')} - {row['Event']} (Severity: {row['Severity']})", ln=True)
                pdf.multi_cell(0, 10, f"Notes: {row['Notes']}")
            pdf.output("MS_Report.pdf")
            with open("MS_Report.pdf", "rb") as f:
                st.download_button("Download PDF", f, file_name="MS_Symptom_Report.pdf")

    with tab4:
        st.subheader("Logout")
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
