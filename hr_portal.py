

import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import altair as alt   # charts
from pathlib import Path
import base64

def get_logo_base64():
    image_path = Path(__file__).parent / "logo.png"
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# ────────────────────────────────────────────────
# 1. DATABASE INIT
# ────────────────────────────────────────────────
DB = "rbo.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

cursor.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);

CREATE TABLE IF NOT EXISTS jdjs_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code TEXT UNIQUE,
    jd_text   TEXT
);

CREATE TABLE IF NOT EXISTS rbo_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    s_no INTEGER,
    unit TEXT, function TEXT, department TEXT,
    role_category TEXT, role_code TEXT, role TEXT,
    job_code TEXT, job TEXT,
    emp_no TEXT, emp_name TEXT,
    position_code TEXT, position TEXT, type_of_position TEXT,
    pos_bw_low TEXT, pos_bw_high TEXT, pos_match TEXT,
    availability TEXT, remarks TEXT,
    mpr_status TEXT, jd_issued TEXT,
    reporting_mgr_job_code TEXT, status TEXT, signed_off TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
try:
    cursor.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'Dark'")
    conn.commit()
except sqlite3.OperationalError:
    pass  # Column already exists

cursor.execute(
    "INSERT OR IGNORE INTO users (username,password) VALUES (?,?)",
    ("admin", "admin123")
)
conn.commit()
def show_header():
    st.markdown(f"""
    <div style='display: flex; align-items: center; justify-content: space-between;
                background-color: #e8f1fb; padding: 10px 16px; border-radius: 8px;
                margin-bottom: 16px; flex-wrap: wrap;'>
        <h2 style='margin: 0; color: #003366;'>CACPL HR RBO Master Data</h2>
        <div style='color: #003366; font-weight: bold; font-size: 16px;'>
            👤 {st.session_state.get("username", "Guest")}
        </div>
    </div>
    """, unsafe_allow_html=True)

