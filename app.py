import streamlit as st
import requests
from bs4 import BeautifulSoup
import random

st.set_page_config(page_title="Проверка ЦИАН")

st.title("Проверка содержимого объявления ЦИАН")

with open("proxies.txt", "r") as f:
    proxies = [x.strip() for x in f if x.strip()]

proxy = random.choice(proxies)

st.write("Прокси:")
st.code(proxy)

url = st.text_input(
    "Ссылка на объявление ЦИАН",
    "https://www.cian.ru/"
)

if st.button("Проверить"):

    try:
        r = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            proxies={
                "http": proxy,
                "https": proxy
            },
            timeout=20
        )

        st.write("Статус:", r.status_code)
        st.write("Размер страницы:", len(r.text))

        st.subheader("Первые 5000 символов")

        st.text_area(
            "",
            r.text[:5000],
            height=500
        )

    except Exception as e:
        st.error(str(e))
