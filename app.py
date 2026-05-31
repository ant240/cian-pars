import streamlit as st
import requests
import random
import os

st.set_page_config(page_title="Тест ЦИАН")

st.title("Проверка доступа к ЦИАН")

if not os.path.exists("proxies.txt"):
    st.error("Файл proxies.txt не найден")
    st.stop()

with open("proxies.txt", "r") as f:
    proxies = [x.strip() for x in f if x.strip()]

st.write(f"Прокси загружено: {len(proxies)}")

proxy = random.choice(proxies)

st.code(proxy)

proxy_dict = {
    "http": f"http://{proxy}",
    "https": f"http://{proxy}"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0 Safari/537.36"
}

if st.button("Проверить ЦИАН"):
    try:

        url = "https://www.cian.ru/"

        r = requests.get(
            url,
            headers=headers,
            proxies=proxy_dict,
            timeout=20
        )

        st.success(f"HTTP статус: {r.status_code}")

        st.write("Размер ответа:")
        st.write(len(r.text))

        st.text_area(
            "Первые 1000 символов",
            r.text[:1000],
            height=300
        )

    except Exception as e:
        st.error(str(e))