# 2.1 THEME SWITCHER
# ────────────────────────────────────────────────
# ─── 2.1 FIXED THEME (blue-white + better fields visibility) ───
def apply_theme():
    st.markdown("""
    <style>
    /* Base theme styles */
    .stApp {
        background-color: #f3f9ff;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Sidebar */
    .stSidebar {
        background-color: #003366;
        padding-top: 1rem;
        border-right: 1px solid #c0d4e8;
    }

    .stSidebar h1, .stSidebar h2, .stSidebar h3,
    .stSidebar label, .stSidebar p, .stSidebar span {
        color: black !important;
        font-weight: bold;
    }

    .stSidebar .stRadio > div {
        background-color: #d0e4ff;
        border-radius: 8px;
        padding: 6px;
        color: black !important;
        font-weight: bold;
    }

    /* Inputs */
    .stTextInput input, .stSelectbox div, .stNumberInput input,
    .stTextArea textarea, .stDateInput input {
        color: #003366 !important;
        background-color: #ffffff !important;
    }

    label, .stSelectbox label, .stTextInput label {
        color: #003366 !important;
        font-weight: 500;
    }

    .stSelectbox div[role="button"]:hover {
        background-color: #d6eaff !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #003366;
        color: white;
        border-radius: 5px;
        font-weight: bold;
    }

    .stSidebar button {
        background-color: #005cbf;
        color: white;
    }

    /* Metrics */
    .stMetric label {
        color: #003366;
    }

    /* Logout button */
    .logout-button {
        position: fixed;
        bottom: 30px;
        left: 15px;
        width: calc(100% - 30px);
    }

    .logout-button button {
        background-color: #003366;
        color: white;
        width: 100%;
        border: none;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }

    /* Fix spacing in forms */
    .stTextInput, .stSelectbox, .stNumberInput {
        margin-bottom: 10px;
    }

    /* Responsive adjustments for mobile */
    @media only screen and (max-width: 768px) {
        h1, h2, h3, h4, .stHeader {
            font-size: 18px !important;
        }
        .stButton>button, .stSelectbox div[role="button"], input, textarea, select {
            font-size: 14px !important;
            padding: 6px 10px !important;
        }
        .stMetric label {
            font-size: 14px !important;
        }
        .stApp {
            padding: 0 10px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
# ────────────────────────────────────────────────
# 2. SESSION / RERUN
# ────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def _rerun():
    (st.rerun if hasattr(st, "rerun") else st.experimental_rerun)()



# ────────────────────────────────────────────────
# 3. AUTH PAGES
# ────────────────────────────────────────────────
def auth_page():
    st.title("CACPL HR RBO Entry")
    login_tab, reg_tab = st.tabs(["Login", "Register"])

    with login_tab:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            row = cursor.execute("SELECT password, theme FROM users WHERE username=?", (u,)).fetchone()
            if row and row[0] == p:
                st.session_state.logged_in = True
                st.session_state.username = u
                apply_theme()  # ✅ Blue & white theme applied here
                _rerun()

            else:
                st.error("Invalid credentials")

    with reg_tab:
        nu = st.text_input("New username")
        np = st.text_input("New password", type="password")
        np2 = st.text_input("Repeat password", type="password")
        theme_pref = st.selectbox("Default Theme", ["Dark", "Light"])
        if st.button("Create account"):
            if np != np2:
                st.warning("Passwords do not match")
            else:
                try:
                    cursor.execute("INSERT INTO users (username,password,theme) VALUES (?,?,?)", (nu, np, theme_pref))
                    conn.commit()
                    st.success("Account created. Please login.")
                except:
                    st.error("Username already exists")
# ────────────────────────────────────────────────
# 4. MASTER ENTRY
# ────────────────────────────────────────────────
def master_entry():
    show_header()
    st.header("Master Entry")
    with st.form("master"):
        if st.columns(1):  # stack vertically on small devices
            c1 = st.container()
            c2 = st.container()
            c3 = st.container()
        else:
            c1, c2, c3 = st.columns(3)
        s_no              = c1.number_input("S.No", min_value=1, step=1)
        unit              = c1.text_input("Unit")
        function          = c2.text_input("Function")
        department        = c3.text_input("Department")
        role_category     = c1.text_input("Role Category")
        role_code         = c2.text_input("Role Code")
        role              = c3.text_input("Role")
        job_code          = c1.text_input("Job Code")
        job               = c2.text_input("Job")
        emp_no            = c3.text_input("Emp No")
        emp_name          = c1.text_input("Emp Name")
        position_code     = c2.text_input("Position Code")
        position          = c3.text_input("Position")
        type_of_pos       = c1.text_input("Type of Position")
        pos_bw_low        = c2.text_input("Band Low")
        pos_bw_high       = c3.text_input("Band High")
        pos_match         = c1.selectbox("Position Match", ["MATCH","MISMATCH","—"])
        availability      = c2.selectbox("Availability", ["OCCUPIED","Vacant","Resigned"])
        remarks           = c3.text_input("Remarks")
        mpr_status        = c1.selectbox("MPR Status", ["Raised","Closed","—"])
        jd_issued         = c2.selectbox("JD Issued", ["Yes","No"])
        rpt_mgr_code      = c3.text_input("Reporting Manager Job Code")
        status            = c1.selectbox("Workflow Status", ["Completed","In‑Progress"])
        signed_off        = c2.selectbox("Signed Off", ["Yes","No"])

        if st.form_submit_button("Save row"):
            cursor.execute("""
            INSERT INTO rbo_master (
                s_no, unit, function, department, role_category, role_code, role,
                job_code, job, emp_no, emp_name, position_code, position,
                type_of_position, pos_bw_low, pos_bw_high, pos_match,
                availability, remarks, mpr_status, jd_issued,
                reporting_mgr_job_code, status, signed_off
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                s_no, unit, function, department, role_category, role_code, role,
                job_code, job, emp_no, emp_name, position_code, position,
                type_of_pos, pos_bw_low, pos_bw_high, pos_match,
                availability, remarks, mpr_status, jd_issued,
                rpt_mgr_code, status, signed_off
            ))
            conn.commit(); st.success("Row saved")

