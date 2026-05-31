import requests
import os
import random
from concurrent.futures import ThreadPoolExecutor

TEST_URL = "https://api.ipify.org?format=json"

def load_proxies():
    with open("proxies.txt", "r") as f:
        return [x.strip() for x in f if x.strip()]

def test_proxy(proxy):
    try:
        r = requests.get(
            TEST_URL,
            proxies={
                "http": proxy,
                "https": proxy
            },
            timeout=15
        )

        return {
            "proxy": proxy,
            "status": r.status_code,
            "ip": r.text
        }

    except Exception as e:
        return {
            "proxy": proxy,
            "error": str(e)
        }

proxies = load_proxies()

sample = random.sample(
    proxies,
    min(50, len(proxies))
)

with ThreadPoolExecutor(max_workers=10) as pool:
    results = list(pool.map(test_proxy, sample))

working = []
failed = []

for r in results:

    if "status" in r:
        working.append(r)

    else:
        failed.append(r)

print()
print("=" * 50)
print("WORKING:", len(working))
print("FAILED :", len(failed))
print("=" * 50)

for w in working[:10]:
    print("OK:", w["ip"])

for f in failed[:10]:
    print("ERR:", f["error"])
