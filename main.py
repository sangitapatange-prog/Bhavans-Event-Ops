import streamlit as st
import pandas as pd
import sqlite3
import json

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Bhavan's GVM | Event Ops", layout="wide", page_icon="🏫", initial_sidebar_state="expanded")

# --- SESSION STATE INITIALIZATION ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# --- CLOUD-PROOF ENTERPRISE CSS ---
st.markdown("""
    <style>
    /* Force Dark Mode on Streamlit Cloud Framework */
    [data-testid="stAppViewContainer"] { background-color: #0E1117 !important; color: #E6EDF3 !important; }
    [data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D !important; }
    [data-testid="stHeader"] { background-color: transparent !important; }
    
    /* Text Color Fixes for Light/Dark Mode Clashes */
    .stMarkdown, p, span, label, h1, h2, h3, h4 { color: #E6EDF3 !important; font-family: 'Segoe UI', system-ui, sans-serif !important; }
    
    .stApp::before {
        content: "BHAVAN'S GVM"; position: fixed; top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-15deg);
        font-size: 10vw; color: rgba(255, 255, 255, 0.02); 
        z-index: 0; pointer-events: none; white-space: nowrap; 
        font-weight: 900; letter-spacing: 12px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Input Fields styling */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stNumberInput>div>div>input, .stMultiSelect>div>div>div {
        background-color: #0D1117 !important; color: #ffffff !important; 
        border: 1px solid #30363D !important; border-radius: 6px !important; 
        padding: 12px !important; font-size: 1.15rem !important; 
    }
    
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus { 
        border-color: #FF9933 !important; box-shadow: none !important; 
    }
    
    /* Button Styling */
    .stButton>button {
        background-color: #161B22; color: #FF9933 !important; 
        border: 1px solid #FF9933; border-radius: 6px; padding: 0.6rem 2rem; 
        font-size: 1.1rem !important; font-weight: bold; width: 100%; transition: all 0.2s ease;
    }
    .stButton>button:hover { 
        background-color: #FF9933 !important; color: #0E1117 !important; border-color: #FF9933 !important; 
    }
    
    /* Data Grid Fixes */
    .stDataFrame { border: 1px solid #30363D; border-radius: 6px; }
    [data-testid="stDataFrame"] div { color: #ffffff !important; }
    
    .login-container { max-width: 450px; margin: 15vh auto; text-align: center; }
    
    /* Analytics Cards */
    .metric-card {
        background: #161B22; border: 1px solid #30363D; border-left: 4px solid #FF9933;
        border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-title { color: #8B949E !important; font-size: 0.95rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; }
    .metric-value { color: #E6EDF3 !important; font-size: 2.5rem; font-weight: 900; margin-top: 10px; }
    
    /* Developer Tag */
    .dev-tag {
        position: fixed; bottom: 15px; right: 20px; font-size: 0.85rem !important; color: #8B949E !important; 
        font-family: 'Courier New', monospace; z-index: 100;
    }
    .dev-tag span { color: #FF9933 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE ARCHITECTURE ---
def init_db():
    conn = sqlite3.connect('bhavans_events.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS performance_registry
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  faculty_incharge TEXT, program_category TEXT, custom_category_name TEXT,
                  duration_mins INTEGER, practice_location TEXT, technical_requisites TEXT, 
                  student_matrix JSON, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    try:
        c.execute("ALTER TABLE performance_registry ADD COLUMN run_sequence INTEGER DEFAULT 999")
    except sqlite3.OperationalError:
        pass 
        
    conn.commit()
    conn.close()

def log_performance(faculty, category, custom_cat, duration, location, reqs, student_json):
    conn = sqlite3.connect('bhavans_events.db')
    c = conn.cursor()
    c.execute("""INSERT INTO performance_registry 
                 (faculty_incharge, program_category, custom_category_name, duration_mins, practice_location, technical_requisites, student_matrix) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)""", (faculty, category, custom_cat, duration, location, reqs, student_json))
    conn.commit()
    conn.close()

def fetch_all_data():
    conn = sqlite3.connect('bhavans_events.db')
    df = pd.read_sql_query("SELECT * FROM performance_registry ORDER BY run_sequence ASC, id ASC", conn)
    
    if not df.empty and (df['run_sequence'] == 999).any():
        c = conn.cursor()
        valid_seqs = df[df['run_sequence'] != 999]['run_sequence']
        current_seq = valid_seqs.max() + 1 if not valid_seqs.empty else 1
        
        for index, row in df.iterrows():
            if row['run_sequence'] == 999:
                c.execute("UPDATE performance_registry SET run_sequence = ? WHERE id = ?", (int(current_seq), int(row['id'])))
                current_seq += 1
        conn.commit()
        df = pd.read_sql_query("SELECT * FROM performance_registry ORDER BY run_sequence ASC, id ASC", conn)
        
    conn.close()
    return df

init_db()

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("<h3 style='color: #FF9933 !important;'>≡ Menu</h3>", unsafe_allow_html=True)
app_mode = st.sidebar.radio("", ["📝 Registration Portal", "🛡️ Incharge Dashboard"])

if app_mode == "🛡️ Incharge Dashboard" and st.session_state.admin_logged_in:
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout System"):
        st.session_state.admin_logged_in = False
        st.rerun()

st.sidebar.markdown("---")
st.markdown("<div class='dev-tag'>Engineered by <span>YATHARTH DESHMUKH</span></div>", unsafe_allow_html=True)


# ==========================================
# 1. TEACHER REGISTRATION PORTAL 
# ==========================================
if app_mode == "📝 Registration Portal":
    
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem; font-weight: 900; margin-bottom: 0px;'>Event Operations Registration</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; font-size: 2.2rem; font-weight: 700; color: #8B949E !important; margin-top: 5px; margin-bottom: 40px;'>Bhavan's GVM Hinganghat</h2>", unsafe_allow_html=True)
    
    with st.container():
        faculty_incharge = st.text_input("Primary Faculty Incharge", placeholder="Enter official teacher name...")
        
        col1, col2 = st.columns(2)
        with col1:
            program_category = st.selectbox("Program Classification", ["Solo Dance", "Group Dance", "Speech / Oration", "Skit / Drama", "Choir / Group Song", "Custom / Other"])
            custom_category = ""
            if program_category == "Custom / Other":
                custom_category = st.text_input("Specify Custom Program")
        
        with col2:
            practice_venue = st.text_input("Rehearsal / Practice Venue", placeholder="e.g., Main Auditorium, Library...")
            
            if practice_venue:
                conn = sqlite3.connect('bhavans_events.db')
                venues_df = pd.read_sql_query("SELECT practice_location, faculty_incharge FROM performance_registry", conn)
                conn.close()
                
                venue_dict = {str(row['practice_location']).strip().lower(): row['faculty_incharge'] 
                              for index, row in venues_df.iterrows() if pd.notnull(row['practice_location'])}
                
                venue_lower = practice_venue.strip().lower()
                if venue_lower in venue_dict:
                    st.warning(f"⚠️ Note: '{practice_venue}' is currently occupied by **{venue_dict[venue_lower]}**.")
        
        technical_reqs = st.text_input("Technical & Prop Requirements", placeholder="e.g., 2 Wireless Mics, Podium...")

        st.markdown("<h4 style='margin-top: 20px; font-weight: bold;'>Participant Matrix</h4>", unsafe_allow_html=True)
        
        num_participants = st.number_input("Number of Students Participating", min_value=1, max_value=100, value=1)
        
        if "student_data" not in st.session_state:
            st.session_state.student_data = pd.DataFrame(columns=["Student Name", "Class", "Section", "Roll No"], index=range(1))
        
        current_len = len(st.session_state.student_data)
        if num_participants > current_len:
            new_rows = pd.DataFrame(index=range(num_participants - current_len), columns=["Student Name", "Class", "Section", "Roll No"])
            st.session_state.student_data = pd.concat([st.session_state.student_data, new_rows], ignore_index=True)
        elif num_participants < current_len:
            st.session_state.student_data = st.session_state.student_data.iloc[:num_participants]

        dynamic_height = max(150, (num_participants * 40) + 45)
        
        edited_students_df = st.data_editor(
            st.session_state.student_data, 
            num_rows="dynamic", 
            use_container_width=True,
            height=dynamic_height,
            column_config={
                "Student Name": st.column_config.TextColumn("Student Name", required=True),
                "Class": st.column_config.SelectboxColumn("Class", options=["Nursery", "KG1", "KG2"] + [str(i) for i in range(1, 13)], required=True),
                "Section": st.column_config.SelectboxColumn("Section", options=["A", "B", "C", "D", "E"], required=True),
                "Roll No": st.column_config.NumberColumn("Roll No", min_value=1, step=1)
            }
        )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Submit Program Data"):
            cleaned_df = edited_students_df.dropna(how="all") 
            if not faculty_incharge or (program_category == "Custom / Other" and not custom_category) or not practice_venue or cleaned_df.empty or pd.isna(cleaned_df.iloc[0]['Student Name']):
                st.error("⚠️ System Alert: Please fill all mandatory fields and add at least one student.")
            else:
                log_performance(faculty_incharge, program_category, custom_category, 0, practice_venue, technical_reqs, cleaned_df.to_json(orient="records"))
                st.success("✅ Protocol complete. Data synchronized with the master database.")


# ==========================================
# 2. INCHARGE DASHBOARD 
# ==========================================
elif app_mode == "🛡️ Incharge Dashboard":
    
    if not st.session_state.admin_logged_in:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px;'>BHAVAN'S GVM HINGANGHAT</h2>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #8B949E !important; margin-bottom: 30px;'>System Authentication</h3>", unsafe_allow_html=True)
        
        admin_pin = st.text_input("PIN", type="password", placeholder="Enter Security PIN", label_visibility="collapsed")
        
        if st.button("Unlock Dashboard"):
            # SAFE SECRETS LOGIC: Won't crash if Streamlit secrets aren't set properly yet
            try:
                valid_pins = st.secrets["ADMIN_PINS"]
            except:
                valid_pins = ["1508", "2601", "admin123"] # Fallback PINs
                
            if admin_pin in valid_pins: 
                st.session_state.admin_logged_in = True
                st.rerun() 
            else:
                st.error("Invalid Credentials")
        st.markdown("</div>", unsafe_allow_html=True)
                    
    else:
        st.markdown("<h1 style='text-align: center; font-size: 3.5rem; font-weight: 900; margin-bottom: 10px;'>Admin Event Console</h1>", unsafe_allow_html=True)
        st.markdown("<hr style='border: 1px solid #30363D;'>", unsafe_allow_html=True)
        
        df = fetch_all_data()
        
        if df.empty:
            st.info("The central registry is currently empty.")
        else:
            df['Total_Students'] = df['student_matrix'].apply(lambda x: len(json.loads(x)) if pd.notnull(x) else 0)
            
            total_programs = len(df)
            total_students_enrolled = df['Total_Students'].sum()
            total_time_duration = df['duration_mins'].sum()

            st.markdown("<h4 style='color: #FF9933 !important; font-weight: bold; margin-bottom: 15px;'>Executive Telemetry & Global Insights</h4>", unsafe_allow_html=True)
            
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Programs</div><div class='metric-value'>{total_programs}</div></div>", unsafe_allow_html=True)
            with m_col2:
                st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Enrollment</div><div class='metric-value'>{total_students_enrolled}</div></div>", unsafe_allow_html=True)
            with m_col3:
                st.markdown(f"<div class='metric-card'><div class='metric-title'>Allocated Duration</div><div class='metric-value'>{total_time_duration} <span style='font-size: 1.2rem; color: #8B949E !important;'>Mins</span></div></div>", unsafe_allow_html=True)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            st.markdown("<h4 style='color: #FF9933 !important; font-weight: bold;'>Data Filtration</h4>", unsafe_allow_html=True)
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                t_filter = st.multiselect("Faculty Incharge", options=sorted(df['faculty_incharge'].unique()), placeholder="Search Teacher...")
            with f_col2:
                c_filter = st.multiselect("Program Category", options=sorted(df['program_category'].unique()), placeholder="Search Category...")
            with f_col3:
                v_filter = st.multiselect("Practice Venue", options=sorted(df['practice_location'].unique()), placeholder="Search Venue...")
            
            filtered_df = df.copy()
            if t_filter: filtered_df = filtered_df[filtered_df['faculty_incharge'].isin(t_filter)]
            if c_filter: filtered_df = filtered_df[filtered_df['program_category'].isin(c_filter)]
            if v_filter: filtered_df = filtered_df[filtered_df['practice_location'].isin(v_filter)]

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<span style='color: #8B949E !important;'>Displaying {len(filtered_df)} valid records. <b>Admin Info: Double-click 'Duration' or 'Run Sequence' to edit them. Press ENTER to sync data.</b></span>", unsafe_allow_html=True)
            
            display_cols = ['run_sequence', 'id', 'faculty_incharge', 'program_category', 'duration_mins', 'practice_location', 'Total_Students']
            grid_df = filtered_df[display_cols].copy()
            grid_df.columns = ['Sequence', 'ID', 'Incharge', 'Category', 'Duration (m)', 'Venue', 'Participants']
            
            final_df = st.data_editor(grid_df, use_container_width=True, hide_index=True, disabled=['ID', 'Incharge', 'Category', 'Venue', 'Participants'])
            
            changes_made = False
            conn = sqlite3.connect('bhavans_events.db')
            c = conn.cursor()
            
            for i in range(len(grid_df)):
                orig_dur = grid_df.iloc[i]['Duration (m)']
                new_dur = final_df.iloc[i]['Duration (m)']
                orig_seq = grid_df.iloc[i]['Sequence']
                new_seq = final_df.iloc[i]['Sequence']
                row_id = final_df.iloc[i]['ID']
                
                if orig_dur != new_dur or orig_seq != new_seq:
                    c.execute("UPDATE performance_registry SET duration_mins = ?, run_sequence = ? WHERE id = ?", (int(new_dur), int(new_seq), int(row_id)))
                    changes_made = True
                    
            conn.commit()
            conn.close()
            
            if changes_made:
                st.rerun()
            
            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Final Sequence", data=csv, file_name='bhavans_sequence_final.csv', mime='text/csv')
            
            st.markdown("<hr style='border: 1px solid #30363D;'>", unsafe_allow_html=True)
            
            st.markdown("<h4 style='color: #FF9933 !important; font-weight: bold;'>Systematic Deep Dive</h4>", unsafe_allow_html=True)
            st.markdown("<p style='color: #8B949E !important;'>Select a program to inspect technical requirements and student roster.</p>", unsafe_allow_html=True)
            
            if not filtered_df.empty:
                prog_dict = pd.Series(filtered_df['faculty_incharge'].values + " - " + filtered_df['program_category'].values, index=filtered_df['id']).to_dict()
                
                selected_id = st.selectbox("Search & Select Program to Inspect", options=list(prog_dict.keys()), format_func=lambda x: f"Form #{x}: {prog_dict[x]}")
                
                if selected_id:
                    row_data = df[df['id'] == selected_id].iloc[0]
                    
                    with st.container(border=True):
                        d_col1, d_col2 = st.columns(2)
                        
                        with d_col1:
                            st.markdown(f"<span style='color: #8B949E !important;'>Faculty Coordinator</span><br><strong style='font-size: 1.2rem;'>{row_data['faculty_incharge']}</strong>", unsafe_allow_html=True)
                            cat_name = row_data['custom_category_name'] if row_data['program_category'] == "Custom / Other" else row_data['program_category']
                            st.markdown(f"<br><span style='color: #8B949E !important;'>Performance Type</span><br><strong style='font-size: 1.2rem;'>{cat_name}</strong>", unsafe_allow_html=True)
                            
                        with d_col2:
                            st.markdown(f"<span style='color: #FF9933 !important;'>Technical & Prop Requirements</span><br><span style='font-size: 1.1rem;'>{row_data['technical_requisites'] if row_data['technical_requisites'] else 'None specified'}</span>", unsafe_allow_html=True)
                        
                        st.markdown("<hr style='border: 1px solid #30363D; margin: 15px 0;'>", unsafe_allow_html=True)
                        st.markdown("<span style='color: #8B949E !important;'>Participant Matrix Database</span>", unsafe_allow_html=True)
                        
                        try:
                            student_df = pd.DataFrame(json.loads(row_data['student_matrix']))
                            st.dataframe(student_df, use_container_width=True, hide_index=True)
                        except:
                            st.error("Error decrypting student matrix data.")
