import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import pandas as pd

st.set_page_config(page_title="Проверка ЦИАН")

st.title("Проверка данных ЦИАН")

# --------------------
# Загрузка прокси
# --------------------

try:
    with open("proxies.txt", "r") as f:
        proxies = [x.strip() for x in f if x.strip()]
except:
    st.error("Файл proxies.txt не найден")
    st.stop()

st.write("Прокси загружено:", len(proxies))

proxy = random.choice(proxies)

st.write("Текущий прокси:")
st.code(proxy)

# --------------------
# Проверка
# --------------------

if st.button("Проверить объявление"):

    try:

        url = "https://www.cian.ru/sale/flat/321614105/"

        r = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            proxies={
                "http": proxy,
                "https": proxy
            },
            timeout=30
        )

        st.success(f"HTTP статус: {r.status_code}")

        html = r.text

        # показать первые символы ответа
        st.subheader("Начало страницы")

        st.text_area(
            "",
            html[:5000],
            height=300
        )

        # проверка капчи

        if "Вы не робот" in html:
            st.error("ЦИАН вернул капчу")

        elif "captcha" in html.lower():
            st.error("Обнаружена капча")

        else:
            st.success("Капча не обнаружена")

        # ссылки

        soup = BeautifulSoup(html, "html.parser")

        links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "/sale/flat/" in href:
                links.append(href)

        links = list(set(links))

        st.subheader("Найденные ссылки")

        if links:

            df = pd.DataFrame({
                "url": links
            })

            st.dataframe(df)

        else:

            st.warning("Ссылки не найдены")

    except Exception as e:

        st.error(str(e))
