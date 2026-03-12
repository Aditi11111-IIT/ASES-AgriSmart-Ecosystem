import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# --- 1. CONFIGURATION & OGD API ---
st.set_page_config(page_title="ASES: Agri-Smart", layout="centered", page_icon="🌾")
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
OGD_API_KEY = "579b464db66ec23bdd0000019b64f520463c4fba468cc24026c3cff6"

# --- 2. MODULAR IMPORTS ---
try:
    from Locations import india_map
    from crop_master import all_crops
    from crop_engine_data import get_agri_dataframe, recommend_crops
    from schemes_db import get_state_schemes, get_central_schemes
except ImportError:
    st.error("Missing Modules! Ensure Locations.py, crop_master.py, and schemes_db.py are in the same folder.")
    india_map = {"Bihar": ["Patna", "Gaya"]}
    all_crops = []

# --- 3. DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect('agri_khata.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS ledger 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT,
                  date TEXT, type TEXT, item TEXT, qty TEXT, total REAL, season TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. MOBILE-FRIENDLY CSS ---
st.markdown("""
<style>
    .stApp { max-width: 850px; margin: 0 auto; }
    .mobile-card { padding: 15px; border-radius: 12px; border: 1px solid rgba(46,125,50,0.3); background-color: rgba(46,125,50,0.05); margin-bottom: 12px; }
    .scheme-card { padding: 20px; border-radius: 12px; background-color: #e3f2fd; border-left: 8px solid #1976d2; margin-bottom: 15px; }
    .central-card { padding: 20px; border-radius: 12px; background-color: #f1f8e9; border-left: 8px solid #2e7d32; margin-bottom: 15px; }
    .stButton>button { border-radius: 12px; height: 3.5em; font-weight: bold; width: 100%; }
    .call-btn { background-color: #ffc107 !important; color: black !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 5. AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🌾 Agri-Smart Ecosystem")
    t_log, t_sign = st.tabs(["🔐 Login", "📝 Sign Up"])
    with t_log:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            conn = sqlite3.connect('agri_khata.db')
            res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.logged_in, st.session_state.username = True, u
                st.rerun()
            else: st.error("Invalid credentials")
            conn.close()
    with t_sign:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                conn = sqlite3.connect('agri_khata.db')
                conn.execute("INSERT INTO users VALUES (?,?)", (nu, np))
                conn.commit()
                st.success("Account created! Go to Login.")
                conn.close()
            except: st.error("Username already taken.")

# --- 6. MAIN APP INTERFACE ---
else:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=90)
        st.subheader(f"User: {st.session_state.username}")
        menu = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🎯 AgriAI Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📉 Price Trends", "📒 Agri Ledger"])
        
        # State & District Selection
        state_list = sorted(list(india_map.keys()))
        st_sel = st.selectbox("Your State", state_list)
        dt_sel = st.selectbox("Your District", sorted(india_map.get(st_sel, ["Patna"])))
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- DASHBOARD ---
    if menu == "🏠 Dashboard":
        st.header(f"📍 {dt_sel}, {st_sel}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Status", "Online")
        c2.metric("Project", "ASES-IITP")
        c3.metric("Nodes", "4 Active")
        st.info("💡 Tip: Use 'AgriAI Engine' to find crops matching your soil and budget.")

    # --- AGRIAI ENGINE ---
    elif menu == "🎯 AgriAI Engine":
        st.header("🎯 Crop Recommendation Engine")
        df, le = get_agri_dataframe()
        soil = st.selectbox("Select Soil Type", ["Alluvial", "Black Soil", "Red Soil", "Sandy", "Loamy", "Heavy Soil"])
        budget = st.slider("Investment Budget (₹/Acre)", 5000, 50000, 15000)
        
        if st.button("🚀 GET RECOMMENDATIONS"):
            recs = recommend_crops(df, le, soil, budget)
            if not recs.empty:
                for _, row in recs.iterrows():
                    st.markdown(f'''<div class="mobile-card">
                        <b>🌱 {row["Crop Name"]}</b><br>
                        <small>Estimated Cost: ₹{row["Cost per Acre"]}/Acre</small>
                    </div>''', unsafe_allow_html=True)
            else: st.warning("No matches. Try adjusting your budget.")

    # --- RENTAL HUB ---
    elif menu == "🚜 Rental Hub":
        st.header("🚜 Machinery Rentals")
        cat = st.segmented_control("Service Category", ["Preparation", "Sowing", "Harvesting"], default="Preparation")
        machines = {"Preparation": [("Rotavator", "🚜")], "Sowing": [("Seed Drill", "🌱")], "Harvesting": [("Thresher", "🌪️")]}
        for name, icon in machines.get(cat, []):
            with st.container(border=True):
                st.subheader(f"{icon} {name}")
                st.link_button(f"Find in {dt_sel}", f"https://www.google.com/search?q={name}+rental+service+in+{dt_sel}")

    # --- KNOWLEDGE HUB ---
    elif menu == "📚 Knowledge Hub":
        st.header("📚 Detailed Crop Library")
        q = st.text_input("🔍 Search Crop...").strip()
        filtered = [c for c in all_crops if q.lower() in c['Crop'].lower()] if q else all_crops
        for item in filtered:
            with st.expander(f"📖 {item['Crop']} ({item['Type']})"):
                st.write(f"**Season:** {item['Season']} | **Water:** {item['Water']}")
                st.success(f"💡 **Expert Tip:** {item['Pro-Tip']}")

    # --- GOVT SCHEMES (FIXED TYPEERROR) ---
    elif menu == "🏛️ Govt Schemes":
        st.header("🏛️ Welfare & Portal Access")
        try:
            state_data = get_state_schemes(st_sel)
        except:
            state_data = None
            
        central_data = get_central_schemes()
        tab_s, tab_c = st.tabs(["📍 State Schemes", "🇮🇳 Central Schemes"])
        with tab_s:
            if isinstance(state_data, dict) and 'link' in state_data:
                st.markdown(f'''<div class="scheme-card"><h3>🌟 {state_data.get('name', 'State Scheme')}</h3><p>{state_data.get('desc', '')}</p><a href="{state_data['link']}" target="_blank" class="call-btn">📝 Open Official Portal</a></div>''', unsafe_allow_html=True)
            else: st.info(f"No specific links for {st_sel}. Please check Central Schemes.")
        with tab_c:
            for cs in central_data:
                st.markdown(f'<div class="central-card"><h4>🏢 {cs["name"]}</h4><p>{cs["desc"]}</p><a href="{cs["link"]}" target="_blank" style="color:#2e7d32; font-weight:bold;">Visit Portal →</a></div>', unsafe_allow_html=True)

    # --- PRICE TRENDS (FIXED LIVE GRAPH) ---
    elif menu == "📉 Price Trends":
        st.header("📈 Live Mandi Prices")
        # Define common commodities to ensure user gets results
        sel_c = st.selectbox("Choose Commodity", ["Paddy(Dhan)", "Wheat", "Maize", "Barley", "Mustard", "Onion", "Potato"])
        
        url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
        params = {"api-key": OGD_API_KEY, "format": "json", "filters[state]": st_sel, "filters[commodity]": sel_c}
        
        try:
            res = requests.get(url, params=params).json()
            if "records" in res and len(res["records"]) > 0:
                mandi_df = pd.DataFrame(res["records"])
                mandi_df['modal_price'] = pd.to_numeric(mandi_df['modal_price'], errors='coerce')
                
                latest = mandi_df.iloc[0]
                st.metric(f"Mandi Price ({latest['market']})", f"₹{latest['modal_price']} / Qtl")
                
                fig = px.bar(mandi_df, x='market', y='modal_price', color='modal_price', color_continuous_scale='Greens', labels={'modal_price': 'Price (₹/Qtl)'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Live data for {sel_c} in {st_sel} is currently unavailable.")
                st.info("Try selecting 'Paddy(Dhan)' or 'Wheat' as they are more commonly reported.")
        except: st.error("Connection Error with Govt API.")

    # --- AGRI LEDGER ---
    elif menu == "📒 Agri Ledger":
        st.header("📒 Private Digital Ledger")
        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query("SELECT * FROM ledger WHERE user_key=?", conn, params=(st.session_state.username,))
        conn.close()

        if not df_khata.empty:
            df_khata['total'] = pd.to_numeric(df_khata['total'], errors='coerce')
            st.subheader(f"Total Profit: ₹{df_khata[df_khata['type'].str.contains('Income')]['total'].sum() - df_khata[df_khata['type'].str.contains('Expense')]['total'].sum():,.2f}")
            st.dataframe(df_khata.drop(columns=['id', 'user_key']), use_container_width=True, hide_index=True)
        else: st.info("No personal records found.")

        with st.expander("➕ Add Transaction"):
            with st.form("new_entry", clear_on_submit=True):
                t_type = st.selectbox("Category", ["Income (Sales)", "Expense (Seeds/Labor)", "Expense (Machinery)"])
                t_item, t_amt = st.text_input("Description"), st.number_input("Amount (₹)", min_value=0.0)
                if st.form_submit_button("Save to Ledger"):
                    conn = sqlite3.connect('agri_khata.db')
                    conn.execute("INSERT INTO ledger (user_key, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
                                (st.session_state.username, datetime.now().strftime("%Y-%m-%d"), t_type, t_item, "1", t_amt, "Current"))
                    conn.commit()
                    conn.close()
                    st.rerun()
