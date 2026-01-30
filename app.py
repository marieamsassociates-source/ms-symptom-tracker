import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from fpdf import FPDF
import os
import io

# 1. Setup & Data Loading
st.set_page_config(page_title="MS Symptom Tracker", layout="wide")
FILENAME = "ms_health_data.csv"

# Function to ensure data is always fresh and formatted correctly
def load_data():
    if not os.path.isfile(FILENAME):
        df_init = pd.DataFrame(columns=["Date", "Event", "Type", "Severity", "Notes"])
        df_init.to_csv(FILENAME, index=False)
        return df_init
    df_temp = pd.read_csv(FILENAME)
    if not df_temp.empty:
        # errors='coerce' prevents crashes if a date format gets corrupted
        df_temp['Date'] = pd.to_datetime(df_temp['Date'], errors='coerce')
        df_temp = df_temp.dropna(subset=['Date'])
    return df_temp

# Initial load
df = load_data()

st.title("🎗️ MS Symptom & Trigger Tracker")

# 2. Sidebar: Log New Entry
st.sidebar.header("Log New Entry")

c1, c2 = st.sidebar.columns(2)
with c1:
    entry_date = st.sidebar.date_input("Date", datetime.now())
with c2:
    entry_time = st.sidebar.time_input("Time", datetime.now().time(), step=900, key="sidebar_time")

dt_combined = datetime.combine(entry_date, entry_time)
final_timestamp = dt_combined.strftime("%m/%d/%Y %I:%M %p")

symptom_options = ["Fatigue", "Optic Neuritis", "Tingling", "MS Hug (Chest Tightness)", "Incontinence", "Other..."]
trigger_options = ["Cold Exposure", "Heat", "Stress", "Lack of Sleep", "Other..."]
all_options = symptom_options + trigger_options

selected_events = st.sidebar.multiselect("Select Symptoms or Triggers", all_options)

event_data = {}
if selected_events:
    for event in selected_events:
        if event == "Other...":
            custom_name = st.sidebar.text_input("Enter Custom Name", key="new_custom_name")
            display_name = custom_name if custom_name else "Custom Event"
        else:
            display_name = event
        
        score = st.sidebar.slider(f"Intensity for {display_name}", 1, 10, 5, key=f"sidebar_{display_name}")
        event_data[display_name] = score

notes = st.sidebar.text_area("General Notes")

if st.sidebar.button("Save Entry"):
    if not event_data:
        st.sidebar.error("Please select or name a symptom.")
    else:
        new_rows = []
        for event, sev in event_data.items():
            etype = "Symptom" if event in symptom_options else "Trigger"
            new_rows.append({
                "Date": final_timestamp, 
                "Event": event, 
                "Type": etype, 
                "Severity": sev, 
                "Notes": notes
            })
        pd.DataFrame(new_rows).to_csv(FILENAME, mode='a', header=False, index=False)
        st.sidebar.success(f"Logged for {final_timestamp}!")
        st.rerun() # Force app to refresh and show new data immediately

# 3. Main Dashboard Tabs
# We define tabs OUTSIDE of the "if df.empty" block so the UI is always visible
tab1, tab2, tab3 = st.tabs(["📈 Trends", "📋 History & Manage", "📄 Export"])

with tab1:
    st.subheader("Severity Over Time")
    if not df.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        for label, grp in df.groupby('Event'):
            grp.sort_values('Date').plot(x='Date', y='Severity', ax=ax, label=label, marker='o')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        st.pyplot(fig)
    else:
        st.info("No data logged yet. Use the sidebar to save your first entry.")

with tab2:
    st.subheader("History & Management")
    if not df.empty:
        # Sort by Date (Newest first)
        display_df = df.sort_values(by="Date", ascending=False).copy()
        display_df['Date_Display'] = display_df['Date'].dt.strftime("%m/%d/%Y %I:%M %p")
        
        st.dataframe(display_df[['Date_Display', 'Event', 'Type', 'Severity', 'Notes']], use_container_width=True)
        
        st.divider()
        st.write("### Edit or Delete an Entry")
        manage_list = [f"{row['Date_Display']} | {row['Event']}" for _, row in display_df.iterrows()]
        selected_item = st.selectbox("Choose a log to modify:", ["-- Select --"] + manage_list)
        
        if selected_item != "-- Select --":
            item_idx = display_df.index[manage_list.index(selected_item)]
            row_data = df.loc[item_idx]
            
            col_e, col_d = st.columns([2, 1])
            with col_e:
                current_events = row_data['Event'].split(", ")
                temp_options = list(set(all_options + current_events))
                new_events = st.multiselect("Update Symptoms/Triggers", temp_options, default=current_events)
                
                new_severities = {}
                for event in new_events:
                    new_severities[event] = st.slider(f"Severity for {event}", 1, 10, int(row_data['Severity']), key=f"edit_sev_{event}")
                
                new_note = st.text_area("Edit Note", value=row_data['Notes'])
                if st.button("Update Log"):
                    df = df.drop(item_idx)
                    new_entries = []
                    for event, sev in new_severities.items():
                        etype = "Symptom" if event in symptom_options else "Trigger"
                        new_entries.append({
                            "Date": row_data['Date'].strftime("%m/%d/%Y %I:%M %p"),
                            "Event": event, "Type": etype, "Severity": sev, "Notes": new_note
                        })
                    df = pd.concat([df, pd.DataFrame(new_entries)], ignore_index=True)
                    df.to_csv(FILENAME, index=False)
                    st.success("Log updated!")
                    st.rerun()
            
            with col_d:
                st.warning("Action is permanent")
                if st.button("🗑️ Delete Log", type="primary"):
                    df = df.drop(item_idx)
                    df.to_csv(FILENAME, index=False)
                    st.rerun()
    else:
        st.info("No entries found.")

with tab3:
    st.subheader("Export Records")
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV Backup", data=csv, file_name="ms_tracker_data.csv", mime="text/csv")
        
        if st.button("🛠️ Generate PDF Report"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="MS Symptom History Report", ln=True, align='C')
            pdf.set_font("Arial", size=10)
            pdf.ln(10)
            for _, row in df.sort_values(by="Date", ascending=False).iterrows():
                date_str = row['Date'].strftime("%m/%d/%Y %I:%M %p")
                pdf.multi_cell(0, 10, f"{date_str} - {row['Event']} (Severity: {row['Severity']})\nNotes: {row['Notes']}\n{'-'*30}")
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Download PDF Report", data=pdf_output, file_name="MS_Health_Report.pdf", mime="application/pdf")
    else:
        st.info("No data available to export.")
