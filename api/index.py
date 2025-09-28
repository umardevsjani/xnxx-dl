# api/index.py
import random
import re
import urllib.parse
import httpx
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
}

DOMAIN_URL = "your-proxy-domain.com"  # apiConfig.DOMAIN_URL ka python version


class Downloader:
    def __init__(self):
        self.headers = HEADERS

    async def search(self, query: str):
        try:
            random_page = random.randint(1, 3)
            link = f"https://www.xnxx.com/search/{urllib.parse.quote(query)}/{random_page}"

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://{DOMAIN_URL}/api/tools/web/html/v1?url={urllib.parse.quote(link)}",
                    headers=self.headers,
                )
                html = resp.text

            soup = BeautifulSoup(html, "html.parser")
            videos = []
            for element in soup.select("div.thumb-block"):
                title_tag = element.select_one(".thumb-under a")
                if not title_tag:
                    continue
                video = {
                    "title": title_tag.get("title"),
                    "link": f"https://www.xnxx.com{title_tag.get('href')}",
                    "thumbnail": element.select_one(".thumb img")["src"]
                    if element.select_one(".thumb img")
                    else None,
                    "uploader": (element.select_one(".uploader a span") or {}).get_text(strip=True),
                    "views": (element.select_one(".metadata .right") or {}).get_text(strip=True).split(" ")[0],
                    "duration": (
                        (element.select_one(".metadata") or {}).get_text("\n").split("\n")[1]
                        if element.select_one(".metadata")
                        else "N/A"
                    ),
                }
                if video["link"] and "undefined" not in video["link"]:
                    videos.append(video)
            return videos
        except Exception as e:
            raise RuntimeError(f"Error fetching search results: {str(e)}")

    async def detail(self, url: str):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://{DOMAIN_URL}/api/tools/web/html/v1?url={urllib.parse.quote(url)}",
                    headers=self.headers,
                )
                html = resp.text

            soup = BeautifulSoup(html, "html.parser")
            title = soup.select_one('meta[property="og:title"]')["content"]
            duration = soup.select_one('meta[property="og:duration"]')
            duration = duration["content"] if duration else "N/A"
            image = soup.select_one('meta[property="og:image"]')["content"]
            info = (soup.select_one("span.metadata") or {}).get_text(strip=True)

            script_tag = soup.select_one("#video-player-bg > script:nth-child(6)")
            script_content = script_tag.get_text() if script_tag else ""

            def extract(pattern):
                match = re.search(pattern, script_content)
                return match.group(1) if match else None

            files = {
                "low": extract(r"html5player\.setVideoUrlLow\('(.*?)'\);"),
                "high": extract(r"html5player\.setVideoUrlHigh\('(.*?)'\);"),
                "hls": extract(r"html5player\.setVideoHLS\('(.*?)'\);"),
                "thumb": extract(r"html5player\.setThumbUrl\('(.*?)'\);"),
                "thumb_69": extract(r"html5player\.setThumbUrl169\('(.*?)'\);"),
                "slide": extract(r"html5player\.setThumbSlide\('(.*?)'\);"),
                "slide_big": extract(r"html5player\.setThumbSlideBig\('(.*?)'\);"),
            }

            return {
                "status": True,
                "title": title,
                "url": url,
                "duration": duration,
                "image": image,
                "info": info,
                "files": files,
            }
        except Exception as e:
            raise RuntimeError(f"Error fetching detail: {str(e)}")


@app.get("/")
async def handler(
    action: str = Query(None), query: str = Query(None), url: str = Query(None)
):
    if not action:
        return JSONResponse({"error": "Action is required"}, status_code=400)

    downloader = Downloader()
    try:
        if action == "search":
            if not query:
                return JSONResponse({"error": "Query is required for search"}, status_code=400)
            result = await downloader.search(query)
        elif action == "detail":
            if not url:
                return JSONResponse({"error": "URL is required for detail"}, status_code=400)
            result = await downloader.detail(url)
        else:
            return JSONResponse({"error": f"Invalid action: {action}"}, status_code=400)

        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
