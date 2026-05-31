import streamlit as st
import requests
import random
import os
from bs4 import BeautifulSoup

st.set_page_config(page_title="GRADOV FLATS - Тест прямого парсинга")
st.title("GRADOV FLATS - Прямой запрос к ЦИАН")

def load_proxies():
    if os.path.exists("proxies.txt"):
        with open("proxies.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    return None

proxies = load_proxies()
if not proxies:
    st.error("Файл proxies.txt не найден!")
    st.stop()

# Берём случайный прокси
proxy = random.choice(proxies)
st.info(f"Используется прокси: {proxy[:80]}...")

# Преобразуем строку прокси в формат для requests
# Строка вида http://user:pass@host:port
try:
    proxy_dict = {"http": proxy, "https": proxy}
except:
    st.error("Неверный формат прокси. Должен начинаться с http://")
    st.stop()

# Целевой URL страницы поиска (однушки в Москве)
url = "https://cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=1&region=1&room1=1"

# Заголовки, имитирующие реальный браузер
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

try:
    with st.spinner("Отправка запроса к ЦИАН..."):
        response = requests.get(url, headers=headers, proxies=proxy_dict, timeout=15)
    
    st.write(f"**HTTP статус:** {response.status_code}")
    
    if response.status_code == 200:
        st.success("✅ Запрос успешен! Анализируем HTML...")
        # Показываем первые 500 символов для диагностики
        st.text_area("Первые 500 символов ответа:", response.text[:500], height=200)
        
        # Попробуем найти первые ссылки на объявления
        soup = BeautifulSoup(response.text, 'html.parser')
        # Ищем ссылки на объявления (обычно class _93444fe79c)
        links = soup.find_all('a', href=True)
        flat_links = [a['href'] for a in links if '/sale/flat/' in a['href']]
        st.write(f"**Найдено ссылок на объявления:** {len(set(flat_links))}")
        if flat_links:
            st.success("Парсинг работает! Можно собирать детали.")
        else:
            st.warning("Ссылки на объявления не найдены — возможно, изменилась разметка.")
    else:
        st.error(f"Ошибка HTTP {response.status_code}. Возможно, прокси не работает или ЦИАН блокирует.")
        
except Exception as e:
    st.error(f"Исключение: {e}")        return proxies
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def load_all_data(city: str, rooms: tuple) -> Optional[pd.DataFrame]:
    proxy_pool = load_proxies_from_file()
    all_data = []
    page = 1
    max_pages = 100
    progress_bar = st.progress(0)
    status_text = st.empty()
    for i in range(page, max_pages + 1):
        status_text.info(f"Обработка страницы {i}...")
        current_proxy = random.choice(proxy_pool) if proxy_pool else None
        try:
            if current_proxy:
                parser = cianparser.CianParser(
                    location=city,
                    proxies={"http": current_proxy, "https": current_proxy}
                )
            else:
                parser = cianparser.CianParser(location=city)
            time.sleep(random.uniform(0.8, 1.5))
            rooms_tuple = rooms if rooms else (0,1,2,3,4,5,6)
            data = parser.get_flats(
                deal_type="sale",
                rooms=rooms_tuple,
                additional_settings={"start_page": i, "end_page": i}
            )
            if data and len(data) > 0:
                all_data.extend(data)
                progress_bar.progress(min(1.0, i / 70))
            else:
                status_text.info("✅ Все страницы обработаны")
                break
        except Exception as e:
            st.warning(f"Ошибка на странице {i}: {str(e)[:100]}")
            continue
        finally:
            progress_bar.progress(min(1.0, i / 70))
    progress_bar.empty()
    status_text.empty()
    if not all_data:
        return None
    df = pd.DataFrame(all_data)
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
    if 'total_meters' in df.columns:
        df['total_meters'] = pd.to_numeric(df['total_meters'], errors='coerce')
    if 'floor' in df.columns:
        df['floor'] = pd.to_numeric(df['floor'], errors='coerce')
    if 'build_year' in df.columns:
        df['build_year'] = pd.to_numeric(df['build_year'], errors='coerce')
    df = df.dropna(subset=['price', 'total_meters'])
    df = df[(df['price'] > 0) & (df['total_meters'] > 0)]
    if len(df) == 0:
        return None
    df['price_per_sqm'] = (df['price'] / df['total_meters']).round(2)
    if 'is_apartment' in df.columns:
        df['property_type'] = df['is_apartment'].apply(lambda x: 'Новостройка' if x else 'Вторичка')
    else:
        df['property_type'] = 'Не указано'
    if 'residential_complex' in df.columns:
        df['residential_complex'] = df['residential_complex'].fillna('Не указан')
    return df

def filter_data(df, filters):
    df_filtered = df.copy()
    if filters['price_range']:
        df_filtered = df_filtered[(df_filtered['price'] >= filters['price_range'][0]) & (df_filtered['price'] <= filters['price_range'][1])]
    if filters['area_range']:
        df_filtered = df_filtered[(df_filtered['total_meters'] >= filters['area_range'][0]) & (df_filtered['total_meters'] <= filters['area_range'][1])]
    if filters['sqm_range']:
        df_filtered = df_filtered[(df_filtered['price_per_sqm'] >= filters['sqm_range'][0]) & (df_filtered['price_per_sqm'] <= filters['sqm_range'][1])]
    if filters['floor_range']:
        df_filtered = df_filtered[(df_filtered['floor'] >= filters['floor_range'][0]) & (df_filtered['floor'] <= filters['floor_range'][1])]
    if filters['year_range']:
        df_filtered = df_filtered[(df_filtered['build_year'] >= filters['year_range'][0]) & (df_filtered['build_year'] <= filters['year_range'][1])]
    if filters['property_types']:
        df_filtered = df_filtered[df_filtered['property_type'].isin(filters['property_types'])]
    if filters['districts']:
        df_filtered = df_filtered[df_filtered['district'].isin(filters['districts'])]
    if filters['metros']:
        df_filtered = df_filtered[df_filtered['underground'].isin(filters['metros'])]
    return df_filtered

def display_results(df):
    if df.empty:
        st.warning("Нет объявлений, соответствующих выбранным фильтрам.")
        return
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Всего", len(df))
    col2.metric("Средняя цена", f"{df['price'].mean():,.0f} ₽")
    col3.metric("Ср. цена за м²", f"{df['price_per_sqm'].mean():,.0f} ₽")
    col4.metric("Ср. площадь", f"{df['total_meters'].mean():.1f} м²")
    display_cols, rename_map = [], {}
    for col, name in [('residential_complex','ЖК'), ('rooms','Комнат'), ('total_meters','Площадь, м²'),
                      ('price','Цена, ₽'), ('price_per_sqm','Цена за м², ₽'), ('floor','Этаж'),
                      ('build_year','Год'), ('property_type','Тип'), ('district','Район'),
                      ('underground','Метро'), ('author','Автор'), ('phone','📞 Телефон'), ('url','Ссылка')]:
        if col in df.columns:
            display_cols.append(col)
            rename_map[col] = name
    df_display = df[display_cols].copy().rename(columns=rename_map)
    if 'Цена, ₽' in df_display.columns:
        df_display['Цена, ₽'] = df_display['Цена, ₽'].apply(lambda x: f"{x:,.0f}")
    if 'Цена за м², ₽' in df_display.columns:
        df_display['Цена за м², ₽'] = df_display['Цена за м², ₽'].apply(lambda x: f"{x:,.0f}")
    if 'Площадь, м²' in df_display.columns:
        df_display['Площадь, м²'] = df_display['Площадь, м²'].apply(lambda x: f"{x:.1f}")
    st.dataframe(df_display, use_container_width=True, height=400)
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("📥 Скачать CSV", csv_data,
                       file_name=f"gradov_flats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

def valuation_calculator(df):
    if df is None or len(df) == 0:
        st.warning("Нет данных")
        return
    st.markdown("---")
    st.subheader("🏡 Оценка вашей квартиры")
    col1, col2, col3 = st.columns(3)
    with col1:
        own_rooms = st.number_input("Комнат", 0, 6, 2, 1, help="0 — студия")
    with col2:
        own_area = st.number_input("Площадь (м²)", 10.0, 300.0, 50.0, 1.0)
    with col3:
        own_floor = st.number_input("Этаж", 1, 50, 5, 1)
    districts = ["Любой"] + sorted(df['district'].dropna().unique().tolist()) if 'district' in df.columns else ["Любой"]
    own_district = st.selectbox("Район", districts)
    if st.button("Анализировать", type="primary"):
        similar = df.copy()
        if own_district != "Любой" and 'district' in similar.columns:
            similar = similar[similar['district'] == own_district]
        similar = similar[similar['rooms'] == own_rooms]
        similar = similar[(similar['total_meters'] >= own_area * 0.8) & (similar['total_meters'] <= own_area * 1.2)]
        if 'floor' in similar.columns:
            similar = similar[(similar['floor'] >= own_floor - 3) & (similar['floor'] <= own_floor + 3)]
        if len(similar) == 0:
            st.warning("Не найдено похожих объявлений.")
            return
        price_min, price_max, price_median = similar['price'].min(), similar['price'].max(), similar['price'].median()
        price_sqm_min, price_sqm_median, price_sqm_max = similar['price_per_sqm'].min(), similar['price_per_sqm'].median(), similar['price_per_sqm'].max()
        st.subheader("📊 Ценовой коридор")
        st.write(f"Найдено **{len(similar)}** аналогов.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Нижняя граница", f"{price_sqm_min:,.0f} ₽/м²", delta="Быстрая продажа")
        c2.metric("Средняя", f"{price_sqm_median:,.0f} ₽/м²", delta="Рынок")
        c3.metric("Верхняя граница", f"{price_sqm_max:,.0f} ₽/м²", delta="Долгий поиск")
        recommended = (price_min + price_median) / 2
        st.success(f"💰 Рекомендованная цена для старта: **{recommended:,.0f} ₽**")
        st.subheader("🔍 Похожие объявления")
        similar_display = similar[['price', 'total_meters', 'price_per_sqm', 'floor', 'district', 'underground']].copy()
        similar_display.columns = ['Цена, ₽', 'Площадь, м²', 'Цена за м², ₽', 'Этаж', 'Район', 'Метро']
        st.dataframe(similar_display, use_container_width=True)

tab1, tab2 = st.tabs(["📊 Анализ рынка (найти)", "🏡 Оценка квартиры (продать)"])

with tab1:
    with st.sidebar:
        st.markdown("### 🔍 Параметры поиска")
        city = st.text_input("Город", value="Москва")
        rooms = st.multiselect("Количество комнат (пусто = все, включая студии)", 
                               options=[0,1,2,3,4,5,6], 
                               format_func=lambda x: "Студия" if x==0 else f"{x}", 
                               default=[])
        load_button = st.button("🚀 Загрузить данные", type="primary", use_container_width=True)
        st.markdown("---")
        st.markdown("### 🎯 Расширенные фильтры")
        st.caption("Появятся после загрузки")
    if load_button:
        if not city:
            st.error("Укажите город.")
        else:
            with st.spinner("Загрузка данных... Первый раз может занять 1–2 минуты."):
                rooms_tuple = tuple(rooms)
                df = load_all_data(city, rooms_tuple)
                if df is not None and len(df) > 0:
                    st.session_state.data = df
                    st.session_state.data_loaded = True
                    st.success(f"✅ Загружено {len(df)} объявлений.")
                else:
                    st.error("Не удалось загрузить данные. Возможно, проблема с прокси или ЦИАН блокирует запросы.")
                    st.session_state.data_loaded = False
    if st.session_state.data_loaded and st.session_state.data is not None:
        df = st.session_state.data
        filters = {'price_range': None, 'area_range': None, 'sqm_range': None,
                   'floor_range': None, 'year_range': None,
                   'property_types': [], 'districts': [], 'metros': []}
        st.markdown("---")
        st.subheader("📌 Фильтры")
        col1, col2 = st.columns(2)
        with col1:
            filters['price_range'] = st.slider("Цена (₽)", int(df['price'].min()), int(df['price'].max()), (int(df['price'].min()), int(df['price'].max())))
            filters['area_range'] = st.slider("Площадь (м²)", float(df['total_meters'].min()), float(df['total_meters'].max()), (float(df['total_meters'].min()), float(df['total_meters'].max())))
            filters['sqm_range'] = st.slider("Цена за м² (₽)", int(df['price_per_sqm'].min()), int(df['price_per_sqm'].max()), (int(df['price_per_sqm'].min()), int(df['price_per_sqm'].max())))
            if 'floor' in df.columns and not df['floor'].isnull().all():
                fmin, fmax = int(df['floor'].min()), int(df['floor'].max())
                if fmin < fmax:
                    filters['floor_range'] = st.slider("Этаж", fmin, fmax, (fmin, fmax))
            if 'build_year' in df.columns and not df['build_year'].isnull().all():
                ymin, ymax = int(df['build_year'].min()), int(df['build_year'].max())
                if ymin < ymax:
                    filters['year_range'] = st.slider("Год постройки", ymin, ymax, (ymin, ymax))
        with col2:
            prop_types = sorted(df['property_type'].unique())
            if prop_types:
                filters['property_types'] = st.multiselect("Тип недвижимости", prop_types, default=prop_types)
            if 'district' in df.columns and not df['district'].isnull().all():
                filters['districts'] = st.multiselect("Районы", sorted(df['district'].dropna().unique()))
            if 'underground' in df.columns and not df['underground'].isnull().all():
                filters['metros'] = st.multiselect("Станции метро", sorted(df['underground'].dropna().unique()))
        df_filtered = filter_data(df, filters)
        st.markdown("#### 📊 Сортировка")
        sort_col1, sort_col2 = st.columns([3,1])
        with sort_col1:
            sort_by = st.selectbox("Сортировать по", ['price_per_sqm','price','total_meters','rooms'],
                                   format_func=lambda x: {'price_per_sqm':'Цена за м²','price':'Цена','total_meters':'Площадь','rooms':'Комнаты'}[x])
        with sort_col2:
            sort_order = st.radio("Порядок", ['По возрастанию','По убыванию'], horizontal=True)
        df_filtered = df_filtered.sort_values(by=sort_by, ascending=(sort_order=='По возрастанию'))
        st.markdown("---")
        st.subheader("📈 Результаты")
        display_results(df_filtered)
    else:
        if not st.session_state.data_loaded:
            st.info("👈 Выберите параметры в боковой панели и нажмите «Загрузить данные».")
with tab2:
    valuation_calculator(st.session_state.data if st.session_state.data_loaded else None)
    if not st.session_state.data_loaded:
        st.info("Для оценки сначала загрузите данные на вкладке «Анализ рынка».")
st.markdown("---")
st.caption("GRADOV INVEST — профессиональная аналитика рынка недвижимости.")
