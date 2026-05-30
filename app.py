import streamlit as st
import pandas as pd
import cianparser
from datetime import datetime
import os

# Настройка страницы
st.set_page_config(
    page_title=" Аналитика недвижимости ",
    page_icon="🏠",
    layout="wide"
)

st.title(" Аналитика недвижимости ")
st.markdown("---")

# Инициализация session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'parsing_done' not in st.session_state:
    st.session_state.parsing_done = False

# Боковая панель с настройками
with st.sidebar:
    st.header("⚙️ Настройки поиска")

    city = st.text_input("Город", value="Москва")

    st.subheader("Параметры поиска")
    start_page = st.number_input("Начальная страница", min_value=1, value=1)
    end_page = st.number_input("Конечная страница", min_value=1, value=3,
                                help="Максимум 54 страницы")

    rooms = st.multiselect(
        "Количество комнат",
        options=[1, 2, 3, 4, 5, 6],
        default=[1, 2, 3]
    )

    st.subheader("Дополнительные фильтры")
    min_price = st.number_input("Минимальная цена (₽)", min_value=0, value=0)
    max_price = st.number_input("Максимальная цена (₽)", min_value=0, value=0,
                                help="0 = без ограничения")

    min_area = st.number_input("Минимальная площадь (м²)", min_value=0.0, value=0.0)
    max_area = st.number_input("Максимальная площадь (м²)", min_value=0.0, value=0.0,
                               help="0 = без ограничения")

    parse_button = st.button("🚀 Начать парсинг", type="primary", use_container_width=True)

# Функция парсинга
def parse_newbuildings(city, rooms, start_page, end_page):
    try:
        with st.spinner(f'Парсинг данных со страниц {start_page}-{end_page}...'):
            parser = cianparser.CianParser(location=city)
            # ВАЖНО: добавляем параметр pages, он ограничивает количество страниц
            data = parser.get_flats(
                deal_type="sale",
                rooms=tuple(rooms),
                pages=end_page,          # вместо additional_settings
                start_page=start_page
            )
            return data
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        return None
        
# Функция обработки данных
def process_data(df):
    """Обработка и расчет стоимости за кв.м"""
    if df is None or len(df) == 0:
        return None

    # Преобразуем в DataFrame если это не DataFrame
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    # Удаляем дубликаты
    df = df.drop_duplicates()

    # Рассчитываем стоимость за кв.м
    if 'price' in df.columns and 'total_meters' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['total_meters'] = pd.to_numeric(df['total_meters'], errors='coerce')

        # Расчет цены за кв.м
        df['price_per_sqm'] = (df['price'] / df['total_meters']).round(2)

        # Удаляем строки с некорректными данными
        df = df.dropna(subset=['price', 'total_meters', 'price_per_sqm'])
        df = df[df['price'] > 0]
        df = df[df['total_meters'] > 0]

    return df

# Обработка нажатия кнопки парсинга
if parse_button:
    if not rooms:
        st.error("Выберите хотя бы одно количество комнат!")
    elif end_page > 54:
        st.error("Максимальное количество страниц - 54")
    else:
        data = parse_newbuildings(city, rooms, start_page, end_page)

        if data is not None and len(data) > 0:
            processed_data = process_data(data)

            if processed_data is not None and len(processed_data) > 0:
                st.session_state.data = processed_data
                st.session_state.parsing_done = True
                st.success(f"✅ Успешно загружено {len(processed_data)} объявлений!")
            else:
                st.warning("Данные получены, но после обработки не осталось валидных записей.")
        else:
            st.warning("Не удалось получить данные. Попробуйте изменить параметры поиска.")

