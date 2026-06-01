import streamlit as st
import pandas as pd

from data_loader import load_data

st.set_page_config(
    page_title="GRADOV DEBUG",
    layout="wide"
)

st.title("GRADOV DEBUG")

st.info("Диагностика структуры данных")

if st.button("Загрузить данные"):

    with st.spinner("Загрузка..."):

        df = load_data()

    st.success(f"Загружено объектов: {len(df)}")

    st.subheader("Колонки DataFrame")

    st.write(df.columns.tolist())

    st.subheader("Типы колонок")

    st.write(df.dtypes)

    st.subheader("Первые 20 строк")

    st.dataframe(
        df.head(20),
        use_container_width=True
    )

    st.subheader("Размер DataFrame")

    st.write(df.shape)

    st.subheader("Количество заполненных значений")

    st.write(df.count())

    st.subheader("Уникальные значения по важным полям")

    important_columns = [
        "metro",
        "district",
        "street",
        "residential_complex",
        "location"
    ]

    for col in important_columns:

        if col in df.columns:

            st.markdown(f"### {col}")

            values = (
                df[col]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            st.write(values[:100])

    st.subheader("Полный список колонок")

    for col in df.columns:
        st.write(col)