# ────────────────────────────────────────────────
# 5. GRID EDITOR
# ────────────────────────────────────────────────
def grid_editor():
    show_header()
    st.header("Inline Grid Editor")
    df = pd.read_sql_query("SELECT * FROM rbo_master", conn)
    if df.empty:
        st.info("No data yet."); return
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("Save all changes"):
        conn.execute("DELETE FROM rbo_master")
        edited.to_sql("rbo_master", conn, if_exists="append", index=False)
        st.success("Database updated")

# ────────────────────────────────────────────────
# 6. IMPORT / EXPORT  (handles any sheet & header row)
# ────────────────────────────────────────────────
def import_export():
    show_header()
    st.header(" Import /Export Excel")
    uploaded = st.file_uploader("Upload RBO Master or JDJS workbook", type=["xlsx"])

    if uploaded:
        xl = pd.ExcelFile(uploaded)
        sheet_names = xl.sheet_names
        sheet = st.selectbox("Pick sheet", sheet_names)

        header_row = st.number_input("Header row (1 = first row)", value=5, step=1)
        header_idx = int(header_row) - 1

        df_raw = xl.parse(sheet, header=header_idx)
        df_raw.columns = pd.Index([str(c).strip() for c in df_raw.columns])
        is_jdjs = {"Job", "Role", "Role Code"}.issubset(set(df_raw.columns))

        if is_jdjs:
            df = df_raw.loc[:, ["Role Code","Job"]].rename(columns={"Role Code":"role_code","Job":"jd_text"})
            cursor.execute("DELETE FROM jdjs_master"); conn.commit()
            df.to_sql("jdjs_master", conn, if_exists="append", index=False)
            st.success(f"JDJS rows imported: {len(df)}")

        else:
            df = df_raw.loc[:, ~df_raw.columns.str.contains('^Unnamed')]

            colmap = {
                "S.No":"s_no","Unit":"unit","Function":"function","Department":"department",
                "Role Category":"role_category","Role Code":"role_code","Role":"role",
                "Job Code":"job_code","Job":"job","Emp No":"emp_no","Emp Name":"emp_name",
                "Position Code":"position_code","Position":"position",
                "Type of Position":"type_of_position","Position Bandwidth (Low)":"pos_bw_low",
                "Position Bandwidth (High)":"pos_bw_high","Position Match":"pos_match",
                "Availability":"availability","Remarks":"remarks","MPR Status":"mpr_status",
                "JD Issued":"jd_issued","Reporting Manager Job Code":"reporting_mgr_job_code",
                "Status":"status","Signed Off":"signed_off",
            }
            df.rename(columns=colmap, inplace=True)
            df = df[[c for c in colmap.values() if c in df.columns]]

            if df.empty:
                st.error(" No matching columns – adjust header row or mapping."); return

            df.to_sql("rbo_master", conn, if_exists="append", index=False)
            st.success(f"RBO rows imported: {len(df)}")

    if st.button(" Download snapshot"):
        snap = pd.read_sql_query("SELECT * FROM rbo_master", conn)
        snap.to_excel("RBO_snapshot.xlsx", index=False)
        with open("RBO_snapshot.xlsx","rb") as f:
            st.download_button("Download Excel", f, file_name="RBO_snapshot.xlsx")

