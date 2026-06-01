import streamlit as st
import pandas as pd
import cianparser
import time


def run_demo_test():

    progress = st.progress(0)
    status = st.empty()
    counter = st.empty()

    parser = cianparser.CianParser(location="Москва")

    all_flats = []

    TOTAL_PAGES = 3

    for page in range(1, TOTAL_PAGES + 1):

        status.info(
            f"Получение объявлений. Страница {page}/{TOTAL_PAGES}"
        )

        try:

            flats = parser.get_flats(
                deal_type="sale",
                rooms=(1,),
                additional_settings={
                    "start_page": page,
                    "end_page": page
                }
            )

            all_flats.extend(flats)

            counter.success(
                f"Найдено объявлений: {len(all_flats)}"
            )

        except Exception as e:
            st.warning(f"Ошибка страницы {page}: {e}")

        progress.progress(int(page / TOTAL_PAGES * 70))

    status.info("Фильтрация данных")

    df = pd.DataFrame(all_flats)

    # Только Москва
    if "location" in df.columns:
        df = df[
            df["location"]
            .astype(str)
            .str.contains("Москва", case=False, na=False)
        ]

    # Белорусская
    metro_cols = [
        c for c in df.columns
        if "metro" in c.lower()
    ]

    if metro_cols:

        metro_col = metro_cols[0]

        df = df[
            df[metro_col]
            .astype(str)
            .str.contains(
                "Белорус",
                case=False,
                na=False
            )
        ]

    # Цена
    if "price" in df.columns:

        df = df[
            (df["price"] >= 30_000_000)
            &
            (df["price"] <= 40_000_000)
        ]

    # Площадь
    area_col = None

    for c in df.columns:
        if "area" in c.lower():
            area_col = c
            break

    if area_col:

        df = df[
            (df[area_col] >= 40)
        ]

    progress.progress(90)

    status.info("Подготовка результата")

    if "floor" in df.columns:

        df = df[
            (df["floor"] >= 2)
            &
            (df["floor"] <= 5)
        ]

    progress.progress(100)

    status.success(
        f"Готово. Найдено {len(df)} квартир"
    )

    return df
