import streamlit as st
import cianparser
import random

st.set_page_config(page_title="GRADOV FLATS - тест")
st.title("Тест парсера с прокси")

# Загружаем прокси из файла
try:
    with open("proxies.txt", "r") as f:
        proxies = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    st.error("Файл proxies.txt не найден")
    st.stop()

st.write(f"Загружено прокси: {len(proxies)}")

# Выбираем случайный прокси
proxy = random.choice(proxies)
st.code(proxy)

# Пытаемся создать парсер с прокси
try:
    parser = cianparser.CianParser(location="Москва", proxies={"http": proxy, "https": proxy})
    st.success("Парсер создан")
except Exception as e:
    st.error(f"Ошибка создания парсера: {e}")
    st.stop()

# Пытаемся получить данные (1 страница, 1-комнатные)
try:
    flats = parser.get_flats(
        deal_type="sale",
        rooms=(1,),
        additional_settings={"start_page": 1, "end_page": 1}
    )
    st.write(f"Получено объявлений: {len(flats)}")
    if flats:
        st.dataframe(flats[:3])
    else:
        st.warning("Нет данных – возможно, прокси не работает или ЦИАН блокирует")
except Exception as e:
    st.error(f"Ошибка получения данных: {e}")