# ────────────────────────────────────────────────
# 7. DASHBOARD  (new)
# ────────────────────────────────────────────────
def dashboard():
    show_header()
    st.header("DASHBOARD")
    df = pd.read_sql_query("SELECT * FROM rbo_master", conn)
    if df.empty:
        st.info("No data yet.")
        return

    units = sorted(df['unit'].dropna().unique())
    depts = sorted(df['department'].dropna().unique())
    u_sel = st.multiselect("Unit filter", units, default=units)
    d_sel = st.multiselect("Dept filter", depts, default=depts)
    filt = df[df['unit'].isin(u_sel) & df['department'].isin(d_sel)]

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Rows", len(filt))
    k2.metric("Vacant", int((filt['availability']=="Vacant").sum()))
    k3.metric("MPR Raised", int((filt['mpr_status']=="Raised").sum()))
    k4.metric("JD Pending", int((filt['jd_issued']=="No").sum()))

    bar = alt.Chart(filt).mark_bar(color='#007acc').encode(
        x=alt.X('availability:N', title="Availability"),
        y=alt.Y('count()', title="Count"),
        tooltip=['count()']
    )
    st.altair_chart(bar, use_container_width=True)

    pie = alt.Chart(filt).mark_arc().encode(
        theta='count():Q', color='pos_match:N',
        tooltip=['pos_match:N','count():Q']
    )
    st.altair_chart(pie, use_container_width=True)

    with st.expander("Show table"):
        st.dataframe(filt.reset_index(drop=True))

# ────────────────────────────────────────────────
# 8. SEARCH + EDIT  (with JD preview)
# ────────────────────────────────────────────────
def _idx(lst,val): return lst.index(val) if val in lst else 0
def search_and_edit():
    show_header()
    st.header(" Search + Edit")

    # Step 1: Fetch unique values from the database for dropdown suggestions
    role_codes = [r[0] for r in cursor.execute("SELECT DISTINCT role_code FROM rbo_master WHERE role_code IS NOT NULL").fetchall()]
    emp_nos = [e[0] for e in cursor.execute("SELECT DISTINCT emp_no FROM rbo_master WHERE emp_no IS NOT NULL").fetchall()]
    # Step 2: Create a form with searchable dropdowns
    with st.form("search"):
        col1, col2 = st.columns(2)

        # Dropdowns with optional empty choice at the top
        emp = col1.selectbox("Search Emp No", options=[""] + emp_nos)
        role = col2.selectbox("Search Role Code", options=[""] + role_codes)

        # Submit button inside the form
        go = st.form_submit_button("Search")
        if not go: return

    # Step 3: Build the WHERE clause dynamically
    cond, params = [], []
    if emp:
        cond.append("emp_no LIKE ?")
        params.append(f"%{emp}%")  # Allows partial matching
    if role:
        cond.append("role_code LIKE ?")
        params.append(f"%{role}%")

    if not cond:
        st.warning("Please enter or choose a value to search")
        return

    # Step 4: Run the query and fetch the record
    query = f"SELECT * FROM rbo_master WHERE {' AND '.join(cond)} LIMIT 1"
    row = cursor.execute(query, params).fetchone()

    if not row:
        st.warning("No match found.")
        return

    # Step 5: If a row is found, proceed to editing form (your existing code)
    rec = dict(zip([d[0] for d in cursor.description], row))

    jd = cursor.execute("SELECT jd_text FROM jdjs_master WHERE role_code=?", (rec['role_code'],)).fetchone()
    if jd and st.sidebar.button(" JD Preview"):
        st.sidebar.write(jd[0] or "_No JD_")

    with st.form("edit"):
        c1,c2,c3=st.columns(3)
        s_no=c1.number_input("S.No",value=rec['s_no'])
        unit=c1.text_input("Unit",value=rec['unit'])
        function=c2.text_input("Function",value=rec['function'])
        department=c3.text_input("Department",value=rec['department'])
        role_category=c1.text_input("Role Category",value=rec['role_category'])
        role_code=c2.text_input("Role Code",value=rec['role_code'])
        role_txt=c3.text_input("Role",value=rec['role'])
        job_code=c1.text_input("Job Code",value=rec['job_code'])
        job=c2.text_input("Job",value=rec['job'])
        emp_no=c3.text_input("Emp No",value=rec['emp_no'])
        emp_name=c1.text_input("Emp Name",value=rec['emp_name'])
        position_code=c2.text_input("Position Code",value=rec['position_code'])
        position=c3.text_input("Position",value=rec['position'])
        type_pos=c1.text_input("Type of Position",value=rec['type_of_position'])
        pos_low=c2.text_input("Band Low",value=rec['pos_bw_low'])
        pos_high=c3.text_input("Band High",value=rec['pos_bw_high'])
        pos_match=c1.selectbox("Position Match",["MATCH","MISMATCH","—"],index=_idx(["MATCH","MISMATCH","—"],rec['pos_match']))
        avail=c2.selectbox("Availability",["OCCUPIED","Vacant","Resigned"],index=_idx(["OCCUPIED","Vacant","Resigned"],rec['availability']))
        remarks=c3.text_input("Remarks",value=rec['remarks'])
        mpr=c1.selectbox("MPR Status",["Raised","Closed","—"],index=_idx(["Raised","Closed","—"],rec['mpr_status']))
        jd_iss=c2.selectbox("JD Issued",["Yes","No"],index=_idx(["Yes","No"],rec['jd_issued']))
        rpt_mgr=c3.text_input("Reporting Manager Job Code",value=rec['reporting_mgr_job_code'])
        status=c1.selectbox("Status",["Completed","In‑Progress"],index=_idx(["Completed","In‑Progress"],rec['status']))
        signed=c2.selectbox("Signed Off",["Yes","No"],index=_idx(["Yes","No"],rec['signed_off']))
        if st.form_submit_button("Update"):
            cursor.execute("""
            UPDATE rbo_master SET
                s_no=?,unit=?,function=?,department=?,role_category=?,role_code=?,role=?,
                job_code=?,job=?,emp_no=?,emp_name=?,position_code=?,position=?,type_of_position=?,
                pos_bw_low=?,pos_bw_high=?,pos_match=?,availability=?,remarks=?,mpr_status=?,
                jd_issued=?,reporting_mgr_job_code=?,status=?,signed_off=? WHERE id=?""",
            (s_no,unit,function,department,role_category,role_code,role_txt,
             job_code,job,emp_no,emp_name,position_code,position,type_pos,
             pos_low,pos_high,pos_match,avail,remarks,mpr,jd_iss,rpt_mgr,status,signed,rec['id']))
            conn.commit(); st.success("Updated")

