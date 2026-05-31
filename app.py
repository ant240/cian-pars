import streamlit as st
import pandas as pd
import cianparser
import os
import time
import random

st.set_page_config(page_title="GRADOV FLATS")
st.title("GRADOV FLATS - Тест парсинга (1 страница)")

def load_proxies():
    if os.path.exists("proxies.txt"):
        with open("proxies.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    return None

proxies = load_proxies()
if proxies:
    st.info(f"Загружено {len(proxies)} прокси. Используем случайный для теста.")
    current_proxy = random.choice(proxies)
    st.write(f"Прокси: {current_proxy[:80]}...")
    parser = cianparser.CianParser(
        location="Москва",
        proxies={"http": current_proxy, "https": current_proxy}
    )
else:
    st.warning("Прокси не найдены, работаем без прокси")
    parser = cianparser.CianParser(location="Москва")

try:
    with st.spinner("Парсинг страницы 1 (однушки, только собственники)... Это может занять 5-15 секунд."):
        data = parser.get_flats(
            deal_type="sale",
            rooms=(1,),
            additional_settings={"start_page": 1, "end_page": 1},
            is_by_homeowner=True
        )
        if data and len(data) > 0:
            df = pd.DataFrame(data)
            st.success(f"✅ Получено {len(df)} объявлений")
            st.dataframe(df.head(5))
            st.caption("Показаны первые 5 объявлений. Если данные есть, парсинг работает.")
        else:
            st.error("Нет данных. Возможные причины: блокировка ЦИАН, нерабочий прокси, или нет объявлений по запросу.")
except Exception as e:
    st.error(f"Ошибка парсинга: {e}")
    st.code("Проверьте логи для деталей.")
