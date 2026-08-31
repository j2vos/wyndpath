"""Scrape Vinted's catalog API (JSON, behind DataDome) through WyndPath.

    export WYNDPATH_API_KEY=wk_your_key
    python examples/vinted.py "coffret pokemon 151"
"""
import sys

from wyndpath import WyndPath

query = sys.argv[1] if len(sys.argv) > 1 else "nike"
wp = WyndPath()  # reads WYNDPATH_API_KEY

url = (
    "https://www.vinted.fr/api/v2/catalog/items"
    f"?search_text={query}&per_page=20&page=1&order=newest_first"
)
data = wp.get_json(url)

items = data.get("items", [])
print(f"{len(items)} listings for '{query}':\n")
for it in items:
    price = it.get("price", {})
    print(f"  {price.get('amount'):>7} {price.get('currency_code')}  {it.get('title')}")
