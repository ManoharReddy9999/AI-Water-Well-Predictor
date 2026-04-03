import streamlit as st
import pandas as pd
import pickle
import os
import folium
from streamlit_folium import st_folium

# ==============================
# Load Models (Dummy for now)
# ==============================
@st.cache_resource
def load_models():
    models = {}
    try:
        models['site'] = pickle.load(open("models/site_suitability.pkl", "rb"))
        models['depth'] = pickle.load(open("models/depth_predictor.pkl", "rb"))
        models['discharge'] = pickle.load(open("models/discharge_predictor.pkl", "rb"))
        models['drilling'] = pickle.load(open("models/drilling_predictor.pkl", "rb"))
        models['quality'] = pickle.load(open("models/quality_predictor.pkl", "rb"))
    except Exception as e:
        st.warning(f"Some models could not be loaded: {e}")
    return models

models = load_models()

# ==============================
# Streamlit Config
# ==============================
st.set_page_config(page_title="AI-Enabled Water Well Predictor", layout="wide")

st.title("💧 AI-Enabled Water Well Predictor")
st.markdown("AI-powered tool for predicting **site suitability, aquifer depth, discharge, "
            "drilling method, and groundwater quality** using NAQUIM-style datasets.")

# ==============================
# Prediction Logic (separated)
# ==============================
def get_predictions(input_df):
    """
    This function accepts a pandas DataFrame row of features
    and returns model predictions (dummy logic for now).
    """
    site_suitability = "✅ Suitable" if input_df["depth_to_bedrock"].iloc[0] > 20 else "❌ Not Suitable"
    predicted_depth = input_df["depth_to_bedrock"].iloc[0] + 15
    predicted_discharge = "💧 High" if input_df["water_table_depth"].iloc[0] < 50 else "⚖ Moderate"
    drilling_method = "🛠 Rotary Drilling" if input_df["depth_to_bedrock"].iloc[0] > 50 else "🔨 Percussion Drilling"
    water_quality = "👍 Good" if 6.5 <= input_df["ph"].iloc[0] <= 8.5 and input_df["tds"].iloc[0] < 500 else "⚠ Poor"
    return site_suitability, predicted_depth, predicted_discharge, drilling_method, water_quality

# ==============================
# Sidebar Navigation
# ==============================
menu = ["Home", "Predict Well Suitability", "Bulk Prediction", "About"]
choice = st.sidebar.radio("Navigation", menu)

# ==============================
# Home Page
# ==============================
if choice == "Home":
    st.subheader("Overview")
    st.write("""
    This system integrates **NAQUIM-style data** with **Machine Learning models** 
    to predict water well characteristics:
    - Site suitability
    - Depth of water-bearing zone
    - Expected discharge
    - Suitable drilling technique
    - Expected groundwater quality

    **Dataset Used**:
    - AP_NAQUIM_style_water_well_dataset_1000.csv
    """)

