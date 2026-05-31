import streamlit as st
import inspect
import cianparser

st.title("Диагностика CianParser")

try:
    st.write("Версия библиотеки загружена")

    signature = inspect.signature(cianparser.CianParser)

    st.code(str(signature))

except Exception as e:
    st.error(str(e))
