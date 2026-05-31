import streamlit as st
import pandas as pd
import cianparser
from datetime import datetime
import time
import random
import os
from typing import List, Dict, Any, Optional

# ------------------- НАСТРОЙКИ СТРАНИЦЫ -------------------
st.set_page_config(page_title="Аналитика недвижимости", layout="wide")
st.title("🏠 Аналитика недвижимости (Циан + Авито)")
st.markdown("---")

# Скрываем стандартные элементы Streamlit
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Инициализация сессии
if 'data' not in st.session_state:
    st.session_state.data = None
if 'parsing_done' not in st.session_state:
    st.session_state.parsing_done = False

# ------------------- ФУНКЦИЯ ЗАГРУЗКИ ПРОКСИ ИЗ ФАЙЛА -------------------
def load_proxies_from_file(filename: str = "proxies.txt") -> Optional[List[str]]:
    """Загружает прокси из файла (каждая строка - один прокси)"""
    if not os.path.exists(filename):
        return None
    with open(filename, 'r', encoding='utf-8') as f:
        proxies = [line.strip() for line in f if line.strip()]
    return proxies if proxies else None

# ------------------- БОКОВАЯ ПАНЕЛЬ -------------------
with st.sidebar:
    st.header("⚙️ Настройки поиска")
    city = st.text_input("Город", value="Москва")
    rooms = st.multiselect("Количество комнат", [1,2,3,4,5,6], default=[1,2,3])
    
    st.subheader("⚙️ Промышленный парсинг")
    st.markdown("""
    **Автоматический сбор ВСЕХ объявлений** (до последней страницы).
    Для защиты от блокировок используйте прокси.
    """)
    
    # Загрузка прокси
    auto_proxies = load_proxies_from_file("proxies.txt")
    if auto_proxies:
        st.success(f"✅ Загружено {len(auto_proxies)} прокси из файла proxies.txt")
        use_proxy = True
        proxy_pool = auto_proxies
    else:
        st.info("Файл proxies.txt не найден. Можно ввести прокси вручную или работать без них (риск блокировки).")
        use_proxy = st.checkbox("Использовать прокси (обход блокировок)", value=False)
        proxy_list_input = st.text_area(
            "Список прокси (по одному в строке)",
            placeholder="http://user:pass@ip:port\nhttp://user:pass@ip:port",
            help="Каждый прокси с новой строки в формате http://логин:пароль@хост:порт"
        )
        if use_proxy and proxy_list_input:
            proxy_pool = [p.strip() for p in proxy_list_input.split('\n') if p.strip()]
        else:
            proxy_pool = None
    
    st.subheader("Предварительные фильтры (до парсинга)")
    min_price = st.number_input("Мин. цена (₽)", min_value=0, value=0, step=100000)
    max_price = st.number_input("Макс. цена (₽)", min_value=0, value=0, step=100000)
    min_area = st.number_input("Мин. площадь (м²)", min_value=0.0, value=0.0, step=5.0)
    max_area = st.number_input("Макс. площадь (м²)", min_value=0.0, value=0.0, step=5.0)
    
    st.subheader("Спецопции (поиск в описании)")
    is_penthouse = st.checkbox("🏢 Пентхаус")
    has_terrace = st.checkbox("🌿 Терраса / балкон")
    
    parse_button = st.button("🚀 Начать парсинг ВСЕХ страниц", type="primary")

# ------------------- ФУНКЦИИ ПАРСИНГА -------------------
def get_proxied_parser(base_parser: cianparser.CianParser, proxy: str) -> cianparser.CianParser:
    """Создаёт новый экземпляр парсера с указанным прокси"""
    return cianparser.CianParser(
        location=base_parser.location,
        proxies={"http": proxy, "https": proxy}
    )

