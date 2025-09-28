from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
import random
import os
from urllib.parse import quote

app = FastAPI()

class Downloader:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
        }
        # Replace with your actual API domain or remove if not needed
        self.api_domain = os.getenv("DOMAIN_URL", "https://xnxx-dl.vercel.app")

    async def search(self, query: str):
        try:
            random_page = random.randint(1, 3)
            encoded_query = quote(query)
            link = f"https://www.xnxx.com/search/{encoded_query}/{random_page}"
            encoded_url = quote(link)
            response = requests.get(f"https://{self.api_domain}/api/tools/web/html/v1?url={encoded_url}", headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            videos = []

            for element in soup.select("div.thumb-block"):
                video = {
                    "title": element.select_one(".thumb-under a").get("title", ""),
                    "link": f"https://www.xnxx.com{element.select_one('.thumb-under a').get('href', '')}",
                    "thumbnail": element.select_one(".thumb img").get("src", ""),
                    "uploader": element.select_one(".uploader a span").text if element.select_one(".uploader a span") else "",
                    "views": element.select_one(".metadata .right").text.strip().split(" ")[0] if element.select_one(".metadata .right") else "",
                    "duration": element.select_one(".metadata").text.strip().split("\n")[1] if len(element.select_one(".metadata").text.strip().split("\n")) > 1 else "N/A"
                }
                if video["link"] and "undefined" not in video["link"]:
                    videos.append(video)

            return videos
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

    async def detail(self, url: str):
        try:
            encoded_url = quote(url)
            response = requests.get(f"https://{self.api_domain}/api/tools/web/html/v1?url={encoded_url}", headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            title = soup.select_one('meta[property="og:title"]').get("content", "") if soup.select_one('meta[property="og:title"]') else ""
            duration = soup.select_one('meta[property="og:duration"]').get("content", "N/A") if soup.select_one('meta[property="og:duration"]') else "N/A"
            image = soup.select_one('meta[property="og:image"]').get("content", "") if soup.select_one('meta[property="og:image"]') else ""
            info = soup.select_one("span.metadata").text.strip() if soup.select_one("span.metadata") else ""

            script_content = soup.select_one("#video-player-bg > script:nth-child(6)")
            script_text = script_content.text if script_content else ""

            files = {
                "low": (script_text.split("html5player.setVideoUrlLow('")[1].split("');")[0] if "html5player.setVideoUrlLow('" in script_text else ""),
                "high": (script_text.split("html5player.setVideoUrlHigh('")[1].split("');")[0] if "html5player.setVideoUrlHigh('" in script_text else ""),
                "hls": (script_text.split("html5player.setVideoHLS('")[1].split("');")[0] if "html5player.setVideoHLS('" in script_text else ""),
                "thumb": (script_text.split("html5player.setThumbUrl('")[1].split("');")[0] if "html5player.setThumbUrl('" in script_text else ""),
                "thumb_69": (script_text.split("html5player.setThumbUrl169('")[1].split("');")[0] if "html5player.setThumbUrl169('" in script_text else ""),
                "slide": (script_text.split("html5player.setThumbSlide('")[1].split("');")[0] if "html5player.setThumbSlide('" in script_text else ""),
                "slide_big": (script_text.split("html5player.setThumbSlideBig('")[1].split("');")[0] if "html5player.setThumbSlideBig('" in script_text else "")
            }

            return {
                "status": True,
                "title": title,
                "url": url,
                "duration": duration,
                "image": image,
                "info": info,
                "files": files
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

@app.get("/api")
@app.post("/api")
async def handler(action: str = None, query: str = None, url: str = None):
    if not action:
        raise HTTPException(status_code=400, detail="Action is required")

    downloader = Downloader()
    try:
        if action == "search":
            if not query:
                raise HTTPException(status_code=400, detail="Query is required for search")
            result = await downloader.search(query)
        elif action == "detail":
            if not url:
                raise HTTPException(status_code=400, detail="URL is required for detail")
            result = await downloader.detail(url)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
