import streamlit as st
import requests
import random
import os
import re

st.set_page_config(page_title="Тест ЦИАН")

st.title("Проверка объявлений ЦИАН")

if not os.path.exists("proxies.txt"):
    st.error("Файл proxies.txt не найден")
    st.stop()

with open("proxies.txt", "r") as f:
    proxies = [x.strip() for x in f if x.strip()]

st.write(f"Прокси загружено: {len(proxies)}")

proxy = random.choice(proxies)

st.code(proxy)

proxy_dict = {
    "http": proxy,
    "https": proxy
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
}

if st.button("Проверить объявления"):
    try:

        url = "https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=1&room1=1"

        r = requests.get(
            url,
            headers=headers,
            proxies=proxy_dict,
            timeout=30
        )

        st.success(f"HTTP статус: {r.status_code}")

        st.write("Размер ответа:")
        st.write(len(r.text))

        matches = re.findall(
            r'https://www\.cian\.ru/sale/flat/\d+/',
            r.text
        )

        matches = list(set(matches))

        st.write("Найдено ссылок:")
        st.write(len(matches))

        if matches:

            st.success("Объявления найдены")

            for link in matches[:20]:
                st.write(link)

        else:

            st.error("Ссылки на объявления не найдены")

            st.text_area(
                "Первые 2000 символов ответа",
                r.text[:2000],
                height=400
            )

    except Exception as e:
        st.error(str(e))
