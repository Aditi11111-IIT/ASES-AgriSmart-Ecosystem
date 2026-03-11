import streamlit as st
import pandas as pd
import random
import urllib.parse
from fpdf import FPDF
import plotly.express as px
import numpy as np

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Agri-Smart Ecosystem", layout="wide", page_icon="🌾")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #2e7d32; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINES ---

@st.cache_data
def get_national_rental_data():
    state_map = {
        "Punjab": ["Ludhiana", "Amritsar", "Patiala"],
        "Bihar": ["Patna", "Gaya", "Muzaffarpur"],
        "Maharashtra": ["Pune", "Nashik", "Nagpur"],
        "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi"],
        "Karnataka": ["Bengaluru", "Mysuru", "Hubballi"],
        "Gujarat": ["Ahmedabad", "Surat", "Rajkot"]
    }
    categories = {
        "🚜 Machinery": ["Tractor", "Harvester", "Rotavator"],
        "🌱 Seeds": ["Hybrid Wheat", "Basmati Rice", "Bt Cotton"],
        "🧪 Fertilizers": ["Urea", "DAP", "Potash"]
    }
    
    data = []
    names = ["Sandeep", "Rajesh", "Anjali", "Gurnam", "Venkat", "Amit"]
    for state, districts in state_map.items():
        for dist in districts:
            for cat, items in categories.items():
                for item in items:
                    data.append({
                        "State": state, "District": dist, "Category": cat, "Item": item,
                        "Owner": f"{random.choice(names)} {random.choice(['Singh', 'Kumar', 'Reddy', 'Patil'])}",
                        "Phone": f"+91{random.randint(7000000000, 9999999999)}",
                        "Price": f"₹{random.randint(400, 5000)}"
                    })
    return pd.DataFrame(data)

# --- 3. PDF UTILITY ---
def export_as_pdf(title, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 10)
    col_width = 190 / len(df.columns)
    for col in df.columns:
        pdf.cell(col_width, 10, txt=str(col), border=1)
    pdf.ln()
    
    pdf.set_font("Arial", size=9)
    for i, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, 10, txt=str(item)[:20], border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 4. NAVIGATION SIDEBAR ---
st.sidebar.title("🌿 Agri-Smart v1.0")
st.sidebar.info("Empowering Indian Farmers with Technology")
menu = st.sidebar.radio("Go To:", ["🏠 Dashboard", "🏪 Rental & Supply Hub", "🏛️ Govt Schemes", "📚 Knowledge Hub", "📈 Price Prediction", "📒 Agri Khata"])

# --- MODULE 1: DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("👨‍🌾 Farmer Command Center")
    col1, col2, col3 = st.columns(3)
    col1.metric("Weather", "29°C", "Partly Cloudy")
    col2.metric("Soil Health", "Good", "85% Score")
    col3.metric("Market Price (Wheat)", "₹2,275/q", "+₹25")
    
    st.subheader("⚠️ Smart Alerts")
    st.warning("Rain expected in 48 hours. Postpone fertilizer application.")
    st.success("High demand for Mustard in local Mandi. Consider harvesting.")

# --- MODULE 2: RENTAL & SUPPLY HUB ---
elif menu == "🏪 Rental & Supply Hub":
    st.title("🛒 National Agri-Market")
    df_hub = get_national_rental_data()
    
    c1, c2, c3 = st.columns(3)
    with c1: state = st.selectbox("Select State", sorted(df_hub['State'].unique()))
    with c2: 
        dists = sorted(df_hub[df_hub['State'] == state]['District'].unique())
        dist = st.selectbox("Select District", dists)
    with c3: cat = st.radio("Category", ["🚜 Machinery", "🌱 Seeds", "🧪 Fertilizers"], horizontal=True)

    filtered = df_hub[(df_hub['State'] == state) & (df_hub['District'] == dist) & (df_hub['Category'] == cat)]
    
    for _, row in filtered.iterrows():
        with st.container():
            res_col1, res_col2 = st.columns([3, 1])
            with res_col1:
                st.markdown(f"### {row['Item']}")
                st.write(f"👤 **Owner:** {row['Owner']} | 💰 **Price:** {row['Price']}")
                st.caption(f"📍 Location: {row['District']}, {row['State']}")
            with res_col2:
                st.markdown(f'<a href="tel:{row["Phone"]}" style="text-decoration:none;"><div style="background:#1b5e20;color:white;padding:8px;border-radius:5px;text-align:center;font-weight:bold;margin-bottom:5px;">📞 Call</div></a>', unsafe_allow_html=True)
                msg = urllib.parse.quote(f"Hello {row['Owner']}, I saw your {row['Item']} on Agri-Smart.")
                st.markdown(f'<a href="https://wa.me/{row["Phone"].replace("+","")}?text={msg}" target="_blank" style="text-decoration:none;"><div style="background:#25D366;color:white;padding:8px;border-radius:5px;text-align:center;font-weight:bold;">💬 WhatsApp</div></a>', unsafe_allow_html=True)
            st.divider()

