import streamlit as st
import cianparser
import inspect

st.title("Проверка cianparser")

st.write("Версия конструктора:")

st.code(str(inspect.signature(cianparser.CianParser)))

try:

    parser = cianparser.CianParser(
        location="Москва"
    )

    st.success("Парсер создан")

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

    if len(data) > 0:
        st.write(data[0])

except Exception as e:
    st.error(str(e))