# ==============================
# Prediction Page
# ==============================
elif choice == "Predict Well Suitability":
    st.subheader("Select Input Mode")

    input_mode = st.radio("Choose Input Mode", ["Manual Entry", "From NAQUIM Dataset", "From Map"])
    input_df, lat, lon = None, None, None

    if input_mode == "Manual Entry":
        lithology = st.selectbox("Lithology Type", ["Sandstone", "Shale", "Limestone", "Granite"])
        depth_to_bedrock = st.number_input("Depth to Bedrock (m)", min_value=0.0, step=1.0)
        water_table_depth = st.number_input("Water Table Depth (m)", min_value=0.0, step=0.5)
        discharge = st.number_input("Expected Yield (LPM)", min_value=0.0, step=10.0)
        tds = st.number_input("Total Dissolved Solids (mg/L)", min_value=0.0, step=10.0)
        ph = st.slider("pH Level", 0.0, 14.0, 7.0)

        input_df = pd.DataFrame({
            "lithology": [lithology],
            "depth_to_bedrock": [depth_to_bedrock],
            "water_table_depth": [water_table_depth],
            "discharge": [discharge],
            "tds": [tds],
            "ph": [ph]
        })

    elif input_mode == "From NAQUIM Dataset":
        dataset_path = "data/processed/AP_NAQUIM_style_water_well_dataset_1000.csv"
        if os.path.exists(dataset_path):
            df = pd.read_csv(dataset_path)
            st.write("📂 Sample Dataset", df.head())
            row = st.number_input("Select Row ID", min_value=0, max_value=len(df)-1, step=1)
            input_df = df.iloc[[row]]
            st.write("📊 Selected Data", input_df)
        else:
            st.error("Dataset not found. Please place the CSV file in `data/processed/` folder.")

    elif input_mode == "From Map":
        st.subheader("🌍 Select Location on Map")
        m = folium.Map(location=[23.5, 80.5], zoom_start=5)  # India center
        map_data = st_folium(m, width=700, height=500)

        if map_data and map_data["last_clicked"]:
            lat = map_data["last_clicked"]["lat"]
            lon = map_data["last_clicked"]["lng"]
            st.success(f"Selected Location: {lat:.4f}, {lon:.4f}")

            # TODO: Map lat/lon → nearest dataset row
            input_df = pd.DataFrame({
                "lithology": ["Sandstone"],
                "depth_to_bedrock": [45],
                "water_table_depth": [30],
                "discharge": [100],
                "tds": [400],
                "ph": [7.2]
            })

    # ==============================
    # Better Results Display
    # ==============================
    if input_df is not None:
        site, depth, discharge, drill, quality = get_predictions(input_df)

        st.markdown("### 🔎 Prediction Results")
        st.write("---")

        col1, col2, col3 = st.columns(3)
        with col1: st.success(f"**Suitability:** {site}")
        with col2: st.info(f"**Depth (m):** {depth}")
        with col3: st.warning(f"**Discharge:** {discharge}")

        col4, col5 = st.columns(2)
        with col4: st.success(f"**Drilling Method:** {drill}")
        with col5: st.error(f"**Quality:** {quality}")

        st.write("---")

        # ==============================
        # Structured Feedback Section
        # ==============================
        st.subheader("📝 User Feedback")
        with st.form("feedback_form"):
            user_name = st.text_input("Your Name")
            user_email = st.text_input("Your Email")
            rating = st.slider("How accurate were the predictions?", 1, 5, 3)
            feedback_text = st.text_area("Additional Feedback")

            submitted = st.form_submit_button("Submit Feedback")
            if submitted:
                feedback_entry = pd.DataFrame([{
                    "name": user_name,
                    "email": user_email,
                    "rating": rating,
                    "feedback": feedback_text
                }])
                if os.path.exists("feedback.csv"):
                    feedback_entry.to_csv("feedback.csv", mode="a", header=False, index=False)
                else:
                    feedback_entry.to_csv("feedback.csv", index=False)
                st.success("✅ Feedback submitted successfully!")

# ==============================
# Bulk Prediction (NAQUIM Dataset)
# ==============================
elif choice == "Bulk Prediction":
    st.subheader("Upload NAQUIM Dataset for Bulk Predictions")
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("📂 Uploaded Data", df.head())

        predictions = []
        for i in range(len(df)):
            site, depth, discharge, drill, quality = get_predictions(df.iloc[[i]])
            predictions.append([site, depth, discharge, drill, quality])

        results_df = pd.DataFrame(predictions, columns=["Suitability", "Depth", "Discharge", "Drilling", "Quality"])
        st.write("🔮 Bulk Prediction Results", results_df.head())

        st.download_button("📥 Download Results", results_df.to_csv(index=False), "bulk_predictions.csv")

# ==============================
# About Page
# ==============================
else:
    st.subheader("About Project")
    st.write("""
    - **Frontend**: Streamlit  
    - **Backend**: Machine Learning Models (Random Forest, XGBoost, Neural Networks)  
    - **Dataset**: NAQUIM-style dataset (for site, depth, discharge, drilling, water quality)  
    """)
