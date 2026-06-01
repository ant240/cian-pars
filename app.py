import streamlit as st
import pandas as pd
import cianparser
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="GRADOV SEARCH — Тест", layout="wide")
st.title("GRADOV SEARCH — Быстрый тест")
st.caption("Москва, 1-комнатные квартиры, быстрый тест данных")

# ---------- Быстрый тест ----------
if st.button("🚀 Запустить тест"):
    try:
        parser = cianparser.CianParser(location="Москва")
        # Берём только первую страницу, однушки
        flats = parser.get_flats(
            deal_type="sale",
            rooms=(1,),
            additional_settings={"start_page":1, "end_page":1}
        )
        if not flats:
            st.warning("Объекты не найдены")
            st.stop()
        df = pd.DataFrame(flats)
        # Оставляем только объекты с корректной ценой и площадью
        df = df[df["price"] > 0]
        df = df[df["total_meters"] > 0]

        # ---------- Дополнительный парсер карточки ----------
        def parse_extra(url):
            try:
                resp = requests.get(url, timeout=10)
                soup = BeautifulSoup(resp.text, "html.parser")
                data = {}
                # Пример поиска данных по ключевым шаблонам
                # Год постройки
                match = re.search(r'Год постройки</.*?>(\d{4})', resp.text)
                if match: data["build_year"] = int(match.group(1))
                # Тип дома
                match = re.search(r'Тип дома</.*?>(.*?)<', resp.text)
                if match: data["building_type"] = match.group(1).strip()
                # Время до метро
                match = re.search(r'До метро</.*?>(\d+)\s*мин', resp.text)
                if match: data["time_to_metro"] = int(match.group(1))
                # Отделка
                match = re.search(r'Отделка</.*?>(.*?)<', resp.text)
                if match: data["finishing"] = match.group(1).strip()
                # Высота потолков
                match = re.search(r'Высота потолков</.*?>([\d,\.]+)', resp.text)
                if match: data["ceiling_height"] = float(match.group(1).replace(",","."))
                # Дата сдачи
                match = re.search(r'Срок сдачи</.*?>(.*?)<', resp.text)
                if match: data["completion_date"] = match.group(1).strip()
                return data
            except:
                return {}

        # Добавляем новые поля
        extra_data_list = []
        for url in df["url"].head(10):  # для теста только первые 10 объектов
            extra_data_list.append(parse_extra(url))
        extra_df = pd.DataFrame(extra_data_list)
        df = pd.concat([df.reset_index(drop=True), extra_df.reset_index(drop=True)], axis=1)

        # Цена за квадратный метр
        df["price_m2"] = (df["price"] / df["total_meters"]).round()

        # ---------- Вывод ----------
        st.success(f"Найдено {len(df)} объектов Москвы")
        st.dataframe(df, width="stretch")

    except Exception as e:
        st.error(f"Ошибка: {e}")
