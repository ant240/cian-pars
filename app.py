import streamlit as st
import pandas as pd
import cianparser
from datetime import datetime

# --- Настройка страницы ---
st.set_page_config(page_title="Аналитика недвижимости", layout="wide")
st.title("🏠 Аналитика недвижимости (Циан + Авито)")
st.markdown("---")

# --- Инициализация состояния сессии ---
if 'data' not in st.session_state:
    st.session_state.data = None
if 'parsing_done' not in st.session_state:
    st.session_state.parsing_done = False

# --- Боковая панель с настройками парсинга ---
with st.sidebar:
    st.header("⚙️ Настройки поиска")
    city = st.text_input("Город", value="Москва")
    
    st.subheader("Параметры парсинга")
    start_page = st.number_input("Начальная страница", min_value=1, value=1)
    end_page = st.number_input("Конечная страница", min_value=1, value=2, 
                               help="Для теста ставьте 1-2. Больше 2 — могут заблокировать.")
    rooms = st.multiselect("Количество комнат", options=[1,2,3,4,5,6], default=[1,2,3])
    
    st.subheader("Фильтры (предварительные)")
    min_price = st.number_input("Мин. цена (₽)", min_value=0, value=0)
    max_price = st.number_input("Макс. цена (₽)", min_value=0, value=0, help="0 = без ограничения")
    min_area = st.number_input("Мин. площадь (м²)", min_value=0.0, value=0.0)
    max_area = st.number_input("Макс. площадь (м²)", min_value=0.0, value=0.0, help="0 = без ограничения")
    
    parse_button = st.button("🚀 Начать парсинг", type="primary", use_container_width=True)

# --- Функция парсинга ---
def parse_newbuildings(city, rooms, start_page, end_page):
    try:
        with st.spinner(f'Парсинг страниц {start_page}-{end_page}... Это может занять 10-30 секунд.'):
            parser = cianparser.CianParser(location=city)
            additional_settings = {
                "start_page": start_page,
                "end_page": end_page
            }
            data = parser.get_flats(
                deal_type="sale",
                rooms=tuple(rooms),
                additional_settings=additional_settings
            )
            return data
    except Exception as e:
        st.error(f"Ошибка при парсинге: {str(e)}")
        return None

# --- Обработка данных (расчёт цены за м², очистка) ---
def process_data(df):
    if df is None or len(df) == 0:
        return None
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    
    # Проверяем, что нужные колонки есть
    if 'price' not in df.columns or 'total_meters' not in df.columns:
        return None
    
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['total_meters'] = pd.to_numeric(df['total_meters'], errors='coerce')
    
    # Удаляем строки с некорректными значениями
    df = df.dropna(subset=['price', 'total_meters'])
    df = df[(df['price'] > 0) & (df['total_meters'] > 0)]
    
    if len(df) == 0:
        return None
    
    df['price_per_sqm'] = (df['price'] / df['total_meters']).round(2)
    return df

# --- Обработка кнопки парсинга ---
if parse_button:
    if not rooms:
        st.error("Выберите хотя бы одно количество комнат!")
    else:
        raw_data = parse_newbuildings(city, rooms, start_page, end_page)
        if raw_data is not None and len(raw_data) > 0:
            processed = process_data(raw_data)
            if processed is not None and len(processed) > 0:
                # Применяем предварительные фильтры из боковой панели
                if min_price > 0:
                    processed = processed[processed['price'] >= min_price]
                if max_price > 0:
                    processed = processed[processed['price'] <= max_price]
                if min_area > 0:
                    processed = processed[processed['total_meters'] >= min_area]
                if max_area > 0:
                    processed = processed[processed['total_meters'] <= max_area]
                
                if len(processed) > 0:
                    st.session_state.data = processed
                    st.session_state.parsing_done = True
                    st.success(f"✅ Загружено {len(processed)} объявлений!")
                else:
                    st.warning("Данные получены, но после предварительных фильтров не осталось записей.")
            else:
                st.warning("Данные получены, но не содержат цен или площади.")
        else:
            st.warning("Не удалось получить данные. Причины: блокировка ЦИАН, неверные параметры или временная недоступность.")

