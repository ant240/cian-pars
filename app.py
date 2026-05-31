import streamlit as st
import pandas as pd
import cianparser

st.set_page_config(page_title="GRADOV FLATS")
st.title("GRADOV FLATS - Тест импорта")

st.write("✅ pandas и cianparser импортированы")

# Создаём тестовую таблицу
test_df = pd.DataFrame({
    'Название': ['Тестовая квартира'],
    'Цена': [10_000_000],
    'Площадь': [50]
})
st.dataframe(test_df)

st.success("Этап 1 пройден. Теперь можно переходить к этапу 2.")
