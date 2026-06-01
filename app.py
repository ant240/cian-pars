import streamlit as st
import pandas as pd
from cianparser import CianParser

st.set_page_config(
    page_title="GRADOV SEARCH DATA TEST",
    layout="wide"
)

st.title("GRADOV SEARCH")
st.subheader("Проверка качества данных")

# -------------------------
# ПАРСЕР
# -------------------------

parser = CianParser(location="Москва")

# -------------------------
# ЗАГРУЗКА
# -------------------------

@st.cache_data(ttl=3600)
def load_data():

    data = parser.get_flats(
        deal_type="sale",
        rooms=(1,),
        with_extra_data=True
    )

    return pd.DataFrame(data)

try:

    with st.spinner("Загрузка данных..."):

        df = load_data()

except Exception as e:

    st.error(str(e))
    st.stop()

# -------------------------
# ОБЩАЯ ИНФОРМАЦИЯ
# -------------------------

st.success(f"Получено объектов: {len(df)}")

st.write("Колонки:")

st.write(list(df.columns))

# -------------------------
# ПЕРВЫЕ ОБЪЕКТЫ
# -------------------------

st.subheader("Первые объекты")

st.dataframe(df.head(20), width="stretch")

# -------------------------
# ГОРОДА
# -------------------------

st.subheader("Уникальные location")

locations = (
    df["location"]
    .fillna("")
    .astype(str)
    .str.strip()
    .unique()
)

locations = sorted(locations)

st.write(locations)

# -------------------------
# РАЙОНЫ
# -------------------------

st.subheader("Уникальные районы")

districts = (
    df["district"]
    .fillna("")
    .astype(str)
    .str.strip()
    .unique()
)

districts = sorted(districts)

st.write(districts)

# -------------------------
# МЕТРО
# -------------------------

st.subheader("Уникальные станции метро")

metro = (
    df["underground"]
    .fillna("")
    .astype(str)
    .str.strip()
    .unique()
)

metro = sorted(metro)

st.write(metro)

# -------------------------
# ПРОВЕРКА МОСКВЫ
# -------------------------

st.subheader("Проверка Москвы")

moscow_keywords = [
    "Москва",
    "Аэропорт",
    "Хамовники",
    "Арбат",
    "Якиманка",
    "Раменки",
    "Тверской",
    "Пресненский",
    "Дорогомилово",
    "Алексеевский",
    "Савеловский"
]

def is_moscow(row):

    text = " ".join([
        str(row.get("location", "")),
        str(row.get("district", "")),
        str(row.get("street", "")),
        str(row.get("underground", "")),
        str(row.get("residential_complex", ""))
    ])

    text = text.lower()

    return any(
        k.lower() in text
        for k in moscow_keywords
    )

df["is_moscow"] = df.apply(is_moscow, axis=1)

moscow_df = df[df["is_moscow"]]

non_moscow_df = df[~df["is_moscow"]]

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Похоже на Москву",
        len(moscow_df)
    )

with col2:
    st.metric(
        "Не похоже на Москву",
        len(non_moscow_df)
    )

# -------------------------
# ПРОБЛЕМНЫЕ ОБЪЕКТЫ
# -------------------------

st.subheader("Подозрительные объекты")

if len(non_moscow_df):

    st.dataframe(
        non_moscow_df[
            [
                "location",
                "district",
                "street",
                "house_number",
                "underground",
                "price",
                "url"
            ]
        ],
        width="stretch"
    )

else:

    st.success("Посторонних регионов не найдено")

# -------------------------
# ПРОПУЩЕННЫЕ ПОЛЯ
# -------------------------

st.subheader("Заполненность данных")

quality = []

for col in df.columns:

    filled = df[col].notna().sum()

    quality.append({
        "Поле": col,
        "Заполнено": filled,
        "Всего": len(df),
        "%": round(
            filled / len(df) * 100,
            1
        )
    })

quality_df = pd.DataFrame(quality)

st.dataframe(
    quality_df.sort_values("%"),
    width="stretch"
)

# -------------------------
# ЦЕНА ЗА М2
# -------------------------

if (
    "price" in df.columns
    and
    "total_meters" in df.columns
):

    df["price_per_m2"] = (
        df["price"]
        /
        df["total_meters"]
    )

    st.subheader("Цена за м²")

    st.dataframe(
        df[
            [
                "district",
                "street",
                "price",
                "total_meters",
                "price_per_m2"
            ]
        ],
        width="stretch"
    )

# -------------------------
# ЭКСПОРТ
# -------------------------

csv = df.to_csv(index=False)

st.download_button(
    "Скачать CSV",
    csv,
    "gradov_data_test.csv",
    "text/csv"
)