# --- Отображение результатов и фильтрация ---
if st.session_state.parsing_done and st.session_state.data is not None:
    df = st.session_state.data.copy()
    
    st.markdown("---")
    st.header("📊 Результаты парсинга")
    
    # Краткая статистика
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего объявлений", len(df))
    with col2:
        st.metric("Средняя цена", f"{df['price'].mean():,.0f} ₽")
    with col3:
        st.metric("Средняя цена за м²", f"{df['price_per_sqm'].mean():,.0f} ₽")
    with col4:
        st.metric("Средняя площадь", f"{df['total_meters'].mean():.1f} м²")
    
    st.markdown("---")
    st.subheader("🔍 Уточняющие фильтры (после парсинга)")
    
    # Фильтр по цене
    price_min_global = int(df['price'].min())
    price_max_global = int(df['price'].max())
    price_range = st.slider("Цена (₽)", price_min_global, price_max_global, (price_min_global, price_max_global))
    df = df[(df['price'] >= price_range[0]) & (df['price'] <= price_range[1])]
    
    # Фильтр по площади
    area_min_global = float(df['total_meters'].min())
    area_max_global = float(df['total_meters'].max())
    area_range = st.slider("Площадь (м²)", area_min_global, area_max_global, (area_min_global, area_max_global))
    df = df[(df['total_meters'] >= area_range[0]) & (df['total_meters'] <= area_range[1])]
    
    # Фильтр по цене за м²
    price_sqm_min = int(df['price_per_sqm'].min())
    price_sqm_max = int(df['price_per_sqm'].max())
    price_sqm_range = st.slider("Цена за м² (₽)", price_sqm_min, price_sqm_max, (price_sqm_min, price_sqm_max))
    df = df[(df['price_per_sqm'] >= price_sqm_range[0]) & (df['price_per_sqm'] <= price_sqm_range[1])]
    
    # Фильтр по району (если есть колонка)
    if 'district' in df.columns and not df['district'].isnull().all():
        districts = sorted(df['district'].dropna().unique())
        if len(districts) > 0:
            selected_districts = st.multiselect("Район / округ (можно несколько)", districts)
            if selected_districts:
                df = df[df['district'].isin(selected_districts)]
    
    # Фильтр по метро
    if 'underground' in df.columns and not df['underground'].isnull().all():
        metros = sorted(df['underground'].dropna().unique())
        if len(metros) > 0:
            selected_metros = st.multiselect("Ближайшее метро", metros)
            if selected_metros:
                df = df[df['underground'].isin(selected_metros)]
    
    # Фильтр по этажу
    if 'floor' in df.columns and not df['floor'].isnull().all():
        floor_min = int(df['floor'].min())
        floor_max = int(df['floor'].max())
        if floor_min != floor_max:
            floor_range = st.slider("Этаж", floor_min, floor_max, (floor_min, floor_max))
            df = df[(df['floor'] >= floor_range[0]) & (df['floor'] <= floor_range[1])]
    
    # Сортировка
    st.subheader("📈 Сортировка")
    sort_col1, sort_col2 = st.columns([3, 1])
    with sort_col1:
        sort_by = st.selectbox(
            "Сортировать по",
            options=['price_per_sqm', 'price', 'total_meters', 'rooms'],
            format_func=lambda x: {
                'price_per_sqm': 'Цена за м²',
                'price': 'Общая цена',
                'total_meters': 'Площадь',
                'rooms': 'Количество комнат'
            }[x]
        )
    with sort_col2:
        sort_order = st.radio("Порядок", options=['По возрастанию', 'По убыванию'])
    
    ascending = (sort_order == 'По возрастанию')
    df = df.sort_values(by=sort_by, ascending=ascending)
    
    st.info(f"📌 Показано {len(df)} объявлений после всех фильтров")
    
    # --- Подготовка таблицы для отображения ---
    display_cols = []
    rename_map = {}
    if 'residential_complex' in df.columns:
        display_cols.append('residential_complex')
        rename_map['residential_complex'] = 'ЖК'
    if 'rooms' in df.columns:
        display_cols.append('rooms')
        rename_map['rooms'] = 'Комнат'
    if 'total_meters' in df.columns:
        display_cols.append('total_meters')
        rename_map['total_meters'] = 'Площадь (м²)'
    if 'price' in df.columns:
        display_cols.append('price')
        rename_map['price'] = 'Цена (₽)'
    if 'price_per_sqm' in df.columns:
        display_cols.append('price_per_sqm')
        rename_map['price_per_sqm'] = 'Цена за м² (₽)'
    if 'floor' in df.columns:
        display_cols.append('floor')
        rename_map['floor'] = 'Этаж'
    if 'district' in df.columns:
        display_cols.append('district')
        rename_map['district'] = 'Район'
    if 'underground' in df.columns:
        display_cols.append('underground')
        rename_map['underground'] = 'Метро'
    if 'url' in df.columns:
        display_cols.append('url')
        rename_map['url'] = 'Ссылка'
    
    df_display = df[display_cols].copy()
    df_display = df_display.rename(columns=rename_map)
    
    # Форматирование чисел
    if 'Цена (₽)' in df_display.columns:
        df_display['Цена (₽)'] = df_display['Цена (₽)'].apply(lambda x: f"{x:,.0f}")
    if 'Цена за м² (₽)' in df_display.columns:
        df_display['Цена за м² (₽)'] = df_display['Цена за м² (₽)'].apply(lambda x: f"{x:,.0f}")
    if 'Площадь (м²)' in df_display.columns:
        df_display['Площадь (м²)'] = df_display['Площадь (м²)'].apply(lambda x: f"{x:.1f}")
    
    st.dataframe(df_display, use_container_width=True, height=500)
    
    # --- Экспорт данных ---
    st.markdown("---")
    st.subheader("💾 Экспорт")
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Скачать CSV",
        data=csv_data,
        file_name=f"real_estate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
else:
    if not st.session_state.parsing_done:
        st.info("ℹ️ Нажмите «Начать парсинг» в боковой панели. Рекомендуем начальную страницу = 1, конечную = 1-2.")

st.markdown("---")
st.caption("🔍 Данные собираются с ЦИАН. При долгом ожидании или отсутствии результатов — возможно, сайт временно блокирует IP. Для стабильной работы нужны прокси.")
