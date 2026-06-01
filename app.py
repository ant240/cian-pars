import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import cianparser

st.set_page_config(page_title="GRADOV SEARCH — Быстрый тест", layout="wide")
st.title("GRADOV SEARCH — Быстрый тест")
st.caption("Москва, однокомнатные квартиры, демонстрационный тест")

# ------------------ Функция парсинга дополнительной информации по объекту ------------------
def parse_extra(url):
    """Парсинг карточки объекта для дополнительных полей"""
    data = {}
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        # Примеры регулярок для ключевых полей
        match = re.search(r'Год постройки</.*?>(\d{4})', resp.text)
        data["build_year"] = int(match.group(1)) if match else None
        match = re.search(r'Тип дома</.*?>(.*?)<', resp.text)
        data["building_type"] = match.group(1).strip() if match else None
        match = re.search(r'До метро</.*?>(\d+)\s*мин', resp.text)
        data["time_to_metro"] = int(match.group(1)) if match else None
        match = re.search(r'Отделка</.*?>(.*?)<', resp.text)
        data["finish"] = match.group(1).strip() if match else None
        match = re.search(r'Высота потолков</.*?>([\d\.]+)', resp.text)
        data["ceiling_height"] = float(match.group(1)) if match else None
        match = re.search(r'Дата сдачи</.*?>(.*?)<', resp.text)
        data["completion_date"] = match.group(1).strip() if match else None
    except Exception as e:
        st.error(f"Ошибка парсинга {url}: {e}")
    return data

# ------------------ Быстрый тест GRADOV SEARCH ------------------
if st.button("Выполнить тест: 1-комнатные на Белорусской, 40-40млн"):
    st.info("Запуск теста...")
    # Инициализация парсера
    parser = cianparser.CianParser(location="Москва")
    try:
        # Берем однокомнатные квартиры
        flats = parser.get_flats(deal_type="sale", rooms=1)
    except TypeError:
        st.error("Ошибка: метод get_flats требует deal_type и rooms")
        flats = []

    # Фильтруем только Москва
    moscow_flats = [f for f in flats if f.get("location") == "Москва"]
    # Пример фильтрации по району и метро (Белорусская)
    test_flats = [
        f for f in moscow_flats
        if "Белорусская" in (f.get("underground") or "")
        and f.get("total_meters", 0) >= 40
        and f.get("price", 0) <= 40000000
    ]

    # Дополнительно парсим карточки для тестовых объектов
    for f in test_flats:
        extra = parse_extra(f["url"])
        f.update(extra)

    if not test_flats:
        st.warning("Нет объектов, удовлетворяющих условиям теста")
    else:
        df = pd.DataFrame(test_flats)
        st.success(f"Объектов найдено: {len(df)}")
        st.dataframe(df)

        # Проверка ошибок
        errors = df[df[["price","total_meters","street"]].isnull().any(axis=1)]
        if not errors.empty:
            st.error("Некорректные данные:")
            st.dataframe(errors)
        else:
            st.info("Все данные корректны")

# ------------------ Кнопка очистки ------------------
if st.button("Очистить результаты теста"):
    st.experimental_rerun()
