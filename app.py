import streamlit as st
import pandas as pd
import cianparser
from datetime import datetime

st.set_page_config(page_title="Аналитика недвижимости", layout="wide")
st.title("🏠 Аналитика недвижимости (Циан)")
st.markdown("---")

if 'data' not in st.session_state:
    st.session_state.data = None
if 'parsing_done' not in st.session_state:
    st.session_state.parsing_done = False

with st.sidebar:
    st.header("⚙️ Настройки")
    city = st.text_input("Город", value="Москва")
    
    start_page = st.number_input("Начальная страница", min_value=1, value=1, step=1)
    end_page = st.number_input("Конечная страница", min_value=1, value=2, step=1,
                               help="Для теста 1-2 страницы")
    
    rooms = st.multiselect("Количество комнат", options=[1,2,3,4,5,6], default=[1])
    
    st.subheader("Фильтр по цене (необязательно)")
    min_price = st.number_input("Мин. цена (₽)", min_value=0, value=0, step=100000, format="%d")
    max_price = st.number_input("Макс. цена (₽)", min_value=0, value=0, step=100000, format="%d")
    
    st.subheader("Фильтр по площади (необязательно)")
    min_area = st.number_input("Мин. площадь (м²)", min_value=0.0, value=0.0, step=5.0, format="%.1f")
    max_area = st.number_input("Макс. площадь (м²)", min_value=0.0, value=0.0, step=5.0, format="%.1f")
    
    parse_button = st.button("🚀 Начать парсинг", type="primary", use_container_width=True)

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
        st.error(f"Ошибка парсинга: {str(e)}")
        return None

if parse_button:
    with st.spinner("Парсинг..."):
        raw = parse_data()
    
    if raw and len(raw) > 0:
        df = pd.DataFrame(raw)
        # Преобразуем цены и площади
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
        if 'total_meters' in df.columns:
            df['total_meters'] = pd.to_numeric(df['total_meters'], errors='coerce')
        
        df = df.dropna(subset=['price', 'total_meters'])
        df = df[(df['price'] > 0) & (df['total_meters'] > 0)]
        
        if len(df) > 0:
            # Создаём колонку цена за м²
            df['price_per_sqm'] = (df['price'] / df['total_meters']).round(2)
            
            # Применяем фильтры, если они заданы
            if min_price > 0:
                df = df[df['price'] >= min_price]
            if max_price > 0:
                df = df[df['price'] <= max_price]
            if min_area > 0:
                df = df[df['total_meters'] >= min_area]
            if max_area > 0:
                df = df[df['total_meters'] <= max_area]
            
            if len(df) > 0:
                st.session_state.data = df
                st.session_state.parsing_done = True
                st.success(f"✅ Загружено {len(df)} объявлений")
            else:
                st.warning("После применения фильтров не осталось объявлений")
        else:
            st.warning("Нет данных с корректной ценой и площадью")
    else:
        st.warning("Не удалось получить данные. ЦИАН может блокировать запросы. Попробуйте позже или уменьшите количество страниц до 1.")

# Отображение результатов
if st.session_state.parsing_done and st.session_state.data is not None:
    df = st.session_state.data
    st.markdown("---")
    st.subheader("📊 Результаты поиска")
    
    # Краткая статистика
    col1, col2, col3 = st.columns(3)
    col1.metric("Всего", len(df))
    if 'price' in df.columns:
        col2.metric("Средняя цена", f"{df['price'].mean():,.0f} ₽")
    if 'price_per_sqm' in df.columns:
        col3.metric("Средняя цена за м²", f"{df['price_per_sqm'].mean():,.0f} ₽")
    
    # Показываем таблицу с существующими колонками
    # Список желаемых колонок
    desired_cols = ['residential_complex', 'rooms', 'total_meters', 'price', 'price_per_sqm', 'floor', 'district', 'underground', 'url']
    available_cols = [col for col in desired_cols if col in df.columns]
    if not available_cols:
        available_cols = df.columns.tolist()  # если нет ни одной из желаемых, показываем все
    
    st.dataframe(df[available_cols], use_container_width=True)
    
    # Кнопка скачивания
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("📥 Скачать CSV", csv, f"real_estate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
else:
    if not st.session_state.parsing_done:
        st.info("👈 Настройте параметры в боковой панели и нажмите «Начать парсинг»")

st.markdown("---")
st.caption("Примечание: ЦИАН может блокировать частые запросы. Для стабильной работы рекомендуются прокси.")
