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
    },
    {
        "Crop": "Arhar (Pigeon Pea)", 
        "Type": "Pulse", "Season": "Kharif", "N-P-K": "20:50:20", 
        "Fertilizer": "DAP, Sulphur", "Sowing Depth": "5 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Well-drained Alluvial", "Water": "Low", 
        "Pest": "Pod Fly", "Harvesting": "Jan-March",
        "Pro-Tip": "Very sensitive to waterlogging; ensure fields have excellent drainage."
    },
    {
        "Crop": "Sunflower", 
        "Type": "Oilseed", "Season": "Zaid/Kharif", "N-P-K": "60:80:40", 
        "Fertilizer": "Urea, SSP, Boron", "Sowing Depth": "3-4 cm", 
        "Sowing Method": "Dibbling", "Soil": "Deep Loamy", "Water": "Moderate", 
        "Pest": "Head Borer", "Harvesting": "90-100 Days",
        "Pro-Tip": "Hand pollination or keeping beehives nearby significantly improves seed setting."
    },
    {
        "Crop": "Moong (Green Gram)", 
        "Type": "Pulse", "Season": "Summer/Kharif", "N-P-K": "20:40:20", 
        "Fertilizer": "DAP, MOP", "Sowing Depth": "3-4 cm", 
        "Sowing Method": "Broadcasting/Drilling", "Soil": "Sandy Loam", "Water": "Low", 
        "Pest": "Yellow Mosaic Virus", "Harvesting": "65-75 Days",
        "Pro-Tip": "Pick mature pods in 2-3 rounds to prevent shattering of early ripened seeds."
    },
    {
        "Crop": "Tobacco", 
        "Type": "Cash Crop", "Season": "Rabi", "N-P-K": "100:50:100", 
        "Fertilizer": "Ammonium Sulphate, Potash", "Sowing Depth": "0.5 cm (Nursery)", 
        "Sowing Method": "Transplanting", "Soil": "Light Sandy", "Water": "Moderate", 
        "Pest": "Leaf Eater", "Harvesting": "Feb-March",
        "Pro-Tip": "Desuckering (removing side shoots) is vital for improving leaf quality and size."
    },
    {
        "Crop": "Bajra (Pearl Millet)", 
        "Type": "Millet", "Season": "Kharif", "N-P-K": "80:40:40", 
        "Fertilizer": "Urea, DAP", "Sowing Depth": "2-3 cm", 
        "Sowing Method": "Drilling", "Soil": "Sandy", "Water": "Very Low", 
        "Pest": "Ergot", "Harvesting": "Oct-Nov",
        "Pro-Tip": "Highly drought-tolerant; avoid irrigation during the flowering stage unless extremely dry."
    },
    {
        "Crop": "Jute", 
        "Type": "Fiber", "Season": "Kharif", "N-P-K": "40:20:20", 
        "Fertilizer": "Urea, SSP", "Sowing Depth": "3 cm", 
        "Sowing Method": "Broadcasting", "Soil": "New Alluvial", "Water": "High", 
        "Pest": "Semi-looper", "Harvesting": "July-Sept",
        "Pro-Tip": "Harvest at the 'small pod' stage to get the best fiber strength and fineness."
    },
    {
        "Crop": "Chilli", 
        "Type": "Spice", "Season": "Kharif/Rabi", "N-P-K": "100:60:60", 
        "Fertilizer": "FYM, Urea, Potash", "Sowing Depth": "1-2 cm", 
        "Sowing Method": "Transplanting", "Soil": "Black/Loamy", "Water": "Moderate", 
        "Pest": "Thrips/Mites", "Harvesting": "Multiple Pickings",
        "Pro-Tip": "Spray Neem oil regularly to control Thrips, which cause leaf curling."
    },
    {
        "Crop": "Onion", 
        "Type": "Vegetable", "Season": "Rabi/Kharif", "N-P-K": "100:50:80", 
        "Fertilizer": "Urea, Potash, Sulphur", "Sowing Depth": "2 cm", 
        "Sowing Method": "Transplanting", "Soil": "Sandy Loam", "Water": "Moderate", 
        "Pest": "Onion Thrips", "Harvesting": "March-May",
        "Pro-Tip": "Stop irrigation 15 days before harvest to improve the storage life of bulbs."
    },
    {
        "Crop": "Tomato", 
        "Type": "Vegetable", "Season": "Year-round", "N-P-K": "100:80:60", 
        "Fertilizer": "DAP, Calcium Nitrate", "Sowing Depth": "1 cm", 
        "Sowing Method": "Transplanting", "Soil": "Well-drained Loam", "Water": "Moderate", 
        "Pest": "Fruit Borer", "Harvesting": "60-70 Days post-transplant",
        "Pro-Tip": "Use stakes to keep plants upright; this prevents fruit rot and improves air circulation."
    },
    {
        "Crop": "Turmeric", 
        "Type": "Spice", "Season": "Annual", "N-P-K": "60:60:120", 
        "Fertilizer": "FYM, Urea, MOP", "Sowing Depth": "5 cm (Rhizomes)", 
        "Sowing Method": "Pit/Ridge Method", "Soil": "Sandy Loam", "Water": "High", 
        "Pest": "Rhizome Rot", "Harvesting": "Jan-March",
        "Pro-Tip": "Mulching with green leaves immediately after planting helps in moisture retention."
    },
    {
        "Crop": "Black Gram (Urad)", 
        "Type": "Pulse", "Season": "Kharif/Summer", "N-P-K": "20:40:20", 
        "Fertilizer": "DAP, MOP, Rhizobium", "Sowing Depth": "3-4 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Loamy/Black Soil", "Water": "Low", 
        "Pest": "Hairy Caterpillar", "Harvesting": "75-90 Days",
        "Pro-Tip": "Seed treatment with Rhizobium increases nitrogen fixation and yield by 15%."
    },
    {
        "Crop": "Coffee", 
        "Type": "Plantation", "Season": "Perennial", "N-P-K": "160:120:160", 
        "Fertilizer": "Ammonium Sulphate, Urea, MOP", "Sowing Depth": "2-3 cm (Seeds)", 
        "Sowing Method": "Pit Planting", "Soil": "Red/Laterite", "Water": "High", 
        "Pest": "Coffee Berry Borer", "Harvesting": "Nov-Feb",
        "Pro-Tip": "Coffee requires shade trees (like Silver Oak) to protect it from direct hot sun."
    },
    {
        "Crop": "Tea", 
        "Type": "Plantation", "Season": "Perennial", "N-P-K": "120:60:60", 
        "Fertilizer": "NPK Mixtures, Urea", "Sowing Depth": "N/A (Cuttings)", 
        "Sowing Method": "Contour Planting", "Soil": "Acidic/Forest Soil", "Water": "Very High", 
        "Pest": "Tea Mosquito Bug", "Harvesting": "Frequent Plucking",
        "Pro-Tip": "Maintain soil pH between 4.5 and 5.5 for high-quality leaf production."
    },
    {
        "Crop": "Ginger", 
        "Type": "Spice", "Season": "Annual", "N-P-K": "75:50:50", 
        "Fertilizer": "FYM, Urea, SSP, MOP", "Sowing Depth": "5 cm (Rhizomes)", 
        "Sowing Method": "Raised Beds", "Soil": "Sandy Loam", "Water": "High", 
        "Pest": "Soft Rot", "Harvesting": "Dec-Feb",
        "Pro-Tip": "Earthing up should be done at 45 and 90 days to prevent rhizome exposure."
    },
    {
        "Crop": "Sesamum (Til)", 
        "Type": "Oilseed", "Season": "Kharif/Summer", "N-P-K": "40:20:20", 
        "Fertilizer": "Urea, SSP, MOP", "Sowing Depth": "2-3 cm", 
        "Sowing Method": "Broadcasting", "Soil": "Sandy/Well-drained", "Water": "Low", 
        "Pest": "Leaf Webber", "Harvesting": "Aug-Oct",
        "Pro-Tip": "Harvest when 75% of the capsules turn yellow to avoid seed shattering."
    },
    {
        "Crop": "Garlic", 
        "Type": "Spice/Vegetable", "Season": "Rabi", "N-P-K": "100:50:50", 
        "Fertilizer": "Urea, Potash, Sulphur", "Sowing Depth": "3-5 cm (Cloves)", 
        "Sowing Method": "Dibbling", "Soil": "Rich Loam", "Water": "Moderate", 
        "Pest": "Thrips", "Harvesting": "March-April",
        "Pro-Tip": "Curing (drying) in shade for 7-10 days is essential for good storage life."
    },
    {
        "Crop": "Lentil (Masoor)", 
        "Type": "Pulse", "Season": "Rabi", "N-P-K": "20:40:20", 
        "Fertilizer": "DAP, MOP", "Sowing Depth": "3-4 cm", 
        "Sowing Method": "Drilling", "Soil": "Alluvial/Light", "Water": "Low", 
        "Pest": "Aphids", "Harvesting": "Feb-March",
        "Pro-Tip": "Provide one light irrigation at the pod-filling stage for significantly better grain size."
    },
    {
        "Crop": "Barley", 
        "Type": "Cereal", "Season": "Rabi", "N-P-K": "60:30:20", 
        "Fertilizer": "Urea, DAP, MOP", "Sowing Depth": "4-5 cm", 
        "Sowing Method": "Drilling", "Soil": "Sandy to Moderately Heavy", "Water": "Moderate", 
        "Pest": "Cereal Cyst Nematode", "Harvesting": "March-April",
        "Pro-Tip": "Barley is more salt-tolerant than wheat, making it ideal for slightly saline soils."
    },
    {
        "Crop": "Rubber", 
        "Type": "Commercial", "Season": "Perennial", "N-P-K": "30:30:30 (Young)", 
        "Fertilizer": "NPK Mixture, Rock Phosphate", "Sowing Depth": "N/A (Budded)", 
        "Sowing Method": "Square/Rectangular", "Soil": "Laterite/Alluvial", "Water": "High", 
        "Pest": "Scale Insects", "Harvesting": "Tapping (6-7 years)",
        "Pro-Tip": "Apply rain-guarding during monsoons to allow tapping even on rainy days."
    },
    {
        "Crop": "Peas", 
        "Type": "Vegetable/Pulse", "Season": "Rabi", "N-P-K": "40:60:40", 
        "Fertilizer": "DAP, Urea, MOP", "Sowing Depth": "5-7 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Well-drained Loam", "Water": "Moderate", 
        "Pest": "Pod Borer/Powdery Mildew", "Harvesting": "Multiple Pickings",
        "Pro-Tip": "Maintain soil moisture at flowering; drought at this stage causes flower drop."
    },
    {
        "Crop": "Ragi (Finger Millet)", 
        "Type": "Millet", "Season": "Kharif", "N-P-K": "60:30:30", 
        "Fertilizer": "Urea, SSP, MOP", "Sowing Depth": "2-3 cm", 
        "Sowing Method": "Transplanting/Drilling", "Soil": "Red/Sandy Loam", "Water": "Low", 
        "Pest": "Ragi Blast", "Harvesting": "Oct-Nov",
        "Pro-Tip": "Ragi is highly rich in Calcium; avoid over-irrigation as it thrives in dry conditions."
    },
    {
        "Crop": "Banana", 
        "Type": "Fruit/Commercial", "Season": "Year-round", "N-P-K": "200:100:300", 
        "Fertilizer": "Urea, MOP, Wood Ash", "Sowing Depth": "30 cm (Suckers)", 
        "Sowing Method": "Pit Method", "Soil": "Deep Clay Loam", "Water": "Very High", 
        "Pest": "Panama Wilt", "Harvesting": "12-15 Months",
        "Pro-Tip": "Remove the 'male bud' (Denavelling) after the last hand opens to increase fruit weight."
    },
    {
        "Crop": "Black Pepper", 
        "Type": "Spice/Plantation", "Season": "Perennial", "N-P-K": "100:40:140", 
        "Fertilizer": "NPK Mixture, Neem Cake", "Sowing Depth": "N/A (Cuttings)", 
        "Sowing Method": "Support-tree Planting", "Soil": "Red Laterite", "Water": "High", 
        "Pest": "Quick Wilt", "Harvesting": "Dec-Jan",
        "Pro-Tip": "Requires 50% shade; standard trees like Silver Oak or Teak are used for support vines."
    },
    {
        "Crop": "Cumin (Jeera)", 
        "Type": "Spice", "Season": "Rabi", "N-P-K": "30:20:0", 
        "Fertilizer": "Urea, DAP", "Sowing Depth": "1-2 cm", 
        "Sowing Method": "Broadcasting", "Soil": "Sandy Loam", "Water": "Moderate", 
        "Pest": "Blight/Wilt", "Harvesting": "Feb-March",
        "Pro-Tip": "Very sensitive to atmospheric moisture; avoid irrigation during cloudy weather to prevent blight."
    },
    {
        "Crop": "Sunflower", 
        "Type": "Oilseed", "Season": "Year-round", "N-P-K": "60:40:40", 
        "Fertilizer": "Urea, SSP, Boron", "Sowing Depth": "4-5 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Deep Loam", "Water": "Moderate", 
        "Pest": "Head Borer", "Harvesting": "90-100 Days",
        "Pro-Tip": "Applying Boron at the flowering stage ensures better seed filling and higher oil yield."
    },
    {
        "Crop": "Green Pea", 
        "Type": "Vegetable", "Season": "Rabi", "N-P-K": "20:60:40", 
        "Fertilizer": "DAP, MOP", "Sowing Depth": "5 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Well-drained Loam", "Water": "Moderate", 
        "Pest": "Powdery Mildew", "Harvesting": "Multiple Pickings",
        "Pro-Tip": "Harvest in the morning for maximum sweetness; sugar content drops after picking."
    },
    {
        "Crop": "Small Millet (Kutki)", 
        "Type": "Millet", "Season": "Kharif", "N-P-K": "20:20:0", 
        "Fertilizer": "FYM, Urea", "Sowing Depth": "2 cm", 
        "Sowing Method": "Broadcasting", "Soil": "Poor/Stony Soil", "Water": "Very Low", 
        "Pest": "Shoot Fly", "Harvesting": "Aug-Sept",
        "Pro-Tip": "Can grow in very poor soils where no other crop survives; excellent for tribal hilly areas."
    },
    {
        "Crop": "Safflower", 
        "Type": "Oilseed", "Season": "Rabi", "N-P-K": "40:40:20", 
        "Fertilizer": "Urea, SSP", "Sowing Depth": "5 cm", 
        "Sowing Method": "Drilling", "Soil": "Black Cotton Soil", "Water": "Low", 
        "Pest": "Aphids", "Harvesting": "March-April",
        "Pro-Tip": "Highly drought-resistant due to deep taproot; ideal for dryland farming regions."
    },
    {
        "Crop": "Guar (Cluster Bean)", 
        "Type": "Gum/Vegetable", "Season": "Kharif", "N-P-K": "20:40:20", 
        "Fertilizer": "DAP, SSP", "Sowing Depth": "3-4 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Sandy", "Water": "Low", 
        "Pest": "Bacterial Blight", "Harvesting": "Oct-Nov",
        "Pro-Tip": "Used industrially for 'Guar Gum'; requires dry weather during the ripening stage."
    },
    {
        "Crop": "Cardamom", 
        "Type": "Spice/Plantation", "Season": "Perennial", "N-P-K": "75:75:150", 
        "Fertilizer": "NPK, Bone Meal, Neem Cake", "Sowing Depth": "N/A (Suckers)", 
        "Sowing Method": "Pit Planting", "Soil": "Forest Loam", "Water": "High", 
        "Pest": "Thrips/Capsule Borer", "Harvesting": "Multiple (Aug-Feb)",
        "Pro-Tip": "Thrives best in tropical rainforest climates with filtered sunlight and high humidity."
    },
    {
        "Crop": "Coconut", 
        "Type": "Plantation", "Season": "Perennial", "N-P-K": "500:320:1200", 
        "Fertilizer": "MOP, Urea, Neem Cake", "Sowing Depth": "60-90 cm (Pits)", 
        "Sowing Method": "Pit Planting", "Soil": "Sandy/Coastal Alluvial", "Water": "High", 
        "Pest": "Rhinoceros Beetle", "Harvesting": "Every 45-60 Days",
        "Pro-Tip": "Apply common salt (NaCl) to the basin to improve moisture retention and nut size."
    },
    {
        "Crop": "Ashwagandha", 
        "Type": "Medicinal", "Season": "Late Kharif", "N-P-K": "15:20:0", 
        "Fertilizer": "FYM, Vermicompost", "Sowing Depth": "1-2 cm", 
        "Sowing Method": "Broadcasting", "Soil": "Sandy Loam/Red", "Water": "Low", 
        "Pest": "Aphids/Mites", "Harvesting": "150-180 Days",
        "Pro-Tip": "Avoid waterlogged soils as roots (the main product) will rot quickly."
    },
    {
        "Crop": "Mentha (Mint)", 
        "Type": "Aromatic", "Season": "Zaid (Summer)", "N-P-K": "120:50:40", 
        "Fertilizer": "Urea, SSP, MOP", "Sowing Depth": "5 cm (Suckers)", 
        "Sowing Method": "Furrow Planting", "Soil": "Deep Loam", "Water": "Very High", 
        "Pest": "Termites", "Harvesting": "100-120 Days",
        "Pro-Tip": "First harvest should be taken at 100 days; subsequent harvests every 60 days."
    },
    {
        "Crop": "Cowpea (Lobia)", 
        "Type": "Pulse/Vegetable", "Season": "Kharif/Summer", "N-P-K": "20:40:20", 
        "Fertilizer": "DAP, Urea", "Sowing Depth": "3-5 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Sandy/Well-drained", "Water": "Moderate", 
        "Pest": "Aphids", "Harvesting": "60-90 Days",
        "Pro-Tip": "Ideal for intercropping with Pearl Millet or Sorghum to restore soil nitrogen."
    },
    {
        "Crop": "Coriander (Dhaniya)", 
        "Type": "Spice/Vegetable", "Season": "Rabi", "N-P-K": "40:30:20", 
        "Fertilizer": "Urea, SSP", "Sowing Depth": "2-3 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Loamy/Clayey", "Water": "Moderate", 
        "Pest": "Powdery Mildew", "Harvesting": "90-110 Days (Seed)",
        "Pro-Tip": "Split the seeds into two (halves) before sowing to improve the germination rate."
    },
    {
        "Crop": "Garlic", 
        "Type": "Spice", "Season": "Rabi", "N-P-K": "100:50:50", 
        "Fertilizer": "Ammonium Sulphate, MOP", "Sowing Depth": "3-5 cm", 
        "Sowing Method": "Dibbling", "Soil": "Rich Silty Loam", "Water": "Moderate", 
        "Pest": "Thrips", "Harvesting": "130-150 Days",
        "Pro-Tip": "Stop irrigation when the tops start falling over (neck fall) to allow the bulbs to mature."
    },
    {
        "Crop": "Sorghum (Jowar)", 
        "Type": "Millet", "Season": "Kharif/Rabi", "N-P-K": "80:40:40", 
        "Fertilizer": "Urea, DAP", "Sowing Depth": "3-4 cm", 
        "Sowing Method": "Drilling", "Soil": "Heavy/Black Cotton", "Water": "Low", 
        "Pest": "Shoot Fly", "Harvesting": "Oct-Nov / Feb-Mar",
        "Pro-Tip": "Avoid feeding cattle green Sorghum at the early stage due to high HCN (Prussic acid) content."
    },
    {
        "Crop": "Mango", 
        "Type": "Fruit/Plantation", "Season": "Perennial", "N-P-K": "100:50:100 (Per Year)", 
        "Fertilizer": "NPK Mixture, Bone Meal", "Sowing Depth": "1m x 1m x 1m (Pits)", 
        "Sowing Method": "Grafted Saplings", "Soil": "Deep Alluvial/Loam", "Water": "Moderate", 
        "Pest": "Mango Hopper", "Harvesting": "March-July",
        "Pro-Tip": "Do not irrigate during the flowering period as it causes excessive flower drop."
    },
    {
        "Crop": "Oats", 
        "Type": "Fodder/Cereal", "Season": "Rabi", "N-P-K": "80:40:0", 
        "Fertilizer": "Urea, SSP", "Sowing Depth": "3-4 cm", 
        "Sowing Method": "Drilling", "Soil": "Loamy", "Water": "Moderate", 
        "Pest": "Aphids", "Harvesting": "120-150 Days",
        "Pro-Tip": "Harvest at the 'Dough stage' (when grain is milky) for the best quality fodder."
    },
    {
        "Crop": "Fenugreek (Methi)", 
        "Type": "Spice/Vegetable", "Season": "Rabi", "N-P-K": "25:40:0", 
        "Fertilizer": "DAP, FYM", "Sowing Depth": "2 cm", 
        "Sowing Method": "Broadcasting", "Soil": "Sandy Loam", "Water": "Low", 
        "Pest": "Root Rot", "Harvesting": "30-50 Days (Leaf)",
        "Pro-Tip": "Soaking seeds in water for 12 hours before sowing ensures faster and uniform germination."
    },
    {
        "Crop": "Cashew Nut", 
        "Type": "Plantation/Dry Fruit", "Season": "Perennial", "N-P-K": "500:125:125 (Grams/Tree)", 
        "Fertilizer": "Urea, SSP, MOP", "Sowing Depth": "N/A (Grafted)", 
        "Sowing Method": "Pit Planting", "Soil": "Laterite/Red", "Water": "Low", 
        "Pest": "Tea Mosquito Bug", "Harvesting": "Feb-May",
        "Pro-Tip": "Cashew is a 'wasteland' crop but responds excellently to supplemental irrigation during flowering."
    },
    {
        "Crop": "Watermelon", 
        "Type": "Fruit/Cucurbit", "Season": "Zaid (Summer)", "N-P-K": "100:50:50", 
        "Fertilizer": "DAP, Urea, MOP", "Sowing Depth": "2-3 cm", 
        "Sowing Method": "Pit/Basin", "Soil": "Sandy Riverbeds", "Water": "Moderate", 
        "Pest": "Fruit Fly", "Harvesting": "80-100 Days",
        "Pro-Tip": "A 'thumping' sound (dull) when tapped indicates the fruit is fully ripe and ready for harvest."
    },
    {
        "Crop": "Pomegranate", 
        "Type": "Fruit", "Season": "Annual (Ambe/Mrig Bahar)", "N-P-K": "625:250:250 (Grams/Tree)", 
        "Fertilizer": "FYM, Urea, Potash", "Sowing Depth": "N/A (Air Layering)", 
        "Sowing Method": "High Density Planting", "Soil": "Deep Loamy", "Water": "Low", 
        "Pest": "Anar Butterfly", "Harvesting": "150-180 Days post-bloom",
        "Pro-Tip": "Pruning is essential to maintain a single stem and allow sunlight to reach the inner branches."
    },
    {
        "Crop": "Grapes", 
        "Type": "Fruit", "Season": "Perennial", "N-P-K": "500:500:1000 (Kg/Hectare)", 
        "Fertilizer": "Potassium Nitrate, Urea", "Sowing Depth": "N/A (Cuttings)", 
        "Sowing Method": "Bower/Trellis System", "Soil": "Well-drained Sandy Loam", "Water": "Moderate", 
        "Pest": "Downy Mildew", "Harvesting": "Jan-April",
        "Pro-Tip": "Regular pruning in October and April is vital for fruit quality and controlling vine growth."
    },
    {
        "Crop": "Small Millets (Kodo)", 
        "Type": "Millet", "Season": "Kharif", "N-P-K": "40:20:0", 
        "Fertilizer": "Urea, SSP", "Sowing Depth": "2-3 cm", 
        "Sowing Method": "Broadcasting", "Soil": "Gravelly/Poor Soil", "Water": "Very Low", 
        "Pest": "Shoot Fly", "Harvesting": "Oct-Nov",
        "Pro-Tip": "Kodo millet has the highest antioxidant content among millets and survives extreme drought."
    },
    {
        "Crop": "Guava", 
        "Type": "Fruit", "Season": "Twice Yearly", "N-P-K": "600:400:600 (Grams/Tree)", 
        "Fertilizer": "FYM, Urea, SSP", "Sowing Depth": "N/A (Grafted)", 
        "Sowing Method": "Square System", "Soil": "Alluvial/Red Loam", "Water": "Low", 
        "Pest": "Fruit Fly/Wilt", "Harvesting": "Winter/Monsoon",
        "Pro-Tip": "Winter crop (Mrig Bahar) is superior in quality and sweetness compared to the monsoon crop."
    },
    {
        "Crop": "Betel Vine", 
        "Type": "Cash Crop", "Season": "Perennial", "N-P-K": "150:100:50", 
        "Fertilizer": "Oil Cakes, Urea", "Sowing Depth": "N/A (Cuttings)", 
        "Sowing Method": "Trellis/Bareja", "Soil": "Fertile Clayey", "Water": "High", 
        "Pest": "Foot Rot", "Harvesting": "Regular Picking",
        "Pro-Tip": "Requires a humid, shaded environment; often grown in 'Barejas' (bamboo structures)."
    },
    {
        "Crop": "Linseed (Alsi)", 
        "Type": "Oilseed", "Season": "Rabi", "N-P-K": "60:40:20", 
        "Fertilizer": "Urea, SSP, MOP", "Sowing Depth": "2-3 cm", 
        "Sowing Method": "Drilling", "Soil": "Clayey Loam", "Water": "Low", 
        "Pest": "Linseed Gall Fly", "Harvesting": "Feb-March",
        "Pro-Tip": "Harvest when 90% of pods turn brown; delay causes seeds to fall and reduces oil quality."
    },
    {
        "Crop": "Opium Poppy", 
        "Type": "Medicinal", "Season": "Rabi", "N-P-K": "90:50:30", 
        "Fertilizer": "FYM, Urea, DAP", "Sowing Depth": "1 cm", 
        "Sowing Method": "Broadcasting", "Soil": "Well-drained Loam", "Water": "Moderate", 
        "Pest": "Downy Mildew", "Harvesting": "Feb-April (Lancing)",
        "Pro-Tip": "Latex collection (lancing) must be done in the early morning for maximum yield."
    },
    {
        "Crop": "Cabbage", 
        "Type": "Vegetable", "Season": "Rabi", "N-P-K": "120:60:60", 
        "Fertilizer": "Urea, DAP, Boron", "Sowing Depth": "1 cm", 
        "Sowing Method": "Transplanting", "Soil": "Sandy Loam to Clayey", "Water": "Moderate", 
        "Pest": "Diamondback Moth", "Harvesting": "90-120 Days",
        "Pro-Tip": "Applying Boron prevents 'hollow stem' and ensures firm, heavy heads."
    },
    {
        "Crop": "Areca Nut (Supari)", 
        "Type": "Plantation", "Season": "Perennial", "N-P-K": "100:40:140 (Grams/Tree)", 
        "Fertilizer": "Urea, SSP, MOP, Green Manure", "Sowing Depth": "2-3 cm (Seeds)", 
        "Sowing Method": "Pit Planting", "Soil": "Laterite/Alluvial", "Water": "High", 
        "Pest": "Mahali (Fruit Rot)", "Harvesting": "Nov-Feb",
        "Pro-Tip": "Provide proper drainage as waterlogging can cause severe root rot and golden leaf disease."
    },
    {
        "Crop": "Papaya", 
        "Type": "Fruit", "Season": "Year-round", "N-P-K": "250:250:500 (Grams/Tree)", 
        "Fertilizer": "Urea, DAP, MOP", "Sowing Depth": "1 cm", 
        "Sowing Method": "Transplanting", "Soil": "Sandy Loam", "Water": "Moderate", 
        "Pest": "Ring Spot Virus", "Harvesting": "10-12 Months",
        "Pro-Tip": "Thin out the fruits to prevent overcrowding, which ensures larger fruit size and better quality."
    },
    {
        "Crop": "Cauliflower", 
        "Type": "Vegetable", "Season": "Rabi", "N-P-K": "120:80:80", 
        "Fertilizer": "Urea, DAP, Borax", "Sowing Depth": "1 cm", 
        "Sowing Method": "Transplanting", "Soil": "Loamy", "Water": "Moderate", 
        "Pest": "Diamondback Moth", "Harvesting": "90-120 Days",
        "Pro-Tip": "Perform 'Blanching' (covering the curd with leaves) to keep the cauliflower white and protect it from sun."
    },
    {
        "Crop": "Saffron (Kesar)", 
        "Type": "Spice/Cash Crop", "Season": "Rabi", "N-P-K": "20:30:20", 
        "Fertilizer": "Well-rotted FYM, DAP", "Sowing Depth": "10-15 cm (Corms)", 
        "Sowing Method": "Pit/Ridge", "Soil": "Calcareous/Well-drained", "Water": "Low", 
        "Pest": "Corm Rot", "Harvesting": "Oct-Nov",
        "Pro-Tip": "Harvesting must be done at dawn before the flowers wilt to maintain the high quality of the stigmas."
    },
    {
        "Crop": "Black Gram (Summer)", 
        "Type": "Pulse", "Season": "Summer (Zaid)", "N-P-K": "20:40:20", 
        "Fertilizer": "DAP, Sulphur", "Sowing Depth": "3-4 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Loamy/Black", "Water": "Moderate", 
        "Pest": "Whitefly", "Harvesting": "65-75 Days",
        "Pro-Tip": "Irrigate at the flowering and pod-setting stages to prevent significant yield loss in high heat."
    },
    {
        "Crop": "Brinjal (Eggplant)", 
        "Type": "Vegetable", "Season": "Year-round", "N-P-K": "100:50:50", 
        "Fertilizer": "Urea, SSP, MOP", "Sowing Depth": "1 cm", 
        "Sowing Method": "Transplanting", "Soil": "Silt Loam/Clayey", "Water": "High", 
        "Pest": "Shoot and Fruit Borer", "Harvesting": "70-90 Days",
        "Pro-Tip": "Spray Neem oil at 10-day intervals to control fruit borers without using heavy chemicals."
    },
    {
        "Crop": "Poppy Seed (Posta Dana)", 
        "Type": "Spice/Medicinal", "Season": "Rabi", "N-P-K": "60:40:20", 
        "Fertilizer": "Urea, DAP", "Sowing Depth": "1 cm", 
        "Sowing Method": "Broadcasting", "Soil": "Sandy Loam", "Water": "Moderate", 
        "Pest": "Downy Mildew", "Harvesting": "Feb-April",
        "Pro-Tip": "Thinning is mandatory at 20 days post-sowing to maintain a 10cm distance between plants."
    },
    {
        "Crop": "Pineapple", 
        "Type": "Fruit", "Season": "Annual/Perennial", "N-P-K": "12:4:12 (Grams/Plant)", 
        "Fertilizer": "Urea, MOP, Zinc", "Sowing Depth": "N/A (Suckers/Slips)", 
        "Sowing Method": "Trench/Pit", "Soil": "Acidic Loam", "Water": "Moderate", 
        "Pest": "Mealybug", "Harvesting": "18-24 Months",
        "Pro-Tip": "Apply flower-inducing chemicals (like Ethrel) for uniform flowering across the whole field."
    },
    {
        "Crop": "Okra (Bhindi)", 
        "Type": "Vegetable", "Season": "Kharif/Summer", "N-P-K": "100:50:50", 
        "Fertilizer": "Urea, SSP, MOP", "Sowing Depth": "2-3 cm", 
        "Sowing Method": "Line Sowing", "Soil": "Loose Alluvial", "Water": "Moderate", 
        "Pest": "Yellow Vein Mosaic", "Harvesting": "45-60 Days",
        "Pro-Tip": "Soak seeds in water for 24 hours before sowing to break seed dormancy and speed up germination."
    },
    {
        "Crop": "Cardamom (Small)", 
        "Type": "Spice", "Season": "Annual", "N-P-K": "75:75:150", 
        "Fertilizer": "NPK 1:1:2, Neem Cake", "Sowing Depth": "N/A (Rhizomes)", 
        "Sowing Method": "Pit Method", "Soil": "Forest Loam", "Water": "High", 
        "Pest": "Thrips", "Harvesting": "Aug-Feb (Multiple)",
        "Pro-Tip": "Known as the 'Queen of Spices,' it requires high organic matter and constant soil moisture."
    },
    {"Crop": "Apple", "Type": "Fruit", "Season": "Perennial", "N-P-K": "700:350:700 (g/tree)", "Fertilizer": "Urea, MOP, Zinc", "Sowing Method": "Orchard Planting", "Soil": "Loamy", "Water": "Moderate", "Pest": "San Jose Scale", "Harvesting": "Aug-Oct", "Pro-Tip": "Requires specific 'chilling hours' (below 7°C) during winter to break dormancy and fruit well."},
    {"Crop": "Walnut", "Type": "Dry Fruit", "Season": "Perennial", "N-P-K": "100:50:50 (kg/ha)", "Fertilizer": "FYM, Urea", "Sowing Method": "Pit Method", "Soil": "Deep Silt Loam", "Water": "Moderate", "Pest": "Codling Moth", "Harvesting": "Sept-Oct", "Pro-Tip": "Avoid planting near sensitive crops; walnut roots release 'juglone', a natural herbicide that inhibits other plants."},
    {"Crop": "Strawberry", "Type": "Fruit", "Season": "Rabi", "N-P-K": "80:40:40", "Fertilizer": "NPK, Boron", "Sowing Method": "Raised Bed/Mulching", "Soil": "Sandy Loam", "Water": "Moderate", "Pest": "Red Spider Mite", "Harvesting": "Feb-April", "Pro-Tip": "Black plastic mulching is essential to keep berries off the soil and prevent fruit rot."},
    {"Crop": "Jackfruit", "Type": "Fruit", "Season": "Perennial", "N-P-K": "1:1:1 ratio", "Fertilizer": "Organic Manure, NPK", "Sowing Method": "Pit Method", "Soil": "Alluvial/Laterite", "Water": "Low", "Pest": "Shoot Borer", "Harvesting": "March-June", "Pro-Tip": "It is the largest tree-borne fruit; thinning excess small fruits helps the remaining ones grow larger."},
    {"Crop": "Litchi", "Type": "Fruit", "Season": "Perennial", "N-P-K": "600:400:600 (g/tree)", "Fertilizer": "Urea, SSP, MOP", "Sowing Method": "Square System", "Soil": "Deep Alluvial", "Water": "High", "Pest": "Litchi Mite", "Harvesting": "May-June", "Pro-Tip": "High humidity and protection from 'Loo' (hot summer winds) are critical during fruit development."},
    {"Crop": "Custard Apple", "Type": "Fruit", "Season": "Annual", "N-P-K": "250:125:125 (g/tree)", "Fertilizer": "FYM, Urea", "Sowing Method": "Pit Planting", "Soil": "Stony/Sandy Loam", "Water": "Very Low", "Pest": "Mealybug", "Harvesting": "Oct-Dec", "Pro-Tip": "Highly drought-tolerant; hand pollination can significantly increase fruit set in dry areas."},
    {"Crop": "Pear", "Type": "Fruit", "Season": "Perennial", "N-P-K": "60:30:60 (kg/ha)", "Fertilizer": "Urea, MOP", "Sowing Method": "Orchard", "Soil": "Deep/Well-drained", "Water": "Moderate", "Pest": "Aphids", "Harvesting": "July-Sept", "Pro-Tip": "Pears are best harvested when slightly under-ripe; they ripen better off the tree in a cool environment."},
    {"Crop": "Plum", "Type": "Fruit", "Season": "Perennial", "N-P-K": "500:250:500 (g/tree)", "Fertilizer": "NPK Mixture", "Sowing Method": "Orchard", "Soil": "Sandy Loam", "Water": "Moderate", "Pest": "Scale Insects", "Harvesting": "May-July", "Pro-Tip": "Thinning fruits to a 5-10cm distance ensures high-quality, large-sized plums."},
    {"Crop": "Almond", "Type": "Dry Fruit", "Season": "Perennial", "N-P-K": "500:300:700 (g/tree)", "Fertilizer": "Urea, Potash", "Sowing Method": "Pit Planting", "Soil": "Deep/Loamy", "Water": "Moderate", "Pest": "Almond Moth", "Harvesting": "July-Sept", "Pro-Tip": "Requires cross-pollination; always plant at least two different varieties together for fruit production."},
    {"Crop": "Peach", "Type": "Fruit", "Season": "Perennial", "N-P-K": "500:250:500 (g/tree)", "Fertilizer": "Urea, SSP, MOP", "Sowing Method": "Square System", "Soil": "Sandy Loam", "Water": "Moderate", "Pest": "Leaf Curl", "Harvesting": "May-July", "Pro-Tip": "Pruning should be heavy to encourage new growth, as peaches only bear fruit on one-year-old wood."},

    # --- VEGETABLES & SPICES (10) ---
    {"Crop": "Radish", "Type": "Vegetable", "Season": "Rabi/Kharif", "N-P-K": "50:50:50", "Fertilizer": "FYM, Urea", "Sowing Method": "Ridge & Furrow", "Soil": "Sandy Loam", "Water": "Moderate", "Pest": "Aphids", "Harvesting": "30-50 Days", "Pro-Tip": "Early harvesting is key; if left too long, the root becomes pithy and loses flavor."},
    {"Crop": "Carrot", "Type": "Vegetable", "Season": "Rabi", "N-P-K": "60:60:100", "Fertilizer": "Urea, Potash", "Sowing Method": "Line Sowing", "Soil": "Deep/Loose Loam", "Water": "Moderate", "Pest": "Carrot Rust Fly", "Harvesting": "90-110 Days", "Pro-Tip": "Avoid fresh manure; it causes roots to fork (split). Use well-rotted compost instead."},
    {"Crop": "Spinach", "Type": "Vegetable", "Season": "Year-round", "N-P-K": "80:40:40", "Fertilizer": "Urea (Side dressing)", "Sowing Method": "Broadcasting", "Soil": "Rich Loam", "Water": "High", "Pest": "Leaf Miner", "Harvesting": "30-45 Days", "Pro-Tip": "Apply nitrogen after each cutting to encourage rapid regrowth of leaves."},
    {"Crop": "Bottle Gourd", "Type": "Vegetable", "Season": "Summer/Kharif", "N-P-K": "40:30:30", "Fertilizer": "DAP, Urea", "Sowing Method": "Pit/Trellis", "Soil": "Silt Loam", "Water": "Moderate", "Pest": "Red Pumpkin Beetle", "Harvesting": "60-75 Days", "Pro-Tip": "Training vines on a trellis improves fruit shape and prevents soil-borne diseases."},
    {"Crop": "Bitter Gourd", "Type": "Vegetable", "Season": "Summer/Kharif", "N-P-K": "50:50:50", "Fertilizer": "FYM, NPK", "Sowing Method": "Pit Planting", "Soil": "Sandy Loam", "Water": "Moderate", "Pest": "Fruit Fly", "Harvesting": "55-70 Days", "Pro-Tip": "Seed coat is hard; soak seeds in water for 24 hours to ensure 90%+ germination."},
    {"Crop": "Pumpkin", "Type": "Vegetable", "Season": "Kharif/Summer", "N-P-K": "60:50:50", "Fertilizer": "DAP, Urea", "Sowing Method": "Pit Method", "Soil": "Alluvial", "Water": "Moderate", "Pest": "Epilachna Beetle", "Harvesting": "90-120 Days", "Pro-Tip": "Harvest only when the stem connecting the fruit to the vine begins to shrivel and turn woody."},
    {"Crop": "Cucumber", "Type": "Vegetable", "Season": "Summer", "N-P-K": "50:50:50", "Fertilizer": "Urea, SSP", "Sowing Method": "Basin Method", "Soil": "Sandy Loam", "Water": "High", "Pest": "Downy Mildew", "Harvesting": "45-60 Days", "Pro-Tip": "Bitterness in cucumber is caused by water stress; maintain consistent soil moisture."},
    {"Crop": "Capsicum", "Type": "Vegetable", "Season": "Rabi/Kharif", "N-P-K": "150:120:120", "Fertilizer": "DAP, MOP, Calcium", "Sowing Method": "Transplanting", "Soil": "Sandy Loam", "Water": "Moderate", "Pest": "Thrips/Mites", "Harvesting": "75-90 Days", "Pro-Tip": "Often grown in poly-houses to control temperature and prevent virus transmission by insects."},
    {"Crop": "French Beans", "Type": "Vegetable", "Season": "Kharif/Rabi", "N-P-K": "60:80:40", "Fertilizer": "Urea, DAP", "Sowing Method": "Line Sowing", "Soil": "Well-drained Loam", "Water": "Moderate", "Pest": "Bean Aphid", "Harvesting": "50-70 Days", "Pro-Tip": "Avoid high nitrogen after flowering as it promotes leaf growth at the expense of bean pods."},
    {"Crop": "Garlic (Spring)", "Type": "Spice", "Season": "Zaid", "N-P-K": "120:60:60", "Fertilizer": "Ammonium Sulphate", "Sowing Method": "Dibbling", "Soil": "Loamy", "Water": "Moderate", "Pest": "Thrips", "Harvesting": "120 Days", "Pro-Tip": "Spacing is vital (15x10cm) for bulb expansion; shallow weeding is needed to avoid root damage."},

    # --- COMMERCIAL, MILLET & FLOWERS (10) ---
    {"Crop": "Marigold", "Type": "Flower", "Season": "Year-round", "N-P-K": "100:100:100", "Fertilizer": "NPK Mixture", "Sowing Method": "Transplanting", "Soil": "Sandy Loam", "Water": "Moderate", "Pest": "Bud Borer", "Harvesting": "60-70 Days", "Pro-Tip": "Pinch the terminal buds (top) at 40 days to encourage more lateral branches and flowers."},
    {"Crop": "Rose", "Type": "Flower/Commercial", "Season": "Perennial", "N-P-K": "10:20:10 (ratio)", "Fertilizer": "Bone Meal, FYM", "Sowing Method": "Budded Plants", "Soil": "Well-drained Clayey", "Water": "Moderate", "Pest": "Die-back Disease", "Harvesting": "Multiple Pickings", "Pro-Tip": "Annual pruning in October is essential to remove dead wood and stimulate new flowering shoots."},
    {"Crop": "Jasmine", "Type": "Flower/Aromatic", "Season": "Perennial", "N-P-K": "60:120:120 (g/plant)", "Fertilizer": "NPK, Neem Cake", "Sowing Method": "Cuttings", "Soil": "Sandy Loam", "Water": "Moderate", "Pest": "Bud Worm", "Harvesting": "Early Morning", "Pro-Tip": "Stop irrigation before pruning (January) to allow the plant to rest before the flowering season."},
    {"Crop": "Little Millet", "Type": "Millet", "Season": "Kharif", "N-P-K": "40:20:0", "Fertilizer": "Urea, SSP", "Sowing Method": "Broadcasting", "Soil": "Poor/Gravelly", "Water": "Low", "Pest": "Shoot Fly", "Harvesting": "80-90 Days", "Pro-Tip": "Known as 'Kutki'; it is the most reliable crop for tribal regions with poor soil and high rainfall."},
    {"Crop": "Foxtail Millet", "Type": "Millet", "Season": "Kharif/Rabi", "N-P-K": "40:40:0", "Fertilizer": "DAP, Urea", "Sowing Method": "Drilling", "Soil": "Sandy to Loamy", "Water": "Low", "Pest": "Armyworm", "Harvesting": "90-100 Days", "Pro-Tip": "High in iron and pest-resistant; ideal for dryland farming as it has a very low water requirement."},
    {"Crop": "Buckwheat", "Type": "Pseudo-cereal", "Season": "Rabi", "N-P-K": "40:20:20", "Fertilizer": "FYM, DAP", "Sowing Method": "Line Sowing", "Soil": "Acidic/Poor Soil", "Water": "Moderate", "Pest": "Aphids", "Harvesting": "70-90 Days", "Pro-Tip": "Grown in high altitudes (Himalayas); it is gluten-free and improves soil structure for next crops."},
    {"Crop": "Clove", "Type": "Spice/Plantation", "Season": "Perennial", "N-P-K": "300:250:750 (g/tree)", "Fertilizer": "NPK, Bone Meal", "Sowing Method": "Pit Planting", "Soil": "Deep Red Loam", "Water": "High", "Pest": "Stem Borer", "Harvesting": "Sept-Oct", "Pro-Tip": "Harvest the flower buds when they turn pinkish; if they open, they lose their spice value."},
    {"Crop": "Nutmeg", "Type": "Spice", "Season": "Perennial", "N-P-K": "500:250:1000 (g/tree)", "Fertilizer": "Manure, Potash", "Sowing Method": "Pit Method", "Soil": "Alluvial/Laterite", "Water": "High", "Pest": "Scale Insects", "Harvesting": "June-Aug", "Pro-Tip": "Produces two spices (Nutmeg and Mace); requires high humidity and shade during the first 3 years."},
    {"Crop": "Rubber (Mature)", "Type": "Commercial", "Season": "Perennial", "N-P-K": "30:30:30", "Fertilizer": "NPK Mixture", "Sowing Method": "Tapping", "Soil": "Laterite", "Water": "High", "Pest": "Powdery Mildew", "Harvesting": "Latex Tapping", "Pro-Tip": "Tapping should be done early in the morning (before 9 AM) when the turgor pressure in the tree is highest."},
    {"Crop": "Hops", "Type": "Commercial", "Season": "Rabi", "N-P-K": "150:100:100", "Fertilizer": "Urea, SSP, MOP", "Sowing Method": "Trellis/Vine", "Soil": "Deep Loam", "Water": "High", "Pest": "Downy Mildew", "Harvesting": "Aug-Sept", "Pro-Tip": "The female flowers (cones) are the economic part; requires long daylight hours during the growth phase."}
]
    crops_hi = [
    {
        "फसल": "गेहूं (Wheat)", 
        "प्रकार": "अनाज", "सीजन": "रबी", "N-P-K": "120:60:40", 
        "उर्वरक": "यूरिया, DAP, MOP", "बुवाई की गहराई": "4-5 सेमी", 
        "बुवाई की विधि": "ड्रिलिंग (Drilling)", "मिट्टी": "दोमट", "पानी": "मध्यम", 
        "कीट": "माहू (Aphids)/रतुआ (Rust)", "कटाई": "मार्च-अप्रैल",
        "प्रो-टिप": "अधिक उपज के लिए CRI (ताज जड़ निकलना) चरण पर सिंचाई अवश्य करें।"
    },
    {
        "फसल": "धान (Rice/Paddy)", 
        "प्रकार": "अनाज", "सीजन": "खरीफ", "N-P-K": "100:60:40", 
        "उर्वरक": "जिंक सल्फेट, यूरिया, DAP", "बुवाई की गहराई": "2-3 सेमी", 
        "बुवाई की विधि": "रोपाई (Transplanting)", "मिट्टी": "चिकनी", "पानी": "अधिक", 
        "कीट": "तना छेदक (Stem Borer)", "कटाई": "नवंबर-दिसंबर",
        "प्रो-टिप": "कल्ले फूटते समय (Tillering) खेत में 2-5 सेमी पानी भरकर रखें।"
    },
    {
        "फसल": "सरसों (Mustard)", 
        "प्रकार": "तिलहन", "सीजन": "रबी", "N-P-K": "80:40:40", 
        "उर्वरक": "SSP, यूरिया, MOP", "बुवाई की गहराई": "2.5-3 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "बलुई दोमट", "पानी": "कम", 
        "कीट": "सरसों का माहू", "कटाई": "फरवरी-मार्च",
        "प्रो-टिप": "सल्फर (SSP के माध्यम से) डालने से बीजों में तेल की मात्रा काफी बढ़ जाती है।"
    },
    {
        "फसल": "कपास (Cotton)", 
        "प्रकार": "रेशा", "सीजन": "खरीफ", "N-P-K": "100:50:50", 
        "उर्वरक": "DAP, यूरिया, पोटाश", "बुवाई की गहराई": "4-5 सेमी", 
        "बुवाई की विधि": "डिबलिंग (Dibbling)", "मिट्टी": "काली मिट्टी", "पानी": "मध्यम", 
        "कीट": "गुलाबी सुंडी (Bollworm)", "कटाई": "अक्टूबर-दिसंबर",
        "प्रो-टिप": "कीटों से बचने के लिए सीजन के अंत में अधिक नाइट्रोजन डालने से बचें।"
    },
    {
        "फसल": "मक्का (Maize)", 
        "प्रकार": "अनाज", "सीजन": "खरीफ/रबी", "N-P-K": "120:60:40", 
        "उर्वरक": "यूरिया, DAP, जिंक", "बुवाई की गहराई": "3-5 सेमी", 
        "बुवाई की विधि": "मेड़ और नाली", "मिट्टी": "लाल/दोमट", "पानी": "मध्यम", 
        "कीट": "फॉल आर्मीवर्म", "कटाई": "सितंबर-अक्टूबर",
        "प्रो-टिप": "नाइट्रोजन को 3 बार में डालें: बुवाई, घुटने की ऊंचाई, और फूल आने के समय।"
    },
    {
        "फसल": "चना (Chickpea)", 
        "प्रकार": "दलहन", "सीजन": "रबी", "N-P-K": "20:60:20", 
        "उर्वरक": "DAP, MOP", "बुवाई की गहराई": "7-10 सेमी", 
        "बुवाई की विधि": "ड्रिलिंग", "मिट्टी": "भारी मिट्टी", "पानी": "कम", 
        "कीट": "फली छेदक (Pod Borer)", "कटाई": "फरवरी-अप्रैल",
        "प्रो-टिप": "50 दिनों पर 'निपिंग' (ऊपरी शाखाओं को तोड़ना) करने से अधिक शाखाएँ निकलती हैं।"
    },
    {
        "फसल": "गन्ना (Sugarcane)", 
        "प्रकार": "नकदी फसल", "सीजन": "वार्षिक", "N-P-K": "150:80:60", 
        "उर्वरक": "यूरिया, SSP, MOP", "बुवाई की गहराई": "10-12 सेमी", 
        "बुवाई की विधि": "ट्रेंच विधि", "मिट्टी": "जलोढ़", "पानी": "अधिक", 
        "कीट": "चोटी छेदक (Top Borer)", "कटाई": "दिसंबर-मार्च",
        "प्रो-टिप": "बेहतर जमाव के लिए गन्ने के ऊपरी 1/3 हिस्से का ही बीज (Setts) के रूप में उपयोग करें।"
    },
    {
        "फसल": "मूंगफली (Groundnut)", 
        "प्रकार": "तिलहन", "सीजन": "खरीफ", "N-P-K": "20:40:40", 
        "उर्वरक": "जिप्सम, SSP, DAP", "बुवाई की गहराई": "5 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "रेतीली", "पानी": "मध्यम", 
        "कीट": "सफेद गिंडार (White Grub)", "कटाई": "अक्टूबर-नवंबर",
        "प्रो-टिप": "बेहतर फली विकास के लिए सुइयां बनते समय (Pegging - 45 दिन) जिप्सम डालें।"
    },
    {
        "फसल": "सोयाबीन (Soybean)", 
        "प्रकार": "तिलहन/दलहन", "सीजन": "खरीफ", "N-P-K": "20:60:40", 
        "उर्वरक": "DAP, MOP, सल्फर", "बुवाई की गहराई": "3-4 सेमी", 
        "बुवाई की विधि": "ब्रॉड बेड फरो", "मिट्टी": "काली मिट्टी", "पानी": "मध्यम", 
        "कीट": "गर्डल बीटल", "कटाई": "सितंबर-अक्टूबर",
        "प्रो-टिप": "नाइट्रोजन स्थिरीकरण के लिए राइजोबियम कल्चर से बीज उपचार अनिवार्य है।"
    },
    {
        "फसल": "आलू (Potato)", 
        "प्रकार": "कंद", "सीजन": "रबी", "N-P-K": "120:100:120", 
        "उर्वरक": "CAN, DAP, MOP", "बुवाई की गहराई": "5-7 सेमी", 
        "बुवाई की विधि": "रिडिंग (Ridging)", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", 
        "कीट": "झुलसा रोग (Blight)", "कटाई": "जनवरी-मार्च",
        "प्रो-टिप": "खुदाई से 10 दिन पहले पौधों की कटाई (De-haulming) करने से आलू की त्वचा मोटी हो जाती है।"
    },
    {
        "फसल": "अरहर (Pigeon Pea)", 
        "प्रकार": "दलहन", "सीजन": "खरीफ", "N-P-K": "20:50:20", 
        "उर्वरक": "DAP, सल्फर", "बुवाई की गहराई": "5 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "अच्छी जलनिकासी वाली जलोढ़", "पानी": "कम", 
        "कीट": "फली मक्खी (Pod Fly)", "कटाई": "जनवरी-मार्च",
        "प्रो-टिप": "यह जलजमाव के प्रति बहुत संवेदनशील है; सुनिश्चित करें कि खेत में जल निकासी की अच्छी व्यवस्था हो।"
    },
    {
        "फसल": "सूरजमुखी (Sunflower)", 
        "प्रकार": "तिलहन", "सीजन": "जायद/खरीफ", "N-P-K": "60:80:40", 
        "उर्वरक": "यूरिया, SSP, बोरॉन", "बुवाई की गहराई": "3-4 सेमी", 
        "बुवाई की विधि": "डिबलिंग (Dibbling)", "मिट्टी": "गहरी दोमट", "पानी": "मध्यम", 
        "कीट": "शीर्ष छेदक (Head Borer)", "कटाई": "90-100 दिन",
        "प्रो-टिप": "हाथ से परागण करने या पास में मधुमक्खी के छत्ते रखने से बीजों की पैदावार काफी बढ़ जाती है।"
    },
    {
        "फसल": "मूंग (Green Gram)", 
        "प्रकार": "दलहन", "सीजन": "गर्मी/खरीफ", "N-P-K": "20:40:20", 
        "उर्वरक": "DAP, MOP", "बुवाई की गहराई": "3-4 सेमी", 
        "बुवाई की विधि": "छिड़काव/ड्रिलिंग", "मिट्टी": "बलुई दोमट", "पानी": "कम", 
        "कीट": "पीला मोज़ेक वायरस", "कटाई": "65-75 दिन",
        "प्रो-टिप": "जल्दी पके हुए बीजों को झड़ने से रोकने के लिए परिपक्व फलियों को 2-3 बार में तोड़ें।"
    },
    {
        "फसल": "तंबाकू (Tobacco)", 
        "प्रकार": "नकदी फसल", "सीजन": "रबी", "N-P-K": "100:50:100", 
        "उर्वरक": "अमोनियम सल्फेट, पोटाश", "बुवाई की गहराई": "0.5 सेमी (नर्सरी)", 
        "बुवाई की विधि": "रोपाई", "मिट्टी": "हल्की रेतीली", "पानी": "मध्यम", 
        "कीट": "पत्ता खाने वाला कीट", "कटाई": "फरवरी-मार्च",
        "प्रो-टिप": "पत्तियों की गुणवत्ता और आकार सुधारने के लिए 'डीसकरिंग' (बगल की टहनियों को हटाना) महत्वपूर्ण है।"
    },
    {
        "फसल": "बाजरा (Pearl Millet)", 
        "प्रकार": "मोटा अनाज", "सीजन": "खरीफ", "N-P-K": "80:40:40", 
        "उर्वरक": "यूरिया, DAP", "बुवाई की गहराई": "2-3 सेमी", 
        "बुवाई की विधि": "ड्रिलिंग", "मिट्टी": "रेतीली", "पानी": "बहुत कम", 
        "कीट": "एर्गोट (Ergot)", "कटाई": "अक्टूबर-नवंबर",
        "प्रो-टिप": "यह सूखा सहन करने वाली फसल है; फूल आने के दौरान सिंचाई से बचें जब तक कि बहुत सूखा न हो।"
    },
    {
        "फसल": "जूट (Jute)", 
        "प्रकार": "रेशा", "सीजन": "खरीफ", "N-P-K": "40:20:20", 
        "उर्वरक": "यूरिया, SSP", "बुवाई की गहराई": "3 सेमी", 
        "बुवाई की विधि": "छिड़काव", "मिट्टी": "नई जलोढ़", "पानी": "अधिक", 
        "कीट": "सेमी-लूपर", "कटाई": "जुलाई-सितंबर",
        "प्रो-टिप": "सर्वोत्तम रेशे की मजबूती और चमक के लिए 'छोटी फली' अवस्था में ही कटाई करें।"
    },
    {
        "फसल": "मिर्च (Chilli)", 
        "प्रकार": "मसाला", "सीजन": "खरीफ/रबी", "N-P-K": "100:60:60", 
        "उर्वरक": "गोबर खाद, यूरिया, पोटाश", "बुवाई की गहराई": "1-2 सेमी", 
        "बुवाई की विधि": "रोपाई", "मिट्टी": "काली/दोमट", "पानी": "मध्यम", 
        "कीट": "थ्रिप्स/माइट्स", "कटाई": "कई बार तुड़ाई",
        "प्रो-टिप": "पत्ता मरोड़ रोग पैदा करने वाले थ्रिप्स को नियंत्रित करने के लिए नियमित रूप से नीम के तेल का छिड़काव करें।"
    },
    {
        "फसल": "प्याज (Onion)", 
        "प्रकार": "सब्जी", "सीजन": "रबी/खरीफ", "N-P-K": "100:50:80", 
        "उर्वरक": "यूरिया, पोटाश, सल्फर", "बुवाई की गहराई": "2 सेमी", 
        "बुवाई की विधि": "रोपाई", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", 
        "कीट": "प्याज थ्रिप्स", "कटाई": "मार्च-मई",
        "प्रो-टिप": "प्याज की भंडारण क्षमता बढ़ाने के लिए कटाई से 15 दिन पहले सिंचाई बंद कर दें।"
    },
    {
        "फसल": "टमाटर (Tomato)", 
        "प्रकार": "सब्जी", "सीजन": "वर्षभर", "N-P-K": "100:80:60", 
        "उर्वरक": "DAP, कैल्शियम नाइट्रेट", "बुवाई की गहराई": "1 सेमी", 
        "बुवाई की विधि": "रोपाई", "मिट्टी": "अच्छी जलनिकासी वाली दोमट", "पानी": "मध्यम", 
        "कीट": "फल छेदक (Fruit Borer)", "कटाई": "रोपाई के 60-70 दिन बाद",
        "प्रो-टिप": "पौधों को सीधा रखने के लिए डंडों (Staking) का सहारा दें; इससे फलों को सड़ने से बचाया जा सकता है।"
    },
    {
        "फसल": "हल्दी (Turmeric)", 
        "प्रकार": "मसाला", "सीजन": "वार्षिक", "N-P-K": "60:60:120", 
        "उर्वरक": "गोबर खाद, यूरिया, MOP", "बुवाई की गहराई": "5 सेमी (प्रकंद)", 
        "बुवाई की विधि": "गड्डा/मेड़ विधि", "मिट्टी": "बलुई दोमट", "पानी": "अधिक", 
        "कीट": "प्रकंद सड़न (Rhizome Rot)", "कटाई": "जनवरी-मार्च",
        "प्रो-टिप": "रोपण के तुरंत बाद हरी पत्तियों से मल्चिंग (आच्छादन) करने से नमी बनाए रखने में मदद मिलती है।"
    },
    {
        "फसल": "उड़द (Black Gram)", 
        "प्रकार": "दलहन", "सीजन": "खरीफ/गर्मी", "N-P-K": "20:40:20", 
        "उर्वरक": "DAP, MOP, राइजोबियम", "बुवाई की गहराई": "3-4 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "दोमट/काली मिट्टी", "पानी": "कम", 
        "कीट": "बालों वाली इल्ली (Hairy Caterpillar)", "कटाई": "75-90 दिन",
        "प्रो-टिप": "राइजोबियम से बीज उपचार करने से नाइट्रोजन स्थिरीकरण और पैदावार में 15% तक वृद्धि होती है।"
    },
    {
        "फसल": "कॉफी (Coffee)", 
        "प्रकार": "बागानी", "सीजन": "बारहमासी", "N-P-K": "160:120:160", 
        "उर्वरक": "अमोनियम सल्फेट, यूरिया, MOP", "बुवाई की गहराई": "2-3 सेमी (बीज)", 
        "बुवाई की विधि": "गड्डा रोपण", "मिट्टी": "लाल/लैटराइट", "पानी": "अधिक", 
        "कीट": "कॉफी बेरी बोरर", "कटाई": "नवंबर-फरवरी",
        "प्रो-टिप": "कॉफी को सीधी तेज धूप से बचाने के लिए छायादार पेड़ों (जैसे सिल्वर ओक) की आवश्यकता होती है।"
    },
    {
        "फसल": "चाय (Tea)", 
        "प्रकार": "बागानी", "सीजन": "बारहमासी", "N-P-K": "120:60:60", 
        "उर्वरक": "NPK मिश्रण, यूरिया", "बुवाई की गहराई": "लागू नहीं (कलम)", 
        "बुवाई की विधि": "कंटूर रोपण", "मिट्टी": "अम्लीय/वन मिट्टी", "पानी": "बहुत अधिक", 
        "कीट": "चाय मच्छर कीट", "कटाई": "लगातार तुड़ाई",
        "प्रो-टिप": "उच्च गुणवत्ता वाली पत्तियों के उत्पादन के लिए मिट्टी का pH 4.5 से 5.5 के बीच रखें।"
    },
    {
        "फसल": "अदरक (Ginger)", 
        "प्रकार": "मसाला", "सीजन": "वार्षिक", "N-P-K": "75:50:50", 
        "उर्वरक": "गोबर खाद, यूरिया, SSP, MOP", "बुवाई की गहराई": "5 सेमी (प्रकंद)", 
        "बुवाई की विधि": "उठी हुई क्यारियाँ", "मिट्टी": "बलुई दोमट", "पानी": "अधिक", 
        "कीट": "नरम सड़न (Soft Rot)", "कटाई": "दिसंबर-फरवरी",
        "प्रो-टिप": "प्रकंदों को बाहर निकलने से रोकने के लिए 45 और 90 दिनों पर 'मिट्टी चढ़ाना' (Earthing up) आवश्यक है।"
    },
    {
        "फसल": "तिल (Sesamum)", 
        "प्रकार": "तिलहन", "सीजन": "खरीफ/गर्मी", "N-P-K": "40:20:20", 
        "उर्वरक": "यूरिया, SSP, MOP", "बुवाई की गहराई": "2-3 सेमी", 
        "बुवाई की विधि": "छिड़काव", "मिट्टी": "रेतीली/अच्छी जलनिकासी", "पानी": "कम", 
        "कीट": "लीफ वेबर (Leaf Webber)", "कटाई": "अगस्त-अक्टूबर",
        "प्रो-टिप": "बीजों को झड़ने से बचाने के लिए जब 75% फलियाँ पीली हो जाएं तभी कटाई कर लें।"
    },
    {
        "फसल": "लहसुन (Garlic)", 
        "प्रकार": "मसाला/सब्जी", "सीजन": "रबी", "N-P-K": "100:50:50", 
        "उर्वरक": "यूरिया, पोटाश, सल्फर", "बुवाई की गहराई": "3-5 सेमी (कलियाँ)", 
        "बुवाई की विधि": "डिबलिंग", "मिट्टी": "उपजाऊ दोमट", "पानी": "मध्यम", 
        "कीट": "थ्रिप्स", "कटाई": "मार्च-अप्रैल",
        "प्रो-टिप": "अच्छी भंडारण क्षमता के लिए 7-10 दिनों तक छाया में 'क्यूरिंग' (सुखाना) अनिवार्य है।"
    },
    {
        "फसल": "मसूर (Lentil)", 
        "प्रकार": "दलहन", "सीजन": "रबी", "N-P-K": "20:40:20", 
        "उर्वरक": "DAP, MOP", "बुवाई की गहराई": "3-4 सेमी", 
        "बुवाई की विधि": "ड्रिलिंग", "मिट्टी": "जलोढ़/हल्की मिट्टी", "पानी": "कम", 
        "कीट": "माहू (Aphids)", "कटाई": "फरवरी-मार्च",
        "प्रो-टिप": "दाने के बेहतर आकार के लिए फली भरते समय एक हल्की सिंचाई अवश्य करें।"
    },
    {
        "फसल": "जौ (Barley)", 
        "प्रकार": "अनाज", "सीजन": "रबी", "N-P-K": "60:30:20", 
        "उर्वरक": "यूरिया, DAP, MOP", "बुवाई की गहराई": "4-5 सेमी", 
        "बुवाई की विधि": "ड्रिलिंग", "मिट्टी": "रेतीली से मध्यम भारी", "पानी": "मध्यम", 
        "कीट": "सीरियल सिस्ट नेमाटोड", "कटाई": "मार्च-अप्रैल",
        "प्रो-टिप": "जौ गेहूं की तुलना में अधिक नमक-सहिष्णु है, जो इसे थोड़ी क्षारीय मिट्टी के लिए आदर्श बनाता है।"
    },
    {
        "फसल": "रबड़ (Rubber)", 
        "प्रकार": "व्यावसायिक", "सीजन": "बारहमासी", "N-P-K": "30:30:30 (युवा)", 
        "उर्वरक": "NPK मिश्रण, रॉक फॉस्फेट", "बुवाई की गहराई": "लागू नहीं", 
        "बुवाई की विधि": "वर्गाकार/आयताकार", "मिट्टी": "लैटराइट/जलोढ़", "पानी": "अधिक", 
        "कीट": "स्केल इंसेक्ट्स", "कटाई": "टैपिंग (6-7 साल बाद)",
        "प्रो-टिप": "मानसून के दौरान 'रेन-गार्डिंग' का उपयोग करें ताकि बारिश के दिनों में भी टैपिंग की जा सके।"
    },
    {
        "फसल": "मटर (Peas)", 
        "प्रकार": "सब्जी/दलहन", "सीजन": "रबी", "N-P-K": "40:60:40", 
        "उर्वरक": "DAP, यूरिया, MOP", "बुवाई की गहराई": "5-7 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "अच्छी जलनिकासी वाली दोमट", "पानी": "मध्यम", 
        "कीट": "फली छेदक/चूर्णिल आसिता (Powdery Mildew)", "कटाई": "कई बार तुड़ाई",
        "प्रो-टिप": "फूल आने के समय मिट्टी में नमी बनाए रखें; इस चरण में सूखे से फूल झड़ सकते हैं।"
    },
    {
        "फसल": "रागी (Finger Millet)", 
        "प्रकार": "मोटा अनाज", "सीजन": "खरीफ", "N-P-K": "60:30:30", 
        "उर्वरक": "यूरिया, SSP, MOP", "बुवाई की गहराई": "2-3 सेमी", 
        "बुवाई की विधि": "रोपाई/ड्रिलिंग", "मिट्टी": "लाल/बलुई दोमट", "पानी": "कम", 
        "कीट": "रागी ब्लास्ट", "कटाई": "अक्टूबर-नवंबर",
        "प्रो-टिप": "रागी कैल्शियम से भरपूर होती है; यह सूखे में अच्छी बढ़ती है, इसलिए ज्यादा सिंचाई से बचें।"
    },
    {
        "फसल": "केला (Banana)", 
        "प्रकार": "फल/व्यावसायिक", "सीजन": "वर्षभर", "N-P-K": "200:100:300", 
        "उर्वरक": "यूरिया, MOP, लकड़ी की राख", "बुवाई की गहराई": "30 सेमी (सकर्स)", 
        "बुवाई की विधि": "गड्डा विधि", "मिट्टी": "गहरी चिकनी दोमट", "पानी": "बहुत अधिक", 
        "कीट": "पनामा विल्ट", "कटाई": "12-15 महीने",
        "प्रो-टिप": "अंतिम फल आने के बाद 'नर कली' (Denavelling) को हटा दें, इससे फलों का वजन बढ़ता है।"
    },
    {
        "फसल": "काली मिर्च (Black Pepper)", 
        "प्रकार": "मसाला/बागानी", "सीजन": "बारहमासी", "N-P-K": "100:40:140", 
        "उर्वरक": "NPK मिश्रण, नीम की खली", "बुवाई की गहराई": "लागू नहीं (कलम)", 
        "बुवाई की विधि": "सहारा-पेड़ रोपण", "मिट्टी": "लाल लैटराइट", "पानी": "अधिक", 
        "कीट": "त्वरित विल्ट (Quick Wilt)", "कटाई": "दिसंबर-जनवरी",
        "प्रो-टिप": "इसे 50% छाया की आवश्यकता होती है; बेलों को सहारा देने के लिए सिल्वर ओक जैसे पेड़ों का उपयोग करें।"
    },
    {
        "फसल": "जीरा (Cumin/Jeera)", 
        "प्रकार": "मसाला", "सीजन": "रबी", "N-P-K": "30:20:0", 
        "उर्वरक": "यूरिया, DAP", "बुवाई की गहराई": "1-2 सेमी", 
        "बुवाई की विधि": "छिड़काव", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", 
        "कीट": "झुलसा/विल्ट", "कटाई": "फरवरी-मार्च",
        "प्रो-टिप": "यह हवा की नमी के प्रति संवेदनशील है; झुलसा रोग से बचने के लिए बादल वाले मौसम में सिंचाई न करें।"
    },
    {
        "फसल": "सूरजमुखी (Sunflower)", 
        "प्रकार": "तिलहन", "सीजन": "वर्षभर", "N-P-K": "60:40:40", 
        "उर्वरक": "यूरिया, SSP, बोरॉन", "बुवाई की गहराई": "4-5 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "गहरी दोमट", "पानी": "मध्यम", 
        "कीट": "शीर्ष छेदक (Head Borer)", "कटाई": "90-100 दिन",
        "प्रो-टिप": "फूल आने के चरण में बोरॉन का उपयोग करने से बीज अच्छी तरह भरते हैं और तेल की मात्रा बढ़ती है।"
    },
    {
        "फसल": "हरी मटर (Green Pea)", 
        "प्रकार": "सब्जी", "सीजन": "रबी", "N-P-K": "20:60:40", 
        "उर्वरक": "DAP, MOP", "बुवाई की गहराई": "5 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "अच्छी जलनिकासी वाली दोमट", "पानी": "मध्यम", 
        "कीट": "चूर्णिल आसिता (Powdery Mildew)", "कटाई": "कई बार तुड़ाई",
        "प्रो-टिप": "अधिक मिठास के लिए सुबह के समय तुड़ाई करें; तोड़ने के बाद चीनी की मात्रा कम होने लगती है।"
    },
    {
        "फसल": "कुटकी (Small Millet)", 
        "प्रकार": "मोटा अनाज", "सीजन": "खरीफ", "N-P-K": "20:20:0", 
        "उर्वरक": "गोबर खाद, यूरिया", "बुवाई की गहराई": "2 सेमी", 
        "बुवाई की विधि": "छिड़काव", "मिट्टी": "खराब/पथरीली मिट्टी", "पानी": "बहुत कम", 
        "कीट": "शूट फ्लाई", "कटाई": "अगस्त-सितंबर",
        "प्रो-टिप": "यह बहुत खराब मिट्टी में भी उग सकती है; आदिवासी पहाड़ी क्षेत्रों के लिए उत्कृष्ट फसल है।"
    },
    {
        "फसल": "कुसुम (Safflower)", 
        "प्रकार": "तिलहन", "सीजन": "रबी", "N-P-K": "40:40:20", 
        "उर्वरक": "यूरिया, SSP", "बुवाई की गहराई": "5 सेमी", 
        "बुवाई की विधि": "ड्रिलिंग", "मिट्टी": "काली कपासी मिट्टी", "पानी": "कम", 
        "कीट": "माहू (Aphids)", "कटाई": "मार्च-अप्रैल",
        "प्रो-टिप": "गहरी मूसला जड़ के कारण यह अत्यधिक सूखा-प्रतिरोधी है; शुष्क खेती के लिए आदर्श है।"
    },
    {
        "फसल": "ग्वार (Cluster Bean)", 
        "प्रकार": "गोंद/सब्जी", "सीजन": "खरीफ", "N-P-K": "20:40:20", 
        "उर्वरक": "DAP, SSP", "बुवाई की गहराई": "3-4 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "रेतीली", "पानी": "कम", 
        "कीट": "जीवाणु झुलसा", "कटाई": "अक्टूबर-नवंबर",
        "प्रो-टिप": "इसका उपयोग 'ग्वार गम' के औद्योगिक उत्पादन के लिए होता है; पकने के समय शुष्क मौसम आवश्यक है।"
    },
    {
        "फसल": "इलायची (Cardamom)", 
        "प्रकार": "मसाला/बागानी", "सीजन": "बारहमासी", "N-P-K": "75:75:150", 
        "उर्वरक": "NPK, बोन मील, नीम की खली", "बुवाई की गहराई": "लागू नहीं", 
        "बुवाई की विधि": "गड्डा रोपण", "मिट्टी": "वन दोमट", "पानी": "अधिक", 
        "कीट": "थ्रिप्स/कैप्सूल बोरर", "कटाई": "अगस्त-फरवरी",
        "प्रो-टिप": "छनकर आने वाली धूप और उच्च आर्द्रता वाले उष्णकटिबंधीय वर्षावन जलवायु में सर्वोत्तम होती है।"
    },
    {
        "फसल": "नारियल (Coconut)", 
        "प्रकार": "बागानी", "सीजन": "बारहमासी", "N-P-K": "500:320:1200", 
        "उर्वरक": "MOP, यूरिया, नीम की खली", "बुवाई की गहराई": "60-90 सेमी (गड्ढे)", 
        "बुवाई की विधि": "गड्डा रोपण", "मिट्टी": "रेतीली/तटीय जलोढ़", "पानी": "अधिक", 
        "कीट": "राइनोसेरोस बीटल (Rhinoceros Beetle)", "कटाई": "प्रत्येक 45-60 दिन",
        "प्रो-टिप": "नमी बनाए रखने और फल का आकार बढ़ाने के लिए पेड़ के चारों ओर साधारण नमक (NaCl) डालें।"
    },
    {
        "फसल": "अश्वगंधा (Ashwagandha)", 
        "प्रकार": "औषधीय", "सीजन": "पछेती खरीफ", "N-P-K": "15:20:0", 
        "उर्वरक": "गोबर खाद, वर्मीकम्पोस्ट", "बुवाई की गहराई": "1-2 सेमी", 
        "बुवाई की विधि": "छिड़काव", "मिट्टी": "बलुई दोमट/लाल", "पानी": "कम", 
        "कीट": "माहू/माइट्स", "कटाई": "150-180 दिन",
        "प्रो-टिप": "जलजमाव वाली मिट्टी से बचें क्योंकि जड़ें (मुख्य उत्पाद) बहुत जल्दी सड़ जाती हैं।"
    },
    {
        "फसल": "मेंथा (Mint)", 
        "प्रकार": "सुगंधित", "सीजन": "जायद (गर्मी)", "N-P-K": "120:50:40", 
        "उर्वरक": "यूरिया, SSP, MOP", "बुवाई की गहराई": "5 सेमी (सकर्स)", 
        "बुवाई की विधि": "नाली रोपण", "मिट्टी": "गहरी दोमट", "पानी": "बहुत अधिक", 
        "कीट": "दीमक", "कटाई": "100-120 दिन",
        "प्रो-टिप": "पहली कटाई 100 दिनों पर और उसके बाद हर 60 दिनों में कटाई की जानी चाहिए।"
    },
    {
        "फसल": "लोबिया (Cowpea)", 
        "प्रकार": "दलहन/सब्जी", "सीजन": "खरीफ/गर्मी", "N-P-K": "20:40:20", 
        "उर्वरक": "DAP, यूरिया", "बुवाई की गहराई": "3-5 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "रेतीली/अच्छी जलनिकासी", "पानी": "मध्यम", 
        "कीट": "माहू (Aphids)", "कटाई": "60-90 दिन",
        "प्रो-टिप": "मिट्टी में नाइट्रोजन वापस लाने के लिए बाजरा या ज्वार के साथ अंतर-फसल (Intercropping) के लिए आदर्श है।"
    },
    {
        "फसल": "धनिया (Coriander)", 
        "प्रकार": "मसाला/सब्जी", "सीजन": "रबी", "N-P-K": "40:30:20", 
        "उर्वरक": "यूरिया, SSP", "बुवाई की गहराई": "2-3 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "दोमट/चिकनी", "पानी": "मध्यम", 
        "कीट": "चूर्णिल आसिता (Powdery Mildew)", "कटाई": "90-110 दिन (बीज)",
        "प्रो-टिप": "जमाव दर सुधारने के लिए बुवाई से पहले बीजों को दो भागों (दाल की तरह) में तोड़ लें।"
    },
    {
        "फसल": "लहसुन (Garlic)", 
        "प्रकार": "मसाला", "सीजन": "रबी", "N-P-K": "100:50:50", 
        "उर्वरक": "अमोनियम सल्फेट, MOP", "बुवाई की गहराई": "3-5 सेमी", 
        "बुवाई की विधि": "डिबलिंग", "मिट्टी": "उपजाऊ गाद वाली दोमट", "पानी": "मध्यम", 
        "कीट": "थ्रिप्स", "कटाई": "130-150 दिन",
        "प्रो-टिप": "जब पौधों के ऊपरी हिस्से गिरने लगें (Neck fall), तो सिंचाई बंद कर दें ताकि कंद अच्छी तरह पक सकें।"
    },
    {
        "फसल": "ज्वार (Sorghum)", 
        "प्रकार": "मोटा अनाज", "सीजन": "खरीफ/रबी", "N-P-K": "80:40:40", 
        "उर्वरक": "यूरिया, DAP", "बुवाई की गहराई": "3-4 सेमी", 
        "बुवाई की विधि": "ड्रिलिंग", "मिट्टी": "भारी/काली मिट्टी", "पानी": "कम", 
        "कीट": "शूट फ्लाई", "कटाई": "अक्टूबर-नवंबर / फरवरी-मार्च",
        "प्रो-टिप": "शुरुआती चरण में मवेशियों को हरा ज्वार न खिलाएं क्योंकि इसमें HCN (प्रुसिक एसिड) की मात्रा अधिक होती है।"
    },
    {
        "फसल": "आम (Mango)", 
        "प्रकार": "फल/बागानी", "सीजन": "बारहमासी", "N-P-K": "100:50:100 (प्रति वर्ष)", 
        "उर्वरक": "NPK मिश्रण, बोन मील", "बुवाई की गहराई": "1m x 1m x 1m (गड्ढे)", 
        "बुवाई की विधि": "कलमी पौधे", "मिट्टी": "गहरी जलोढ़/दोमट", "पानी": "मध्यम", 
        "कीट": "आम का भुनगा (Mango Hopper)", "कटाई": "मार्च-जुलाई",
        "प्रो-टिप": "फूल आने के दौरान सिंचाई न करें क्योंकि इससे बहुत अधिक फूल झड़ने लगते हैं।"
    },
    {
        "फसल": "जई (Oats)", 
        "प्रकार": "चारा/अनाज", "सीजन": "रबी", "N-P-K": "80:40:0", 
        "उर्वरक": "यूरिया, SSP", "बुवाई की गहराई": "3-4 सेमी", 
        "बुवाई की विधि": "ड्रिलिंग", "मिट्टी": "दोमट", "पानी": "मध्यम", 
        "कीट": "माहू (Aphids)", "कटाई": "120-150 दिन",
        "प्रो-टिप": "सबसे अच्छी गुणवत्ता वाले चारे के लिए 'डफ स्टेज' (जब दाना दूधिया हो) पर कटाई करें।"
    },
    {
        "फसल": "मेथी (Fenugreek)", 
        "प्रकार": "मसाला/सब्जी", "सीजन": "रबी", "N-P-K": "25:40:0", 
        "उर्वरक": "DAP, गोबर खाद", "बुवाई की गहराई": "2 सेमी", 
        "बुवाई की विधि": "छिड़काव", "मिट्टी": "बलुई दोमट", "पानी": "कम", 
        "कीट": "जड़ सड़न (Root Rot)", "कटाई": "30-50 दिन (पत्ता)",
        "प्रो-टिप": "तेजी से और एकसमान अंकुरण के लिए बुवाई से 12 घंटे पहले बीजों को पानी में भिगो दें।"
    },
    {
        "फसल": "काजू (Cashew Nut)", 
        "प्रकार": "बागानी/सूखा मेवा", "सीजन": "बारहमासी", "N-P-K": "500:125:125 (ग्राम/पेड़)", 
        "उर्वरक": "यूरिया, SSP, MOP", "बुवाई की गहराई": "लागू नहीं (कलमी)", 
        "बुवाई की विधि": "गड्डा रोपण", "मिट्टी": "लैटराइट/लाल", "पानी": "कम", 
        "कीट": "चाय मच्छर कीट (Tea Mosquito Bug)", "कटाई": "फरवरी-मई",
        "प्रो-टिप": "काजू एक 'बंजर भूमि' की फसल है, लेकिन फूल आने के समय सिंचाई करने से पैदावार बहुत बढ़ जाती है।"
    },
    {
        "फसल": "तरबूज (Watermelon)", 
        "प्रकार": "फल/कद्दू वर्गीय", "सीजन": "जायद (गर्मी)", "N-P-K": "100:50:50", 
        "उर्वरक": "DAP, यूरिया, पोटाश", "बुवाई की गहराई": "2-3 सेमी", 
        "बुवाई की विधि": "गड्डा/बेसिन विधि", "मिट्टी": "रेतीले नदी तट", "पानी": "मध्यम", 
        "कीट": "फल मक्खी", "कटाई": "80-100 दिन",
        "प्रो-टिप": "थपथपाने पर 'भारी' (dull) आवाज आना इस बात का संकेत है कि फल पूरी तरह से पक चुका है।"
    },
    {
        "फसल": "अनार (Pomegranate)", 
        "प्रकार": "फल", "सीजन": "वार्षिक (अम्बे/मृग बहार)", "N-P-K": "625:250:250 (ग्राम/पेड़)", 
        "उर्वरक": "गोबर खाद, यूरिया, पोटाश", "बुवाई की गहराई": "लागू नहीं", 
        "बुवाई की विधि": "सघन रोपण (High Density)", "मिट्टी": "गहरी दोमट", "पानी": "कम", 
        "कीट": "अनार की तितली", "कटाई": "फूल आने के 150-180 दिन बाद",
        "प्रो-टिप": "एक मुख्य तना बनाए रखने और अंदर की शाखाओं तक धूप पहुँचाने के लिए छंटाई (Pruning) आवश्यक है।"
    },
    {
        "फसल": "अंगूर (Grapes)", 
        "प्रकार": "फल", "सीजन": "बारहमासी", "N-P-K": "500:500:1000 (किग्रा/हेक्टेयर)", 
        "उर्वरक": "पोटेशियम नाइट्रेट, यूरिया", "बुवाई की गहराई": "लागू नहीं (कलम)", 
        "बुवाई की विधि": "बौवर/ट्रेलीस सिस्टम", "मिट्टी": "अच्छी जलनिकासी वाली बलुई दोमट", "पानी": "मध्यम", 
        "कीट": "डाउन मिल्ड्यू (Downy Mildew)", "कटाई": "जनवरी-अप्रैल",
        "प्रो-टिप": "अक्टूबर और अप्रैल में नियमित छंटाई फलों की गुणवत्ता और बेल की वृद्धि को नियंत्रित करने के लिए महत्वपूर्ण है।"
    },
    {
        "फसल": "कोदो बाजरा (Kodo Millet)", 
        "प्रकार": "मोटा अनाज", "सीजन": "खरीफ", "N-P-K": "40:20:0", 
        "उर्वरक": "यूरिया, SSP", "बुवाई की गहराई": "2-3 सेमी", 
        "बुवाई की विधि": "छिड़काव", "मिट्टी": "पथरीली/कम उपजाऊ", "पानी": "बहुत कम", 
        "कीट": "शूट फ्लाई", "कटाई": "अक्टूबर-नवंबर",
        "प्रो-टिप": "बाजरा प्रजातियों में कोदो में सबसे अधिक एंटीऑक्सीडेंट होते हैं और यह भीषण सूखे में भी जीवित रहता है।"
    },
    {
        "फसल": "अमरूद (Guava)", 
        "प्रकार": "फल", "सीजन": "वर्ष में दो बार", "N-P-K": "600:400:600 (ग्राम/पेड़)", 
        "उर्वरक": "गोबर खाद, यूरिया, SSP", "बुवाई की गहराई": "लागू नहीं", 
        "बुवाई की विधि": "वर्गाकार विधि", "मिट्टी": "जलोढ़/लाल दोमट", "पानी": "कम", 
        "कीट": "फल मक्खी/विल्ट", "कटाई": "सर्दियों/मानसून",
        "प्रो-टिप": "मानसून की फसल की तुलना में सर्दियों की फसल (मृग बहार) गुणवत्ता और मिठास में बहुत बेहतर होती है।"
    },
    {
        "फसल": "पान (Betel Vine)", 
        "प्रकार": "नकदी फसल", "सीजन": "बारहमासी", "N-P-K": "150:100:50", 
        "उर्वरक": "खली, यूरिया", "बुवाई की गहराई": "लागू नहीं (कलम)", 
        "बुवाई की विधि": "ट्रेलीस/बरेजा", "मिट्टी": "उपजाऊ चिकनी मिट्टी", "पानी": "अधिक", 
        "कीट": "फुट रॉट (Foot Rot)", "कटाई": "नियमित तुड़ाई",
        "प्रो-टिप": "इसे नम और छायादार वातावरण की आवश्यकता होती है; अक्सर 'बरेजा' (बांस की संरचनाओं) में उगाया जाता है।"
    },
    {
        "फसल": "अलसी (Linseed/Alsi)", 
        "प्रकार": "तिलहन", "सीजन": "रबी", "N-P-K": "60:40:20", 
        "उर्वरक": "यूरिया, SSP, MOP", "बुवाई की गहराई": "2-3 सेमी", 
        "बुवाई की विधि": "ड्रिलिंग", "मिट्टी": "चिकनी दोमट", "पानी": "कम", 
        "कीट": "अलसी की गॉल फ्लाई", "कटाई": "फरवरी-मार्च",
        "प्रो-टिप": "जब 90% फलियाँ भूरी हो जाएँ तब कटाई करें; देरी से बीज गिरने लगते हैं और तेल की गुणवत्ता कम हो जाती है।"
    },
    {
        "फसल": "अफीम (Opium Poppy)", 
        "प्रकार": "औषधीय", "सीजन": "रबी", "N-P-K": "90:50:30", 
        "उर्वरक": "गोबर खाद, यूरिया, DAP", "बुवाई की गहराई": "1 सेमी", 
        "बुवाई की विधि": "छिड़काव", "मिट्टी": "अच्छी जलनिकासी वाली दोमट", "पानी": "मध्यम", 
        "कीट": "डाउन मिल्ड्यू", "कटाई": "फरवरी-अप्रैल (लैंसिंग)",
        "प्रो-टिप": "अधिकतम उपज के लिए लेटेक्स संग्रह (lancing) सुबह-सुबह किया जाना चाहिए।"
    },
    {
        "फसल": "पत्तागोभी (Cabbage)", 
        "प्रकार": "सब्जी", "सीजन": "रबी", "N-P-K": "120:60:60", 
        "उर्वरक": "यूरिया, DAP, बोरॉन", "बुवाई की गहराई": "1 सेमी", 
        "बुवाई की विधि": "रोपाई", "मिट्टी": "बलुई दोमट से चिकनी", "पानी": "मध्यम", 
        "कीट": "डायमंडबैक मोथ", "कटाई": "90-120 दिन",
        "प्रो-टिप": "बोरॉन का उपयोग तने को खोखला होने से रोकता है और गोभी के सिर को सख्त और भारी बनाता है।"
    },
    {
        "फसल": "सुपारी (Areca Nut)", 
        "प्रकार": "बागानी", "सीजन": "बारहमासी", "N-P-K": "100:40:140 (ग्राम/पेड़)", 
        "उर्वरक": "यूरिया, SSP, MOP, हरी खाद", "बुवाई की गहराई": "2-3 सेमी (बीज)", 
        "बुवाई की विधि": "गड्डा रोपण", "मिट्टी": "लैटराइट/जलोढ़", "पानी": "अधिक", 
        "कीट": "महाली (फल सड़न)", "कटाई": "नवंबर-फरवरी",
        "प्रो-टिप": "जल निकासी की उचित व्यवस्था करें क्योंकि जलजमाव से जड़ सड़न और सुनहरा पत्ता रोग हो सकता है।"
    },
    {
        "फसल": "पपीता (Papaya)", 
        "प्रकार": "फल", "सीजन": "वर्षभर", "N-P-K": "250:250:500 (ग्राम/पेड़)", 
        "उर्वरक": "यूरिया, DAP, पोटाश", "बुवाई की गहराई": "1 सेमी", 
        "बुवाई की विधि": "रोपाई (Transplanting)", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", 
        "कीट": "रिंग स्पॉट वायरस", "कटाई": "10-12 महीने",
        "प्रो-टिप": "फलों की छंटाई करें ताकि वे एक-दूसरे के बहुत करीब न हों, इससे फलों का आकार और गुणवत्ता बेहतर होती है।"
    },
    {
        "फसल": "फूलगोभी (Cauliflower)", 
        "प्रकार": "सब्जी", "सीजन": "रबी", "N-P-K": "120:80:80", 
        "उर्वरक": "यूरिया, DAP, बोरेक्स", "बुवाई की गहराई": "1 सेमी", 
        "बुवाई की विधि": "रोपाई", "मिट्टी": "दोमट", "पानी": "मध्यम", 
        "कीट": "डायमंडबैक मोथ", "कटाई": "90-120 दिन",
        "प्रो-टिप": "'ब्लांचिंग' (फूल को पत्तियों से ढकना) करें ताकि फूल सफेद रहे और सूरज की रोशनी से सुरक्षित रहे।"
    },
    {
        "फसल": "केसर (Saffron/Kesar)", 
        "प्रकार": "मसाला/नकदी फसल", "सीजन": "रबी", "N-P-K": "20:30:20", 
        "उर्वरक": "सड़ी हुई गोबर खाद, DAP", "बुवाई की गहराई": "10-15 सेमी (कंद)", 
        "बुवाई की विधि": "गड्डा/मेड़", "मिट्टी": "चूनेदार/अच्छी जलनिकासी", "पानी": "कम", 
        "कीट": "कंद सड़न (Corm Rot)", "कटाई": "अक्टूबर-नवंबर",
        "प्रो-टिप": "गुणवत्ता बनाए रखने के लिए फूलों की कटाई भोर के समय, उनके मुरझाने से पहले करनी चाहिए।"
    },
    {
        "फसल": "उड़द (ग्रीष्मकालीन)", 
        "प्रकार": "दलहन", "सीजन": "जायद (गर्मी)", "N-P-K": "20:40:20", 
        "उर्वरक": "DAP, सल्फर", "बुवाई की गहराई": "3-4 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "दोमट/काली", "पानी": "मध्यम", 
        "कीट": "सफेद मक्खी (Whitefly)", "कटाई": "65-75 दिन",
        "प्रो-टिप": "भीषण गर्मी में उपज के नुकसान से बचने के लिए फूल आने और फलियाँ बनते समय सिंचाई अवश्य करें।"
    },
    {
        "फसल": "बैंगन (Brinjal)", 
        "प्रकार": "सब्जी", "सीजन": "वर्षभर", "N-P-K": "100:50:50", 
        "उर्वरक": "यूरिया, SSP, MOP", "बुवाई की गहराई": "1 सेमी", 
        "बुवाई की विधि": "रोपाई", "मिट्टी": "गाद युक्त दोमट/चिकनी", "पानी": "अधिक", 
        "कीट": "तना और फल छेदक", "कटाई": "70-90 दिन",
        "प्रो-टिप": "भारी रसायनों के बिना फल छेदक को नियंत्रित करने के लिए 10 दिनों के अंतराल पर नीम के तेल का छिड़काव करें।"
    },
    {
        "फसल": "पोस्ता दाना (Poppy Seed)", 
        "प्रकार": "मसाला/औषधीय", "सीजन": "रबी", "N-P-K": "60:40:20", 
        "उर्वरक": "यूरिया, DAP", "बुवाई की गहराई": "1 सेमी", 
        "बुवाई की विधि": "छिड़काव", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", 
        "कीट": "डाउन मिल्ड्यू", "कटाई": "फरवरी-अप्रैल",
        "प्रो-टिप": "पौधों के बीच 10 सेमी की दूरी बनाए रखने के लिए बुवाई के 20 दिन बाद छंटाई (Thinning) अनिवार्य है।"
    },
    {
        "फसल": "अनानास (Pineapple)", 
        "प्रकार": "फल", "सीजन": "वार्षिक/बारहमासी", "N-P-K": "12:4:12 (ग्राम/पौधा)", 
        "उर्वरक": "यूरिया, MOP, जिंक", "बुवाई की गहराई": "लागू नहीं", 
        "बुवाई की विधि": "खाई/गड्डा विधि", "मिट्टी": "अम्लीय दोमट", "पानी": "मध्यम", 
        "कीट": "मिलीबग (Mealybug)", "कटाई": "18-24 महीने",
        "प्रो-टिप": "पूरे खेत में एक समान फूल आने के लिए फूल-उत्प्रेरक रसायनों (जैसे एथ्रेल) का उपयोग करें।"
    },
    {
        "फसल": "भिंडी (Okra)", 
        "प्रकार": "सब्जी", "सीजन": "खरीफ/गर्मी", "N-P-K": "100:50:50", 
        "उर्वरक": "यूरिया, SSP, पोटाश", "बुवाई की गहराई": "2-3 सेमी", 
        "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "हल्की जलोढ़", "पानी": "मध्यम", 
        "कीट": "पीला मोज़ेक वायरस (YVMV)", "कटाई": "45-60 दिन",
        "प्रो-टिप": "बीज की सुप्तावस्था तोड़ने और अंकुरण तेज करने के लिए बुवाई से पहले बीजों को 24 घंटे पानी में भिगो दें।"
    },
    {
        "फसल": "छोटी इलायची", 
        "प्रकार": "मसाला", "सीजन": "वार्षिक", "N-P-K": "75:75:150", 
        "उर्वरक": "NPK 1:1:2, नीम की खली", "बुवाई की गहराई": "लागू नहीं", 
        "बुवाई की विधि": "गड्डा विधि", "मिट्टी": "वन दोमट", "पानी": "अधिक", 
        "कीट": "थ्रिप्स", "कटाई": "अगस्त-फरवरी (कई बार)",
        "प्रो-टिप": "'मसालों की रानी' के रूप में जानी जाने वाली इस फसल को उच्च जैविक पदार्थ और निरंतर नमी की आवश्यकता होती है।"
    },
    {"फसल": "सेब (Apple)", "प्रकार": "फल", "सीजन": "बारहमासी", "N-P-K": "700:350:700 (ग्राम/पेड़)", "उर्वरक": "यूरिया, पोटाश, जिंक", "बुवाई की विधि": "बागान रोपण", "मिट्टी": "दोमट", "पानी": "मध्यम", "कीट": "सैन जोस स्केल", "कटाई": "अगस्त-अक्टूबर", "प्रो-टिप": "सर्दियों में सुषुप्ति तोड़ने और अच्छे फल आने के लिए विशिष्ट 'चिलिंग आवर्स' (7°C से कम तापमान) की आवश्यकता होती है।"},
    {"फसल": "अखरोट (Walnut)", "प्रकार": "सूखा मेवा", "सीजन": "बारहमासी", "N-P-K": "100:50:50 (किग्रा/हेक्टेयर)", "उर्वरक": "गोबर खाद, यूरिया", "बुवाई की विधि": "गड्डा विधि", "मिट्टी": "गहरी गाद वाली दोमट", "पानी": "मध्यम", "कीट": "कॉडलिंग मोथ", "कटाई": "सितंबर-अक्टूबर", "प्रो-टिप": "संवेदनशील फसलों के पास न लगाएं; अखरोट की जड़ें 'जुगलोन' छोड़ती हैं, जो अन्य पौधों की वृद्धि को रोकती हैं।"},
    {"फसल": "स्ट्रॉबेरी (Strawberry)", "प्रकार": "फल", "सीजन": "रबी", "N-P-K": "80:40:40", "उर्वरक": "NPK, बोरॉन", "बुवाई की विधि": "उठी हुई क्यारी/मल्चिंग", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", "कीट": "रेड स्पाइडर माइट", "कटाई": "फरवरी-अप्रैल", "प्रो-टिप": "फलों को मिट्टी से दूर रखने और सड़न रोकने के लिए ब्लैक प्लास्टिक मल्चिंग अनिवार्य है।"},
    {"फसल": "कटहल (Jackfruit)", "प्रकार": "फल", "सीजन": "बारहमासी", "N-P-K": "1:1:1 अनुपात", "उर्वरक": "जैविक खाद, NPK", "बुवाई की विधि": "गड्डा विधि", "मिट्टी": "जलोढ़/लैटराइट", "पानी": "कम", "कीट": "तना छेदक", "कटाई": "मार्च-जून", "प्रो-टिप": "यह पेड़ पर उगने वाला सबसे बड़ा फल है; छोटे फलों की छंटाई करने से बचे हुए फल बड़े होते हैं।"},
    {"फसल": "लीची (Litchi)", "प्रकार": "फल", "सीजन": "बारहमासी", "N-P-K": "600:400:600 (ग्राम/पेड़)", "उर्वरक": "यूरिया, SSP, पोटाश", "बुवाई की विधि": "वर्गाकार विधि", "मिट्टी": "गहरी जलोढ़", "पानी": "अधिक", "कीट": "लीची माइट", "कटाई": "मई-जून", "प्रो-टिप": "फल विकास के दौरान उच्च आर्द्रता और 'लू' (गर्म हवाओं) से सुरक्षा बहुत महत्वपूर्ण है।"},
    {"फसल": "शरीफा (Custard Apple)", "प्रकार": "फल", "सीजन": "वार्षिक", "N-P-K": "250:125:125 (ग्राम/पेड़)", "उर्वरक": "गोबर खाद, यूरिया", "बुवाई की विधि": "गड्डा रोपण", "मिट्टी": "पथरीली/बलुई दोमट", "पानी": "बहुत कम", "कीट": "मिलीबग", "कटाई": "अक्टूबर-दिसंबर", "प्रो-टिप": "अत्यधिक सूखा-सहिष्णु; शुष्क क्षेत्रों में हाथ से परागण करने से फलों की संख्या काफी बढ़ सकती है।"},
    {"फसल": "नाशपाती (Pear)", "प्रकार": "फल", "सीजन": "बारहमासी", "N-P-K": "60:30:60 (किग्रा/हेक्टेयर)", "उर्वरक": "यूरिया, पोटाश", "बुवाई की विधि": "बागान", "मिट्टी": "गहरी/अच्छी जलनिकासी", "पानी": "मध्यम", "कीट": "माहू (Aphids)", "कटाई": "जुलाई-सितंबर", "प्रो-टिप": "नाशपाती की कटाई तब करें जब वह थोड़ी कच्ची हो; पेड़ से टूटने के बाद ठंडे वातावरण में यह बेहतर पकती है।"},
    {"फसल": "आलू बुखारा (Plum)", "प्रकार": "फल", "सीजन": "बारहमासी", "N-P-K": "500:250:500 (ग्राम/पेड़)", "उर्वरक": "NPK मिश्रण", "बुवाई की विधि": "बागान", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", "कीट": "स्केल कीट", "कटाई": "मई-जुलाई", "प्रो-टिप": "फलों को 5-10 सेमी की दूरी पर रखने से उच्च गुणवत्ता वाले, बड़े आकार के फल मिलते हैं।"},
    {"फसल": "बादाम (Almond)", "प्रकार": "सूखा मेवा", "सीजन": "बारहमासी", "N-P-K": "500:300:700 (ग्राम/पेड़)", "उर्वरक": "यूरिया, पोटाश", "बुवाई की विधि": "गड्डा रोपण", "मिट्टी": "गहरी/दोमट", "पानी": "मध्यम", "कीट": "बादाम मोथ", "कटाई": "जुलाई-सितंबर", "प्रो-टिप": "इसे क्रॉस-परागण की आवश्यकता होती है; फल उत्पादन के लिए हमेशा दो अलग-अलग किस्मों को साथ लगाएं।"},
    {"फसल": "आड़ू (Peach)", "प्रकार": "फल", "सीजन": "बारहमासी", "N-P-K": "500:250:500 (ग्राम/पेड़)", "उर्वरक": "यूरिया, SSP, पोटाश", "बुवाई की विधि": "वर्गाकार विधि", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", "कीट": "लीफ कर्ल (पत्ती मरोड़)", "कटाई": "मई-जुलाई", "प्रो-टिप": "नई वृद्धि को प्रोत्साहित करने के लिए भारी छंटाई की जानी चाहिए, क्योंकि आड़ू केवल एक साल पुरानी लकड़ी पर ही फल देता है।"},

    # --- सब्जियां और मसाले (10) ---
    {"फसल": "मूली (Radish)", "प्रकार": "सब्जी", "सीजन": "रबी/खरीफ", "N-P-K": "50:50:50", "उर्वरक": "गोबर खाद, यूरिया", "बुवाई की विधि": "मेड़ और नाली", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", "कीट": "माहू", "कटाई": "30-50 दिन", "प्रो-टिप": "जल्दी कटाई महत्वपूर्ण है; अधिक समय तक छोड़ने पर जड़ सख्त और बेस्वाद हो जाती है।"},
    {"फसल": "गाजर (Carrot)", "प्रकार": "सब्जी", "सीजन": "रबी", "N-P-K": "60:60:100", "उर्वरक": "यूरिया, पोटाश", "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "गहरी/हल्की दोमट", "पानी": "मध्यम", "कीट": "गाजर की मक्खी", "कटाई": "90-110 दिन", "प्रो-टिप": "ताजी गोबर खाद से बचें; इससे जड़ें दो हिस्सों में बँट (fork) जाती हैं। सड़ी हुई कंपोस्ट का उपयोग करें।"},
    {"फसल": "पालक (Spinach)", "प्रकार": "सब्जी", "सीजन": "वर्षभर", "N-P-K": "80:40:40", "उर्वरक": "यूरिया (छिड़काव)", "बुवाई की विधि": "छिड़काव", "मिट्टी": "उपजाऊ दोमट", "पानी": "अधिक", "कीट": "लीफ माइनर", "कटाई": "30-45 दिन", "प्रो-टिप": "हर कटाई के बाद नाइट्रोजन डालें ताकि पत्तियों की दोबारा वृद्धि तेजी से हो सके।"},
    {"फसल": "लौकी (Bottle Gourd)", "प्रकार": "सब्जी", "सीजन": "गर्मी/खरीफ", "N-P-K": "40:30:30", "उर्वरक": "DAP, यूरिया", "बुवाई की विधि": "गड्डा/मचान", "मिट्टी": "गाद युक्त दोमट", "पानी": "मध्यम", "कीट": "लाल कद्दू भृंग", "कटाई": "60-75 दिन", "प्रो-टिप": "बेलों को मचान पर चढ़ाने से फलों का आकार सुधरता है और मिट्टी जनित रोगों से बचाव होता।"},
    {"फसल": "करेला (Bitter Gourd)", "प्रकार": "सब्जी", "सीजन": "गर्मी/खरीफ", "N-P-K": "50:50:50", "उर्वरक": "गोबर खाद, NPK", "बुवाई की विधि": "गड्डा रोपण", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", "कीट": "फल मक्खी", "कटाई": "55-70 दिन", "प्रो-टिप": "बीज का आवरण सख्त होता है; 90% से अधिक अंकुरण के लिए बीजों को 24 घंटे पानी में भिगोएँ।"},
    {"फसल": "कद्दू (Pumpkin)", "प्रकार": "सब्जी", "सीजन": "खरीफ/गर्मी", "N-P-K": "60:50:50", "उर्वरक": "DAP, यूरिया", "बुवाई की विधि": "गड्डा विधि", "मिट्टी": "जलोढ़", "पानी": "मध्यम", "कीट": "एपिलाचना बीटल", "कटाई": "90-120 दिन", "प्रो-टिप": "कटाई तभी करें जब फल को बेल से जोड़ने वाला तना सूखकर लकड़ी जैसा हो जाए।"},
    {"फसल": "खीरा (Cucumber)", "प्रकार": "सब्जी", "सीजन": "गर्मी", "N-P-K": "50:50:50", "उर्वरक": "यूरिया, SSP", "बुवाई की विधि": "बेसिन विधि", "मिट्टी": "बलुई दोमट", "पानी": "अधिक", "कीट": "डाउन मिल्ड्यू", "कटाई": "45-60 दिन", "प्रो-टिप": "खीरे में कड़वाहट पानी की कमी के कारण आती है; मिट्टी में नमी का स्तर बनाए रखें।"},
    {"फसल": "शिमला मिर्च (Capsicum)", "प्रकार": "सब्जी", "सीजन": "रबी/खरीफ", "N-P-K": "150:120:120", "उर्वरक": "DAP, पोटाश, कैल्शियम", "बुवाई की विधि": "रोपाई", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", "कीट": "थ्रिप्स/माइट्स", "कटाई": "75-90 दिन", "प्रो-टिप": "अक्सर तापमान नियंत्रित करने और वायरस रोगों को रोकने के लिए पॉली-हाउस में उगाया जाता है।"},
    {"फसल": "फ्रेंच बीन्स", "प्रकार": "सब्जी", "सीजन": "खरीफ/रबी", "N-P-K": "60:80:40", "उर्वरक": "यूरिया, DAP", "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "अच्छी जलनिकासी वाली दोमट", "पानी": "मध्यम", "कीट": "बीन एफिड", "कटाई": "50-70 दिन", "प्रो-टिप": "फूल आने के बाद अधिक नाइट्रोजन से बचें, क्योंकि यह फलियों के बजाय पत्तियों की वृद्धि को बढ़ावा देता है।"},
    {"फसल": "लहसुन (वसंतकालीन)", "प्रकार": "मसाला", "सीजन": "जायद", "N-P-K": "120:60:60", "उर्वरक": "अमोनियम सल्फेट", "बुवाई की विधि": "डिबलिंग", "मिट्टी": "दोमट", "पानी": "मध्यम", "कीट": "थ्रिप्स", "कटाई": "120 दिन", "प्रो-टिप": "कंदों के विस्तार के लिए उचित दूरी (15x10 सेमी) और जड़ों को नुकसान से बचाने के लिए उथली निराई आवश्यक है।"},

    # --- व्यावसायिक, मोटा अनाज और फूल (10) ---
    {"फसल": "गेंदा (Marigold)", "प्रकार": "फूल", "सीजन": "वर्षभर", "N-P-K": "100:100:100", "उर्वरक": "NPK मिश्रण", "बुवाई की विधि": "रोपाई", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", "कीट": "कलिका छेदक", "कटाई": "60-70 दिन", "प्रो-टिप": "अधिक शाखाओं और फूलों के लिए 40 दिनों पर मुख्य कली को तोड़ दें (Pinching)।"},
    {"फसल": "गुलाब (Rose)", "प्रकार": "फूल/व्यावसायिक", "सीजन": "बारहमासी", "N-P-K": "10:20:10 (अनुपात)", "उर्वरक": "बोन मील, गोबर खाद", "बुवाई की विधि": "कलमी पौधे", "मिट्टी": "अच्छी जलनिकासी वाली चिकनी", "पानी": "मध्यम", "कीट": "डाई-बैक रोग", "कटाई": "नियमित तुड़ाई", "प्रो-टिप": "अक्टूबर में वार्षिक छंटाई मृत लकड़ियों को हटाने और नए फूलों को प्रोत्साहित करने के लिए अनिवार्य है।"},
    {"फसल": "चमेली (Jasmine)", "प्रकार": "फूल/सुगंधित", "सीजन": "बारहमासी", "N-P-K": "60:120:120 (ग्राम/पौधा)", "उर्वरक": "NPK, नीम की खली", "बुवाई की विधि": "कलम", "मिट्टी": "बलुई दोमट", "पानी": "मध्यम", "कीट": "बड वॉर्म", "कटाई": "सुबह-सुबह", "प्रो-टिप": "फूलों के मौसम से पहले पौधे को आराम देने के लिए छंटाई (जनवरी) से पहले सिंचाई बंद कर दें।"},
    {"फसल": "कुटकी (Little Millet)", "प्रकार": "मोटा अनाज", "सीजन": "खरीफ", "N-P-K": "40:20:0", "उर्वरक": "यूरिया, SSP", "बुवाई की विधि": "छिड़काव", "मिट्टी": "खराब/पथरीली", "पानी": "कम", "कीट": "शूट फ्लाई", "कटाई": "80-90 दिन", "प्रो-टिप": "खराब मिट्टी और अधिक वर्षा वाले आदिवासी क्षेत्रों के लिए यह सबसे भरोसेमंद फसल है।"},
    {"फसल": "कंगनी (Foxtail Millet)", "प्रकार": "मोटा अनाज", "सीजन": "खरीफ/रबी", "N-P-K": "40:40:0", "उर्वरक": "DAP, यूरिया", "बुवाई की विधि": "ड्रिलिंग", "मिट्टी": "रेतीली से दोमट", "पानी": "कम", "कीट": "आर्मीवॉर्म", "कटाई": "90-100 दिन", "प्रो-टिप": "आयरन से भरपूर और कीट-प्रतिरोधी; शुष्क खेती के लिए आदर्श क्योंकि इसकी पानी की आवश्यकता बहुत कम है।"},
    {"फसल": "कुट्टू (Buckwheat)", "प्रकार": "छद्म अनाज", "सीजन": "रबी", "N-P-K": "40:20:20", "उर्वरक": "गोबर खाद, DAP", "बुवाई की विधि": "कतार में बुवाई", "मिट्टी": "अम्लीय/खराब मिट्टी", "पानी": "मध्यम", "कीट": "माहू", "कटाई": "70-90 दिन", "प्रो-टिप": "हिमालयी क्षेत्रों में उगाया जाता है; यह ग्लूटेन-मुक्त है और अगली फसलों के लिए मिट्टी की संरचना में सुधार करता है।"},
    {"फसल": "लौंग (Clove)", "प्रकार": "मसाला/बागानी", "सीजन": "बारहमासी", "N-P-K": "300:250:750 (ग्राम/पेड़)", "उर्वरक": "NPK, बोन मील", "बुवाई की विधि": "गड्डा रोपण", "मिट्टी": "गहरी लाल दोमट", "पानी": "अधिक", "कीट": "तना छेदक", "कटाई": "सितंबर-अक्टूबर", "प्रो-टिप": "फूलों की कलियों की कटाई तब करें जब वे गुलाबी हो जाएं; अगर वे खुल जाएं, तो उनका मसाला मूल्य कम हो जाता है।"},
    {"फसल": "जायफल (Nutmeg)", "प्रकार": "मसाला", "सीजन": "बारहमासी", "N-P-K": "500:250:1000 (ग्राम/पेड़)", "उर्वरक": "खाद, पोटाश", "बुवाई की विधि": "गड्डा विधि", "मिट्टी": "जलोढ़/लैटराइट", "पानी": "अधिक", "कीट": "स्केल कीट", "कटाई": "जून-अगस्त", "प्रो-टिप": "एक ही पौधे से दो मसाले (जायफल और जावित्री) मिलते हैं; पहले 3 वर्षों के दौरान छाया की आवश्यकता होती है।"},
    {"फसल": "रबड़ (वयस्क)", "प्रकार": "व्यावसायिक", "सीजन": "बारहमासी", "N-P-K": "30:30:30", "उर्वरक": "NPK मिश्रण", "बुवाई की विधि": "टैपिंग", "मिट्टी": "लैटराइट", "पानी": "अधिक", "कीट": "पाउडर मिल्ड्यू", "कटाई": "लेटेक्स टैपिंग", "प्रो-टिप": "टैपिंग सुबह 9 बजे से पहले की जानी चाहिए जब पेड़ में दबाव (Turgor pressure) सबसे अधिक होता है।"},
    {"फसल": "हॉप्स (Hops)", "प्रकार": "व्यावसायिक", "सीजन": "रबी", "N-P-K": "150:100:100", "उर्वरक": "यूरिया, SSP, पोटाश", "बुवाई की विधि": "मचान/बेल", "मिट्टी": "गहरी दोमट", "पानी": "अधिक", "कीट": "डाउन मिल्ड्यू", "कटाई": "अगस्त-सितंबर", "प्रो-टिप": "मादा फूल (कोन) आर्थिक हिस्सा हैं; विकास चरण के दौरान लंबी धूप की अवधि की आवश्यकता होती है।"}
]
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
