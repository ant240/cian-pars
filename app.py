import streamlit as st
import pandas as pd
import cianparser
from datetime import datetime

st.set_page_config(page_title="Аналитика недвижимости", layout="wide")
st.title("🏠 Аналитика недвижимости")
st.markdown("---")

if 'data' not in st.session_state:
    st.session_state.data = None
if 'parsing_done' not in st.session_state:
    st.session_state.parsing_done = False

with st.sidebar:
    st.header("⚙️ Настройки")
    city = st.text_input("Город", "Москва")
    start_page = st.number_input("Страница от", 1, 1)
    end_page = st.number_input("Страница до", 1, 2, help="1-2 для теста")
    rooms = st.multiselect("Комнаты", [1,2,3,4,5,6], [1])
    min_price = st.number_input("Мин. цена", 0, 0)
    max_price = st.number_input("Макс. цена", 0, 0)
    min_area = st.number_input("Мин. площадь", 0.0, 0.0)
    max_area = st.number_input("Макс. площадь", 0.0, 0.0)
    parse_button = st.button("🚀 Начать парсинг")

def parse_data():
    try:
        parser = cianparser.CianParser(location=city)
        data = parser.get_flats(
            deal_type="sale",
            rooms=tuple(rooms),
            additional_settings={"start_page": start_page, "end_page": end_page}
        )
        return data
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        return None

if parse_button:
    raw = parse_data()
    if raw and len(raw) > 0:
        df = pd.DataFrame(raw)
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['total_meters'] = pd.to_numeric(df['total_meters'], errors='coerce')
        df = df.dropna(subset=['price', 'total_meters'])
        if len(df) > 0:
            df['price_per_sqm'] = df['price'] / df['total_meters']
            if min_price > 0:
                df = df[df['price'] >= min_price]
            if max_price > 0:
                df = df[df['price'] <= max_price]
            if min_area > 0:
                df = df[df['total_meters'] >= min_area]
            if max_area > 0:
                df = df[df['total_meters'] <= max_area]
            st.session_state.data = df
            st.session_state.parsing_done = True
            st.success(f"Загружено {len(df)} объявлений")
        else:
            st.warning("Нет данных после фильтрации")
    else:
        st.warning("Не удалось получить данные (возможно, блокировка ЦИАН)")

if st.session_state.parsing_done and st.session_state.data is not None:
    df = st.session_state.data
    st.dataframe(df[['residential_complex','rooms','total_meters','price','price_per_sqm']], use_container_width=True)
    csv = df.to_csv(index=False)
    st.download_button("📥 Скачать CSV", csv, f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
else:
    if not st.session_state.parsing_done:
        st.info("Нажмите «Начать парсинг» в боковой панели")

st.markdown("---")
st.caption("Парсинг ЦИАН. Если долго нет данных — сайт блокирует IP, нужны прокси.")
