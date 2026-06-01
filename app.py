import streamlit as st
import cianparser
import inspect

st.set_page_config(page_title="GRADOV SEARCH DEBUG", layout="wide")

st.title("GRADOV SEARCH — Диагностика cianparser")

st.subheader("Версия конструктора")

st.code(
    str(
        inspect.signature(
            cianparser.CianParser
        )
    )
)

st.subheader("Сигнатура get_flats()")

st.code(
    str(
        inspect.signature(
            cianparser.CianParser.get_flats
        )
    )
)

try:
    with open("proxies.txt", "r") as f:
        proxies = [x.strip() for x in f if x.strip()]

    st.success(f"Прокси загружено: {len(proxies)}")

except Exception as e:
    proxies = None
    st.error(f"Ошибка загрузки прокси: {e}")

if st.button("Создать парсер"):

    try:

        parser = cianparser.CianParser(
            location="Москва",
            proxies=proxies
        )

        st.success("Парсер успешно создан")

        st.write("Тип объекта:")
        st.code(str(type(parser)))

    except Exception as e:

        st.error(f"Ошибка создания парсера:\n{e}")

st.markdown("---")

st.subheader("Тест загрузки данных")

deal_type = st.selectbox(
    "Тип сделки",
    ["sale", "rent_long"]
)

rooms = st.multiselect(
    "Комнаты",
    [1, 2, 3, 4],
    default=[1]
)

if st.button("Получить объявления"):

    try:

        parser = cianparser.CianParser(
            location="Москва",
            proxies=proxies
        )

        st.write("Запрашиваем данные...")

        data = parser.get_flats(
            deal_type=deal_type,
            rooms=tuple(rooms)
        )

        st.success(f"Получено объектов: {len(data)}")

        if len(data) > 0:

            st.markdown("---")

            st.subheader("Полный JSON первого объекта")

            st.json(data[0])

            st.markdown("---")

            st.subheader("Все ключи первого объекта")

            st.write(sorted(data[0].keys()))

            st.markdown("---")

            st.subheader("Тип каждого поля")

            field_types = {}

            for k, v in data[0].items():
                field_types[k] = str(type(v))

            st.json(field_types)

        else:

            st.warning("Объекты не получены")

    except Exception as e:

        st.error(f"Ошибка:\n{e}")
