import asyncio, platform, re
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
import httpx

async def check():
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
        urls = [
            "https://ddosecrets.com",
            "https://ddosecrets.com/wiki/Main_Page",
            "https://ddosecrets.com/wiki/Special:AllPages",
        ]
        for url in urls:
            try:
                r = await c.get(url, headers={"User-Agent": "Mozilla/5.0"})
                hrefs = re.findall(r'href="([^"]+)"', r.text)
                docs = re.findall(r'href="([^"]*\.(?:pdf|zip|7z|tar|gz|sql|csv))"', r.text, re.I)
                print(f"{url}: HTTP {r.status_code}, {len(r.text)}b, {len(hrefs)} hrefs, {len(docs)} docs")
                if docs:
                    for d in docs[:3]:
                        print(f"  DOC: {d}")
            except Exception as e:
                print(f"{url}: ERROR {e}")

asyncio.run(check())
