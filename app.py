import streamlit as st
import pandas as pd
import cianparser
from datetime import datetime

# --- Скрыть элементы Streamlit (меню, футер) ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Настройка страницы (адаптивная) ---
st.set_page_config(
    page_title="Аналитика недвижимости",
    layout="centered",
    initial_sidebar_state="auto"
)
st.title("🏠 Аналитика недвижимости (Циан)")
st.markdown("---")

# --- Инициализация ---
if 'data' not in st.session_state:
    st.session_state.data = None
if 'parsing_done' not in st.session_state:
    st.session_state.parsing_done = False

# --- Боковая панель ---
with st.sidebar:
    st.header("⚙️ Настройки")
    city = st.text_input("Город", value="Москва")
    
    property_type = st.radio(
        "Тип недвижимости",
        ["Квартиры", "Дома и участки", "Коммерческая"]
    )
    
    st.subheader("Параметры")
    start_page = st.number_input("Начальная страница", 1, 1)
    end_page = st.number_input("Конечная страница", 1, 2, help="1-2 для теста")
    
    if property_type == "Квартиры":
        rooms = st.multiselect("Комнаты", [1,2,3,4,5,6], default=[1,2,3])
    else:
        rooms = [1]
    
    st.subheader("Фильтры (до парсинга)")
    min_price = st.number_input("Мин. цена (₽)", 0, 0)
    max_price = st.number_input("Макс. цена (₽)", 0, 0)
    min_area = st.number_input("Мин. площадь (м²)", 0.0, 0.0)
    max_area = st.number_input("Макс. площадь (м²)", 0.0, 0.0)
    
    st.subheader("Спецопции (по описанию)")
    is_penthouse = st.checkbox("🏢 Пентхаус")
    has_terrace = st.checkbox("🌿 Терраса/балкон")
    
    parse_button = st.button("🚀 Начать парсинг", type="primary")

# --- Функция парсинга ---
def parse_property(city, ptype, rooms, start, end):
    try:
        parser = cianparser.CianParser(location=city)
        settings = {"start_page": start, "end_page": end}
        if ptype == "Квартиры":
            return parser.get_flats(deal_type="sale", rooms=tuple(rooms), additional_settings=settings)
        elif ptype == "Дома и участки":
            try:
                return parser.get_suburban(deal_type="sale", additional_settings=settings)
            except:
                return parser.get_flats(deal_type="sale", rooms=(1,), additional_settings=settings)
        else:
            try:
                return parser.get_commercial(deal_type="sale", additional_settings=settings)
            except:
                return parser.get_flats(deal_type="sale", rooms=(1,), additional_settings=settings)
    except Exception as e:
        st.error(f"Ошибка парсинга: {e}")
        return None

def process_data(df, penthouse, terrace):
    if df is None or len(df) == 0:
        return None
    df = pd.DataFrame(df)
    if 'price' not in df.columns or 'total_meters' not in df.columns:
        return None
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['total_meters'] = pd.to_numeric(df['total_meters'], errors='coerce')
    df = df.dropna(subset=['price', 'total_meters'])
    df = df[(df['price'] > 0) & (df['total_meters'] > 0)]
    if len(df) == 0:
        return None
    df['price_per_sqm'] = (df['price'] / df['total_meters']).round(2)
    if 'description' in df.columns:
        if penthouse:
            df = df[df['description'].str.contains('пентхаус|penthouse', case=False, na=False)]
        if terrace:
            df = df[df['description'].str.contains('террас|балкон|лоджи', case=False, na=False)]
    return df

# --- Запуск парсинга ---
if parse_button:
    if property_type == "Квартиры" and not rooms:
        st.error("Выберите комнаты")
    else:
        raw = parse_property(city, property_type, rooms, start_page, end_page)
        if raw and len(raw) > 0:
            processed = process_data(raw, is_penthouse, has_terrace)
            if processed is not None and len(processed) > 0:
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
                    st.success(f"✅ Загружено {len(processed)} объявлений")
                else:
                    st.warning("После фильтров нет записей")
            else:
                st.warning("Нет данных с ценой/площадью или по спецопциям")
        else:
            st.warning("Не удалось получить данные (блокировка или пустой ответ)")

