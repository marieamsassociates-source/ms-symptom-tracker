import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from fpdf import FPDF
import os
import io
import dropbox

# 1. Setup & Dropbox Sync Logic
st.set_page_config(page_title="MS Symptom Tracker", layout="wide")
FILENAME = "ms_health_data.csv"

def get_dropbox_client():
    if "dropbox" not in st.secrets:
        return None
    return dropbox.Dropbox(
        app_key=st.secrets["dropbox"]["app_key"],
        app_secret=st.secrets["dropbox"]["app_secret"],
        oauth2_refresh_token=st.secrets["dropbox"]["refresh_token"]
    )

def sync_data(df):
    # Save locally
    df.to_csv(FILENAME, index=False)
    # Sync to Dropbox
    dbx = get_dropbox_client()
    if dbx:
        try:
            csv_buffer = io.BytesIO()
            df.to_csv(csv_buffer, index=False)
            dbx.files_upload(csv_buffer.getvalue(), f"/{FILENAME}", mode=dropbox.files.WriteMode("overwrite"))
        except Exception as e:
            st.error(f"Dropbox Sync Failed: {e}")

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
    entry_time = st.sidebar.time_input("Time", datetime.now().time(), step=900)

dt_combined = datetime.combine(entry_date, entry_time)
final_timestamp = dt_combined.strftime("%m/%d/%Y %I:%M %p")

symptom_options = ["Fatigue", "Optic Neuritis", "Tingling", "MS Hug", "Incontinence", "Other..."]
selected_events = st.sidebar.multiselect("Select Symptoms or Triggers", symptom_options)

event_data = {}
for event in selected_events:
    score = st.sidebar.slider(f"Intensity for {event}", 1, 10, 5, key=f"sidebar_{event}")
    event_data[event] = score

notes = st.sidebar.text_area("General Notes")

if st.sidebar.button("Save Entry"):
    if not event_data:
        st.sidebar.error("Please select a symptom.")
    else:
        new_rows = []
        for event, sev in event_data.items():
            new_rows.append({"Date": final_timestamp, "Event": event, "Type": "Symptom", "Severity": sev, "Notes": notes})
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        sync_data(df)
        st.sidebar.success("Saved & Synced!")
        st.rerun()

# 3. Tabs
tab1, tab2, tab3 = st.tabs(["📈 Trends", "📋 History", "📄 Export"])

with tab1:
    if not df.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        for label, grp in df.groupby('Event'):
            grp.sort_values('Date').plot(x='Date', y='Severity', ax=ax, label=label, marker='o')
        st.pyplot(fig)

with tab2:
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)

with tab3:
    st.subheader("Manual Backup")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV Backup", data=csv, file_name="ms_tracker_backup.csv")
