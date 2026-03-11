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
    }
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
    }
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
