import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import re
import json

st.set_page_config(page_title="GRADOV FLATS - поиск JSON")
st.title("Поиск JSON с данными на странице ЦИАН")

# Загрузка прокси
try:
    with open("proxies.txt", "r") as f:
        proxies = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    st.error("Файл proxies.txt не найден")
    st.stop()

st.write(f"Загружено прокси: {len(proxies)}")

proxy = random.choice(proxies)
st.code(proxy)

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
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    scripts = soup.find_all('script')
    st.write(f"Найдено скриптов: {len(scripts)}")
    
    # Ищем все возможные JSON-данные в скриптах
    found = False
    for i, script in enumerate(scripts):
        if not script.string:
            continue
        # Ищем window.__search__ или window.__cian__
        for pattern in [r'window\.__search__\s*=\s*({.*?});', r'window\.__cian__\s*=\s*({.*?});', r'__INITIAL_STATE__\s*=\s*({.*?});']:
            match = re.search(pattern, script.string, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    st.success(f"Найден JSON в скрипте {i} по паттерну {pattern[:30]}")
                    st.json(data)  # показываем структуру
                    found = True
                    break
                except:
                    continue
        if found:
            break
    
    if not found:
        st.warning("Не удалось найти JSON. Показываю первые 5 скриптов с содержимым:")
        for i, script in enumerate(scripts[:5]):
            if script.string and len(script.string) > 100:
                st.text_area(f"Скрипт {i}", script.string[:2000], height=200)
    
except Exception as e:
    st.error(f"Ошибка: {e}")
