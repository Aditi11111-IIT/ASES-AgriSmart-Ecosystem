import streamlit as st
import pandas as pd
import random
import urllib.parse
from fpdf import FPDF
import plotly.express as px
import numpy as np
import requests
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import LabelEncoder

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="ASES: Agri-Smart Ecosystem", layout="wide", page_icon="🌾")

# 🔑 OpenWeatherMap API Key
API_KEY = "886705b4c1182ebf6969f51d03f973f9"

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .main-card { 
        padding: 25px; border-radius: 12px; 
        background-color: #FFFFFF !important; 
        border: 1px solid #2481CC; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
        margin-bottom: 20px;
    }
    .main-card h3, .main-card p { color: #1c1c1c !important; }
    .highlight-text { color: #2481CC !important; font-weight: bold; }
    .stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; width: 100%; }
    .call-btn {
        background-color: #28a745 !important; color: white !important;
        padding: 12px; border-radius: 8px; text-decoration: none;
        display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }
    .wa-btn {
        background-color: #25D366; color: white; padding: 10px;
        text-align: center; border-radius: 5px; text-decoration: none;
        display: block; font-weight: bold; margin-top: 5px;
    }
    [data-testid="stSidebar"] { background-color: #243139 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINES ---
@st.cache_data
def load_agri_data():
    crops = {
        'Crop Name': ['Wheat', 'Rice', 'Cotton', 'Maize', 'Groundnut', 'Soybean', 'Mustard', 'Sugarcane', 'Chickpea', 'Potato'],
        'Soil Type': ['Alluvial', 'Alluvial', 'Black Soil', 'Red Soil', 'Sandy', 'Black Soil', 'Alluvial', 'Loamy', 'Heavy Soil', 'Sandy Loam'],
        'Water Requirement': [500, 1200, 800, 600, 400, 700, 450, 1500, 300, 550],
        'Sowing Month': [11, 6, 6, 6, 5, 6, 10, 2, 10, 10],
        'Cost per Acre': [15000, 25000, 20000, 12000, 18000, 16000, 14000, 30000, 13000, 35000]
    }
    pest_data = {
        'Crop': ['Wheat', 'Rice', 'Cotton', 'Sugarcane', 'Mustard', 'Potato'],
        'Common Pest': ['Rust/Aphids', 'Stem Borer', 'Bollworm', 'Red Rot', 'Aphids', 'Blight'],
        'Fertilizer': ['NPK 12:32:16', 'Urea + Zinc', 'DAP + Potash', 'Nitrogen Rich', 'NPK + Sulphur', 'NPK + Potash'],
        'Pesticide': ['Tilt', 'Chlorpyrifos', 'Spinosad', 'Carbendazim', 'Dimethoate', 'Mancozeb']
    }
    return pd.DataFrame(crops), pd.DataFrame(pest_data)

df, pest_df = load_agri_data()
le = LabelEncoder()
df['Soil_Idx'] = le.fit_transform(df['Soil Type'])

# --- 3. SESSION STATE ---
if 'temp' not in st.session_state: st.session_state.temp = 25
if 'hum' not in st.session_state: st.session_state.hum = 50
if 'soil' not in st.session_state: st.session_state.soil = "Alluvial"
if 'selected_machine' not in st.session_state: st.session_state.selected_machine = "Tractor"
if 'ledger' not in st.session_state: st.session_state.ledger = pd.DataFrame([{"Item": "Seed Purchase", "Cost": 1200}])

# --- 4. NAVIGATION & LOCATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    lang = st.radio("Language / भाषा", ["English", "Hindi"], horizontal=True)
    tab = st.radio("SELECT SERVICE", ["🏠 Dashboard", "🌾 Crop Engine", "🛡️ Pest & Fertilizer", "🚜 Rental Hub", "📚 Knowledge Hub", "📈 Price Prediction", "📒 Agri Khata"])
    
    st.markdown("---")
    india_map = {
        "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Tirupati"],
        "Arunachal Pradesh": ["Itanagar", "Tawang", "Ziro", "Pasighat"],
        "Assam": ["Guwahati", "Dibrugarh", "Silchar", "Jorhat", "Tezpur"],
        "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga"],
        "Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur", "Korba"],
        "Goa": ["Panaji", "Margao", "Vasco da Gama", "Mapusa"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar"],
        "Haryana": ["Gurgaon", "Faridabad", "Panipat", "Ambala", "Hisar"],
        "Himachal Pradesh": ["Shimla", "Manali", "Dharamshala", "Solan"],
        "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro"],
        "Karnataka": ["Bengaluru", "Mysuru", "Hubballi", "Belagavi", "Mangaluru"],
        "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur"],
        "Madhya Pradesh": ["Indore", "Bhopal", "Jabalpur", "Gwalior", "Ujjain"],
        "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
        "Manipur": ["Imphal", "Churachandpur", "Thoubal"],
        "Meghalaya": ["Shillong", "Tura", "Jowai"],
        "Mizoram": ["Aizawl", "Lunglei", "Champhai"],
        "Nagaland": ["Kohima", "Dimapur", "Mokokchung"],
        "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Sambalpur"],
        "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda"],
        "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner"],
        "Sikkim": ["Gangtok", "Namchi", "Geyzing"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
        "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Khammam"],
        "Tripura": ["Agartala", "Udaipur", "Dharmanagar"],
        "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra", "Meerut", "Prayagraj"],
        "Uttarakhand": ["Dehradun", "Haridwar", "Roorkee", "Haldwani"],
        "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Siliguri", "Asansol"],
        "A&N Islands": ["Port Blair"], "Chandigarh": ["Chandigarh"],
        "Dadra & Nagar Haveli": ["Silvassa"], "Daman & Diu": ["Daman", "Diu"],
        "Delhi": ["New Delhi", "North Delhi", "South Delhi", "West Delhi"],
        "Jammu & Kashmir": ["Srinagar", "Jammu", "Anantnag", "Baramulla"],
        "Ladakh": ["Leh", "Kargil"], "Lakshadweep": ["Kavaratti"],
        "Puducherry": ["Puducherry", "Karaikal"]
    }
    st_loc = st.selectbox("Your State", list(india_map.keys()))
    dt_loc = st.selectbox("Your District", india_map[st_loc])
    
    if st.button("Update Local Weather"):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            st.session_state.temp, st.session_state.hum = res['main']['temp'], res['main']['humidity']
            st.success("Weather Synced!")
        except: st.error("Weather API Error")

