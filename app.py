import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import re
import json
import time
import pandas as pd

st.set_page_config(page_title="GRADOV FLATS - парсинг объявлений")
st.title("Парсинг объявлений с ЦИАН через прокси")

# Загрузка прокси
try:
    with open("proxies.txt", "r") as f:
        proxies = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    st.error("Файл proxies.txt не найден")
    st.stop()

st.write(f"Загружено прокси: {len(proxies)}")

max_pages = st.slider("Страниц поиска для сбора ссылок", 1, 5, 1)
max_flats = st.slider("Максимум объявлений для парсинга", 1, 50, 10)
if st.button("🚀 Начать парсинг"):
    def get_proxy():
        return random.choice(proxies)

    def fetch(url, proxy):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }
        proxies_dict = {"http": proxy, "https": proxy}
        try:
            resp = requests.get(url, headers=headers, proxies=proxies_dict, timeout=15)
            return resp if resp.status_code == 200 else None
        except:
            return None

    # Шаг 1: собираем ссылки на объявления
    links = []
    progress_bar = st.progress(0)
    status = st.empty()
    for page in range(1, max_pages+1):
        status.text(f"Сбор ссылок: страница {page}...")
        proxy = get_proxy()
        search_url = f"https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=1&room1=1&p={page}"
        resp = fetch(search_url, proxy)
        if resp:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/sale/flat/' in href:
                    full_url = 'https://www.cian.ru' + href if href.startswith('/') else href
                    links.append(full_url)
        time.sleep(random.uniform(1, 2))
        progress_bar.progress(page / max_pages / 2)
    links = list(set(links))[:max_flats]
    st.write(f"Найдено уникальных ссылок: {len(links)}")

    # Шаг 2: парсим каждое объявление
    flats = []
    for idx, link in enumerate(links):
        status.text(f"Парсинг объявления {idx+1} из {len(links)}...")
        proxy = get_proxy()
        resp = fetch(link, proxy)
        if resp:
            soup = BeautifulSoup(resp.text, 'html.parser')
            data = {}
            # Ищем JSON в скриптах
            scripts = soup.find_all('script')
            for script in scripts:
                if not script.string:
                    continue
                # Паттерны для JSON
                patterns = [
                    r'window\.__state__\s*=\s*({.*?});',
                    r'__INITIAL_STATE__\s*=\s*({.*?});',
                    r'window\.__search__\s*=\s*({.*?});'
                ]
                for pat in patterns:
                    match = re.search(pat, script.string, re.DOTALL)
                    if match:
                        try:
                            state = json.loads(match.group(1))
                            # Пробуем извлечь offer
                            if 'offer' in state:
                                offer = state['offer']
                                data['price'] = offer.get('price', 0)
                                data['area'] = offer.get('totalArea', 0)
                                data['rooms'] = offer.get('roomsCount', 0)
                                data['floor'] = offer.get('floorNumber', '')
                                data['floors_total'] = offer.get('floorsTotal', '')
                                data['address'] = offer.get('address', {}).get('address', '')
                                data['district'] = offer.get('district', {}).get('name', '')
                                metro = offer.get('metro', [])
                                data['metro'] = ', '.join([m['name'] for m in metro]) if metro else ''
                                data['build_year'] = offer.get('buildYear', '')
                                data['phone'] = offer.get('phone', '')
                                data['url'] = link
                                break
                        except:
                            continue
                if data:
                    break
            # Если JSON не найден, пробуем извлечь из HTML-тегов
            if not data:
                price_elem = soup.find('span', class_=re.compile(r'_93444fe79c|price'))
                price_text = price_elem.text if price_elem else ''
                price_match = re.search(r'(\d+[\.,]?\d*)\s*(млн|тыс|₽)', price_text)
                if price_match:
                    val = float(price_match.group(1).replace(',', '.'))
                    if 'млн' in price_text:
                        data['price'] = int(val * 1000000)
                    elif 'тыс' in price_text:
                        data['price'] = int(val * 1000)
                area_elem = soup.find('div', class_=re.compile(r'total_meters|area'))
                if area_elem:
                    area_match = re.search(r'(\d+[,.]?\d*)', area_elem.text)
                    data['area'] = float(area_match.group(1).replace(',', '.')) if area_match else 0
                rooms_elem = soup.find('div', class_=re.compile(r'rooms|_93444fe79c'))
                if rooms_elem:
                    rooms_match = re.search(r'(\d+)', rooms_elem.text)
                    data['rooms'] = int(rooms_match.group(1)) if rooms_match else 0
                data['url'] = link
            if data:
                flats.append(data)
        time.sleep(random.uniform(1, 2))
        progress_bar.progress(0.5 + (idx+1) / len(links) / 2)

    if flats:
        df = pd.DataFrame(flats)
        st.success(f"Успешно спарсено {len(df)} объявлений")
        st.dataframe(df)
        csv = df.to_csv(index=False)
        st.download_button("📥 Скачать CSV", csv, "gradov_flats.csv")
    else:
        st.error("Не удалось получить данные ни по одному объявлению. Попробуйте другие прокси или увеличьте таймаут.")
