import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import re

st.set_page_config(page_title="GRADOV FLATS - прямой парсинг")
st.title("Прямой парсинг ЦИАН через прокси")

# Загрузка прокси
try:
    with open("proxies.txt", "r") as f:
        proxies = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    st.error("Файл proxies.txt не найден")
    st.stop()

st.write(f"Загружено прокси: {len(proxies)}")

# Выбираем случайный прокси
proxy = random.choice(proxies)
st.code(proxy)

# URL поиска квартир (1-комнатные, Москва, страница 1)
url = "https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=1&room1=1&p=1"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

proxy_dict = {"http": proxy, "https": proxy}

try:
    with st.spinner("Загрузка страницы..."):
        resp = requests.get(url, headers=headers, proxies=proxy_dict, timeout=15)
    st.write(f"HTTP статус: {resp.status_code}")
    if resp.status_code != 200:
        st.error("Не удалось загрузить страницу")
        st.stop()
    
    # Парсим HTML
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Ищем все ссылки на объявления
    links = soup.find_all('a', href=True)
    flat_links = [a['href'] for a in links if '/sale/flat/' in a['href']]
    st.write(f"Найдено ссылок на объявления: {len(set(flat_links))}")
    
    if not flat_links:
        st.warning("Ссылки на объявления не найдены. Возможно, изменилась структура страницы.")
        st.stop()
    
    # Показываем первые 3 ссылки для примера
    st.subheader("Примеры ссылок на объявления")
    for link in list(set(flat_links))[:3]:
        st.write(link)
    
    # Ищем блоки с ценами (универсальные классы)
    price_spans = soup.find_all('span', class_=re.compile(r'_93444fe79c|_a0e19f63a5|_1j4hn'))
    st.write(f"Найдено блоков с ценами: {len(price_spans)}")
    
    if price_spans:
        st.success("Цены найдены! Парсинг возможен.")
        for span in price_spans[:5]:
            st.write(span.get_text(strip=True))
    else:
        st.warning("Цены не найдены — возможно, страница динамическая.")
    
except Exception as e:
    st.error(f"Ошибка: {e}")
