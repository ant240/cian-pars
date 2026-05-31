import streamlit as st
import pandas as pd
import cianparser
from datetime import datetime
import time
import random
import os
from typing import List, Optional, Dict, Any

# ======================= НАСТРОЙКИ СТРАНИЦЫ =======================
st.set_page_config(page_title="GRADOV FLATS", layout="wide")

# Скрываем стандартные элементы Streamlit
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Заголовок и подзаголовок
st.markdown("""
    <h1 style='text-align: center; color: #1a1a1a;'>GRADOV FLATS</h1>
    <p style='text-align: center; color: #555; margin-top: -20px;'>Аналитика рынка недвижимости Москвы</p>
    <hr>
""", unsafe_allow_html=True)

# Инициализация состояния
if 'data' not in st.session_state:
    st.session_state.data = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# ======================= ЗАГРУЗКА СПИСКОВ ДЛЯ ФИЛЬТРОВ =======================
# Списки районов и станций метро Москвы (можно расширить или загружать из файла)
MOSCOW_DISTRICTS = [
    "Раменки", "Арбат", "Пресненский", "Тверской", "Хамовники", "Якиманка",
    "Басманный", "Замоскворечье", "Мещанский", "Таганский", "Аэропорт", "Беговой",
    "Бескудниковский", "Войковский", "Головинский", "Дмитровский", "Западное Дегунино",
    "Коптево", "Левобережный", "Молжаниновский", "Савёловский", "Сокол",
    "Тимирязевский", "Ховрино", "Хорошёвский", "Бабушкинский", "Бибирево",
    "Лосиноостровский", "Медведково", "Отрадное", "Ростокино", "Свиблово",
    "Северное Медведково", "Южное Медведково", "Богородское", "Вешняки",
    "Восточное Измайлово", "Гольяново", "Ивановское", "Измайлово",
    "Косино-Ухтомский", "Метрогородок", "Новогиреево", "Новокосино", "Перово",
    "Преображенское", "Северное Измайлово", "Соколиная Гора", "Выхино-Жулебино",
    "Капотня", "Кузьминки", "Люблино", "Марьино", "Некрасовка", "Нижегородский",
    "Печатники", "Рязанский", "Текстильщики", "Южнопортовый", "Даниловский",
    "Донской", "Зюзино", "Коньково", "Котловка", "Ломоносовский", "Нагорный",
    "Обручевский", "Северное Бутово", "Тёплый Стан", "Черёмушки", "Южное Бутово",
    "Ясенево", "Академический", "Гагаринский", "Проспект Вернадского", "Тропарёво-Никулино",
    "Бирюлёво Восточное", "Бирюлёво Западное", "Братеево", "Зябликово",
    "Москворечье-Сабурово", "Нагатино-Садовники", "Нагатинский Затон",
    "Орехово-Борисово Северное", "Орехово-Борисово Южное", "Царицыно",
    "Чертаново Северное", "Чертаново Центральное", "Чертаново Южное",
    "Внуково", "Дорогомилово", "Крылатское", "Кунцево", "Можайский",
    "Ново-Переделкино", "Очаково-Матвеевское", "Солнцево", "Филёвский Парк",
    "Фили-Давыдково", "Куркино", "Строгино", "Митино", "Покровское-Стрешнево",
    "Рублёво-Архангельское", "Северное Тушино", "Хорошёво-Мнёвники", "Щукино", "Южное Тушино"
]

MOSCOW_METRO = [
    "Раменки", "Ломоносовский проспект", "Минская", "Славянский бульвар", "Кунцевская",
    "Парк Победы", "Киевская", "Смоленская", "Арбатская", "Александровский сад",
    "Боровицкая", "Полянка", "Серпуховская", "Тульская", "Нагатинская", "Коломенская",
    "Каширская", "Кантемировская", "Царицыно", "Орехово", "Домодедовская",
    "Красногвардейская", "Алма-Атинская", "Петровско-Разумовская", "Тимирязевская",
    "Дмитровская", "Савёловская", "Менделеевская", "Цветной бульвар", "Чеховская",
    "Охотный Ряд", "Театральная", "Площадь Революции", "Кузнецкий мост", "Лубянка",
    "Чистые пруды", "Красные Ворота", "Комсомольская", "Красносельская", "Сокольники",
    "Преображенская площадь", "Черкизовская", "Щёлковская", "Первомайская", "Измайловская",
    "Партизанская", "Семёновская", "Электрозаводская", "Бауманская", "Курская",
    "Таганская", "Павелецкая", "Добрынинская", "Октябрьская"
]

