import pandas as pd
import streamlit as st
from cianparser import CianParser
import requests
from bs4 import BeautifulSoup


@st.cache_data(ttl=3600)
def load_data():

    parser = CianParser(location="Москва")

    data = parser.get_flats(
        deal_type="sale",
        rooms=(1, 2, 3, 4, 5),
        with_saving_csv=False,
        additional_settings={
            "start_page": 1,
            "end_page": 1
        }
    )

    df = pd.DataFrame(data)

    if len(df) == 0:
        return pd.DataFrame()

    if "city" in df.columns:
        df = df[df["city"].astype(str).str.contains("Москва", na=False)]

    if "price" in df.columns:
        df = df[df["price"] > 0]

    if "total_meters" in df.columns:
        df = df[df["total_meters"] > 0]

    return df


@st.cache_data(ttl=86400)
def load_card_details(url):

    result = {
        "Год постройки": "",
        "Тип дома": "",
        "Высота потолков": "",
        "Отделка": "",
        "Сдача": "",
        "До метро": ""
    }

    try:

        headers = {
            "User-Agent":
            "Mozilla/5.0"
        }

        r = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        html = r.text

        if len(html) < 1000:
            return result

        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text(" ", strip=True)

        if "Год постройки" in text:
            result["Год постройки"] = "Найдено"

        if "Высота потолков" in text:
            result["Высота потолков"] = "Найдена"

        if "Отделка" in text:
            result["Отделка"] = "Найдена"

        return result

    except Exception:
        return result
