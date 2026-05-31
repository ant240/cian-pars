import streamlit as st
import cianparser
import random

st.title("Проверка CianParser через прокси")

with open("proxies.txt") as f:
    proxies = [x.strip() for x in f if x.strip()]

proxy = random.choice(proxies)

st.write("Прокси:")
st.code(proxy)

try:

    parser = cianparser.CianParser(
        location="Москва",
        proxies={
            "http": proxy,
            "https": proxy
        }
    )

    st.success("Парсер создался")

    data = parser.get_flats(
        deal_type="sale",
        rooms=(1,),
        additional_settings={
            "start_page": 1,
            "end_page": 1
        }
    )

    st.write("Количество объектов:")

    st.write(len(data))

    if len(data):
        st.json(data[0])

except Exception as e:
    st.error(str(e))