# ======================= ФУНКЦИЯ ЗАГРУЗКИ ПРОКСИ ИЗ ФАЙЛА (скрыто) =======================
def load_proxies_from_file(filename: str = "proxies.txt") -> Optional[List[str]]:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    return None

# ======================= ФУНКЦИЯ ЗАГРУЗКИ ДАННЫХ С ЦИАН =======================
def load_data(city: str, rooms: List[int], start_page: int, end_page: int, proxy_pool: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
    """Загружает данные с ЦИАН, используя пул прокси (если есть) для ротации."""
    all_data = []
    for page in range(start_page, end_page + 1):
        current_proxy = random.choice(proxy_pool) if proxy_pool else None
        try:
            if current_proxy:
                parser = cianparser.CianParser(
                    location=city,
                    proxies={"http": current_proxy, "https": current_proxy}
                )
            else:
                parser = cianparser.CianParser(location=city)
            
            # Небольшая задержка, чтобы имитировать человека
            time.sleep(random.uniform(1.0, 2.5))
            
            data = parser.get_flats(
                deal_type="sale",
                rooms=tuple(rooms),
                additional_settings={"start_page": page, "end_page": page}
            )
            if data:
                all_data.extend(data)
        except Exception as e:
            # Если ошибка, пробуем следующий прокси или продолжаем без него
            continue
    
    if not all_data:
        return None
    
    df = pd.DataFrame(all_data)
    # Преобразуем числовые колонки
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
    if 'total_meters' in df.columns:
        df['total_meters'] = pd.to_numeric(df['total_meters'], errors='coerce')
    if 'floor' in df.columns:
        df['floor'] = pd.to_numeric(df['floor'], errors='coerce')
    if 'build_year' in df.columns:
        df['build_year'] = pd.to_numeric(df['build_year'], errors='coerce')
    
    # Удаляем некорректные строки
    df = df.dropna(subset=['price', 'total_meters'])
    df = df[(df['price'] > 0) & (df['total_meters'] > 0)]
    
    if len(df) == 0:
        return None
    
    df['price_per_sqm'] = (df['price'] / df['total_meters']).round(2)
    
    # Если есть колонка is_apartment, создаём читаемый тип
    if 'is_apartment' in df.columns:
        df['property_type'] = df['is_apartment'].apply(lambda x: 'Новостройка' if x else 'Вторичка')
    else:
        df['property_type'] = 'Не указано'
    
    return df

# ======================= БОКОВАЯ ПАНЕЛЬ (фильтры для загрузки) =======================
with st.sidebar:
    st.markdown("### 🔍 Параметры поиска")
    city = st.text_input("Город", value="Москва")
    rooms = st.multiselect("Количество комнат", options=[1,2,3,4,5,6], default=[1,2,3])
    start_page = st.number_input("Начальная страница", min_value=1, value=1, step=1)
    end_page = st.number_input("Конечная страница", min_value=1, value=5, step=1,
                               help="Чем больше страниц, тем полнее данные, но дольше загрузка.")
    
    load_button = st.button("🚀 Загрузить актуальные данные", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 🎯 Уточняющие фильтры (после загрузки)")
    st.caption("Эти фильтры применяются к уже загруженным данным.")

# ======================= ЗАГРУЗКА ДАННЫХ ПО КНОПКЕ =======================
if load_button:
    if not rooms:
        st.error("Выберите хотя бы одно количество комнат.")
    else:
        with st.spinner("Загрузка данных... Это может занять несколько секунд."):
            # Пытаемся загрузить прокси из файла (скрыто от пользователя)
            proxy_pool = load_proxies_from_file()
            df = load_data(city, rooms, start_page, end_page, proxy_pool)
            if df is not None and len(df) > 0:
                st.session_state.data = df
                st.session_state.data_loaded = True
                st.success(f"✅ Загружено {len(df)} объявлений. Теперь можно применять фильтры.")
            else:
                st.error("Не удалось загрузить данные. Попробуйте изменить параметры или повторить позже.")
                st.session_state.data_loaded = False

# ======================= ЕСЛИ ДАННЫЕ ЗАГРУЖЕНЫ, ПОКАЗЫВАЕМ ФИЛЬТРЫ И РЕЗУЛЬТАТЫ =======================
if st.session_state.data_loaded and st.session_state.data is not None:
    df = st.session_state.data.copy()
    
    # --- БЛОК ФИЛЬТРОВ (MULTISELECT, СЛАЙДЕРЫ) ---
    st.markdown("---")
    st.subheader("📌 Фильтрация данных")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Фильтр по цене
        price_min = int(df['price'].min())
        price_max = int(df['price'].max())
        price_range = st.slider("Цена (₽)", price_min, price_max, (price_min, price_max))
        df = df[(df['price'] >= price_range[0]) & (df['price'] <= price_range[1])]
        
        # Фильтр по площади
        area_min = float(df['total_meters'].min())
        area_max = float(df['total_meters'].max())
        area_range = st.slider("Площадь (м²)", area_min, area_max, (area_min, area_max))
        df = df[(df['total_meters'] >= area_range[0]) & (df['total_meters'] <= area_range[1])]
        
        # Фильтр по цене за м²
        sqm_min = int(df['price_per_sqm'].min())
        sqm_max = int(df['price_per_sqm'].max())
        sqm_range = st.slider("Цена за м² (₽)", sqm_min, sqm_max, (sqm_min, sqm_max))
        df = df[(df['price_per_sqm'] >= sqm_range[0]) & (df['price_per_sqm'] <= sqm_range[1])]
    
    with col2:
        # Фильтр по этажу (если есть данные)
        if 'floor' in df.columns and not df['floor'].isnull().all():
            floor_min = int(df['floor'].min())
            floor_max = int(df['floor'].max())
            if floor_min < floor_max:
                floor_range = st.slider("Этаж", floor_min, floor_max, (floor_min, floor_max))
                df = df[(df['floor'] >= floor_range[0]) & (df['floor'] <= floor_range[1])]
        
        # Фильтр по году постройки/сдачи (если есть)
        if 'build_year' in df.columns and not df['build_year'].isnull().all():
            year_min = int(df['build_year'].min())
            year_max = int(df['build_year'].max())
            if year_min < year_max:
                year_range = st.slider("Год постройки/сдачи", year_min, year_max, (year_min, year_max))
                df = df[(df['build_year'] >= year_range[0]) & (df['build_year'] <= year_range[1])]
        
        # Фильтр по типу недвижимости
        prop_types = sorted(df['property_type'].unique())
        if prop_types:
            selected_types = st.multiselect("Тип недвижимости", prop_types, default=prop_types)
            if selected_types:
                df = df[df['property_type'].isin(selected_types)]
    
    # Фильтры по локации (районы, метро)
    st.markdown("#### 🗺️ Локация")
    loc_col1, loc_col2 = st.columns(2)
    with loc_col1:
        if 'district' in df.columns and not df['district'].isnull().all():
            available_districts = sorted(df['district'].dropna().unique())
            selected_districts = st.multiselect("Районы (можно несколько)", available_districts)
            if selected_districts:
                df = df[df['district'].isin(selected_districts)]
        else:
            st.info("Данные о районах недоступны в текущей выборке.")
    
    with loc_col2:
        if 'underground' in df.columns and not df['underground'].isnull().all():
            available_metros = sorted(df['underground'].dropna().unique())
            selected_metros = st.multiselect("Станции метро (можно несколько)", available_metros)
            if selected_metros:
                df = df[df['underground'].isin(selected_metros)]
        else:
            st.info("Данные о метро недоступны в текущей выборке.")
    
    # Дополнительный фильтр: время до метро (если есть колонка 'time_to_metro')
    if 'time_to_metro' in df.columns and not df['time_to_metro'].isnull().all():
        time_max = int(df['time_to_metro'].max())
        time_min = int(df['time_to_metro'].min())
        time_range = st.slider("Время до метро (мин)", time_min, time_max, (time_min, time_max))
        df = df[(df['time_to_metro'] >= time_range[0]) & (df['time_to_metro'] <= time_range[1])]
    
    # Сортировка
    st.markdown("#### 📊 Сортировка результатов")
    sort_col1, sort_col2 = st.columns([3,1])
    with sort_col1:
        sort_by = st.selectbox("Сортировать по", 
                               options=['price_per_sqm', 'price', 'total_meters', 'rooms'],
                               format_func=lambda x: {
                                   'price_per_sqm': 'Цена за м²',
                                   'price': 'Общая цена',
                                   'total_meters': 'Площадь',
                                   'rooms': 'Количество комнат'
                               }[x])
    with sort_col2:
        sort_order = st.radio("Порядок", options=['По возрастанию', 'По убыванию'])
    ascending = (sort_order == 'По возрастанию')
    df = df.sort_values(by=sort_by, ascending=ascending)
    
    # Отображение статистики и таблицы
    st.markdown("---")
    st.subheader("📈 Результаты поиска")
    
    # Краткая статистика
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Всего объявлений", len(df))
    col2.metric("Средняя цена", f"{df['price'].mean():,.0f} ₽")
    col3.metric("Средняя цена за м²", f"{df['price_per_sqm'].mean():,.0f} ₽")
    col4.metric("Средняя площадь", f"{df['total_meters'].mean():.1f} м²")
    
    # Таблица с данными
    # Выбираем основные колонки для отображения
    display_cols = []
    rename_map = {}
    for col, name in [('residential_complex','ЖК'), ('rooms','Комнат'), ('total_meters','Площадь, м²'),
                      ('price','Цена, ₽'), ('price_per_sqm','Цена за м², ₽'), ('floor','Этаж'),
                      ('build_year','Год'), ('property_type','Тип'), ('district','Район'),
                      ('underground','Метро'), ('url','Ссылка')]:
        if col in df.columns:
            display_cols.append(col)
            rename_map[col] = name
    
    if display_cols:
        df_display = df[display_cols].copy().rename(columns=rename_map)
        # Форматирование чисел
        if 'Цена, ₽' in df_display.columns:
            df_display['Цена, ₽'] = df_display['Цена, ₽'].apply(lambda x: f"{x:,.0f}")
        if 'Цена за м², ₽' in df_display.columns:
            df_display['Цена за м², ₽'] = df_display['Цена за м², ₽'].apply(lambda x: f"{x:,.0f}")
        if 'Площадь, м²' in df_display.columns:
            df_display['Площадь, м²'] = df_display['Площадь, м²'].apply(lambda x: f"{x:.1f}")
        
        st.dataframe(df_display, use_container_width=True, height=500)
    else:
        st.info("Нет данных для отображения после применения фильтров.")
    
    # ======================= ОЦЕНКА СВОЕЙ КВАРТИРЫ =======================
    st.markdown("---")
    st.subheader("🏡 Оценка вашей квартиры")
    st.caption("Введите характеристики вашей квартиры, и мы сравним их с загруженными объявлениями.")
    
    val_col1, val_col2, val_col3 = st.columns(3)
    with val_col1:
        own_rooms = st.number_input("Количество комнат", min_value=1, max_value=6, value=2, step=1)
    with val_col2:
        own_area = st.number_input("Площадь (м²)", min_value=10.0, max_value=300.0, value=50.0, step=1.0)
    with val_col3:
        own_floor = st.number_input("Этаж", min_value=1, max_value=50, value=5, step=1)
    
    own_district = st.selectbox("Район", options=["Любой"] + sorted(df['district'].dropna().unique()) if 'district' in df.columns else ["Любой"])
    
    if st.button("Оценить стоимость", type="primary"):
        # Фильтруем похожие объявления
        similar = df.copy()
        if own_district != "Любой" and 'district' in similar.columns:
            similar = similar[similar['district'] == own_district]
        similar = similar[similar['rooms'] == own_rooms]
        # Допуск по площади ±20%
        similar = similar[(similar['total_meters'] >= own_area * 0.8) & (similar['total_meters'] <= own_area * 1.2)]
        # Допуск по этажу ±3
        if 'floor' in similar.columns:
            similar = similar[(similar['floor'] >= own_floor - 3) & (similar['floor'] <= own_floor + 3)]
        
        if len(similar) == 0:
            st.warning("Не найдено похожих объявлений для оценки.")
        else:
            avg_price_sqm = similar['price_per_sqm'].mean()
            estimated_price = avg_price_sqm * own_area
            st.success(f"**Средняя цена за м²** в похожих объектах: **{avg_price_sqm:,.0f} ₽**")
            st.success(f"**Примерная стоимость вашей квартиры:** **{estimated_price:,.0f} ₽**")
            st.caption(f"Найдено {len(similar)} объявлений-аналогов.")
    
    # Экспорт данных
    st.markdown("---")
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("📥 Скачать отфильтрованные данные (CSV)", csv,
                       file_name=f"gradov_flats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
else:
    if not st.session_state.data_loaded:
        st.info("👈 Настройте параметры в боковой панели и нажмите «Загрузить актуальные данные».")

# Подвал
st.markdown("---")
st.caption("GRADOV INVEST — профессиональная аналитика рынка недвижимости.")
