import streamlit as st
import pandas as pd
import cianparser
from datetime import datetime

# --- Настройка страницы ---
st.set_page_config(page_title="Аналитика недвижимости", layout="wide")
st.title("🏠 Аналитика недвижимости (Циан)")
st.markdown("---")

# --- Инициализация состояния сессии ---
if 'data' not in st.session_state:
    st.session_state.data = None
if 'parsing_done' not in st.session_state:
    st.session_state.parsing_done = False

# --- Боковая панель ---
with st.sidebar:
    st.header("⚙️ Настройки поиска")
    city = st.text_input("Город", value="Москва")
    
    # Выбор типа недвижимости
    property_type = st.radio(
        "Тип недвижимости",
        options=["Квартиры", "Дома и участки", "Коммерческая"],
        help="Квартиры — обычный парсинг. Дома/Коммерческая — требуется поддержка библиотеки."
    )
    
    st.subheader("Параметры парсинга")
    start_page = st.number_input("Начальная страница", min_value=1, value=1)
    end_page = st.number_input("Конечная страница", min_value=1, value=2,
                               help="Для теста 1-2. Больше 2 — риск блокировки.")
    
    # Для квартир показываем выбор комнат
    if property_type == "Квартиры":
        rooms = st.multiselect("Количество комнат", options=[1,2,3,4,5,6], default=[1,2,3])
    else:
        rooms = [1]  # заглушка, для других типов не используется
    
    st.subheader("Фильтры (предварительные)")
    min_price = st.number_input("Мин. цена (₽)", min_value=0, value=0)
    max_price = st.number_input("Макс. цена (₽)", min_value=0, value=0, help="0 = без ограничения")
    min_area = st.number_input("Мин. площадь (м²)", min_value=0.0, value=0.0)
    max_area = st.number_input("Макс. площадь (м²)", min_value=0.0, value=0.0, help="0 = без ограничения")
    
    st.subheader("Специальные опции (поиск по описанию)")
    is_penthouse = st.checkbox("🏢 Пентхаус")
    has_terrace = st.checkbox("🌿 Терраса / балкон")
    # можно добавить любые другие опции (например, "студия", "отделка", "вид на город")
    
    parse_button = st.button("🚀 Начать парсинг", type="primary", use_container_width=True)

# --- Функция парсинга (с выбором типа) ---
def parse_property(city, property_type, rooms, start_page, end_page):
    try:
        with st.spinner(f'Парсинг {property_type}, страницы {start_page}-{end_page}...'):
            parser = cianparser.CianParser(location=city)
            additional_settings = {"start_page": start_page, "end_page": end_page}
            
            if property_type == "Квартиры":
                data = parser.get_flats(
                    deal_type="sale",
                    rooms=tuple(rooms),
                    additional_settings=additional_settings
                )
            elif property_type == "Дома и участки":
                # Предположительный метод — уточните в документации cianparser
                # Если метода нет, можно сделать заглушку и потом отфильтровать по описанию
                try:
                    data = parser.get_suburban(
                        deal_type="sale",
                        additional_settings=additional_settings
                    )
                except AttributeError:
                    st.warning("Метод get_suburban не найден. Используется общий поиск (фильтрация по описанию позже).")
                    data = parser.get_flats(deal_type="sale", rooms=(1,), additional_settings=additional_settings)
            else:  # Коммерческая
                try:
                    data = parser.get_commercial(
                        deal_type="sale",
                        additional_settings=additional_settings
                    )
                except AttributeError:
                    st.warning("Метод get_commercial не найден. Используется общий поиск (фильтрация по описанию позже).")
                    data = parser.get_flats(deal_type="sale", rooms=(1,), additional_settings=additional_settings)
            return data
    except Exception as e:
        st.error(f"Ошибка парсинга: {str(e)}")
        return None

# --- Обработка данных (расчёт цены за м², фильтр по описанию) ---
def process_data(df, is_penthouse, has_terrace):
    if df is None or len(df) == 0:
        return None
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    
    # Необходимые колонки
    if 'price' not in df.columns or 'total_meters' not in df.columns:
        return None
    
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['total_meters'] = pd.to_numeric(df['total_meters'], errors='coerce')
    df = df.dropna(subset=['price', 'total_meters'])
    df = df[(df['price'] > 0) & (df['total_meters'] > 0)]
    if len(df) == 0:
        return None
    
    df['price_per_sqm'] = (df['price'] / df['total_meters']).round(2)
    
    # Фильтрация по ключевым словам в описании (если есть колонка description)
    if 'description' in df.columns:
        if is_penthouse:
            df = df[df['description'].str.contains('пентхаус|penthouse', case=False, na=False)]
        if has_terrace:
            df = df[df['description'].str.contains('террас|балкон|лоджи', case=False, na=False)]
    
    # Добавим фиктивную колонку "Тип недвижимости" для отображения
    if 'is_apartment' in df.columns:
        df['property_type_label'] = df['is_apartment'].apply(lambda x: 'Новостройка' if x else 'Вторичка')
    else:
        df['property_type_label'] = 'Не указано'
    
    return df

