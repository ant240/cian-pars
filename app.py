import streamlit as st
import pandas as pd
import cianparser
import time

st.set_page_config(page_title="GRADOV SEARCH TEST", layout="wide")


# ---------------------------
# КЭШ ПОСЛЕДНЕГО УСПЕШНОГО РЕЗУЛЬТАТА
# ---------------------------
if "last_df" not in st.session_state:
    st.session_state.last_df = None


# ---------------------------
# ФУНКЦИЯ ПАРСИНГА (СТАБИЛЬНАЯ ВЕРСИЯ)
# ---------------------------
def safe_parse():

    parser = cianparser.CianParser(location="Москва")

    progress = st.progress(0)
    status = st.empty()
    counter = st.empty()

    all_flats = []

    TOTAL_PAGES = 3  # ВАЖНО: это то, что раньше у тебя РАБОТАЛО

    for page in range(1, TOTAL_PAGES + 1):

        try:
            status.info(f"📡 Загрузка страницы {page}/{TOTAL_PAGES}")

            flats = parser.get_flats(
                deal_type="sale",
                rooms=(1,),
                additional_settings={
                    "start_page": page,
                    "end_page": page
                }
            )

            all_flats.extend(flats)

            counter.success(f"Найдено: {len(all_flats)} объектов")

            progress.progress(int(page / TOTAL_PAGES * 60))

        except Exception as e:
            st.warning(f"Ошибка страницы {page}: {e}")

        time.sleep(0.2)

    status.info("Фильтрация (Москва / метро / цена / площадь)")

    df = pd.DataFrame(all_flats)

    # ---------------------------
    # ЖЁСТКАЯ СТАБИЛИЗАЦИЯ (ВАЖНО)
    # ---------------------------

    # Москва
    if "location" in df.columns:
        df = df[df["location"].astype(str).str.contains("Москва", na=False)]

    # метро Белорусская (если есть)
    metro_cols = [c for c in df.columns if "metro" in c.lower()]
    if metro_cols:
        df = df[df[metro_cols[0]].astype(str).str.contains("Белорус", na=False)]

    # цена
    if "price" in df.columns:
        df = df[(df["price"] >= 30_000_000) & (df["price"] <= 40_000_000)]

    # площадь
    area_col = next((c for c in df.columns if "area" in c.lower()), None)
    if area_col:
        df = df[df[area_col] >= 40]

    progress.progress(85)

    status.info("Финальная очистка")

    # этажность
    if "floor" in df.columns:
        df = df[(df["floor"] >= 2) & (df["floor"] <= 5)]

    progress.progress(100)

    status.success(f"Готово: {len(df)} объектов")

    # СОХРАНЯЕМ РЕЗУЛЬТАТ (КЛЮЧЕВО)
    st.session_state.last_df = df

    return df


# ---------------------------
# UI
# ---------------------------
st.title("GRADOV SEARCH — TEST MODE")

tab1, tab2 = st.tabs(["🧪 ТЕСТ", "📊 РЕЗУЛЬТАТ"])

with tab1:

    st.subheader("Быстрый тест (стабильная версия)")

    st.write("""
    Запрос:
    - 1-комнатные
    - Москва
    - метро Белорусская
    - 30–40 млн ₽
    - от 40 м²
    - этаж 2–5
    """)

    if st.button("🚀 Запустить тест", use_container_width=True):
        df = safe_parse()
        st.success("Тест завершён")

with tab2:

    st.subheader("Последний результат")

    if st.session_state.last_df is not None:
        st.dataframe(st.session_state.last_df, use_container_width=True)
    else:
        st.info("Пока нет данных. Запусти тест.")