def parse_page_with_retry(base_parser: cianparser.CianParser,
                          page_num: int,
                          proxy_list: Optional[List[str]],
                          rooms_list: List[int],
                          max_retries: int = 3) -> Optional[List[Dict[str, Any]]]:
    """Парсит одну страницу, перебирая прокси при ошибках"""
    for attempt in range(max_retries):
        try:
            current_proxy = random.choice(proxy_list) if proxy_list else None
            if current_proxy:
                parser = get_proxied_parser(base_parser, current_proxy)
            else:
                parser = base_parser
            
            # Случайная задержка (имитация человека)
            time.sleep(random.uniform(1.0, 2.5))
            
            data = parser.get_flats(
                deal_type="sale",
                rooms=tuple(rooms_list),
                additional_settings={"start_page": page_num, "end_page": page_num}
            )
            if data and len(data) > 0:
                return data
            else:
                if current_proxy:
                    st.warning(f"Страница {page_num}: нет данных. Пробуем другой прокси...")
                else:
                    st.warning(f"Страница {page_num}: нет данных.")
        except Exception as e:
            if current_proxy:
                st.warning(f"Ошибка с прокси {current_proxy[:50]}... Попытка {attempt+1}/{max_retries}")
            else:
                st.warning(f"Ошибка на странице {page_num}: {str(e)[:100]}")
            time.sleep(2)
    return None

def process_data(df: pd.DataFrame, penthouse: bool, terrace: bool) -> pd.DataFrame:
    """Очистка данных, расчёт цены за м², фильтр по ключевым словам"""
    if df is None or len(df) == 0:
        return None
    # Преобразование числовых колонок
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
    if 'total_meters' in df.columns:
        df['total_meters'] = pd.to_numeric(df['total_meters'], errors='coerce')
    df = df.dropna(subset=['price', 'total_meters'])
    df = df[(df['price'] > 0) & (df['total_meters'] > 0)]
    if len(df) == 0:
        return None
    df['price_per_sqm'] = (df['price'] / df['total_meters']).round(2)
    
    # Фильтр по описанию
    if 'description' in df.columns:
        if penthouse:
            df = df[df['description'].str.contains('пентхаус|penthouse', case=False, na=False)]
        if terrace:
            df = df[df['description'].str.contains('террас|балкон|лоджи', case=False, na=False)]
    return df

# ------------------- ОСНОВНОЙ БЛОК ПАРСИНГА -------------------
if parse_button:
    if not rooms:
        st.error("Выберите хотя бы одно количество комнат!")
        st.stop()
    
    base_parser = cianparser.CianParser(location=city)
    all_data = []
    page = 1
    max_pages = 200  # безопасный лимит (ЦИАН редко даёт больше 54 страниц)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while page <= max_pages:
        status_text.text(f"Парсинг страницы {page}...")
        page_data = parse_page_with_retry(base_parser, page, proxy_pool, rooms)
        if page_data is None or len(page_data) == 0:
            status_text.text(f"⛔ Данные на странице {page} не найдены. Парсинг завершён.")
            break
        all_data.extend(page_data)
        progress_bar.progress(min(1.0, page / 100))
        page += 1
    
    if all_data:
        df_raw = pd.DataFrame(all_data)
        df_processed = process_data(df_raw, is_penthouse, has_terrace)
        if df_processed is not None and len(df_processed) > 0:
            # Применяем предварительные фильтры (цена/площадь)
            if min_price > 0:
                df_processed = df_processed[df_processed['price'] >= min_price]
            if max_price > 0:
                df_processed = df_processed[df_processed['price'] <= max_price]
            if min_area > 0:
                df_processed = df_processed[df_processed['total_meters'] >= min_area]
            if max_area > 0:
                df_processed = df_processed[df_processed['total_meters'] <= max_area]
            
            if len(df_processed) > 0:
                st.session_state.data = df_processed
                st.session_state.parsing_done = True
                st.success(f"✅ Парсинг завершён! Собрано {len(df_processed)} объявлений.")
            else:
                st.warning("После предварительных фильтров не осталось объявлений.")
        else:
            st.warning("Не удалось получить данные с корректной ценой/площадью или по спецопциям.")
    else:
        st.warning("Не удалось получить данные. Проверьте прокси или параметры поиска.")