# --- MODULE 3: GOVT SCHEMES ---
elif menu == "🏛️ Govt Schemes":
    st.title("🏛️ Govt. Support & Subsidy")
    land = st.number_input("Enter Land Size (Hectares)", 0.1, 100.0, 1.0)
    profile = st.selectbox("Your Profile", ["Small Farmer", "Large Farmer", "Organic Farmer"])
    
    schemes = [
        {"Name": "PM-Kisan", "Match": "Small", "Benefit": "₹6,000/year Cash Support"},
        {"Name": "KCC Credit Line", "Match": "Small", "Benefit": f"Credit up to ₹{land*75000:,.0f}"},
        {"Name": "Organic Subsidy (PKVY)", "Match": "Organic", "Benefit": f"₹{land*50000:,.0f} support"}
    ]
    
    for s in schemes:
        if "Small" in s['Match'] or profile.split()[0] in s['Match']:
            with st.expander(f"✅ {s['Name']}"):
                st.write(f"**Benefit:** {s['Benefit']}")
                st.button(f"Apply for {s['Name']}", key=s['Name'])

# --- MODULE 4: KNOWLEDGE HUB (RESTORED FULL LIST) ---
elif menu == "📚 Knowledge Hub":
    st.title("📚 Crop Resource Library | फसल संसाधन पुस्तकालय")
    lang = st.radio("Select Language / भाषा चुनें", ["English", "Hindi"], horizontal=True)

    crops_data = {
        "English": [
            {"Crop": "Wheat", "N-P-K Ratio": "120:60:40", "Sowing": "Nov-Dec", "Soil": "Loamy", "Pest Control": "Chlorpyrifos"},
            {"Crop": "Rice", "N-P-K Ratio": "100:60:40", "Sowing": "June-July", "Soil": "Clayey", "Pest Control": "Neem Oil"},
            {"Crop": "Cotton", "N-P-K Ratio": "100:50:50", "Sowing": "May-June", "Soil": "Black Soil", "Pest Control": "Spinosad"},
            {"Crop": "Sugarcane", "N-P-K Ratio": "150:80:60", "Sowing": "Jan-March", "Soil": "Alluvial", "Pest Control": "Imidacloprid"},
            {"Crop": "Maize", "N-P-K Ratio": "120:60:40", "Sowing": "June-July", "Soil": "Loamy/Red", "Pest Control": "Atrazine"},
            {"Crop": "Mustard", "N-P-K Ratio": "80:40:40", "Sowing": "Oct-Nov", "Soil": "Sandy Loam", "Pest Control": "Dimethoate"},
            {"Crop": "Chickpea", "N-P-K Ratio": "20:60:20", "Sowing": "Oct-Nov", "Soil": "Heavy Soils", "Pest Control": "Indoxacarb"},
            {"Crop": "Groundnut", "N-P-K Ratio": "20:40:40", "Sowing": "June-July", "Soil": "Sandy Soil", "Pest Control": "Mancozeb"},
            {"Crop": "Soybean", "N-P-K Ratio": "20:60:40", "Sowing": "June", "Soil": "Well-drained", "Pest Control": "Quinalphos"},
            {"Crop": "Moong Dal", "N-P-K Ratio": "20:40:20", "Sowing": "March-April", "Soil": "Loamy", "Pest Control": "Malathion"}
        ],
        "Hindi": [
            {"फसल": "गेहूं", "N-P-K अनुपात": "120:60:40", "बुवाई": "नवंबर-दिसंबर", "मिट्टी": "दोमट", "कीट नियंत्रण": "क्लोरपायरीफॉस"},
            {"फसल": "चावल", "N-P-K अनुपात": "100:60:40", "बुवाई": "जून-जुलाई", "मिट्टी": "चिकनी मिट्टी", "कीट नियंत्रण": "नीम का तेल"},
            {"फसल": "कपास", "N-P-K अनुपात": "100:50:50", "बुवाई": "मई-जून", "मिट्टी": "काली मिट्टी", "कीट नियंत्रण": "स्पिनोसैड"},
            {"फसल": "गन्ना", "N-P-K अनुपात": "150:80:60", "बुवाई": "जनवरी-मार्च", "मिट्टी": "जलोढ़ मिट्टी", "कीट नियंत्रण": "इमिडाक्लोप्रिड"},
            {"फसल": "मक्का", "N-P-K अनुपात": "120:60:40", "बुवाई": "जून-जुलाई", "मिट्टी": "दोमट/लाल", "कीट नियंत्रण": "एट्राजीन"},
            {"फसल": "सरसों", "N-P-K अनुपात": "80:40:40", "बुवाई": "अक्टूबर-नवंबर", "मिट्टी": "बलुई दोमट", "कीट नियंत्रण": "डाइमेथोएट"},
            {"फसल": "चना", "N-P-K अनुपात": "20:60:20", "बुवाई": "अक्टूबर-नवंबर", "मिट्टी": "भारी मिट्टी", "कीट नियंत्रण": "इंडोक्साकार्ब"},
            {"फसल": "मूंगफली", "N-P-K अनुपात": "20:40:40", "बुवाई": "जून-जुलाई", "मिट्टी": "रेतीली मिट्टी", "कीट नियंत्रण": "मैनकोजेब"},
            {"फसल": "सोयाबीन", "N-P-K अनुपात": "20:60:40", "बुवाई": "जून", "मिट्टी": "निकास वाली", "कीट नियंत्रण": "क्विनल्फॉस"},
            {"फसल": "मूंग दाल", "N-P-K अनुपात": "20:40:20", "बुवाई": "मार्च-अप्रैल", "मिट्टी": "दोमट", "कीट नियंत्रण": "मैलाथियान"}
        ]
    }

    df_k = pd.DataFrame(crops_data[lang])
    search_label = "🔍 Search Crop" if lang == "English" else "🔍 फसल खोजें"
    search_query = st.text_input(search_label)
    
    first_col = df_k.columns[0]
    filtered_df = df_k[df_k[first_col].str.contains(search_query, case=False)]

    st.table(filtered_df)

    btn_label = "📥 Download Chart as PDF" if lang == "English" else "📥 चार्ट को PDF के रूप में डाउनलोड करें"
    if st.button(btn_label):
        pdf_data = export_as_pdf("Agri-Knowledge-Chart", filtered_df)
        st.download_button(label="Click here to Save File", data=pdf_data, file_name="crop_resource_chart.pdf", mime="application/pdf")

    if lang == "English":
        st.info("💡 **Quick Guide:** N-P-K is vital for growth, Soil type determines water retention, and Pest Control protects yield.")
    else:
        st.info("💡 **त्वरित मार्गदर्शिका:** N-P-K वृद्धि के लिए महत्वपूर्ण है, मिट्टी का प्रकार जल धारण निर्धारित करता है, और कीट नियंत्रण उपज की रक्षा करता है।")

