import streamlit as st

# Шаг 1: самая первая строка после импорта
st.write("Шаг 1: импорт выполнен")

try:
    st.set_page_config(page_title="GRADOV FLATS")
    st.write("Шаг 2: set_page_config выполнен")
except Exception as e:
    st.write(f"Ошибка в set_page_config: {e}")

try:
    st.title("GRADOV FLATS")
    st.write("Шаг 3: заголовок установлен")
except Exception as e:
    st.write(f"Ошибка при установке заголовка: {e}")

try:
    import time
    time.sleep(0.5)
    st.write("Шаг 4: задержка прошла")
except Exception as e:
    st.write(f"Ошибка в задержке: {e}")

try:
    import pandas as pd
    st.write("Шаг 5: pandas импортирован")
except Exception as e:
    st.write(f"Ошибка импорта pandas: {e}")

try:
    import cianparser
    st.write("Шаг 6: cianparser импортирован")
except Exception as e:
    st.write(f"Ошибка импорта cianparser: {e}")

st.success("Все шаги выполнены успешно! Приложение работает.")
