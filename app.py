import streamlit as st
import requests
import random
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="GRADOV FLATS - прямой парсинг")
st.title("Прямой парсинг ЦИАН через прокси")

# Загружаем прокси
with open("proxies.txt", "r") as f:
    proxies = [line.strip() for line in f if line.strip()]
st.write(f"Загружено прокси: {len(proxies)}")

# Выбираем случайный прокси
proxy = random.choice(proxies)
st.code(proxy)

# URL поиска (однушки в Москве)
url = "https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=1&room1=1"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

try:
    response = requests.get(url, headers=headers, proxies={"http": proxy, "https": proxy}, timeout=15)
    st.write(f"HTTP статус: {response.status_code}")
    if response.status_code != 200:
        st.error("Ошибка загрузки")
        st.stop()
except Exception as e:
    st.error(f"Ошибка запроса: {e}")
    st.stop()

soup = BeautifulSoup(response.text, 'html.parser')

# Поиск карточек объявлений (универсальные классы)
cards = soup.find_all('div', class_=re.compile('_93444fe79c|_9a1d73bfe5'))
if not cards:
    cards = soup.find_all('article', class_=re.compile('_096c43b56c'))

st.write(f"Найдено карточек: {len(cards)}")

flats = []
for card in cards[:5]:  # берём первые 5 для примера
    try:
        # Название ЖК
        complex_elem = card.find('div', class_=re.compile('_93444fe79c'))
        residential = complex_elem.text.strip() if complex_elem else ''
        
        # Цена
        price_elem = card.find('span', class_=re.compile('_93444fe79c'))
        price_text = price_elem.text.replace('₽', '').replace(' ', '') if price_elem else ''
        price = 0
        if 'млн' in price_text:
            price = float(price_text.replace('млн', '')) * 1000000
        elif 'тыс' in price_text:
            price = float(price_text.replace('тыс', '')) * 1000
        elif price_text.isdigit():
            price = int(price_text)
        
        # Площадь
        area_elem = card.find('div', class_=re.compile('_93444fe79c'), string=re.compile('м²'))
        if not area_elem:
            area_elem = card.find('div', string=re.compile('м²'))
        area = 0.0
        if area_elem:
            area_text = area_elem.text.split('м²')[0].strip().replace(',', '.')
            area = float(area_text)
        
        if price > 0 and area > 0:
            flats.append({
                'ЖК': residential,
                'Цена': price,
                'Площадь': area,
                'Цена за м²': round(price/area, 2)
            })
    except Exception as e:
        continue

if flats:
    st.success(f"Найдено {len(flats)} объявлений")
    st.dataframe(flats)
else:
    st.warning("Не удалось извлечь объявления. Возможно, изменилась структура страницы.")    st.write(f"Получено объявлений: {len(flats)}")
    if flats:
        st.dataframe(flats[:3])
    else:
        st.warning("Нет данных – возможно, прокси не работает или ЦИАН блокирует")
except Exception as e:
    st.error(f"Ошибка получения данных: {e}")
