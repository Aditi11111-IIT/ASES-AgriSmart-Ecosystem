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
    st.error("One or more modules (Locations, crop_master, etc.) are missing!")
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

# --- 4. MOBILE-FRIENDLY CSS ---
st.markdown("""
<style>
    .stApp { max-width: 850px; margin: 0 auto; }
    .mobile-card { 
        padding: 15px; border-radius: 12px; 
        border: 1px solid rgba(46, 125, 50, 0.3); 
        background-color: rgba(46, 125, 50, 0.05);
        margin-bottom: 12px;
    }
    .scheme-card {
        padding: 20px; border-radius: 12px; background-color: #e3f2fd; 
        border-left: 8px solid #1976d2; margin-bottom: 15px;
    }
    .central-card {
        padding: 20px; border-radius: 12px; background-color: #f1f8e9; 
        border-left: 8px solid #2e7d32; margin-bottom: 15px;
    }
    .stButton>button { border-radius: 12px; height: 3.5em; font-weight: bold; width: 100%; }
    .call-btn { 
        background-color: #ffc107 !important; color: black !important; 
        padding: 12px; border-radius: 10px; text-decoration: none; 
        display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }
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
        # Added Govt Schemes to the radio menu
        menu = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🎯 AgriAI Engine", "🚜 Rental Hub", "📚 Knowledge Hub", "🏛️ Govt Schemes", "📉 Price Trends", "📒 Agri Ledger"])
        
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
                        <small>Estimated Cost: ₹{row["Cost per Acre"]}/Acre</small><br>
                        <small>Recommended Sowing: Month {int(row["Sowing Month"])}</small>
                    </div>''', unsafe_allow_html=True)
            else: st.warning("No matches. Try adjusting your budget.")

    # --- RENTAL HUB ---
    elif menu == "🚜 Rental Hub":
        st.header("🚜 Machinery Rentals")
        cat = st.segmented_control("Service Category", ["Preparation", "Sowing", "Harvesting"], default="Preparation")
        machines = {
            "Preparation": [("Rotavator", "🚜"), ("Power Tiller", "⚙️")],
            "Sowing": [("Seed Drill", "🌱"), ("Rice Transplanter", "🌾")],
            "Harvesting": [("Combine Harvester", "🌾✨"), ("Thresher", "🌪️")]
        }
        for name, icon in machines.get(cat, []):
            with st.container(border=True):
                st.subheader(f"{icon} {name}")
                st.link_button(f"Find in {dt_sel}", f"https://www.google.com/search?q={name}+rental+service+in+{dt_sel}")
                st.markdown(f'<a href="tel:18001801551" class="call-btn">📞 Call Govt Helpline</a>', unsafe_allow_html=True)

    # --- KNOWLEDGE HUB ---
    elif menu == "📚 Knowledge Hub":
        st.header("📚 Detailed Crop Library")
        q = st.text_input("🔍 Search Crop...").strip()
        filtered = [c for c in all_crops if q.lower() in c['Crop'].lower()] if q else all_crops
        for item in filtered:
            with st.expander(f"📖 {item['Crop']} ({item['Type']})"):
                c_a, c_b = st.columns(2)
                c_a.write(f"**Season:** {item['Season']}")
                c_a.write(f"**Soil:** {item['Soil']}")
                c_b.write(f"**N-P-K:** {item['N-P-K']}")
                c_b.write(f"**Water:** {item['Water']}")
                st.success(f"💡 **Expert Tip:** {item['Pro-Tip']}")

    # --- GOVT SCHEMES (NEW INTEGRATION) ---
    elif menu == "🏛️ Govt Schemes":
        st.header("🏛️ Welfare & Portal Access")
        state_data = get_state_schemes(st_sel)
        central_data = get_central_schemes()
        
        tab_s, tab_c = st.tabs(["📍 State Schemes", "🇮🇳 Central Schemes"])
        
        with tab_s:
            if state_data:
                st.markdown(f"""
                    <div class="scheme-card">
                        <h3 style="color: #1976d2;">🌟 {state_data['name']}</h3>
                        <p>{state_data['desc']}</p>
                        <a href="{state_data['link']}" target="_blank" class="call-btn">📝 Register on Official Portal</a>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"No specific portal links found for {st_sel}. Please check Central Schemes.")

        with tab_c:
            for cs in central_data:
                st.markdown(f"""
                    <div class="central-card">
                        <h4 style="color: #2e7d32;">🏢 {cs['name']}</h4>
                        <p style="font-size: 0.9em;">{cs['desc']}</p>
                        <a href="{cs['link']}" target="_blank" style="color: #2e7d32; font-weight: bold;">Visit Portal →</a>
                    </div>
                """, unsafe_allow_html=True)

    # --- PRICE TRENDS ---
    elif menu == "📉 Price Trends":
        st.header("📈 Live Mandi Prices")
        c_names = [c['Crop'] for c in all_crops] if all_crops else ["Wheat", "Rice"]
        sel_c = st.selectbox("Choose Commodity", c_names)
        
        url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
        params = {"api-key": OGD_API_KEY, "format": "json", "filters[state]": st_sel, "filters[commodity]": sel_c}
        
        try:
            res = requests.get(url, params=params).json()
            if "records" in res and res["records"]:
                latest = res["records"][0]
                st.metric(f"Mandi Price ({latest['market']})", f"₹{latest['modal_price']} / Qtl")
                mandi_df = pd.DataFrame(res["records"])
                mandi_df['modal_price'] = pd.to_numeric(mandi_df['modal_price'])
                st.plotly_chart(px.bar(mandi_df, x='market', y='modal_price', color_discrete_sequence=['#2e7d32']), use_container_width=True)
            else: st.warning("Live data currently unavailable.")
        except: st.error("Connection Error")

    # --- AGRI LEDGER ---
    elif menu == "📒 Agri Ledger":
        st.header("📒 Private Digital Ledger")
        conn = sqlite3.connect('agri_khata.db')
        df_khata = pd.read_sql_query(f"SELECT * FROM ledger WHERE user_key='{st.session_state.username}'", conn)
        conn.close()

        if not df_khata.empty:
            inc = df_khata[df_khata['type'].str.contains('Income')]['total'].sum()
            exp = df_khata[df_khata['type'].str.contains('Expense')]['total'].sum()
            st.subheader(f"Current Profit: ₹{inc - exp:,.2f}")
            st.dataframe(df_khata.drop(columns=['id', 'user_key']), use_container_width=True, hide_index=True)
        else: st.info("No personal records found.")

        with st.expander("➕ Add Transaction"):
            with st.form("new_entry"):
                t_type = st.selectbox("Category", ["Income (Sales)", "Expense (Seeds/Labor)", "Expense (Machinery)"])
                t_item = st.text_input("Description")
                t_amt = st.number_input("Amount (₹)", min_value=0.0)
                if st.form_submit_button("Save to Ledger"):
                    conn = sqlite3.connect('agri_khata.db')
                    conn.execute("INSERT INTO ledger (user_key, date, type, item, qty, total, season) VALUES (?,?,?,?,?,?,?)",
                                (st.session_state.username, datetime.now().strftime("%Y-%m-%d"), t_type, t_item, "1", t_amt, "Current"))
                    conn.commit()
                    conn.close()
                    st.rerun()
