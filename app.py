import streamlit as st
import random
import os

from cianparser import CianParser

st.set_page_config(page_title="Тест парсера ЦИАН")

st.title("Проверка парсера ЦИАН")

if not os.path.exists("proxies.txt"):
    st.error("Файл proxies.txt не найден")
    st.stop()

with open("proxies.txt", "r") as f:
    proxies = [x.strip() for x in f if x.strip()]

st.write(f"Прокси загружено: {len(proxies)}")

proxy = random.choice(proxies)

st.code(proxy)

if st.button("Проверить парсер"):

    try:

        parser = CianParser(
            proxy=proxy
        )

        data = parser.get_flats(
            deal_type="sale",
            rooms=(1,),
            location="Москва",
            additional_settings={
                "start_page": 1,
                "end_page": 1
            }
        )

        st.success(f"Получено объявлений: {len(data)}")

        if len(data) > 0:
            st.json(data[0])

    except Exception as e:
        st.error(str(e))
