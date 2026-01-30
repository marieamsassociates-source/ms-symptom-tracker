import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# 1. Setup & Data Loading
st.set_page_config(page_title="MS Symptom Tracker", layout="wide")
FILENAME = "ms_health_data.csv"

# Initialize CSV if it doesn't exist
if not os.path.isfile(FILENAME):
    df_init = pd.DataFrame(columns=["Date", "Event", "Type", "Severity", "Notes"])
    df_init.to_csv(FILENAME, index=False)

# Load data with robust date parsing to prevent crashes
df = pd.read_csv(FILENAME)
if not df.empty:
    # errors='coerce' turns bad date formats into NaT instead of crashing
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])

st.title("🎗️ MS Symptom & Trigger Tracker")

# 2. Sidebar: Log New Entry
st.sidebar.header("Log New Entry")

c1, c2 = st.sidebar.columns(2)
with c1:
    entry_date = st.sidebar.date_input("Date", datetime.now())
with c2:
    # Step=900 sets 15-minute increments
    # Unique key ensures the widget doesn't reset unexpectedly
    entry_time = st.sidebar.time_input("Time", datetime.now().time(), step=900, key="time_input")

# COMBINE & FORMAT: Force 12-hour AM/PM format for the database
dt_combined = datetime.combine(entry_date, entry_time)
final_timestamp = dt_combined.strftime("%m/%d/%Y %I:%M %p")

symptom_options = ["Fatigue", "Optic Neuritis", "Tingling", "MS Hug (Chest Tightness)", "Incontinence"]
trigger_options = ["Cold Exposure", "Heat", "Stress", "Lack of Sleep"]
all_options = symptom_options + trigger_options

selected_events = st.sidebar.multiselect("Select Symptoms or Triggers", all_options)

event_data = {}
if selected_events:
    for event in selected_events:
        event_data[event] = st.sidebar.slider(f"Intensity for {event}", 1, 10, 5, key=f"slider_{event}")

notes = st.sidebar.text_area("General Notes")

if st.sidebar.button("Save Entry"):
    if not selected_events:
        st.sidebar.error("Please select at least one symptom.")
    else:
        new_rows = []
        for event, sev in event_data.items():
            etype = "Symptom" if event in symptom_options else "Trigger"
            new_rows.append({
                "Date": final_timestamp, 
                "Event": event, 
                "Type": etype, 
                "Severity": sev, 
                "Notes":