# ------------------- ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ И ДИНАМИЧЕСКИЕ ФИЛЬТРЫ -------------------
if st.session_state.parsing_done and st.session_state.data is not None:
    df = st.session_state.data.copy()
    st.markdown("---")
    st.header("📊 Результаты парсинга")
    
    # Статистика
    col1, col2, col3 = st.columns(3)
    col1.metric("Всего объявлений", len(df))
    col2.metric("Средняя цена", f"{df['price'].mean():,.0f} ₽")
    col3.metric("Средняя цена за м²", f"{df['price_per_sqm'].mean():,.0f} ₽")
    
    st.markdown("---")
    st.subheader("🔍 Уточняющие фильтры (после парсинга)")
    
    # Фильтр по цене
    if df['price'].min() < df['price'].max():
        price_range = st.slider("Цена (₽)", float(df['price'].min()), float(df['price'].max()),
                                (float(df['price'].min()), float(df['price'].max())))
        df = df[(df['price'] >= price_range[0]) & (df['price'] <= price_range[1])]
    
    # Фильтр по площади
    if df['total_meters'].min() < df['total_meters'].max():
        area_range = st.slider("Площадь (м²)", float(df['total_meters'].min()), float(df['total_meters'].max()),
                               (float(df['total_meters'].min()), float(df['total_meters'].max())))
        df = df[(df['total_meters'] >= area_range[0]) & (df['total_meters'] <= area_range[1])]
    
    # Фильтр по цене за м²
    if df['price_per_sqm'].min() < df['price_per_sqm'].max():
        sqm_range = st.slider("Цена за м² (₽)", float(df['price_per_sqm'].min()), float(df['price_per_sqm'].max()),
                              (float(df['price_per_sqm'].min()), float(df['price_per_sqm'].max())))
        df = df[(df['price_per_sqm'] >= sqm_range[0]) & (df['price_per_sqm'] <= sqm_range[1])]
    
    # Фильтр по району (динамический)
    if 'district' in df.columns and not df['district'].isnull().all():
        districts = sorted(df['district'].dropna().unique())
        if districts:
            selected_districts = st.multiselect("Район (можно несколько)", districts)
            if selected_districts:
                df = df[df['district'].isin(selected_districts)]
    
    # Фильтр по метро
    if 'underground' in df.columns and not df['underground'].isnull().all():
        metros = sorted(df['underground'].dropna().unique())
        if metros:
            selected_metros = st.multiselect("Метро", metros)
            if selected_metros:
                df = df[df['underground'].isin(selected_metros)]
    
    # Фильтр по этажу
    if 'floor' in df.columns and not df['floor'].isnull().all():
        floor_min, floor_max = int(df['floor'].min()), int(df['floor'].max())
        if floor_min != floor_max:
            floor_range = st.slider("Этаж", floor_min, floor_max, (floor_min, floor_max))
            df = df[(df['floor'] >= floor_range[0]) & (df['floor'] <= floor_range[1])]
    
    # Сортировка
    st.subheader("📈 Сортировка")
    sort_by = st.selectbox("Сортировать по",
                          ['price_per_sqm', 'price', 'total_meters', 'rooms'],
                          format_func=lambda x: {'price_per_sqm':'Цена за м²','price':'Цена','total_meters':'Площадь','rooms':'Комнаты'}[x])
    sort_order = st.radio("Порядок", ['По возрастанию', 'По убыванию'], horizontal=True)
    df = df.sort_values(by=sort_by, ascending=(sort_order == 'По возрастанию'))
    
    st.info(f"📌 Показано {len(df)} объявлений после всех фильтров")
    
    # Отображение таблицы (доступные колонки)
    display_cols = []
    rename_map = {}
    for col, name in [('residential_complex','ЖК'), ('rooms','Комнат'), ('total_meters','Площадь (м²)'),
                      ('price','Цена (₽)'), ('price_per_sqm','Цена за м² (₽)'), ('floor','Этаж'),
                      ('district','Район'), ('underground','Метро'), ('url','Ссылка')]:
        if col in df.columns:
            display_cols.append(col)
            rename_map[col] = name
    if display_cols:
        df_display = df[display_cols].copy().rename(columns=rename_map)
        # Форматирование чисел
        for col in ['Цена (₽)', 'Цена за м² (₽)']:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "")
        if 'Площадь (м²)' in df_display.columns:
            df_display['Площадь (м²)'] = df_display['Площадь (м²)'].apply(lambda x: f"{x:.1f}")
        st.dataframe(df_display, use_container_width=True, height=500)
    else:
        st.dataframe(df, use_container_width=True)
    
    # Экспорт
    st.markdown("---")
    st.subheader("💾 Экспорт данных")
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("📥 Скачать CSV", csv_data,
                       file_name=f"real_estate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                       mime="text/csv")
else:
    if not st.session_state.parsing_done:
        st.info("👈 Настройте параметры и нажмите «Начать парсинг ВСЕХ страниц».")

st.markdown("---")
st.caption("Промышленный парсинг ЦИАН с автоматической ротацией прокси. Пентхаусы/террасы фильтруются по описанию.")
