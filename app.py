import streamlit as st
import requests
import random
import os

st.set_page_config(page_title="Проверка прокси")

st.title("Диагностика прокси")

def load_proxies():
    if not os.path.exists("proxies.txt"):
        return []

    with open("proxies.txt", "r") as f:
        return [line.strip() for line in f if line.strip()]

proxies = load_proxies()

st.write(f"Прокси загружено: {len(proxies)}")

if not proxies:
    st.error("Файл proxies.txt не найден")
    st.stop()

if st.button("Запустить тест"):

    proxy = random.choice(proxies)

    st.write("Тестируем прокси:")
    st.code(proxy)

    try:

        response = requests.get(
            "https://api.ipify.org?format=json",
            proxies={
                "http": proxy,
                "https": proxy
            },
            timeout=20
        )

        st.success("Прокси отвечает")

        st.write("HTTP статус:")

        st.code(response.status_code)

        st.write("Ответ:")

        st.code(response.text)

    except Exception as e:

        st.error("Прокси не работает")

        st.code(str(e))