# --- 5. TABS LOGIC ---

if tab == "🏠 Dashboard":
    st.title(f"👨‍🌾 Command Center: {dt_loc}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature", f"{st.session_state.temp}°C")
    col2.metric("Humidity", f"{st.session_state.hum}%")
    col3.metric("Soil Health", "Good (85%)")
    st.warning("⚠️ Rain expected in 48 hours. Postpone fertilizer application.")

elif tab == "🌾 Crop Engine":
    st.title("AgriAI Smart Recommendations")
    soil_opts = ["Alluvial", "Black Soil", "Red Soil", "Sandy"]
    s_cols = st.columns(4)
    for i, s in enumerate(soil_opts):
        if s_cols[i].button(s): st.session_state.soil = s
    st.markdown(f"<b>Current Soil:</b> <span class='highlight-text'>{st.session_state.soil}</span>", unsafe_allow_html=True)
    bud = st.slider("Investment Budget (₹/Acre)", 5000, 50000, 15000)
    
    if st.button("🚀 FIND BEST CROPS"):
        X = df[['Soil_Idx', 'Sowing Month', 'Cost per Acre']]
        knn = NearestNeighbors(n_neighbors=2).fit(X)
        u_idx = le.transform([st.session_state.soil])[0]
        _, idx = knn.kneighbors([[u_idx, 6, bud]])
        recs = df.iloc[idx[0]]
        for i, row in recs.iterrows():
            st.markdown(f'<div class="main-card"><h3>{row["Crop Name"]}</h3><p>Est. Cost: ₹{row["Cost per Acre"]}</p></div>', unsafe_allow_html=True)

