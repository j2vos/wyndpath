"""Fetch a login-protected CardMarket page through WyndPath.

WyndPath logs in for you with the credentials you set once in your console (Targets).
The first call before you add them raises LoginRequired.

    export WYNDPATH_API_KEY=wk_your_key
    python examples/cardmarket.py
"""
from wyndpath import WyndPath, LoginRequired

wp = WyndPath()

url = ("https://www.cardmarket.com/en/Pokemon/Products/Singles/"
       "Celebrations/Pikachu-V-Union")

try:
    r = wp.fetch(url, render_js=True, country="fr")
    logged_in = "My Account" in r.text or "Mon compte" in r.text
    print(f"status={r.status} engine={r.engine} credits={r.credits} "
          f"bytes={len(r.text)} logged_in={logged_in}")
except LoginRequired as e:
    print("Add your CardMarket credentials in the console (Targets), then retry.")
    print("Needed:", [n.get("key") for n in e.payload.get("needs", [])])