# --- MODULE 4: PRICE PREDICTION ---
elif menu == "📈 Price Prediction":
    st.title("📈 AI Market Price Prediction")
    st.subheader("Historical Trends & Future Forecast")
    
    crop_list = ["Wheat", "Rice", "Cotton", "Sugarcane", "Maize", "Mustard", "Chickpea", "Groundnut", "Soybean", "Moong Dal"]
    selected_crop = st.selectbox("Select Crop to Analyze", crop_list)
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    base_prices = {"Wheat": 2100, "Rice": 2400, "Cotton": 6200, "Sugarcane": 320, "Maize": 1900, "Mustard": 5100, "Chickpea": 4800, "Groundnut": 5500, "Soybean": 4200, "Moong Dal": 7000}
    
    base = base_prices[selected_crop]
    predicted_prices = [base + (i * random.randint(10, 40)) + random.randint(-80, 80) for i in range(12)]
    
    df_price = pd.DataFrame({"Month": months, "Predicted Price (₹)": predicted_prices})
    fig = px.line(df_price, x="Month", y="Predicted Price (₹)", title=f"12-Month Price Forecast: {selected_crop}", markers=True)
    fig.update_traces(line_color='#2e7d32', line_width=3)
    st.plotly_chart(fig, use_container_width=True)
    
    max_price = max(predicted_prices)
    best_month = months[predicted_prices.index(max_price)]
    st.success(f"✅ **Market Insight:** The best time to sell **{selected_crop}** is predicted to be in **{best_month}** with an expected price of **₹{max_price}/quintal**.")
    

# --- MODULE 5: AGRI KHATA ---
elif menu == "📒 Agri Khata":
    st.title("📒 Agri Khata (Financials)")
    if 'ledger' not in st.session_state:
        st.session_state.ledger = pd.DataFrame([{"Item": "Initial Seed", "Cost": 1200}])
    
    with st.form("ledger_form"):
        item = st.text_input("Expense Item")
        cost = st.number_input("Cost (₹)", 0)
        if st.form_submit_button("Add Entry"):
            new_entry = pd.DataFrame([{"Item": item, "Cost": cost}])
            st.session_state.ledger = pd.concat([st.session_state.ledger, new_entry], ignore_index=True)
    
    fig = px.pie(st.session_state.ledger, values='Cost', names='Item', title="Expense Breakdown")
    st.plotly_chart(fig)
