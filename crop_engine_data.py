import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import LabelEncoder

def get_agri_dataframe():
    crops = {
        'Crop Name': ['Wheat', 'Rice', 'Cotton', 'Maize', 'Groundnut', 'Soybean', 'Mustard', 'Sugarcane', 'Chickpea', 'Potato'],
        'Soil Type': ['Alluvial', 'Alluvial', 'Black Soil', 'Red Soil', 'Sandy', 'Black Soil', 'Alluvial', 'Loamy', 'Heavy Soil', 'Sandy Loam'],
        'Sowing Month': [11, 6, 6, 6, 5, 6, 10, 2, 10, 10],
        'Cost per Acre': [15000, 25000, 20000, 12000, 18000, 16000, 14000, 30000, 13000, 35000]
    }
    df = pd.DataFrame(crops)
    le = LabelEncoder()
    df['Soil_Idx'] = le.fit_transform(df['Soil Type'])
    return df, le

def recommend_crops(df, le, soil_pref, budget):
    X = df[['Soil_Idx', 'Sowing Month', 'Cost per Acre']]
    knn = NearestNeighbors(n_neighbors=2).fit(X)
    try:
        u_idx = le.transform([soil_pref])[0]
    except:
        u_idx = 0
    _, idx = knn.kneighbors([[u_idx, 6, budget]])
    return df.iloc[idx[0]]
