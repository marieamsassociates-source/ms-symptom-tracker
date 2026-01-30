import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# 1. Setup & Data Loading
st.set_page_config(page_title="MS Symptom Tracker", layout="wide")
FILENAME = "ms_health_data.csv"

# Initialize CSV with correct headers if it doesn't exist
if not os.path.isfile(FILENAME):
    df_init = pd.DataFrame(columns=["Date", "Event", "Type", "Severity", "Notes"])
    df_init.to_csv(FILENAME, index=False)

# Load data with robust date parsing
df = pd.read_csv(FILENAME)
if not df.empty:
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])

st.title("🎗️ MS Symptom & Trigger Tracker")

# 2. Sidebar: Log New Entry
st.sidebar.header("Log New Entry")

c1, c2 = st.sidebar.columns(2)
with c1:
    entry_date = st.sidebar.date_input("Date", datetime.now())
with c2:
    # 15-minute increments
    entry_time = st.sidebar.time_input("Time", datetime.now().time(), step=900, key="time_input")

# Force 12-hour format for the database
dt_combined = datetime.combine(entry_date, entry_time)
final_timestamp = dt_combined.strftime("%m/%d/%Y %I:%M %p")

symptom_options = ["Fatigue", "Optic Neuritis", "Tingling", "MS Hug (Chest Tightness)", "Incontinence"]
trigger_options = ["Cold Exposure", "Heat", "Stress", "Lack of Sleep"]
all_options = symptom_options + trigger_options

# The selection widget shown in your screenshot
selected_events = st.sidebar.multiselect("Select Symptoms or Triggers", all_options)

event_data = {}
if selected_events:
    for event in selected_events:
        # Intensity sliders only appear after you select a symptom
        event_data[event] = st.sidebar.slider(f"Intensity for {event}", 1, 10, 5, key=f"slider_{event}")

notes = st.sidebar.text_area("General Notes")

if st.sidebar.button("Save Entry"):
    if not selected_events:
        st.sidebar.error("Please select at least one symptom from the dropdown first!")
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
        
        # Save and Force Refresh
        pd.DataFrame(new_rows).to_csv(FILENAME, mode='a', header=False, index=False)
        st.sidebar.success(f"Logged for {final_timestamp}!")
        st.rerun() # This makes sure the History tab updates instantly

# 3. Main Dashboard Tabs
tab1, tab2 = st.tabs(["📈 Trends", "📋 History & Entries"])

with tab1:
    st.subheader("Severity Over Time")
    if not df.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        for label, grp in df.groupby('Event'):
            grp.sort_values('Date').plot(x='Date', y='Severity', ax=ax, label=label, marker='o')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        st.pyplot(fig)
    else:
        st.info("No data available yet.")

with tab2:
    st.subheader("Recent Entries")
    # Re-read file to show newly saved data
    current_df = pd.read_csv(FILENAME)
    if not current_df.empty:
        current_df['Date'] = pd.to_datetime(current_df['Date'], errors='coerce')
        display_df = current_df.dropna(subset=['Date']).sort_values(by="Date", ascending=False)
        display_df['Date'] = display_df['Date'].dt.strftime("%m/%d/%Y %I:%M %p")
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No entries found. Select a symptom in the sidebar and click 'Save Entry'.")
