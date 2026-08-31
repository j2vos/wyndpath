# WyndPath — Python client

**WyndPath is a Europe-hosted web scraping & anti-bot API.** You send a URL, WyndPath
picks the right path — plain HTTP or a real browser engine — gets past protections like
**Cloudflare** and **DataDome**, and returns the response. JSON endpoints come back as
**clean JSON**. You are billed **only on success**.

- 🌍 Hosted in the EU (GDPR-friendly), exit from residential or datacenter IPs, choose the country.
- 🛡️ Real browser engines + fingerprint/session handling to pass Cloudflare & DataDome.
- 🔁 Sticky sessions and logins handled **automatically per target** — nothing to wire client-side.
- 💳 **Pay-per-success**: a blocked request costs zero credits.
- 📦 Official Python client (this repo). Language-agnostic HTTP API underneath.

Website & console: **https://console.wyndpath.com** · Docs: **https://console.wyndpath.com/docs** · Guides: **https://console.wyndpath.com/scraper**

---

## Install

```bash
pip install wyndpath
```

## Quickstart

```python
from wyndpath import WyndPath

wp = WyndPath("wk_your_key")          # or set WYNDPATH_API_KEY

# A protected HTML page (Cloudflare, JS): render with a real browser, exit from France
r = wp.fetch("https://example.com/", render_js=True, country="fr")
print(r.status, r.engine, r.credits)  # 200 flaresolverr 10
print(r.text[:200])
```

## Scrape Vinted (JSON API, behind DataDome)

Vinted's catalog API is protected by DataDome and needs a valid anti-bot session.
WyndPath establishes and replays that session for you — you just call the endpoint and
get JSON back:

```python
from wyndpath import WyndPath

wp = WyndPath("wk_your_key")
data = wp.get_json(
    "https://www.vinted.fr/api/v2/catalog/items"
    "?search_text=nike&per_page=96&page=1"
)
for item in data["items"]:
    print(item["title"], item["price"]["amount"], item["price"]["currency_code"])
```

No cookies, no anti-bot token, no browser to manage: WyndPath returns the raw
`application/json`, ready for `resp.json()`.

## Scrape CardMarket (login-protected pages)

Some targets need a logged-in session. WyndPath does the login for you using **your own
credentials**, which you enter **once** in your console (Targets). After that, requests
just work:

```python
from wyndpath import WyndPath, LoginRequired

wp = WyndPath("wk_your_key")
try:
    r = wp.fetch(
        "https://www.cardmarket.com/en/Pokemon/Products/Singles/Celebrations/Pikachu-V-Union",
        render_js=True, country="fr",
    )
    print(r.status, "logged-in page:", len(r.text), "bytes")
except LoginRequired as e:
    # First time only: add your credentials in the console, then retry.
    print("Provide credentials in your console:", e.payload.get("needs"))
```

## Error handling

WyndPath maps failures to typed exceptions:

```python
from wyndpath import WyndPath, QuotaExceeded, LoginRequired, TooManyConcurrent, TargetBlocked

wp = WyndPath("wk_your_key")
try:
    data = wp.get_json("https://www.vinted.fr/api/v2/catalog/items?search_text=lego")
except QuotaExceeded as e:
    print("Monthly quota reached:", e.payload["used"], "/", e.payload["limit"])
except LoginRequired as e:
    print("This target needs credentials:", e.payload["needs"])
except TooManyConcurrent:
    print("Slow down or add capacity / logins")
except TargetBlocked as e:
    # WyndPath will study & configure this target automatically (nightly), retry later
    print("Not reachable yet:", e.payload.get("study_hint"))
```

| HTTP | Exception | Meaning |
|-----|-----------|---------|
| 401 | `InvalidApiKey` | key missing/invalid |
| 402 | `QuotaExceeded` | monthly credits reached |
| 428 | `LoginRequired` | target needs your credentials (enter once in console) |
| 429 | `TooManyConcurrent` | too many parallel requests for your plan |
| 502 | `TargetBlocked` | not fetched yet; WyndPath studies it automatically, retry later |

## How it works

WyndPath tries the cheapest path first and escalates only if needed:

```
your URL ──▶ WyndPath ──▶ light HTTP  ─┐
                          browser (FlareSolverr / nodriver / trawl)
                          + residential / datacenter IP, chosen country
                                        └─▶ Cloudflare / DataDome passed ─▶ response
```

- **Sessions & logins are managed per target.** For a JSON API that needs an anti-bot
  session (Vinted) or a login (CardMarket), WyndPath handles the handshake and replays
  the session from a stable IP — transparently.
- **Self-healing targets.** If a target isn't configured yet, WyndPath registers it,
  analyses it automatically (which engine/IP passes), configures it, and emails you when
  it's ready — so a call that fails today gives a positive result tomorrow.

## Real-world benchmark (Vinted / DataDome)

An independent test of **96 consecutive real calls** to Vinted's `catalog/items`:

| Metric | Result |
|-------|--------|
| Success rate | **96 / 96 (100 %)** |
| Avg. latency (warm session) | **~3.06 s** |
| Results per call | **96 listings** |
| Cost | **10 credits / success** |
| Plain HTTP (no browser), datacenter **and** residential | **0 %** |
| Browser engine, datacenter | **100 %** |

Takeaway: on DataDome, a residential proxy alone is not enough — the browser
identity / fingerprint / challenge handling is what makes the difference, and that's
exactly what WyndPath does. 3 seconds at 100 % beats 500 ms with random 403/429.

## Supported targets (examples)

Vinted, CardMarket, LeBonCoin, Amazon, eBay, Fnac, Cdiscount, ManoMano, Rakuten,
SeLoger, Booking, Indeed, PagesJaunes… and any other site (unknown targets are analysed
and configured automatically). Per-target guides: https://console.wyndpath.com/scraper

## License

MIT © Jérémy D. — see [LICENSE](LICENSE).
