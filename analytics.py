import pandas as pd
import altair as alt

def evaluate_apartment(card: dict):
    """
    Возвращает скоринг и рекомендованную цену для продажи
    """
    base_score = 50
    if card.get("total_meters"):
        if card["total_meters"]>50: base_score += 10
        else: base_score += 5
    if card.get("floor"):
        base_score += int(card["floor"]/10)
    recommended_price = card.get("price",0)*1.05  # +5%
    return base_score, recommended_price

def plot_price_history(card: dict):
    """
    Мини-график для истории цен
    """
    history = card.get("price_history", [])
    if not history:
        history = [{"date":"2024-01","price":card.get("price",0)}]
    df = pd.DataFrame(history)
    chart = alt.Chart(df).mark_line(point=True).encode(
        x="date:T",
        y="price:Q"
    ).properties(
        title="История цены объекта"
    )
    return chart