# ────────────────────────────────────────────────
# 9. VIEW DATA  (simple table)
# ────────────────────────────────────────────────
def view_data():
    show_header()
    st.header("Full Table")
    with st.container():
        st.markdown("""
            <style>
                .scroll-table {
                    overflow-x: auto;
                }
            </style>
            <div class='scroll-table'>
        """, unsafe_allow_html=True)
        st.dataframe(pd.read_sql_query("SELECT * FROM rbo_master", conn), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ────────────────────────────────────────────────
# 10. MAIN MENU ROUTER
# ────────────────────────────────────────────────
def main_app():
    apply_theme()
    st.sidebar.markdown("## " + st.session_state.username)

    menu_options = [
        "Dashboard", "Master Entry", "Grid Editor",
        "Import / Export", "Search + Edit", "View Data"
    ]
    page = st.sidebar.radio(" Menu", menu_options)

    if page == "Dashboard": dashboard()
    elif page == "Master Entry": master_entry()
    elif page == "Grid Editor": grid_editor()
    elif page == "Import / Export": import_export()
    elif page == "Search + Edit": search_and_edit()
    elif page == "View Data": view_data()

    # Add logout button normally using Streamlit, no query
    if st.sidebar.button(" Logout", help="Logout from session"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        _rerun()


# ────────────────────────────────────────────────
# 11. ENTRY POINT
# ────────────────────────────────────────────────
if st.session_state.logged_in:
    main_app()
else:
    auth_page()
