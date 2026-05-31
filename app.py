import streamlit as st
import pandas as pd
import cianparser
import os

st.set_page_config(page_title="GRADOV FLATS")
st.title("GRADOV FLATS - Тест прокси")

st.write("✅ Библиотеки импортированы")

def load_proxies():
    if os.path.exists("proxies.txt"):
        with open("proxies.txt", "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    return None

proxies = load_proxies()
if proxies:
    st.success(f"✅ Найдено {len(proxies)} прокси. Первый: {proxies[0][:60]}...")
else:
    st.warning("Файл proxies.txt не найден. Парсинг будет без прокси (может быть медленнее).")

st.info("Этап 2 пройден. Теперь можно добавлять парсинг.")
