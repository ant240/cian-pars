import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import re
import json
import time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="GRADOV FLATS", layout="wide", initial_sidebar_state="collapsed")

# Стили (чёрно-белые, без эмодзи)
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
.main .block-container { padding-top: 1rem; max-width: 100%; }
.stButton>button { background-color: #000; color: white; border-radius: 40px; width: 100%; border: none; }
.stButton>button:hover { background-color: #333; }
</style>
""", unsafe_allow_html=True)

st.title("GRADOV FLATS")
st.caption("Аналитика рынка недвижимости Москвы")

# Загрузка прокси
try:
    with open("proxies.txt", "r") as f:
        proxies = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    proxies = []
    st.error("Файл proxies.txt не найден")

if 'data' not in st.session_state:
    st.session_state.data = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

def get_proxy():
    return random.choice(proxies) if proxies else None

def fetch(url, proxy):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    proxies_dict = {"http": proxy, "https": proxy} if proxy else None
    try:
        resp = requests.get(url, headers=headers, proxies=proxies_dict, timeout=15)
        return resp if resp.status_code == 200 else None
    except:
        return None

def parse_links(pages=1, max_flats=50):
    links = []
    for page in range(1, pages+1):
        proxy = get_proxy()
        url = f"https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=1&room1=1&p={page}"
        resp = fetch(url, proxy)
        if resp:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/sale/flat/' in href:
                    full = 'https://www.cian.ru' + href if href.startswith('/') else href
                    links.append(full)
        time.sleep(random.uniform(1, 2))
    return list(set(links))[:max_flats]

def parse_flats(links):
    flats = []
    for idx, link in enumerate(links):
        proxy = get_proxy()
        resp = fetch(link, proxy)
        if resp:
            soup = BeautifulSoup(resp.text, 'html.parser')
            data = {}
            scripts = soup.find_all('script')
            for script in scripts:
                if not script.string:
                    continue
                for pat in [r'window\.__state__\s*=\s*({.*?});', r'__INITIAL_STATE__\s*=\s*({.*?});']:
                    match = re.search(pat, script.string, re.DOTALL)
                    if match:
                        try:
                            state = json.loads(match.group(1))
                            if 'offer' in state:
                                o = state['offer']
                                data['price'] = o.get('price', 0)
                                data['area'] = o.get('totalArea', 0)
                                data['rooms'] = o.get('roomsCount', 0)
                                data['floor'] = o.get('floorNumber', '')
                                data['floors_total'] = o.get('floorsTotal', '')
                                data['address'] = o.get('address', {}).get('address', '')
                                data['district'] = o.get('district', {}).get('name', '')
                                metro = o.get('metro', [])
                                data['metro'] = ', '.join([m['name'] for m in metro]) if metro else ''
                                data['build_year'] = o.get('buildYear', '')
                                data['phone'] = o.get('phone', '')
                                data['url'] = link
                                break
                        except:
                            continue
                if data:
                    break
            if data:
                flats.append(data)
        time.sleep(random.uniform(1, 2))
    return pd.DataFrame(flats)

# --- Боковая панель с настройками парсинга ---
with st.sidebar:
    st.subheader("Параметры поиска")
    search_pages = st.slider("Страниц поиска для сбора ссылок", 1, 5, 1)
    max_flats = st.slider("Максимум объявлений для парсинга", 1, 50, 10)
    parse_button = st.button("Загрузить данные", type="primary")

if parse_button:
    if not proxies:
        st.error("Нет прокси. Загрузите файл proxies.txt")
    else:
        with st.spinner("Сбор ссылок..."):
            links = parse_links(search_pages, max_flats)
        if links:
            st.info(f"Найдено ссылок: {len(links)}")
            with st.spinner("Парсинг объявлений..."):
                df = parse_flats(links)
                if not df.empty:
                    st.session_state.data = df
                    st.session_state.data_loaded = True
                    st.success(f"Загружено {len(df)} объявлений")
                else:
                    st.error("Не удалось извлечь данные. Попробуйте другие прокси.")
        else:
            st.error("Не найдено ссылок на объявления")

# --- Отображение данных и фильтры ---
if st.session_state.data_loaded and st.session_state.data is not None:
    df = st.session_state.data
    
    st.markdown("---")
    st.subheader("Уточняющие фильтры")
    
    col1, col2 = st.columns(2)
    with col1:
        price_min = int(df['price'].min())
        price_max = int(df['price'].max())
        price_range = st.slider("Цена (руб)", price_min, price_max, (price_min, price_max))
        df = df[(df['price'] >= price_range[0]) & (df['price'] <= price_range[1])]
        
        area_min = float(df['area'].min())
        area_max = float(df['area'].max())
        area_range = st.slider("Площадь (м²)", area_min, area_max, (area_min, area_max))
        df = df[(df['area'] >= area_range[0]) & (df['area'] <= area_range[1])]
        
        df['price_per_sqm'] = df['price'] / df['area']
        sqm_min = int(df['price_per_sqm'].min())
        sqm_max = int(df['price_per_sqm'].max())
        sqm_range = st.slider("Цена за м² (руб)", sqm_min, sqm_max, (sqm_min, sqm_max))
        df = df[(df['price_per_sqm'] >= sqm_range[0]) & (df['price_per_sqm'] <= sqm_range[1])]
        
        if 'floor' in df.columns:
            floor_vals = df['floor'].dropna().astype(int)
            if not floor_vals.empty:
                floor_min, floor_max = floor_vals.min(), floor_vals.max()
                floor_range = st.slider("Этаж", floor_min, floor_max, (floor_min, floor_max))
                df = df[(df['floor'].astype(int) >= floor_range[0]) & (df['floor'].astype(int) <= floor_range[1])]
    
    with col2:
        if 'district' in df.columns and not df['district'].isnull().all():
            districts = sorted(df['district'].dropna().unique())
            selected_districts = st.multiselect("Районы", districts)
            if selected_districts:
                df = df[df['district'].isin(selected_districts)]
        
        if 'metro' in df.columns and not df['metro'].isnull().all():
            metros = sorted(df['metro'].dropna().unique())
            selected_metros = st.multiselect("Станции метро", metros)
            if selected_metros:
                df = df[df['metro'].isin(selected_metros)]
    
    st.markdown("---")
    st.subheader("Результаты")
    
    # Статистика
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Всего", len(df))
    col_b.metric("Средняя цена", f"{df['price'].mean():,.0f} руб")
    col_c.metric("Средняя цена за м²", f"{df['price_per_sqm'].mean():,.0f} руб")
    col_d.metric("Средняя площадь", f"{df['area'].mean():.1f} м²")
    
    st.dataframe(df, use_container_width=True)
    
    # Экспорт CSV
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("Скачать CSV", csv, f"gradov_flats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    # Оценка квартиры
    st.markdown("---")
    st.subheader("Оценка вашей квартиры")
    own_rooms = st.number_input("Количество комнат", 0, 6, 2)
    own_area = st.number_input("Площадь (м²)", 10.0, 300.0, 50.0)
    own_floor = st.number_input("Этаж", 1, 50, 5)
    own_district = st.selectbox("Район", options=["Любой"] + sorted(df['district'].dropna().unique()) if 'district' in df.columns else ["Любой"])
    
    if st.button("Оценить"):
        similar = df.copy()
        if own_district != "Любой":
            similar = similar[similar['district'] == own_district]
        similar = similar[similar['rooms'] == own_rooms]
        similar = similar[(similar['area'] >= own_area*0.8) & (similar['area'] <= own_area*1.2)]
        similar = similar[(similar['floor'].astype(int) >= own_floor-3) & (similar['floor'].astype(int) <= own_floor+3)]
        if not similar.empty:
            avg_price_per_sqm = similar['price_per_sqm'].mean()
            est_price = avg_price_per_sqm * own_area
            st.success(f"Средняя цена за м²: {avg_price_per_sqm:,.0f} руб")
            st.success(f"Оценочная стоимость квартиры: {est_price:,.0f} руб")
            st.caption(f"Найдено {len(similar)} аналогов")
        else:
            st.warning("Нет похожих объявлений")
else:
    if not st.session_state.data_loaded:
        st.info("Настройте параметры и нажмите «Загрузить данные»")
