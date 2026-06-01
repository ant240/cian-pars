import streamlit as st
from cianparser import CianParser
import pandas as pd
import json
import inspect

st.set_page_config(
    page_title="GRADOV SEARCH",
    layout="wide"
)

st.title("GRADOV SEARCH")
st.subheader("Диагностика структуры данных CIAN")

# ==========================
# ПРОКСИ
# ==========================

PROXIES = []

try:
    with open("proxies.txt", "r", encoding="utf-8") as f:
        PROXIES = [x.strip() for x in f.readlines() if x.strip()]
except:
    pass

st.write("Прокси загружено:", len(PROXIES))

# ==========================
# ИНФОРМАЦИЯ О БИБЛИОТЕКЕ
# ==========================

st.markdown("### Конструктор")

st.code(str(inspect.signature(CianParser)))

parser = CianParser(
    location="Аэропорт",
    proxies=PROXIES
)

st.success("Парсер успешно создан")

st.markdown("### Метод get_flats")

st.code(str(inspect.signature(parser.get_flats)))

# ==========================
# ЗАГРУЗКА 1 СТРАНИЦЫ
# ==========================

if st.button("Получить тестовые данные"):

    try:

        with st.spinner("Загружаем только 1 страницу..."):

            data = parser.get_flats(
                deal_type="sale",
                rooms=(1,),
                additional_settings={
                    "start_page": 1,
                    "end_page": 1
                }
            )

        st.success(f"Получено объектов: {len(data)}")

        if not data:
            st.error("Объекты не найдены")
            st.stop()

        first = data[0]

        st.markdown("---")
        st.subheader("Первый объект целиком")

        st.json(first)

        st.markdown("---")
        st.subheader("Все доступные поля")

        keys = sorted(list(first.keys()))

        st.write(keys)

        st.markdown("---")
        st.subheader("Таблица полей")

        fields_df = pd.DataFrame({
            "Поле": keys,
            "Значение": [str(first.get(k)) for k in keys]
        })

        st.dataframe(
            fields_df,
            use_container_width=True
        )

        st.markdown("---")
        st.subheader("Все объекты")

        df = pd.DataFrame(data)

        st.write("Колонки:")

        st.write(df.columns.tolist())

        st.dataframe(
            df,
            use_container_width=True
        )

    except Exception as e:

        st.error(str(e))
