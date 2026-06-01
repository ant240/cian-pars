import pandas as pd
import streamlit as st
from cianparser import CianParser
import requests
from bs4 import BeautifulSoup


@st.cache_data(ttl=3600)
def load_data():

    parser = CianParser(location="Москва")

    try:

        data = parser.get_flats(
            deal_type="sale",
            rooms=(1, 2, 3, 4, 5),
            with_saving_csv=False,
            additional_settings={
                "start_page": 1,
                "end_page": 10
            }
        )

    except Exception:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if len(df) == 0:
        return pd.DataFrame()

    if "price" in df.columns:
        df = df[df["price"] > 0]

    if "total_meters" in df.columns:
        df = df[df["total_meters"] > 0]

    df = df.reset_index(drop=True)

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
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            return result

        html = response.text

        if len(html) < 1000:
            return result

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        text = soup.get_text(
            " ",
            strip=True
        )

        if "Год постройки" in text:
            result["Год постройки"] = "Есть"

        if "Тип дома" in text:
            result["Тип дома"] = "Есть"

        if "Высота потолков" in text:
            result["Высота потолков"] = "Есть"

        if "Отделка" in text:
            result["Отделка"] = "Есть"

        if "Сдача" in text:
            result["Сдача"] = "Есть"

        if "метро" in text.lower():
            result["До метро"] = "Есть"

        return result

    except Exception:
        return result