elif tab == "🛡️ Pest & Fertilizer":
    st.title("Protection & Nutrition Hub")
    target_crop = st.selectbox("Select Crop", pest_df['Crop'].unique())
    data = pest_df[pest_df['Crop'] == target_crop].iloc[0]
    
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="main-card"><h3>🛡️ Pest: {data["Common Pest"]}</h3><p>Use: {data["Pesticide"]}</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="main-card"><h3>🧪 Fertilizer: {data["Fertilizer"]}</h3></div>', unsafe_allow_html=True)

elif tab == "🚜 Rental Hub":
    st.title(f"🚜 Rental Machinery Desk: {dt_loc}")
    machine_types = {
        "Preparation": [("Rotavator", "🚜"), ("Power Tiller", "⚙️")],
        "Sowing": [("Seed Drill", "🌱"), ("Rice Transplanter", "🌾")],
        "Harvesting": [("Combine Harvester", "🌾✨"), ("Thresher", "🌪️")]
    }
    m_tabs = st.tabs(list(machine_types.keys()))
    for i, category in enumerate(machine_types.keys()):
        with m_tabs[i]:
            m_cols = st.columns(2)
            for idx, (m_name, m_icon) in enumerate(machine_types[category]):
                if m_cols[idx % 2].button(f"{m_icon} {m_name}", key=f"rent_{m_name}"):
                    st.session_state.selected_machine = m_name

    st.markdown(f"**Currently Finding:** <span class='highlight-text'>{st.session_state.selected_machine}</span>", unsafe_allow_html=True)
    
    # Member 4 Integration: Link to Google Maps
    search_query = f"{st.session_state.selected_machine}+Rental+in+{dt_loc}+{st_loc}"
    google_url = f"https://www.google.com/search?q={search_query}"
    st.link_button(f"🔍 Search Commercial {st.session_state.selected_machine} Centers", google_url, use_container_width=True)
    
    st.markdown(f'<a href="tel:18001801551" class="call-btn" style="background:#ffc107 !important; color:black !important;">📞 Call Govt CHC Helpline</a>', unsafe_allow_html=True)

