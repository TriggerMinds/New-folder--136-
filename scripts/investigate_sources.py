"""Investigate actual HTML of primary_raw source URLs."""
import asyncio, platform, re
if platform.system() == "Windows":
    import asyncio as _a
    _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())

import httpx

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


async def check_url(label, url, timeout=15):
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT})
            text = resp.text
            hrefs = re.findall(r'href="([^"]+)"', text)
            doc_links = re.findall(r'href="([^"]*\.(?:pdf|docx?|xlsx?|zip|7z|gz|tar|eml|mbox|sql|csv|json|xml))"', text, re.I)
            print(f"\n=== {label} ===")
            print(f"  HTTP {resp.status_code}, {len(text)} bytes, {len(hrefs)} hrefs, {len(doc_links)} document links")
            for doc in doc_links[:5]:
                print(f"  DOC: {doc}")
            if "class=\"" in text or "id=\"" in text:
                print(f"  Has CSS classes/IDs (structured HTML)")
            if "Index of" in text or "Parent Directory" in text:
                print(f"  *** DIRECTORY LISTING DETECTED ***")
    except Exception as e:
        print(f"\n=== {label} ===")
        print(f"  ERROR: {e}")


async def main():
    await check_url("Cryptome.org", "https://cryptome.org/")
    await check_url("DDoSecrets AllPages", "https://ddosecrets.com/wiki/Special:AllPages")
    await check_url("Archive.org search", "https://archive.org/search?query=Netherlands+AND+leak&sort=-publicdate")
    await check_url("GitHub search repos", "https://github.com/search?q=Netherlands+leak+classified&type=repositories&s=updated")
    await check_url("Pastebin archive", "https://pastebin.com/archive")
    await check_url("WikiLeaks Leaks", "https://wikileaks.org/-Leaks-.html")

asyncio.run(main())
