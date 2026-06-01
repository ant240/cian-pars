import streamlit as st
from cianparser import CianParser  # твой рабочий форк

st.title("GRADOV SEARCH — Проверка ключей объектов")

# Загружаем прокси
try:
    with open("proxies.txt", "r") as f:
        proxies = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    proxies = []
    st.error("Файл proxies.txt не найден")

# Кнопка создания парсера
if st.button("Создать парсер и загрузить данные"):
    parser = CianParser(location="Москва", proxies=proxies)
    st.success("Парсер создан")
    
    # Получаем список объектов
    data = parser.get_flats()  # вернёт список словарей
    if not data:
        st.warning("Нет данных. Попробуйте другой прокси или другой фильтр")
    else:
        st.info(f"Всего объектов получено: {len(data)}")
        
        # Показываем полный JSON первого объекта
        st.subheader("Пример полного объекта (первый элемент)")
        st.json(data[0])
        
        # Список всех ключей для удобства
        st.subheader("Все ключи первого объекта")
        st.write(list(data[0].keys()))