elif tab == "📚 Knowledge Hub":
    st.title("📚 Crop Resource Library")
    crops_en =[
    {
        "Crop": "Wheat", 
        "Type": "Cereal", "Season": "Rabi", "N-P-K": "120:60:40", 
        "Fertilizer": "Urea, DAP, MOP", "Sowing Depth": "4-5 cm", 
        "Sowing Method": "Drilling", "Soil": "Loamy", "Water": "Moderate", 
        "Pest": "Aphids/Rust", "Harvesting": "March-April",
        "Pro-Tip": "Provide irrigation at the CRI (Crown Root Initiation) stage for max yield."
    },
    {
        "Crop": "Rice (Paddy)", 
        "Type": "Cereal", "Season": "Kharif", "N-P-K": "100:60:40", 
        "Fertilizer": "Zinc Sulphate, Urea, DAP", "Sowing Depth": "2-3 cm", 
        "Sowing Method": "Transplanting", "Soil": "Clayey", "Water": "High", 
        "Pest": "Stem Borer", "Harvesting": "Nov-Dec",
        "Pro-Tip": "Maintain 2-5cm of standing water during the tillering stage."
    },
    {
        "Crop": "Mustard", 
        "Type": "Oilseed", "Season": "Rabi", "N-P-K": "80:40:40", 
        "Fertilizer": "SSP, Urea, MOP", "Sowing Depth": "2.5-3 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Sandy Loam", "Water": "Low", 
        "Pest": "Mustard Aphid", "Harvesting": "Feb-March",
        "Pro-Tip": "Adding Sulphur (via SSP) significantly increases oil content."
    },
    {
        "Crop": "Cotton", 
        "Type": "Fiber", "Season": "Kharif", "N-P-K": "100:50:50", 
        "Fertilizer": "DAP, Urea, Potash", "Sowing Depth": "4-5 cm", 
        "Sowing Method": "Dibbling", "Soil": "Black Soil", "Water": "Moderate", 
        "Pest": "Bollworm", "Harvesting": "Oct-Dec",
        "Pro-Tip": "Avoid excessive Nitrogen late in the season to prevent pest outbreaks."
    },
    {
        "Crop": "Maize (Corn)", 
        "Type": "Cereal", "Season": "Kharif/Rabi", "N-P-K": "120:60:40", 
        "Fertilizer": "Urea, DAP, Zinc", "Sowing Depth": "3-5 cm", 
        "Sowing Method": "Ridge & Furrow", "Soil": "Red/Loamy", "Water": "Moderate", 
        "Pest": "Fall Armyworm", "Harvesting": "Sept-Oct",
        "Pro-Tip": "Apply Nitrogen in 3 split doses: Sowing, Knee-high, and Tasseling stages."
    },
    {
        "Crop": "Chickpea (Gram)", 
        "Type": "Pulse", "Season": "Rabi", "N-P-K": "20:60:20", 
        "Fertilizer": "DAP, MOP", "Sowing Depth": "7-10 cm", 
        "Sowing Method": "Drilling", "Soil": "Heavy Soil", "Water": "Low", 
        "Pest": "Pod Borer", "Harvesting": "Feb-April",
        "Pro-Tip": "Nipping (plucking top branches) at 50 days encourages more branching."
    },
    {
        "Crop": "Sugarcane", 
        "Type": "Cash Crop", "Season": "Annual", "N-P-K": "150:80:60", 
        "Fertilizer": "Urea, SSP, MOP", "Sowing Depth": "10-12 cm", 
        "Sowing Method": "Trench Method", "Soil": "Alluvial", "Water": "High", 
        "Pest": "Top Borer", "Harvesting": "Dec-March",
        "Pro-Tip": "Use 'Setts' from the top 1/3rd of the cane for better germination."
    },
    {
        "Crop": "Groundnut", 
        "Type": "Oilseed", "Season": "Kharif", "N-P-K": "20:40:40", 
        "Fertilizer": "Gypsum, SSP, DAP", "Sowing Depth": "5 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Sandy", "Water": "Moderate", 
        "Pest": "White Grub", "Harvesting": "Oct-Nov",
        "Pro-Tip": "Apply Gypsum at the pegging stage (45 days) for better pod development."
    },
    {
        "Crop": "Soybean", 
        "Type": "Oilseed/Pulse", "Season": "Kharif", "N-P-K": "20:60:40", 
        "Fertilizer": "DAP, MOP, Sulphur", "Sowing Depth": "3-4 cm", 
        "Sowing Method": "Broad Bed Furrow", "Soil": "Black Soil", "Water": "Moderate", 
        "Pest": "Girdle Beetle", "Harvesting": "Sept-Oct",
        "Pro-Tip": "Seed treatment with Rhizobium culture is essential for nitrogen fixation."
    },
    {
        "Crop": "Potato", 
        "Type": "Tuber", "Season": "Rabi", "N-P-K": "120:100:120", 
        "Fertilizer": "CAN, DAP, MOP", "Sowing Depth": "5-7 cm", 
        "Sowing Method": "Ridging", "Soil": "Sandy Loam", "Water": "Moderate", 
        "Pest": "Early/Late Blight", "Harvesting": "Jan-March",
        "Pro-Tip": "De-haulming (cutting tops) 10 days before harvest thickens tuber skin."
    }
]
    crops_hi = [{"फसल": "गेहूं", "N-P-K": "120:60:40", "मिट्टी": "दोमट"}, {"फसल": "धान", "N-P-K": "100:60:40", "मिट्टी": "चिकनी"}]
    st.table(pd.DataFrame(crops_hi if lang == "Hindi" else crops_en))

elif tab == "📈 Price Prediction":
    st.title("📈 AI Market Price Prediction")
    df_p = pd.DataFrame({"Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], "Price": [random.randint(2100, 2600) for _ in range(6)]})
    st.plotly_chart(px.line(df_p, x="Month", y="Price", markers=True, title="Forecasted Trend"))

elif tab == "📒 Agri Khata":
    st.title("📒 Agri Khata (Financials)")
    with st.form("ledger"):
        item = st.text_input("Expense Item")
        cost = st.number_input("Cost (₹)", 0)
        if st.form_submit_button("Add Entry"):
            st.session_state.ledger = pd.concat([st.session_state.ledger, pd.DataFrame([{"Item": item, "Cost": cost}])], ignore_index=True)
    st.plotly_chart(px.pie(st.session_state.ledger, values='Cost', names='Item'))
