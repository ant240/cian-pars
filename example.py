"""
Пример использования cianparser для парсинга новостроек
Этот файл демонстрирует базовое использование библиотеки cianparser
"""

import cianparser
import pandas as pd

def example_parse():
    """Пример парсинга новостроек"""

    # Создаем парсер для Москвы
    parser = cianparser.CianParser(location="Москва")

    # Настройки парсинга
    additional_settings = {
        "start_page": 1,
        "end_page": 2  # Парсим только 2 страницы для примера
    }

    print("Начинаем парсинг...")

    # Парсим квартиры в новостройках на продажу
    data = parser.get_flats(
        deal_type="sale",  # Продажа
        rooms=(1, 2, 3),   # 1, 2 и 3-комнатные квартиры
        additional_settings=additional_settings
    )

    # Преобразуем в DataFrame для удобной работы
    df = pd.DataFrame(data)

    # Вычисляем цену за кв.м
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['total_meters'] = pd.to_numeric(df['total_meters'], errors='coerce')
    df['price_per_sqm'] = (df['price'] / df['total_meters']).round(2)

    # Удаляем строки с некорректными данными
    df = df.dropna(subset=['price', 'total_meters', 'price_per_sqm'])

    # Сортируем по цене за кв.м
    df_sorted = df.sort_values(by='price_per_sqm', ascending=True)

    print(f"\nНайдено {len(df)} объявлений")
    print(f"\nТоп-5 самых дешевых по цене за кв.м:")
    print(df_sorted[['residential_complex', 'rooms', 'total_meters', 'price', 'price_per_sqm']].head())

    # Сохраняем в CSV
    df_sorted.to_csv('newbuildings.csv', index=False, encoding='utf-8-sig')
    print("\nДанные сохранены в newbuildings.csv")

    return df_sorted

if __name__ == "__main__":
    example_parse()
