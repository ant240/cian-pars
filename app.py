import streamlit as st
import pandas as pd
import cianparser
from time import sleep

st.set_page_config(page_title="GRADOV SEARCH - Тест", layout="wide")

st.title("GRADOV SEARCH — Тестовый режим")

# --- Кнопка теста ---
if st.button("🚀 Быстрый тест: однушки на Белорусской"):

    # Индикатор загрузки
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Инициализация парсера
    parser = cianparser.CianParser(location="Москва")
    status_text.text("Создаём парсер...")

    # Быстро ограничиваем выбор: 1-комнатные, 2–5 этажи, Белорусская
    rooms = (1,)
    min_floor, max_floor = 2, 5
    min_price, max_price = 0, 40_000_000
    min_area = 40

    status_text.text("Запрашиваем данные...")
    # --- Ограничиваем парсер по страницам для ускорения ---
    flats_raw = parser.get_flats(
        deal_type="sale",
        rooms=rooms,
        additional_settings={
            "start_page": 1,
            "end_page": 2,  # только 2 страницы для быстрого теста
        }
    )

    status_text.text(f"Найдено объявлений: {len(flats_raw)}")
    progress_bar.progress(20)

    # --- Преобразуем в DataFrame ---
    df = pd.DataFrame(flats_raw)

    # --- Фильтруем по улице, площади, цене, этажу ---
    df_test = df[
        df["street"].str.contains("Белорусская", na=False)
        & (df["total_meters"] >= min_area)
        & (df["price"] <= max_price)
        & (df["floor"] >= min_floor)
        & (df["floor"] <= max_floor)
    ]

    progress_bar.progress(50)
    status_text.text(f"После фильтрации: {len(df_test)} объектов")

    # Ограничим количество для теста
    df_test = df_test.head(30)
    progress_bar.progress(100)

    st.success("✅ Тест выполнен!")
    st.dataframe(df_test)

    # --- Ссылки на объекты ---
    st.markdown("### Ссылки на квартиры")
    for i, row in df_test.iterrows():
        st.markdown(f"- [{row['street']} {row.get('house_number','')}]( {row['url']} ) — {row['total_meters']} м², {row['price']:,} ₽, этаж {row['floor']}")

# --- Кнопка очистки ---
if st.button("🧹 Очистить тестовые поля"):
    st.experimental_rerun()
