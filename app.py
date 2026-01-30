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

def load_data():
    if not os.path.isfile(FILENAME):
        df_init = pd.DataFrame(columns=["Date", "Event", "Type", "Severity", "Notes"])
        df_init.to_csv(FILENAME, index=False)
        return df_init
    df_temp = pd.read_csv(FILENAME)
    if not df_temp.empty:
        df_temp['Date'] = pd.to_datetime(df_temp['Date'], errors='coerce')
        df_temp = df_temp.dropna(subset=['Date'])
    return df_temp

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
            new_rows.append({"Date": final_timestamp, "Event": event, "Type": etype, "Severity": sev, "Notes": notes})
        pd.DataFrame(new_rows).to_csv(FILENAME, mode='a', header=False, index=False)
        st.sidebar.success(f"Logged
