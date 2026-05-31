import streamlit as st
import requests
import random
import os

st.title("Проверка 20 прокси")

def load_proxies():
    with open("proxies.txt", "r") as f:
        return [x.strip() for x in f if x.strip()]

proxies = load_proxies()

st.write("Всего прокси:", len(proxies))

if st.button("Проверить 20 прокси"):

    sample = random.sample(
        proxies,
        min(20, len(proxies))
    )

    working = 0
    failed = 0

    for i, proxy in enumerate(sample):

        try:

            r = requests.get(
                "https://api.ipify.org?format=json",
                proxies={
                    "http": proxy,
                    "https": proxy
                },
                timeout=10
            )

            st.success(
                f"{i+1}. OK {r.status_code}"
            )

            working += 1

        except Exception as e:

            st.error(
                f"{i+1}. FAIL"
            )

            st.code(str(e))

            failed += 1

    st.write("---")
    st.write("Рабочих:", working)
    st.write("Не рабочих:", failed)
