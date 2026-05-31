import streamlit as st
import requests
import random
import os
from bs4 import BeautifulSoup

st.set_page_config(page_title="GRADOV FLATS - Диагностика доступа к ЦИАН")
st.title("GRADOV FLATS — Диагностика доступа к ЦИАН")

# -------------------------
# Загрузка прокси
# -------------------------
def load_proxies():
    if not os.path.exists("proxies.txt"):
        return []
    with open("proxies.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

proxies = load_proxies()
st.write(f"Прокси загружено: {len(proxies)}")

if not proxies:
    st.error("Файл proxies.txt не найден или пуст.")
    st.stop()

proxy = random.choice(proxies)
st.info(f"Тестируем прокси:\n{proxy[:100]}")

proxy_dict = {
    "http": proxy,
    "https": proxy
}

# -------------------------
# Проверка IP через прокси
# -------------------------
st.subheader("Шаг 1. Проверка IP")

try:
    ip_response = requests.get(
        "https://api.ipify.org?format=json",
        proxies=proxy_dict,
        timeout=15
    )
    st.success("Прокси отвечает")
    st.json(ip_response.json())
except Exception as e:
    st.error(f"Прокси не работает:\n{e}")
    st.stop()

# -------------------------
# Запрос к ЦИАН
# -------------------------
st.subheader("Шаг 2. Запрос к ЦИАН")

url = (
    "https://cian.ru/cat.php?"
    "deal_type=sale&"
    "engine_version=2&"
    "offer_type=flat&"
    "p=1&"
    "region=1&"
    "room1=1"
)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate"  # br убрал для стабильности
}

try:
    response = requests.get(
        url,
        headers=headers,
        proxies=proxy_dict,
        timeout=25,
        allow_redirects=True
    )
    st.write("HTTP статус:", response.status_code)
    st.write("Финальный URL:", response.url)
    html = response.text
    st.write("Размер ответа:", len(html))
    st.subheader("Первые 1000 символов HTML")
    st.text_area("Ответ сервера", html[:1000], height=300)
except Exception as e:
    st.error(f"Ошибка запроса к ЦИАН:\n{e}")
    st.stop()

# -------------------------
# Проверка признаков блокировки
# -------------------------
st.subheader("Шаг 3. Анализ ответа")

html_lower = html.lower()
block_markers = [
    "captcha", "cloudflare", "access denied", "robot",
    "security check", "проверка безопасности", "доступ ограничен"
]

found_blocks = [m for m in block_markers if m in html_lower]

if found_blocks:
    st.error("Обнаружены признаки блокировки")
    st.write(found_blocks)
else:
    st.success("Явных признаков блокировки не найдено")

# -------------------------
# Поиск объявлений
# -------------------------
st.subheader("Шаг 4. Поиск объявлений")

soup = BeautifulSoup(html, "html.parser")
links = soup.find_all("a", href=True)
flat_links = list({a["href"] for a in links if "/sale/flat/" in a["href"]})

st.write("Ссылок найдено:", len(flat_links))
if flat_links:
    st.success("Объявления найдены")
    for link in flat_links[:10]:
        st.write(link)
else:
    st.warning("Объявления не найдены")
