import random
import re
import urllib.parse
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests

class Downloader:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
        }

    def get_html(self, url):
        # If you need to use a proxy like in the original JS code, uncomment and set DOMAIN_URL
        # DOMAIN_URL = "your-domain-here"  # Replace with your actual DOMAIN_URL
        # proxy_url = f"https://{DOMAIN_URL}/api/tools/web/html/v1?url={urllib.parse.quote(url)}"
        # response = requests.get(proxy_url, headers=self.headers)
        
        # For direct fetch (may not work if site blocks scrapers):
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.text

    def search(self, query):
        try:
            random_page = random.randint(1, 3)
            base_url = f"https://www.xnxx.com/search/{urllib.parse.quote(query)}/{random_page}"
            html = self.get_html(base_url)
            soup = BeautifulSoup(html, 'html.parser')
            videos = []
            for element in soup.select("div.thumb-block"):
                title_elem = element.select_one(".thumb-under a")
                title = title_elem.get("title") if title_elem else None
                link_elem = element.select_one(".thumb-under a")
                link = f"https://www.xnxx.com{link_elem.get('href')}" if link_elem else None
                thumbnail_elem = element.select_one(".thumb img")
                thumbnail = thumbnail_elem.get("src") if thumbnail_elem else None
                uploader_elem = element.select_one(".uploader a span")
                uploader = uploader_elem.text if uploader_elem else "N/A"
                metadata_elem = element.select_one(".metadata")
                metadata_text = metadata_elem.text.strip() if metadata_elem else ""
                duration_lines = [line.strip() for line in metadata_text.splitlines() if line.strip()]
                duration = duration_lines[1] if len(duration_lines) > 1 else "N/A"
                views_elem = element.select_one(".metadata .right")
                views_text = views_elem.text.strip() if views_elem else ""
                views = views_text.split(" ")[0] if views_text else "N/A"
                if link and "undefined" not in link:
                    videos.append({
                        "title": title,
                        "link": link,
                        "thumbnail": thumbnail,
                        "uploader": uploader,
                        "views": views,
                        "duration": duration
                    })
            return videos
        except Exception as error:
            print(f"Error fetching data: {error}")
            raise error

    def detail(self, url):
        try:
            html = self.get_html(url)
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.select_one('meta[property="og:title"]')['content'] if soup.select_one('meta[property="og:title"]') else "N/A"
            duration = soup.select_one('meta[property="og:duration"]')['content'] if soup.select_one('meta[property="og:duration"]') else "N/A"
            image = soup.select_one('meta[property="og:image"]')['content'] if soup.select_one('meta[property="og:image"]') else "N/A"
            info_elem = soup.select_one("span.metadata")
            info = info_elem.text.strip() if info_elem else "N/A"
            script_elem = soup.select_one("#video-player-bg > script:nth-child(6)")
            script_content = script_elem.string if script_elem else ""
            files = {
                "low": re.search(r"html5player\.setVideoUrlLow\('(.*?)'\);", script_content).group(1) if re.search(r"html5player\.setVideoUrlLow\('(.*?)'\);", script_content) else None,
                "high": re.search(r"html5player\.setVideoUrlHigh\('(.*?)'\);", script_content).group(1) if re.search(r"html5player\.setVideoUrlHigh\('(.*?)'\);", script_content) else None,
                "hls": re.search(r"html5player\.setVideoHLS\('(.*?)'\);", script_content).group(1) if re.search(r"html5player\.setVideoHLS\('(.*?)'\);", script_content) else None,
                "thumb": re.search(r"html5player\.setThumbUrl\('(.*?)'\);", script_content).group(1) if re.search(r"html5player\.setThumbUrl\('(.*?)'\);", script_content) else None,
                "thumb_69": re.search(r"html5player\.setThumbUrl169\('(.*?)'\);", script_content).group(1) if re.search(r"html5player\.setThumbUrl169\('(.*?)'\);", script_content) else None,
                "slide": re.search(r"html5player\.setThumbSlide\('(.*?)'\);", script_content).group(1) if re.search(r"html5player\.setThumbSlide\('(.*?)'\);", script_content) else None,
                "slide_big": re.search(r"html5player\.setThumbSlideBig\('(.*?)'\);", script_content).group(1) if re.search(r"html5player\.setThumbSlideBig\('(.*?)'\);", script_content) else None
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
        except Exception as error:
            print(f"Error fetching data: {error}")
            raise error

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def handler():
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    action = data.get('action')
    if not action:
        return jsonify({"error": "Action is required"}), 400
    try:
        downloader = Downloader()
        if action == "search":
            query = data.get('query')
            if not query:
                return jsonify({"error": "Query is required for search"}), 400
            result = downloader.search(query)
        elif action == "detail":
            url = data.get('url')
            if not url:
                return jupytext({"error": "URL is required for detail"}), 400
            result = downloader.detail(url)
        else:
            return jsonify({"error": f"Invalid action: {action}"}), 400
        return jsonify(result), 200
    except Exception as error:
        return jsonify({"error": str(error) or "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
