import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import re
import json
import time
import pandas as pd
from typing import List, Dict, Any

# ---------- НАСТРОЙКИ СТРАНИЦЫ (чёрно-белый стиль, скрытие элементов Streamlit) ----------
st.set_page_config(page_title="GRADOV FLATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    .stApp > header {display: none;}
    .stApp > div:first-child {display: none;}
    .main .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: 100%; }
    body, .stApp { background-color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    h1, h2, h3, .stMarkdown, .stText, .stMetric { color: #1a1a1a; }
    .stButton > button { background-color: #000000; color: white; border-radius: 40px; border: none; padding: 0.5rem 1rem; font-weight: 500; width: 100%; transition: all 0.2s ease; }
    .stButton > button:hover { background-color: #333333; }
    .stSelectbox, .stMultiSelect, .stNumberInput, .stSlider { margin-bottom: 0.5rem; }
    .stMetric { background-color: #f8f9fa; border-radius: 16px; padding: 0.5rem; text-align: center; }
    .stDataFrame { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; margin-bottom: 1rem;'>
    <h1 style='font-size: 2rem; font-weight: 600; margin-bottom: 0;'>GRADOV FLATS</h1>
    <p style='color: #666; margin-top: 0;'>Аналитика рынка недвижимости Москвы</p>
</div>
<hr style='margin: 0.5rem 0;'>
""", unsafe_allow_html=True)

# ---------- СОСТОЯНИЕ ----------
if 'data' not in st.session_state:
    st.session_state.data = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# ---------- ЗАГРУЗКА ПРОКСИ ----------
def load_proxies() -> List[str]:
    try:
        with open("proxies.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        st.error("Файл proxies.txt не найден")
        return []

# ---------- ЗАПРОС С ПРОКСИ ----------
def fetch(url: str, proxy: str, timeout: int = 15):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    proxies_dict = {"http": proxy, "https": proxy}
    try:
        resp = requests.get(url, headers=headers, proxies=proxies_dict, timeout=timeout)
        return resp if resp.status_code == 200 else None
    except:
        return None

# ---------- СБОР ВСЕХ ССЫЛОК (ВСЕ СТРАНИЦЫ ВЫДАЧИ) ----------
def collect_all_links(proxies: List[str], rooms: List[int]) -> List[str]:
    """
    Собирает ссылки на объявления со всех страниц выдачи, пока есть данные.
    Параметры: rooms – список комнат (0,1,2,...). Формирует URL поиска.
    """
    links = set()
    page = 1
    # Формируем базовый URL с учётом комнат
    room_params = []
    if 0 in rooms:
        room_params.append('studio=1')
    for r in rooms:
        if r != 0:
            room_params.append(f'room{r}=1')
    room_str = '&'.join(room_params)
    base_url = f"https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=1&{room_str}&p={{}}"
    while True:
        proxy = random.choice(proxies) if proxies else None
        if not proxy:
            break
        url = base_url.format(page)
        resp = fetch(url, proxy)
        if not resp:
            break
        soup = BeautifulSoup(resp.text, 'html.parser')
        found = False
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/sale/flat/' in href:
                full_url = 'https://www.cian.ru' + href if href.startswith('/') else href
                links.add(full_url)
                found = True
        if not found:
            break
        page += 1
        time.sleep(random.uniform(1, 2))
        if page > 100:  # защита
            break
    return list(links)

# ---------- ПАРСИНГ ОДНОГО ОБЪЯВЛЕНИЯ ----------
def parse_flat(link: str, proxy: str) -> Dict[str, Any]:
    resp = fetch(link, proxy)
    if not resp:
        return {}
    soup = BeautifulSoup(resp.text, 'html.parser')
    data = {}
    # Поиск JSON в скриптах
    scripts = soup.find_all('script')
    for script in scripts:
        if not script.string:
            continue
        match = re.search(r'window\.__state__\s*=\s*({.*?});', script.string, re.DOTALL)
        if not match:
            match = re.search(r'__INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
        if match:
            try:
                state = json.loads(match.group(1))
                if 'offer' in state:
                    offer = state['offer']
                    data['price'] = offer.get('price', 0)
                    data['total_meters'] = offer.get('totalArea', 0)
                    data['rooms'] = offer.get('roomsCount', 0)
                    data['floor'] = offer.get('floorNumber', '')
                    data['floors_total'] = offer.get('floorsTotal', '')
                    data['build_year'] = offer.get('buildYear', '')
                    data['address'] = offer.get('address', {}).get('address', '')
                    data['district'] = offer.get('district', {}).get('name', '')
                    metro = offer.get('metro', [])
                    data['metro'] = ', '.join([m['name'] for m in metro]) if metro else ''
                    data['time_to_metro'] = offer.get('metro', [{}])[0].get('time', '') if metro else ''
                    data['phone'] = offer.get('phone', '')
                    data['property_type'] = 'Новостройка' if offer.get('isApartment', False) else 'Вторичка'
                    data['residential_complex'] = offer.get('residentialComplex', {}).get('name', '')
                    data['url'] = link
                    break
            except:
                continue
    # Если JSON не найден, извлекаем из HTML (минимально)
    if not data:
        # Цена
        price_elem = soup.find('span', class_=re.compile(r'_93444fe79c|price'))
        price_text = price_elem.text if price_elem else ''
        price_match = re.search(r'(\d+[\.,]?\d*)\s*(млн|тыс|₽)', price_text)
        if price_match:
            val = float(price_match.group(1).replace(',', '.'))
            if 'млн' in price_text:
                data['price'] = int(val * 1000000)
            elif 'тыс' in price_text:
                data['price'] = int(val * 1000)
            else:
                data['price'] = int(val)
        # Площадь
        area_elem = soup.find('div', class_=re.compile(r'total_meters|area'))
        if area_elem:
            area_match = re.search(r'(\d+[,.]?\d*)', area_elem.text)
            data['total_meters'] = float(area_match.group(1).replace(',', '.')) if area_match else 0
        # Комнаты
        rooms_elem = soup.find('div', class_=re.compile(r'rooms|_93444fe79c'))
        if rooms_elem:
            rooms_match = re.search(r'(\d+)', rooms_elem.text)
            data['rooms'] = int(rooms_match.group(1)) if rooms_match else 0
        data['url'] = link
    if data.get('price', 0) > 0 and data.get('total_meters', 0) > 0:
        data['price_per_sqm'] = round(data['price'] / data['total_meters'], 2)
    else:
        data['price_per_sqm'] = 0
    return data

# ---------- ПАРСИНГ ВСЕХ ОБЪЯВЛЕНИЙ ----------
def parse_all_flats(links: List[str], proxies: List[str], progress_bar, status_text) -> pd.DataFrame:
    flats = []
    total = len(links)
    for i, link in enumerate(links):
        status_text.text(f"Парсинг {i+1} из {total}")
        proxy = random.choice(proxies) if proxies else None
        if proxy:
            flat = parse_flat(link, proxy)
            if flat:
                flats.append(flat)
        time.sleep(random.uniform(0.5, 1.5))
        progress_bar.progress((i+1)/total)
    return pd.DataFrame(flats)

# ---------- ФИЛЬТРАЦИЯ ----------
def filter_data(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    df_filtered = df.copy()
    if filters['price_range']:
        df_filtered = df_filtered[(df_filtered['price'] >= filters['price_range'][0]) & (df_filtered['price'] <= filters['price_range'][1])]
    if filters['area_range']:
        df_filtered = df_filtered[(df_filtered['total_meters'] >= filters['area_range'][0]) & (df_filtered['total_meters'] <= filters['area_range'][1])]
    if filters['sqm_range']:
        df_filtered = df_filtered[(df_filtered['price_per_sqm'] >= filters['sqm_range'][0]) & (df_filtered['price_per_sqm'] <= filters['sqm_range'][1])]
    if filters['floor_range']:
        df_filtered = df_filtered[(df_filtered['floor'].astype(int) >= filters['floor_range'][0]) & (df_filtered['floor'].astype(int) <= filters['floor_range'][1])]
    if filters['year_range']:
        df_filtered = df_filtered[(df_filtered['build_year'].astype(int) >= filters['year_range'][0]) & (df_filtered['build_year'].astype(int) <= filters['year_range'][1])]
    if filters['property_types']:
        df_filtered = df_filtered[df_filtered['property_type'].isin(filters['property_types'])]
    if filters['districts']:
        df_filtered = df_filtered[df_filtered['district'].isin(filters['districts'])]
    if filters['metros']:
        df_filtered = df_filtered[df_filtered['metro'].str.contains('|'.join(filters['metros']), na=False)]
    return df_filtered

# ---------- ОЦЕНКА КВАРТИРЫ ----------
def valuation_calculator(df: pd.DataFrame):
    st.subheader("Оценка вашей квартиры")
    st.caption("Введите характеристики, чтобы увидеть рыночную вилку цен")
    if df is None or df.empty:
        st.warning("Сначала загрузите данные на вкладке «Анализ рынка».")
        return
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        own_rooms = st.number_input("Комнат", 0, 6, 2, 1, help="0 — студия")
    with col2:
        own_area = st.number_input("Площадь (м²)", 10.0, 300.0, 50.0, 1.0)
    with col3:
        own_floor = st.number_input("Этаж", 1, 50, 5, 1)
    with col4:
        own_year = st.number_input("Год постройки", 1900, 2026, 2010, 1)
    district_list = ["Любой"] + sorted(df['district'].dropna().unique().tolist()) if 'district' in df.columns else ["Любой"]
    own_district = st.selectbox("Район", district_list)
    if st.button("Анализировать", type="primary"):
        similar = df.copy()
        if own_district != "Любой" and 'district' in similar.columns:
            similar = similar[similar['district'] == own_district]
        similar = similar[similar['rooms'] == own_rooms]
        similar = similar[(similar['total_meters'] >= own_area * 0.8) & (similar['total_meters'] <= own_area * 1.2)]
        if 'floor' in similar.columns:
            similar = similar[(similar['floor'].astype(int) >= own_floor - 3) & (similar['floor'].astype(int) <= own_floor + 3)]
        if 'build_year' in similar.columns:
            similar = similar[(similar['build_year'].astype(int) >= own_year - 5) & (similar['build_year'].astype(int) <= own_year + 5)]
        if len(similar) == 0:
            st.warning("Не найдено похожих объявлений.")
            return
        price_min = similar['price'].min()
        price_median = similar['price'].median()
        price_max = similar['price'].max()
        price_sqm_min = similar['price_per_sqm'].min()
        price_sqm_median = similar['price_per_sqm'].median()
        price_sqm_max = similar['price_per_sqm'].max()
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("Нижняя граница (быстрая продажа)", f"{price_sqm_min:,.0f} ₽/м²")
        col2.metric("Средняя по рынку", f"{price_sqm_median:,.0f} ₽/м²")
        col3.metric("Верхняя граница (долгий поиск)", f"{price_sqm_max:,.0f} ₽/м²")
        recommended = (price_min + price_median) / 2
        st.success(f"Рекомендованная цена для старта: **{recommended:,.0f} ₽**")
        st.caption("Эта цена позволит быстро найти покупателя и не потерять в стоимости.")
        with st.expander("Показать похожие объявления"):
            st.dataframe(similar[['price', 'total_meters', 'price_per_sqm', 'floor', 'build_year', 'district', 'metro']])

# ---------- ОСНОВНОЙ ИНТЕРФЕЙС ----------
tab1, tab2 = st.tabs(["Анализ рынка (найти квартиру)", "Оценка своей квартиры (продать)"])

with tab1:
    with st.sidebar:
        st.markdown("### Параметры поиска")
        city = st.text_input("Город", value="Москва")
        rooms = st.multiselect("Количество комнат (пусто = все, включая студии)", options=[0,1,2,3,4,5,6], format_func=lambda x: "Студия" if x==0 else f"{x}", default=[1,2,3])
        load_button = st.button("Загрузить данные", type="primary", use_container_width=True)
        st.markdown("---")
        st.markdown("### Расширенные фильтры")
        st.caption("Появятся после загрузки данных")
    
    if load_button:
        proxies = load_proxies()
        if not proxies:
            st.error("Нет прокси. Загрузите файл proxies.txt")
        else:
            with st.spinner("Сбор ссылок на объявления..."):
                links = collect_all_links(proxies, rooms)
                st.success(f"Найдено {len(links)} ссылок")
            if links:
                progress_bar = st.progress(0)
                status_text = st.empty()
                df = parse_all_flats(links, proxies, progress_bar, status_text)
                if not df.empty:
                    st.session_state.data = df
                    st.session_state.data_loaded = True
                    st.success(f"Загружено {len(df)} объявлений")
                else:
                    st.error("Не удалось спарсить объявления")
    
    if st.session_state.data_loaded and st.session_state.data is not None:
        df = st.session_state.data
        st.markdown("---")
        st.subheader("Фильтры")
        filters = {
            'price_range': None, 'area_range': None, 'sqm_range': None,
            'floor_range': None, 'year_range': None,
            'property_types': [], 'districts': [], 'metros': []
        }
        col1, col2 = st.columns(2)
        with col1:
            filters['price_range'] = st.slider("Цена (₽)", int(df['price'].min()), int(df['price'].max()), (int(df['price'].min()), int(df['price'].max())))
            filters['area_range'] = st.slider("Площадь (м²)", float(df['total_meters'].min()), float(df['total_meters'].max()), (float(df['total_meters'].min()), float(df['total_meters'].max())))
            filters['sqm_range'] = st.slider("Цена за м² (₽)", int(df['price_per_sqm'].min()), int(df['price_per_sqm'].max()), (int(df['price_per_sqm'].min()), int(df['price_per_sqm'].max())))
            if 'floor' in df.columns and df['floor'].notna().any():
                fmin, fmax = int(df['floor'].min()), int(df['floor'].max())
                if fmin < fmax:
                    filters['floor_range'] = st.slider("Этаж", fmin, fmax, (fmin, fmax))
            if 'build_year' in df.columns and df['build_year'].notna().any():
                ymin, ymax = int(df['build_year'].min()), int(df['build_year'].max())
                if ymin < ymax:
                    filters['year_range'] = st.slider("Год постройки", ymin, ymax, (ymin, ymax))
        with col2:
            prop_types = sorted(df['property_type'].unique())
            if prop_types:
                filters['property_types'] = st.multiselect("Тип недвижимости", prop_types, default=prop_types)
            if 'district' in df.columns and df['district'].notna().any():
                districts_avail = sorted(df['district'].dropna().unique())
                filters['districts'] = st.multiselect("Районы", districts_avail)
            if 'metro' in df.columns and df['metro'].notna().any():
                # Разбираем список метро
                all_metros = []
                for m in df['metro'].dropna():
                    all_metros.extend([x.strip() for x in m.split(',')])
                flat_metros = sorted(set(all_metros))
                filters['metros'] = st.multiselect("Станции метро", flat_metros)
        df_filtered = filter_data(df, filters)
        st.markdown("---")
        st.subheader("Результаты")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Всего объявлений", len(df_filtered))
        col2.metric("Средняя цена", f"{df_filtered['price'].mean():,.0f} ₽")
        col3.metric("Средняя цена за м²", f"{df_filtered['price_per_sqm'].mean():,.0f} ₽")
        col4.metric("Средняя площадь", f"{df_filtered['total_meters'].mean():.1f} м²")
        display_cols = ['residential_complex', 'rooms', 'total_meters', 'price', 'price_per_sqm',
                        'floor', 'build_year', 'property_type', 'district', 'metro', 'time_to_metro', 'phone', 'url']
        existing = [c for c in display_cols if c in df_filtered.columns]
        st.dataframe(df_filtered[existing], use_container_width=True)
        csv = df_filtered.to_csv(index=False)
        st.download_button("Скачать данные (CSV)", csv, file_name="gradov_flats.csv")
    else:
        st.info("Нажмите «Загрузить данные» в боковой панели, чтобы начать сбор объявлений.")

with tab2:
    valuation_calculator(st.session_state.data if st.session_state.data_loaded else None)
    if not st.session_state.data_loaded:
        st.info("Для оценки сначала загрузите данные на вкладке «Анализ рынка».")
