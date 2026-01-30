import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# 1. Setup & Data Loading
st.set_page_config(page_title="MS Symptom Tracker", layout="wide")
FILENAME = "ms_health_data.csv"

if not os.path.isfile(FILENAME):
    df_init = pd.DataFrame(columns=["Date", "Event", "Type", "Severity", "Notes"])
    df_init.to_csv(FILENAME, index=False)

# Load data with error handling for mixed date formats
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
    # UPDATED: Defaults to current time with 15-minute steps
    entry_time = st.sidebar.time_input("Time", datetime.now().time(), step=900)

# FIXED: Combine chosen date/time and force 12-hour format for the database
final_timestamp = datetime.combine(entry_date, entry_time).strftime("%m/%d/%Y %I:%M %p")

symptom_options = ["Fatigue", "Optic Neuritis", "Tingling", "MS Hug (Chest Tightness)", "Incontinence"]
selected_events = st.sidebar.multiselect("Select Symptoms or Triggers", symptom_options)

event_data = {}
if selected_events:
    for event in selected_events:
        event_data[event] = st.sidebar.slider(f"Intensity for {event}", 1, 10, 5)

notes = st.sidebar.text_area("General Notes")

if st.sidebar.button("Save Entry"):
    if not selected_events:
        st.sidebar.error("Please select a symptom.")
    else:
        new_rows = []
        for event, sev in event_data.items():
            new_rows.append({"Date": final_timestamp, "Event": event, "Severity": sev, "Notes": notes})
        
        pd.DataFrame(new_rows).to_csv(FILENAME, mode='a', header=False, index=False)
        st.sidebar.success(f"Logged for {final_timestamp}!")
        st.rerun() # Forces the "Entries" tab to update immediately

# 3. Main Tabs
tab1, tab2 = st.tabs(["📈 Trends", "📋 History & Entries"])

with tab1:
    if not df.empty:
        fig, ax = plt.subplots()
        for label, grp in df.groupby('Event'):
            grp.sort_values('Date').plot(x='Date', y='Severity', ax=ax, label=label, marker='o')
        st.pyplot(fig)
    else:
        st.info("No data yet.")

with tab2:
    st.subheader("Recent Entries")
    if not df.empty:
        # Show newest entries at the top
        display_df = df.sort_values(by="Date", ascending=False).copy()
        display_df['Date'] = display_df['Date'].dt.strftime("%m/%d/%Y %I:%M %p")
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No entries found. Log your first symptom in the sidebar!")