# --- Отображение данных с защитой от пустых слайдеров ---
if st.session_state.parsing_done and st.session_state.data is not None:
    df = st.session_state.data.copy()
    if len(df) == 0:
        st.warning("Нет данных для отображения")
        st.stop()
    
    st.markdown("---")
    st.header("📊 Результаты")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Всего", len(df))
    col2.metric("Средняя цена", f"{df['price'].mean():,.0f} ₽")
    col3.metric("Ср. цена за м²", f"{df['price_per_sqm'].mean():,.0f} ₽")
    col4.metric("Ср. площадь", f"{df['total_meters'].mean():.1f} м²")
    
    st.markdown("---")
    st.subheader("🔍 Уточняющие фильтры")
    
    # --- Слайдеры только если min < max и значения конечны ---
    price_min = df['price'].min()
    price_max = df['price'].max()
    if pd.notna(price_min) and pd.notna(price_max) and price_min < price_max:
        price_range = st.slider("Цена (₽)", float(price_min), float(price_max), (float(price_min), float(price_max)))
        df = df[(df['price'] >= price_range[0]) & (df['price'] <= price_range[1])]
    else:
        st.info("Недостаточно данных для фильтра по цене")
    
    area_min = df['total_meters'].min()
    area_max = df['total_meters'].max()
    if pd.notna(area_min) and pd.notna(area_max) and area_min < area_max:
        area_range = st.slider("Площадь (м²)", float(area_min), float(area_max), (float(area_min), float(area_max)))
        df = df[(df['total_meters'] >= area_range[0]) & (df['total_meters'] <= area_range[1])]
    
    sqm_min = df['price_per_sqm'].min()
    sqm_max = df['price_per_sqm'].max()
    if pd.notna(sqm_min) and pd.notna(sqm_max) and sqm_min < sqm_max:
        sqm_range = st.slider("Цена за м² (₽)", float(sqm_min), float(sqm_max), (float(sqm_min), float(sqm_max)))
        df = df[(df['price_per_sqm'] >= sqm_range[0]) & (df['price_per_sqm'] <= sqm_range[1])]
    
    # Фильтры по району, метро, этажу (с проверками)
    if 'district' in df.columns and not df['district'].isnull().all():
        districts = sorted(df['district'].dropna().unique())
        if districts:
            sel_districts = st.multiselect("Район", districts)
            if sel_districts:
                df = df[df['district'].isin(sel_districts)]
    
    if 'underground' in df.columns and not df['underground'].isnull().all():
        metros = sorted(df['underground'].dropna().unique())
        if metros:
            sel_metros = st.multiselect("Метро", metros)
            if sel_metros:
                df = df[df['underground'].isin(sel_metros)]
    
    if 'floor' in df.columns and not df['floor'].isnull().all():
        floor_min = int(df['floor'].min())
        floor_max = int(df['floor'].max())
        if floor_min < floor_max:
            floor_range = st.slider("Этаж", floor_min, floor_max, (floor_min, floor_max))
            df = df[(df['floor'] >= floor_range[0]) & (df['floor'] <= floor_range[1])]
    
    # Сортировка
    st.subheader("📈 Сортировка")
    sort_col1, sort_col2 = st.columns([3,1])
    with sort_col1:
        sort_by = st.selectbox("Сортировать по", ['price_per_sqm','price','total_meters','rooms'],
                               format_func=lambda x: {'price_per_sqm':'Цена за м²','price':'Цена','total_meters':'Площадь','rooms':'Комнаты'}[x])
    with sort_col2:
        sort_order = st.radio("Порядок", ['По возрастанию','По убыванию'])
    df = df.sort_values(by=sort_by, ascending=(sort_order=='По возрастанию'))
    
    st.info(f"📌 Показано {len(df)} объявлений")
    
    # Отображение таблицы
    cols_to_show = []
    rename = {}
    for col, name in [('residential_complex','ЖК'),('rooms','Комнат'),('total_meters','Площадь (м²)'),
                      ('price','Цена (₽)'),('price_per_sqm','Цена за м² (₽)'),('floor','Этаж'),
                      ('district','Район'),('underground','Метро'),('url','Ссылка')]:
        if col in df.columns:
            cols_to_show.append(col)
            rename[col] = name
    df_display = df[cols_to_show].copy().rename(columns=rename)
    for col in ['Цена (₽)','Цена за м² (₽)']:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "")
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
        st.info("Нажмите «Начать парсинг» в боковой панели. Для теста ставьте конечную страницу = 1-2.")

st.markdown("---")
st.caption("Данные с ЦИАН. При блокировке IP нужны прокси. Пентхаусы/террасы — по описанию.")
