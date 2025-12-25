from flask import Flask, render_template, request, send_file, after_this_request
import requests
import re
import subprocess
import os
import uuid
from urllib.parse import quote

app = Flask(__name__)

API_URL = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
HEADERS = {
    'x-rapidapi-host': "youtube-media-downloader.p.rapidapi.com",
    'x-rapidapi-key': "3d74cfda87msh25f14e67ab30bacp106cdfjsnc33f950ca32f"
}

# Docker কন্টেইনারে ffmpeg গ্লোবালি ইনস্টল থাকে, তাই শুধু নাম দিলেই চলে
FFMPEG_PATH = 'ffmpeg'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def extract_video_id(url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    return match.group(1) if match else None

def get_best_media(data):
    best_video = None
    best_audio = None

    if 'videos' in data and 'items' in data['videos']:
        sorted_videos = sorted(data['videos']['items'], key=lambda x: x.get('height', 0), reverse=True)
        if sorted_videos:
            best_video = sorted_videos[0]

    if 'audios' in data and 'items' in data['audios']:
        sorted_audios = sorted(data['audios']['items'], key=lambda x: x.get('size', 0), reverse=True)
        if sorted_audios:
            best_audio = sorted_audios[0]

    return best_video, best_audio

def download_stream(url, filepath):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with requests.get(url, stream=True, headers=headers) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                # 1MB Chunk Size for High Speed inside Docker
                for chunk in r.iter_content(chunk_size=1024 * 1024): 
                    if chunk:
                        f.write(chunk)
    except Exception as e:
        print(f"Download Error: {e}")
        raise e

@app.route('/', methods=['GET', 'POST'])
def index():
    video_data = None
    error = None

    if request.method == 'POST':
        url = request.form.get('url')
        video_id = extract_video_id(url)

        if video_id:
            querystring = {"videoId": video_id, "urlAccess": "normal", "videos": "auto", "audios": "auto"}
            try:
                response = requests.get(API_URL, headers=HEADERS, params=querystring)
                data = response.json()

                if "errorId" in data and data["errorId"] == "Success":
                    best_video, best_audio = get_best_media(data)
                    
                    encoded_v_url = quote(best_video.get("url"), safe='') if best_video else ""
                    encoded_a_url = quote(best_audio.get("url"), safe='') if best_audio else ""

                    video_data = {
                        "title": data.get("title", "Unknown Video"),
                        "thumbnail": data.get("thumbnails", [{}])[-1].get("url"),
                        "safe_video_url": encoded_v_url,
                        "safe_audio_url": encoded_a_url,
                        "direct_video": {
                            "url": best_video.get("url"),
                            "quality": best_video.get("qualityLabel", "Unknown"),
                            "size": best_video.get("sizeText", "Unknown")
                        } if best_video else None,
                        "direct_audio": {
                            "url": best_audio.get("url"),
                            "size": best_audio.get("sizeText", "Unknown"),
                            "ext": best_audio.get("extension", "mp3")
                        } if best_audio else None
                    }
                else:
                    error = "No Data Found."
            except Exception as e:
                error = f"Error: {str(e)}"
        else:
            error = "Invalid URL."

    return render_template('index.html', data=video_data, error=error)

@app.route('/processing')
def processing():
    v_url = request.args.get('v')
    a_url = request.args.get('a')
    title = request.args.get('t')
    return render_template('processing.html', v_url=v_url, a_url=a_url, title=title)

@app.route('/merge_download')
def merge_download():
    video_url = request.args.get('v')
    audio_url = request.args.get('a')
    title = request.args.get('t')
    
    unique_id = str(uuid.uuid4())[:8]
    safe_title = "".join([c if c.isalnum() else "_" for c in title]).strip()[:50]

    temp_video_path = os.path.join(BASE_DIR, f"v_{unique_id}.mp4")
    temp_audio_path = os.path.join(BASE_DIR, f"a_{unique_id}.mp3")
    output_file_path = os.path.join(BASE_DIR, f"{safe_title}_{unique_id}.mp4")

    try:
        download_stream(video_url, temp_video_path)
        download_stream(audio_url, temp_audio_path)

        # Docker এর ভেতরে ffmpeg কমান্ড রান হবে
        command = [
            FFMPEG_PATH, '-i', temp_video_path, '-i', temp_audio_path, 
            '-c:v', 'copy', '-c:a', 'aac', output_file_path, '-y'
        ]
        
        subprocess.run(command, check=True)

        @after_this_request
        def remove_files(response):
            try:
                if os.path.exists(temp_video_path): os.remove(temp_video_path)
                if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
                if os.path.exists(output_file_path): os.remove(output_file_path)
            except Exception as e:
                pass
            return response

        return send_file(output_file_path, as_attachment=True)

    except Exception as e:
        if os.path.exists(temp_video_path): os.remove(temp_video_path)
        if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
        return f"Processing Error: {str(e)}"

if __name__ == '__main__':
    # Docker কন্টেইনারে 0.0.0.0 মাস্ট
    app.run(host='0.0.0.0', port=5477, threaded=True)
