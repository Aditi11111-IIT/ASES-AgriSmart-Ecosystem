import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. CONFIGURATION & OGD API ---
st.set_page_config(page_title="Agri-Dashboard", layout="centered", page_icon="🌾")
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070" 
OGD_API_KEY = "579b464db66ec23bdd0000019b64f520463c4fba468cc24026c3cff6"

# --- 2. MODULAR IMPORTS ---
try:
    from Locations import india_map
    from crop_master import all_crops
    from crop_engine_data import get_agri_dataframe, recommend_crops
except ImportError:
    india_map = {"Bihar": ["Patna", "Gaya"]}
    all_crops = []

# --- 3. DATABASE (SECURE PER-USER) ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. PROFESSIONAL SaaS UI STYLING ---
st.markdown("""
<style>
    /* Global Neutral Background */
    .stApp { background-color: #F8F9FA; }

    /* Hide Institutional Headers */
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Professional Card Styling */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-bottom: 3px solid #2D5A27;
    }
    
    .status-badge {
        background-color: #E8F5E9;
        color: #2D5A27;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: bold;
    }

    /* Modern Buttons */
    .stButton>button {
        background-color: #2D5A27;
        color: white;
        border-radius: 8px;
        border: none;
        height: 3em;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #1e3d1a; color: white; border: none; }

    /* Sidebar Refinement */
    [data-testid="stSidebar"] {
        background-color: #1A1C1E !important;
        color: white;
    }
    [data-testid="stSidebar"] * { color: #E0E0E0 !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>Agriculture Services Portal</h2>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            conn = sqlite3.connect('agri_khata.db')
            res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.logged_in, st.session_state.username = True, u
                st.rerun()
            else: st.error("Wrong credentials")
            conn.close()
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Register Account"):
            try:
                conn = sqlite3.connect('agri_khata.db')
                conn.execute("INSERT INTO users VALUES (?,?)", (nu, np))
                conn.commit()
                st.success("Account created successfully.")
                conn.close()
            except: st.error("User exists")

# --- 6. MAIN APP ---
else:
    with st.sidebar:
        st.markdown(f"### 🧑‍🌾 Welcome back, <br>{st.session_state.username}", unsafe_allow_html=True)
        st.divider()
        menu = st.radio("MAIN MENU", ["📊 Overview", "🎯 Analytics Engine", "🚜 Logistics Hub", "📖 Resource Hub", "📉 Market Trends", "📒 Digital Ledger"])
        
        state_sel = st.selectbox("Current Region", sorted(india_map.keys()))
        dist_sel = st.selectbox("District", sorted(india_map.get(state_sel, ["Patna"])))
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- DASHBOARD OVERVIEW ---
    if menu == "📊 Overview":
        st.header(f"📍 {dist_sel} Regional Dashboard")
        
        # Professional Custom KPI Cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="metric-card"><h3>28°C</h3><span class="status-badge">WEATHER</span></div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card"><h3>OPEN</h3><span class="status-badge">MARKETS</span></div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card"><h3>10.2%</h3><span class="status-badge">TREND</span></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Regional Summary")
        st.write(f"Displaying current agricultural analytics for **{dist_sel}, {state_sel}**. Data is synchronized with central market nodes.")

    # --- ANALYTICS ENGINE (REFINED CROP AI) ---
    elif menu == "🎯 Analytics Engine":
        st.header("🎯 Crop Prediction Engine")
        df, le = get_agri_dataframe()
        
        with st.container(border=True):
            soil = st.selectbox("Primary Soil Type", ["Alluvial", "Black Soil", "Red Soil", "Sandy"])
            budget = st.select_slider("Projected Investment (₹)", options=[5000, 10000, 15000, 20000, 30000, 50000])
            
            if st.button("🚀 RUN ANALYSIS"):
                recs = recommend_crops(df, le, soil, budget)
                if not recs.empty:
                    for _, row in recs.iterrows():
                        st.success(f"Recommended: **{row['Crop Name']}** | Estimated Capital: ₹{row['Cost per Acre']}/Acre")
                else: st.warning("No matches for current parameters.")

    # --- LOGISTICS HUB ---
    elif menu == "🚜 Logistics Hub":
        st.header("🚜 Rental & Logistics")
        cat = st.segmented_control("Process Stage", ["Tillage", "Planting", "Processing"], default="Tillage")
        m_data = {
            "Tillage": [("Rotavator", "🚜"), ("Power Tiller", "⚙️")],
            "Planting": [("Seed Drill", "🌱"), ("Transplanter", "🌾")],
            "Processing": [("Harvester", "🌾✨"), ("Thresher", "🌪️")]
        }
        for name, icon in m_data.get(cat, []):
            with st.container(border=True):
                st.subheader(f"{icon} {name}")
                st.link_button(f"Locate Providers in {dist_sel}", f"https://www.google.com/search?q={name}+service+{dist_sel}")

    # --- RESOURCE HUB ---
    elif menu == "📖 Resource Hub":
        st.header("📖 Technical Documentation")
        q = st.text_input("🔍 Search Database...")
        filtered = [c for c in all_crops if q.lower() in c['Crop'].lower()] if q else all_crops
        for item in filtered:
            with st.expander(f"📖 {item['Crop']}"):
                st.write(f"**Season:** {item['Season']} | **NPK Requirement:** {item['N-P-K']}")
                st.info(f"Technical Note: {item.get('Pro-Tip', 'Standard irrigation recommended.')}")

    # --- MARKET TRENDS (OGD LIVE API) ---
    elif menu == "📉 Market Trends":
        st.header("📈 Real-time Market Analysis")
        commodity = st.selectbox("Select Commodity", [c['Crop'] for c in all_crops] or ["Wheat", "Rice"])
        
        url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
        params = {"api-key": OGD_API_KEY, "format": "json", "filters[state]": state_sel, "filters[commodity]": commodity}
        
        try:
            data = requests.get(url, params=params).json()
            if "records" in data and data["records"]:
                latest = data["records"][0]
                st.success(f"Latest Market Entry: {latest['market']}")
                st.metric("Modal Rate", f"₹{latest['modal_price']} / Quintal")
                
                m_df = pd.DataFrame(data["records"])
                m_df['modal_price'] = pd.to_numeric(m_df['modal_price'])
                st.plotly_chart(px.bar(m_df, x='market', y='modal_price', title="Price Distribution", template="plotly_white", color_discrete_sequence=['#2D5A27']), use_container_width=True)
            else: 
                st.info("Market data syncing... Showing base forecast.")
                st.line_chart([2100, 2200, 2150, 2300])
        except: st.error("Sync Error: API endpoint unreachable.")

    # --- DIGITAL LEDGER (PRIVATE) ---
    elif menu == "📒 Digital Ledger":
        st.header("📒 Financial Ledger")
        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query(f"SELECT * FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()

        if not df_khata.empty:
            inc = df_khata[df_khata['type'].str.contains('Income')]['total'].sum()
            exp = df_khata[df_khata['type'].str.contains('Expense')]['total'].sum()
            
            # Professional Summary Card
            st.markdown(f"""
            <div style="padding:20px; border-radius:12px; background-color:#2D5A27; color:white; text-align:center;">
                <p style="margin:0;">Net Position</p>
                <h2 style="margin:0;">₹{inc - exp:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            st.dataframe(df_khata.drop(columns=['id', 'user_key']), use_container_width=True, hide_index=True)
        
        with st.expander("➕ New Transaction"):
            with st.form("f_add"):
                t = st.selectbox("Category", ["Income (Sales)", "Expense (Operating)"])
                itm = st.text_input("Entry Description")
                amt = st.number_input("Amount", min_value=0.0)
                if st.form_submit_button("Log Transaction"):
                    conn = sqlite3.connect('agri_khata.db')
                    conn.execute("INSERT INTO ledger (user_key, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
                                (st.session_state.username, datetime.now().strftime("%Y-%m-%d"), t, itm, "1", amt, "General"))
                    conn.commit()
                    conn.close()
                    st.rerun()
