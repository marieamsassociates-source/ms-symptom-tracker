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
        entry_time = st.sidebar.time_input("Time", datetime.now().time())

    final_timestamp = datetime.combine(entry_date, entry_time).strftime("%m/%d/%Y %H:%M")

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

    # --- MAIN DASHBOARD: TRENDS REVERTED TO POSITION 1 ---
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
            st.info("No valid data to display.")

    with tab2:
        st.subheader("Manage Entries")
        if not df.empty:
            display_df = df.copy()
            display_df['Date_Str'] = display_df['Date'].dt.strftime("%m/%d/%Y %H:%M")
            st.dataframe(display_df[['Date_Str', 'Event', 'Severity', 'Notes']].sort_values(by="Date_Str", ascending=False), use_container_width=True)
            
            st.write("---")
            entry_options = []
            for time_group, group_data in display_df.groupby('Date_Str'):
                events_list = ", ".join(group_data['Event'].tolist())
                entry_options.append(f"{time_group} | {events_list}")

            entry_options.sort(reverse=True)
            selected_full_line = st.selectbox("Select a log entry to modify/delete:", entry_options)
            selected_time = selected_full_line.split(" | ")[0]
            batch_df = df[df['Date'].dt.strftime("%m/%d/%Y %H:%M") == selected_time]
            
            col_edit, col_del = st.columns([1, 1])
            with col_edit:
                if st.button("📝 Edit Items at this Time", use_container_width=True):
                    st.session_state['editing_time'] = selected_time
            with col_del:
                if st.button("🗑️ Delete All at this Time", type="primary", use_container_width=True):
                    df = df[df['Date'].dt.strftime("%m/%d/%Y %H:%M") != selected_time]
                    df.to_csv(FILENAME, index=False)
                    st.success("Deleted.")
                    st.rerun()

            if 'editing_time' in st.session_state and st.session_state['editing_time'] == selected_time:
                st.info(f"Editing logs for: {selected_time}")
                updated_notes = st.text_area("Update Notes", value=batch_df.iloc[0]['Notes'])
                
                new_severities = {}
                for idx, row in batch_df.iterrows():
                    new_sev = st.slider(f"Intensity: {row['Event']}", 1, 10, int(row['Severity']), key=f"edit_sev_{idx}")
                    new_severities[idx] = new_sev
                
                available_to_add = [opt for opt in all_options if opt not in batch_df['Event'].tolist()]
                added_events = st.multiselect("Include additional items:", available_to_add)
                added_data = {e: st.slider(f"Intensity for {e}", 1, 10, 5, key=f"add_{e}") for e in added_events}

                ec1, ec2 = st.columns(2)
                with ec1:
                    if st.button("Save Changes"):
                        for idx, sev in new_severities.items():
                            df.at[idx, 'Severity'], df.at[idx, 'Notes'] = sev, updated_notes
                        if added_events:
                            for event, sev in added_data.items():
                                etype = "Symptom" if event in symptom_options else "Trigger"
                                new_row = {"Date": datetime.strptime(selected_time, "%m/%d/%Y %H:%M"), "Event": event, "Type": etype, "Severity": sev, "Notes": updated_notes}
                                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        df.to_csv(FILENAME, index=False)
                        del st.session_state['editing_time']
                        st.success("Updated!")
                        st.rerun()
                with ec2:
                    if st.button("Cancel"):
                        del st.session_state['editing_time']
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
                pdf.cell(0, 10, f"{row['Date'].strftime('%m/%d/%Y %H:%M')} - {row['Event']} (Severity: {row['Severity']})", ln=True)
                pdf.multi_cell(0, 10, f"Notes: {row['Notes']}")
            pdf_path = "MS_Report.pdf"
            pdf.output(pdf_path)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="MS_Symptom_Report.pdf")

    with tab4:
        st.subheader("Logout")
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
