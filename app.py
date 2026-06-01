import streamlit as st
import pandas as pd

from data_loader import load_data, load_card_details
from analytics import evaluate_apartment, plot_price_history

st.set_page_config(
    page_title="GRADOV SEARCH",
    layout="wide"
)

st.title("GRADOV SEARCH")

tabs = st.tabs([
    "🧪 ТЕСТ",
    "🏠 ПОКУПКА",
    "💰 ПРОДАЖА"
])

# =====================================================
# ТЕСТ
# =====================================================

with tabs[0]:

    st.header("Тест системы")

    st.info(
        """
        Готовый тест:

        • 1-комнатная квартира

        • метро Белорусская

        • площадь от 40 м²

        • цена до 40 млн ₽

        • этаж 2-5
        """
    )

    if st.button("🚀 Запустить тест"):

        progress = st.progress(0)
        status = st.empty()

        status.info("Загрузка данных...")
        progress.progress(20)

        df = load_data()

        progress.progress(60)

        if len(df) == 0:
            st.error("Нет данных")
            st.stop()

        status.info("Фильтрация...")

        result = df.copy()

        if "rooms_count" in result.columns:
            result = result[result["rooms_count"] == 1]

        if "metro" in result.columns:
            result = result[
                result["metro"]
                .astype(str)
                .str.contains("Белорус", case=False, na=False)
            ]

        if "total_meters" in result.columns:
            result = result[result["total_meters"] >= 40]

        if "price" in result.columns:
            result = result[result["price"] <= 40000000]

        if "floor" in result.columns:
            result = result[result["floor"].between(2, 5)]

        progress.progress(100)

        st.success(f"Найдено объектов: {len(result)}")

        st.dataframe(
            result,
            width="stretch"
        )

# =====================================================
# ПОКУПКА
# =====================================================

with tabs[1]:

    st.header("Поиск квартир")

    col1, col2, col3 = st.columns(3)

    with col1:

        metro_filter = st.text_input(
            "Метро"
        )

        district_filter = st.text_input(
            "Район"
        )

        district_okrug = st.text_input(
            "Округ"
        )

        residential_complex = st.text_input(
            "ЖК"
        )

        street_filter = st.text_input(
            "Улица"
        )

        house_filter = st.text_input(
            "Дом"
        )

    with col2:

        rooms = st.selectbox(
            "Комнаты",
            [0, 1, 2, 3, 4, 5]
        )

        min_price = st.number_input(
            "Цена от",
            value=0
        )

        max_price = st.number_input(
            "Цена до",
            value=500000000
        )

        min_area = st.number_input(
            "Площадь от",
            value=0
        )

        max_area = st.number_input(
            "Площадь до",
            value=500
        )

    with col3:

        min_floor = st.number_input(
            "Этаж от",
            value=1
        )

        max_floor = st.number_input(
            "Этаж до",
            value=99
        )

        year_built = st.text_input(
            "Год постройки"
        )

        house_type = st.text_input(
            "Тип дома"
        )

        finish_type = st.text_input(
            "Отделка"
        )

        ceiling_height = st.text_input(
            "Высота потолков"
        )

    if st.button("🔍 Найти квартиры"):

        progress = st.progress(0)
        status = st.empty()

        status.info("Получение данных...")
        progress.progress(20)

        df = load_data()

        progress.progress(50)

        if len(df) == 0:
            st.error("Нет данных")
            st.stop()

        result = df.copy()

        if rooms > 0 and "rooms_count" in result.columns:
            result = result[
                result["rooms_count"] == rooms
            ]

        if "price" in result.columns:
            result = result[
                result["price"].between(
                    min_price,
                    max_price
                )
            ]

        if "total_meters" in result.columns:
            result = result[
                result["total_meters"].between(
                    min_area,
                    max_area
                )
            ]

        if "floor" in result.columns:
            result = result[
                result["floor"].between(
                    min_floor,
                    max_floor
                )
            ]

        if metro_filter and "metro" in result.columns:
            result = result[
                result["metro"]
                .astype(str)
                .str.contains(
                    metro_filter,
                    case=False,
                    na=False
                )
            ]

        if district_filter and "district" in result.columns:
            result = result[
                result["district"]
                .astype(str)
                .str.contains(
                    district_filter,
                    case=False,
                    na=False
                )
            ]

        if street_filter and "street" in result.columns:
            result = result[
                result["street"]
                .astype(str)
                .str.contains(
                    street_filter,
                    case=False,
                    na=False
                )
            ]

        if residential_complex and "residential_complex" in result.columns:
            result = result[
                result["residential_complex"]
                .astype(str)
                .str.contains(
                    residential_complex,
                    case=False,
                    na=False
                )
            ]

        progress.progress(100)

        st.success(
            f"Найдено объектов: {len(result)}"
        )

        st.dataframe(
            result,
            width="stretch"
        )

        if len(result) > 0:

            first_url = result.iloc[0]["url"]

            with st.expander(
                "Дополнительные данные первого объекта"
            ):

                details = load_card_details(
                    first_url
                )

                st.json(details)

# =====================================================
# ПРОДАЖА
# =====================================================

with tabs[2]:

    st.header("Оценка квартиры")

    col1, col2 = st.columns(2)

    with col1:

        address = st.text_input(
            "Адрес",
            key="sale_address"
        )

        metro = st.text_input(
            "Метро",
            key="sale_metro"
        )

        rooms = st.selectbox(
            "Комнаты",
            [1, 2, 3, 4, 5],
            key="sale_rooms"
        )

        area = st.number_input(
            "Площадь",
            value=50.0,
            key="sale_area"
        )

        floor = st.number_input(
            "Этаж",
            value=5,
            key="sale_floor"
        )

    with col2:

        floors_count = st.number_input(
            "Этажность дома",
            value=10,
            key="sale_floors_count"
        )

        year_built = st.text_input(
            "Год постройки",
            key="sale_year_built"
        )

        house_type = st.text_input(
            "Тип дома",
            key="sale_house_type"
        )

        finish_type = st.text_input(
            "Отделка",
            key="sale_finish_type"
        )

        ceiling_height = st.number_input(
            "Высота потолков",
            value=2.7,
            key="sale_ceiling_height"
        )

    if st.button(
        "📈 Оценить квартиру",
        key="sale_evaluate"
    ):

        card = {
            "price": 15000000,
            "floor": floor,
            "total_meters": area
        }

        score, rec_price = evaluate_apartment(card)

        st.metric(
            "Скоринг",
            score
        )

        st.metric(
            "Рыночная цена",
            f"{int(rec_price):,} ₽"
        )

        st.metric(
            "Быстрая продажа",
            f"{int(rec_price * 0.95):,} ₽"
        )

        st.metric(
            "Максимальная цена",
            f"{int(rec_price * 1.10):,} ₽"
        )

        chart = plot_price_history(card)

        st.altair_chart(
            chart,
            width="stretch"
        )
