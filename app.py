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
all_options = symptom_options + trigger_options

# Choose multiple items
selected_events = st.sidebar.multiselect("Select Symptoms or Triggers", all_options)

# Dictionary to store severity for each selection
event_data = {}

if selected_events:
    st.sidebar.write("### Set Severities")
    for event in selected_events:
        # Create a unique slider for each selected item
        score = st.sidebar.slider(f"Intensity for {event}", 1, 10, 5, key=f"slider_{event}")
        event_data[event] = score

notes = st.sidebar.text_area("General Notes")

if st.sidebar.button("Save Entry"):
    if not selected_events:
        st.sidebar.error("Please select at least one symptom or trigger.")
    else:
        new_rows = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        for event, sev in event_data.items():
            # Determine type automatically
            etype = "Symptom" if event in symptom_options else "Trigger"
            
            new_rows.append({
                "Date": timestamp,
                "Event": event,
                "Type": etype,
                "Severity": sev,
                "Notes": notes
            })
        
        # Append all new rows to the CSV
        new_df = pd.DataFrame(new_rows)
        new_df.to_csv(FILENAME, mode='a', header=False, index=False)
        st.sidebar.success(f"Logged {len(selected_events)} items!")
        st.rerun()
    
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
            
            # This creates three columns to place buttons side-by-side
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("🗑️ Delete Entry", type="primary", use_container_width=True):
                    df = df.drop(idx).drop(columns=['Selection'])
                    df.to_csv(FILENAME, index=False)
                    st.success("Deleted.")
                    st.rerun()
            
            with col2:
                # Changed from checkbox to a button to toggle the edit form
                edit_mode = st.button("📝 Edit Entry", use_container_width=True)
                if edit_mode:
                    st.session_state['editing_idx'] = idx

            # Display the edit form below if the button was clicked
            if 'editing_idx' in st.session_state and st.session_state['editing_idx'] == idx:
                st.info(f"Editing: {selected_event}")
                new_sev = st.slider("Update Severity", 1, 10, int(df.at[idx, 'Severity']))
                new_notes = st.text_area("Update Notes", value=df.at[idx, 'Notes'])
                
                ec1, ec2 = st.columns(2)
                with ec1:
                    if st.button("Save Changes"):
                        df.at[idx, 'Severity'] = new_sev
                        df.at[idx, 'Notes'] = new_notes
                        df = df.drop(columns=['Selection'])
                        df.to_csv(FILENAME, index=False)
                        del st.session_state['editing_idx']
                        st.success("Updated.")
                        st.rerun()
                with ec2:
                    if st.button("Cancel"):
                        del st.session_state['editing_idx']
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
