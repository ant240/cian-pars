import streamlit as st
import requests
import json
import re
import random
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(page_title="GRADOV FLATS", layout="wide", initial_sidebar_state="collapsed")

st.title("GRADOV FLATS")
st.markdown("Аналитика рынка недвижимости Москвы")

if 'data' not in st.session_state:
    st.session_state.data = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

@st.cache_data(ttl=3600)
def load_proxies():
    try:
        with open("proxies.txt", "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    except:
        return None

def extract_flats_from_page(html):
    """Извлекает данные о квартирах из JSON, встроенного в страницу ЦИАН."""
    flats = []
    # Ищем скрипты с данными
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    for script in scripts:
        if not script.string:
            continue
        # Ищем JSON с данными об объявлениях (обычно window.__INITIAL_STATE__ или window._cianConfig)
        if '__INITIAL_STATE__' in script.string:
            try:
                # Извлекаем JSON
                match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    # Пытаемся найти список объявлений
                    offers = data.get('searchResults', {}).get('offers', [])
                    if not offers:
                        offers = data.get('catalog', {}).get('offers', [])
                    for offer in offers:
                        # Извлекаем нужные поля
                        flat = {}
                        flat['url'] = f"https://www.cian.ru/sale/flat/{offer.get('id', '')}/"
                        flat['price'] = offer.get('bargainTerms', {}).get('price', 0)
                        flat['price_per_sqm'] = offer.get('bargainTerms', {}).get('pricePerSquareMeter', 0)
                        flat['total_meters'] = offer.get('totalArea', 0)
                        flat['rooms'] = offer.get('roomsCount', 0)
                        flat['floor'] = offer.get('floorNumber', 0)
                        flat['floors_total'] = offer.get('floorsTotal', 0)
                        geo = offer.get('geo', {})
                        flat['district'] = geo.get('district', {}).get('name', '')
                        flat['underground'] = ', '.join([u.get('name', '') for u in geo.get('undergrounds', [])])
                        flat['residential_complex'] = offer.get('residentialComplex', {}).get('name', '')
                        if flat['price'] and flat['total_meters']:
                            flats.append(flat)
                    break
            except:
                continue
    return flats

def parse_pages(start_page=1, end_page=2, proxy_list=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    all_flats = []
    for page in range(start_page, end_page+1):
        url = f"https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=1&room1=1&p={page}"
        proxy = random.choice(proxy_list) if proxy_list else None
        proxies = {"http": proxy, "https": proxy} if proxy else None
        try:
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
            if resp.status_code == 200:
                flats = extract_flats_from_page(resp.text)
                all_flats.extend(flats)
        except Exception as e:
            st.warning(f"Ошибка страницы {page}: {e}")
    return pd.DataFrame(all_flats)

with st.sidebar:
    pages = st.slider("Количество страниц для парсинга", 1, 20, 2)
    if st.button("🚀 Загрузить данные", type="primary"):
        proxies = load_proxies()
        if not proxies:
            st.warning("Файл proxies.txt не найден. Работаем без прокси.")
        else:
            st.info(f"Загружено {len(proxies)} прокси.")
        with st.spinner("Парсинг..."):
            df = parse_pages(1, pages, proxies)
            if not df.empty:
                st.session_state.data = df
                st.session_state.data_loaded = True
                st.success(f"✅ Загружено {len(df)} объявлений")
            else:
                st.error("Не удалось получить данные. Возможно, структура страницы изменилась.")

if st.session_state.data_loaded and st.session_state.data is not None:
    df = st.session_state.data
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False)
    st.download_button("📥 Скачать CSV", csv, f"gradov_flats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
else:
    st.info("👈 Нажмите «Загрузить данные» для парсинга")
