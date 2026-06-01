import streamlit as st
import pandas as pd
from data_loader import load_data, load_card_details
from analytics import evaluate_apartment, plot_price_history

st.set_page_config(
    page_title="GRADOV SEARCH",
    layout="wide"
)

st.title("GRADOV SEARCH")
tabs = st.tabs(["🧪 ТЕСТ", "🏠 Покупка", "💰 Продажа"])

# -----------------------
# ТЕСТ
# -----------------------
with tabs[0]:
    st.header("Быстрый тест — 1-комнатные, метро Белорусская, Москва")
    
    if st.button("🚀 Выполнить тестовый поиск"):
        progress = st.progress(0)
        status = st.empty()
        
        status.info("Подготовка...")
        progress.progress(10)
        
        df = load_data()  # кэшированная загрузка
        progress.progress(50)
        status.info("Фильтрация по критериям...")
        
        df_test = df[
            (df["rooms_count"] == 1) &
            (df["location"] == "Москва") &
            (df["metro"].str.contains("Белорус", na=False)) &
            (df["total_meters"] >= 40) &
            (df["price"] <= 40000000) &
            (df["floor"].between(2,5))
        ]
        progress.progress(80)
        status.info(f"Формирование таблицы: {len(df_test)} объектов найдено")
        
        st.dataframe(df_test, use_container_width=True)
        progress.progress(100)
        status.success("Тест завершён!")

    if st.button("🗑 Очистить результаты теста"):
        st.session_state.clear()

# -----------------------
# ПОКУПКА
# -----------------------
with tabs[1]:
    st.header("Поиск квартир для покупки")
    
    st.info("Выберите фильтры и нажмите 'Найти'")
    
    df = load_data()
    
    metro = st.multiselect("Метро", sorted(df["metro"].dropna().unique()))
    district = st.multiselect("Районы", sorted(df["district"].dropna().unique()))
    rooms = st.selectbox("Количество комнат", [1,2,3,4,5])
    min_price, max_price = st.slider("Цена, ₽", 0, 500_000_000, (0, 50_000_000), step=100_000)
    min_area, max_area = st.slider("Площадь, м²", 10, 500, (30,100))
    floors = st.slider("Этаж", 1, 50, (1, 20))
    
    if st.button("🔍 Найти"):
        filtered = df[
            (df["rooms_count"]==rooms) &
            (df["price"].between(min_price,max_price)) &
            (df["total_meters"].between(min_area,max_area)) &
            (df["floor"].between(floors[0], floors[1]))
        ]
        if metro:
            filtered = filtered[filtered["metro"].isin(metro)]
        if district:
            filtered = filtered[filtered["district"].isin(district)]
        
        st.success(f"Найдено объектов: {len(filtered)}")
        st.dataframe(filtered, use_container_width=True)
        
        # Получаем детали карточки для первого объекта
        if len(filtered)>0:
            url = filtered.iloc[0]["url"]
            details = load_card_details(url)
            st.json(details)

# -----------------------
# ПРОДАЖА
# -----------------------
with tabs[2]:
    st.header("Оценка квартиры для продажи")
    
    url_input = st.text_input("Вставьте URL квартиры для оценки")
    
    if st.button("📈 Получить оценку"):
        if url_input:
            card = load_card_details(url_input)
            score, recommended_price = evaluate_apartment(card)
            st.metric("Скоринг объекта", score)
            st.metric("Рекомендованная цена ₽", recommended_price)
            st.json(card)
            st.altair_chart(plot_price_history(card), use_container_width=True)
        else:
            st.warning("Введите корректный URL")