# --- Запуск парсинга по кнопке ---
if parse_button:
    if property_type == "Квартиры" and not rooms:
        st.error("Выберите хотя бы одно количество комнат!")
    else:
        raw_data = parse_property(city, property_type, rooms, start_page, end_page)
        if raw_data and len(raw_data) > 0:
            processed = process_data(raw_data, is_penthouse, has_terrace)
            if processed is not None and len(processed) > 0:
                # Применяем предварительные фильтры цены и площади
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
                    st.warning("Данные получены, но после фильтров не осталось записей.")
            else:
                st.warning("Данные получены, но не содержат цены/площади или не прошли фильтр по описанию.")
        else:
            st.warning("Не удалось получить данные. Возможна блокировка ЦИАН или неверные параметры.")

# --- Отображение данных и уточняющие фильтры ---
if st.session_state.parsing_done and st.session_state.data is not None:
    df = st.session_state.data.copy()
    
    st.markdown("---")
    st.header("📊 Результаты парсинга")
    
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
    price_min, price_max = int(df['price'].min()), int(df['price'].max())
    price_range = st.slider("Цена (₽)", price_min, price_max, (price_min, price_max))
    df = df[(df['price'] >= price_range[0]) & (df['price'] <= price_range[1])]
    
    # Фильтр по площади
    area_min, area_max = float(df['total_meters'].min()), float(df['total_meters'].max())
    area_range = st.slider("Площадь (м²)", area_min, area_max, (area_min, area_max))
    df = df[(df['total_meters'] >= area_range[0]) & (df['total_meters'] <= area_range[1])]
    
    # Фильтр по цене за м²
    sqm_min, sqm_max = int(df['price_per_sqm'].min()), int(df['price_per_sqm'].max())
    sqm_range = st.slider("Цена за м² (₽)", sqm_min, sqm_max, (sqm_min, sqm_max))
    df = df[(df['price_per_sqm'] >= sqm_range[0]) & (df['price_per_sqm'] <= sqm_range[1])]
    
    # Динамический фильтр по районам (если есть колонка district)
    if 'district' in df.columns and not df['district'].isnull().all():
        districts = sorted(df['district'].dropna().unique())
        if districts:
            selected_districts = st.multiselect("Район (можно несколько)", districts)
            if selected_districts:
                df = df[df['district'].isin(selected_districts)]
    
    # Фильтр по метро
    if 'underground' in df.columns and not df['underground'].isnull().all():
        metros = sorted(df['underground'].dropna().unique())
        if metros:
            selected_metros = st.multiselect("Метро", metros)
            if selected_metros:
                df = df[df['underground'].isin(selected_metros)]
    
    # Фильтр по этажу
    if 'floor' in df.columns and not df['floor'].isnull().all():
        floor_min, floor_max = int(df['floor'].min()), int(df['floor'].max())
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
                'rooms': 'Комнаты'
            }[x]
        )
    with sort_col2:
        sort_order = st.radio("Порядок", options=['По возрастанию', 'По убыванию'])
    
    df = df.sort_values(by=sort_by, ascending=(sort_order == 'По возрастанию'))
    
    st.info(f"📌 Показано {len(df)} объявлений")
    
    # --- Подготовка таблицы для отображения ---
    display_columns = []
    rename_dict = {}
    if 'residential_complex' in df.columns:
        display_columns.append('residential_complex')
        rename_dict['residential_complex'] = 'ЖК'
    if 'rooms' in df.columns:
        display_columns.append('rooms')
        rename_dict['rooms'] = 'Комнат'
    if 'total_meters' in df.columns:
        display_columns.append('total_meters')
        rename_dict['total_meters'] = 'Площадь (м²)'
    if 'price' in df.columns:
        display_columns.append('price')
        rename_dict['price'] = 'Цена (₽)'
    if 'price_per_sqm' in df.columns:
        display_columns.append('price_per_sqm')
        rename_dict['price_per_sqm'] = 'Цена за м² (₽)'
    if 'floor' in df.columns:
        display_columns.append('floor')
        rename_dict['floor'] = 'Этаж'
    if 'district' in df.columns:
        display_columns.append('district')
        rename_dict['district'] = 'Район'
    if 'underground' in df.columns:
        display_columns.append('underground')
        rename_dict['underground'] = 'Метро'
    if 'url' in df.columns:
        display_columns.append('url')
        rename_dict['url'] = 'Ссылка'
    
    df_display = df[display_columns].copy().rename(columns=rename_dict)
    
    # Форматирование чисел
    if 'Цена (₽)' in df_display.columns:
        df_display['Цена (₽)'] = df_display['Цена (₽)'].apply(lambda x: f"{x:,.0f}")
    if 'Цена за м² (₽)' in df_display.columns:
        df_display['Цена за м² (₽)'] = df_display['Цена за м² (₽)'].apply(lambda x: f"{x:,.0f}")
    if 'Площадь (м²)' in df_display.columns:
        df_display['Площадь (м²)'] = df_display['Площадь (м²)'].apply(lambda x: f"{x:.1f}")
    
    st.dataframe(df_display, use_container_width=True, height=500)
    
    # Экспорт
    st.markdown("---")
    st.subheader("💾 Экспорт")
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("📥 Скачать CSV", csv_data,
                       file_name=f"real_estate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                       mime="text/csv")
else:
    if not st.session_state.parsing_done:
        st.info("ℹ️ Нажмите «Начать парсинг» в боковой панели. Для теста ставьте конечную страницу = 1-2.")

st.markdown("---")
st.caption("🔍 Данные собираются с ЦИАН. При блокировке IP потребуются прокси. Пентхаусы/террасы фильтруются по описанию.")
