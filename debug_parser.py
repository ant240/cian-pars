import streamlit as st
import cianparser
import inspect

st.title("Диагностика CianParser")

st.subheader("Сигнатура get_flats")

st.code(
    str(inspect.signature(cianparser.CianParser.get_flats))
)

st.subheader("Файл библиотеки")

st.code(
    cianparser.__file__
)
