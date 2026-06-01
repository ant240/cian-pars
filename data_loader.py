import pandas as pd
import streamlit as st
from cianparser import CianParser

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    parser = CianParser(location="Москва")
    data = parser.get_flats(
        deal_type="sale",
        rooms=(1,2,3,4,5),
        additional_settings={"start_page":1,"end_page":2},
    )
    
    df = pd.DataFrame(data)
    
    # добавим колонку метро для теста (если пусто)
    if "underground" in df.columns:
        df["metro"] = df["underground"].fillna("")
    else:
        df["metro"] = ""
    
    return df

@st.cache_data(ttl=3600, show_spinner=False)
def load_card_details(url: str):
    parser = CianParser(location="Москва")
    details = parser.get_flat_card(url)
    return details
