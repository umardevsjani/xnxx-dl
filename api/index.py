# api/index.py
import random
import re
import urllib.parse
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
}


class Downloader:
    async def search(self, query: str):
        try:
            random_page = random.randint(1, 3)
            url = f"https://www.xnxx.com/search/{urllib.parse.quote(query)}/{random_page}"

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=HEADERS)
                html = resp.text

            soup = BeautifulSoup(html, "html.parser")
            videos = []

            for element in soup.select("div.thumb-block"):
                title = element.select_one(".thumb-under a").get("title", "")
                link = "https://www.xnxx.com" + element.select_one(".thumb-under a").get("href", "")
                thumbnail = element.select_one(".thumb img").get("src", "")
                uploader = element.select_one(".uploader a span")
                views = element.select_one(".metadata .right")
                duration = element.select_one(".metadata")

                video = {
                    "title": title,
                    "link": link,
                    "thumbnail": thumbnail,
                    "uploader": uploader.text if uploader else "",
                    "views": views.text.strip().split(" ")[0] if views else "0",
                    "duration": duration.text.strip().split("\n")[1] if duration else "N/A"
                }

                if "undefined" not in video["link"]:
                    videos.append(video)

            return videos

        except Exception as e:
            raise Exception(f"Error fetching search: {str(e)}")

    async def detail(self, url: str):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=HEADERS)
                html = resp.text

            soup = BeautifulSoup(html, "html.parser")

            title = soup.select_one('meta[property="og:title"]')
            duration = soup.select_one('meta[property="og:duration"]')
            image = soup.select_one('meta[property="og:image"]')
            info = soup.select_one("span.metadata")

            script_content = ""
            script = soup.select_one("#video-player-bg > script:nth-child(6)")
            if script:
                script_content = script.text

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
                "title": title.get("content") if title else "",
                "url": url,
                "duration": duration.get("content") if duration else "N/A",
                "image": image.get("content") if image else "",
                "info": info.text.strip() if info else "",
                "files": files
            }

        except Exception as e:
            raise Exception(f"Error fetching detail: {str(e)}")


@app.api_route("/", methods=["GET", "POST"])
async def handler(request: Request):
    try:
        if request.method == "GET":
            params = dict(request.query_params)
        else:
            params = await request.json()

        action = params.get("action")
        query = params.get("query")
        url = params.get("url")

        if not action:
            return JSONResponse({"error": "Action is required"}, status_code=400)

        downloader = Downloader()
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
