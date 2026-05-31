import streamlit as st
import cianparser
import random

st.set_page_config(page_title="Debug CianParser")

st.title("Проверка CianParser через прокси")

# Загружаем прокси из файла
try:
    with open("proxies.txt", "r", encoding="utf-8") as f:
        proxies = [x.strip() for x in f if x.strip()]
except FileNotFoundError:
    st.error("Файл proxies.txt не найден")
    st.stop()

st.write(f"Прокси загружено: {len(proxies)}")

# Выбираем случайный прокси
proxy = random.choice(proxies)
st.code(proxy)

# Попробуем создать парсер
try:
    parser = cianparser.CianParser(location="Москва", proxies={"http": proxy, "https": proxy})
    st.success("Парсер создался")
except Exception as e:
    st.error(f"Ошибка при создании парсера: {e}")
    st.stop()

# Попробуем загрузить первые объекты
try:
    flats = parser.get_flats(deal_type="sale", rooms=(1, 2, 3))
    st.write(f"Количество объектов: {len(flats)}")
except Exception as e:
    st.error(f"Ошибка при get_flats: {e}")
