import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from fpdf import FPDF
import os
import io
import dropbox

# 1. Setup & Dropbox Configuration
st.set_page_config(page_title="MS Symptom Tracker", layout="wide")
FILENAME = "ms_health_data.csv"
DROPBOX_PATH = f"/{FILENAME}"

# Access credentials from Streamlit Secrets
def get_dropbox_client():
    return dropbox.Dropbox(
        app_key=st.secrets["dropbox"]["app_key"],
        app_secret=st.secrets["dropbox"]["app_secret"],
        oauth2_refresh_token=st.secrets["dropbox"]["refresh_token"]
    )

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

def sync_to_dropbox(df):
    """Saves locally and uploads to Dropbox folder."""
    # Save locally first
    df.to_csv(FILENAME, index=False)
    
    # Upload to Dropbox
    try:
        dbx = get_dropbox_client()
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False)
        dbx.files_upload(csv_buffer.getvalue(), DROPBOX_PATH, mode=dropbox.files.WriteMode("overwrite"))
        return True
    except Exception as e:
        st.error(f"Dropbox Sync Error: {e}")
        return False

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
        
        updated_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        if sync_to_dropbox(updated_df):
            st.sidebar.success(f"Synced to Dropbox for {final_timestamp}!")
            st.rerun()

# 3. Main Dashboard Tabs
tab1, tab2, tab3 = st.tabs(["📈 Trends", "📋 History & Manage", "📄 Export"])

with tab1:
    st.subheader("Severity Over Time")
    if not df.empty:
        search_query = st.text_input("🔍 Search symptoms or triggers", "").strip().lower()
        filtered_df = df if not search_query else df[df['Event'].str.lower().str.contains(search_query)]

        if not filtered_df.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            for label, grp in filtered_df.groupby('Event'):
                grp.sort_values('Date').plot(x='Date', y='Severity', ax=ax, label=label, marker='o')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.ylabel("Severity Score")
            st.pyplot(fig)
        else:
            st.warning("No matching results.")
    else:
        st.info("No data logged yet.")

with tab2:
    st.subheader("History & Management")
    if not df.empty:
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
                original_dt = row_data['Date']
                new_date = st.date_input("Update Date", value=original_dt)
                new_time = st.time_input("Update Time", value=original_dt.time(), step=900)
                updated_ts = datetime.combine(new_date, new_time).strftime("%m/%d/%Y %I:%M %p")

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
                        new_entries.append({"Date": updated_ts, "Event": event, "Type": etype, "Severity": sev, "Notes": new_note})
                    
                    df = pd.concat([df, pd.DataFrame(new_entries)], ignore_index=True)
                    if sync_to_dropbox(df):
                        st.success("Entry updated and synced!")
                        st.rerun()
            
            with col_d:
                st.warning("Action is permanent")
                if st.button("🗑️ Delete Log", type="primary"):
                    df = df.drop(item_idx)
                    if sync_to_dropbox(df):
                        st.rerun()

with tab3:
    st.subheader("Manual Export")
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV Backup", data=csv, file_name="ms_tracker_data.csv", mime="text/csv")
