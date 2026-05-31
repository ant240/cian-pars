import streamlit as st

st.set_page_config(page_title="GRADOV FLATS")
st.title("GRADOV FLATS")
st.write("Приложение работает!")

if st.button("Проверка"):
    st.success("Всё отлично, кнопка нажимается.")