# Отображение данных
if st.session_state.parsing_done and st.session_state.data is not None:
    df = st.session_state.data.copy()

    st.markdown("---")
    st.header("📊 Результаты парсинга")

    # Статистика
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего объявлений", len(df))
    with col2:
        avg_price = df['price'].mean()
        st.metric("Средняя цена", f"{avg_price:,.0f} ₽")
    with col3:
        avg_price_sqm = df['price_per_sqm'].mean()
        st.metric("Средняя цена за м²", f"{avg_price_sqm:,.0f} ₽")
    with col4:
        avg_area = df['total_meters'].mean()
        st.metric("Средняя площадь", f"{avg_area:.1f} м²")

    st.markdown("---")

    # Фильтры
    st.subheader("🔍 Фильтрация данных")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        if min_price > 0:
            df = df[df['price'] >= min_price]
        if max_price > 0:
            df = df[df['price'] <= max_price]

        price_range = st.slider(
            "Диапазон цен (₽)",
            min_value=int(df['price'].min()),
            max_value=int(df['price'].max()),
            value=(int(df['price'].min()), int(df['price'].max()))
        )
        df = df[(df['price'] >= price_range[0]) & (df['price'] <= price_range[1])]

    with filter_col2:
        if min_area > 0:
            df = df[df['total_meters'] >= min_area]
        if max_area > 0:
            df = df[df['total_meters'] <= max_area]

        area_range = st.slider(
            "Площадь (м²)",
            min_value=float(df['total_meters'].min()),
            max_value=float(df['total_meters'].max()),
            value=(float(df['total_meters'].min()), float(df['total_meters'].max()))
        )
        df = df[(df['total_meters'] >= area_range[0]) & (df['total_meters'] <= area_range[1])]

    with filter_col3:
        price_sqm_range = st.slider(
            "Цена за м² (₽)",
            min_value=int(df['price_per_sqm'].min()),
            max_value=int(df['price_per_sqm'].max()),
            value=(int(df['price_per_sqm'].min()), int(df['price_per_sqm'].max()))
        )
        df = df[(df['price_per_sqm'] >= price_sqm_range[0]) & (df['price_per_sqm'] <= price_sqm_range[1])]

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
        sort_order = st.radio(
            "Порядок",
            options=['По возрастанию', 'По убыванию']
        )

    # Применяем сортировку
    ascending = sort_order == 'По возрастанию'
    df = df.sort_values(by=sort_by, ascending=ascending)

    st.info(f"Показано {len(df)} объявлений после применения фильтров")

    # Форматирование колонок для отображения
    display_columns = {
        'residential_complex': 'ЖК',
        'rooms': 'Комнат',
        'total_meters': 'Площадь (м²)',
        'price': 'Цена (₽)',
        'price_per_sqm': 'Цена за м² (₽)',
        'floor': 'Этаж',
        'district': 'Район',
        'underground': 'Метро',
        'url': 'Ссылка'
    }

    # Выбираем только существующие колонки
    available_columns = [col for col in display_columns.keys() if col in df.columns]
    df_display = df[available_columns].copy()

    # Переименовываем колонки
    df_display.columns = [display_columns[col] for col in available_columns]

    # Форматируем числовые значения
    if 'Цена (₽)' in df_display.columns:
        df_display['Цена (₽)'] = df_display['Цена (₽)'].apply(lambda x: f"{x:,.0f}")
    if 'Цена за м² (₽)' in df_display.columns:
        df_display['Цена за м² (₽)'] = df_display['Цена за м² (₽)'].apply(lambda x: f"{x:,.0f}")
    if 'Площадь (м²)' in df_display.columns:
        df_display['Площадь (м²)'] = df_display['Площадь (м²)'].apply(lambda x: f"{x:.1f}")

    # Отображаем таблицу
    st.dataframe(
        df_display,
        use_container_width=True,
        height=600
    )

    # Экспорт данных
    st.markdown("---")
    st.subheader("💾 Экспорт данных")

    export_col1, export_col2 = st.columns(2)

    with export_col1:
        # CSV экспорт
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Скачать CSV",
            data=csv,
            file_name=f"cian_newbuildings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with export_col2:
        # Excel экспорт
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Новостройки')
        excel_data = output.getvalue()

        st.download_button(
            label="📥 Скачать Excel",
            data=excel_data,
            file_name=f"cian_newbuildings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# Информация в футере
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Приложение для парсинга квартир в новостройках с Циан</p>
    <p>Использует библиотеку cianparser</p>
</div>
""", unsafe_allow_html=True)
