import os
import uuid
from flask import Flask, request, send_from_directory
import yt_dlp

app = Flask(__name__)

# Docker কন্টেইনারের ভেতরে ডাউনলোড ফোল্ডার
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route("/")
def home():
    return """
    <div style="font-family: sans-serif; text-align: center; padding-top: 50px;">
        <h2>YouTube High-Quality Player (Docker + FFmpeg)</h2>
        <form method="post" action="/download">
            <input type="text" name="url" placeholder="YouTube লিংক পেস্ট করুন"
                   style="width:400px; padding:10px; border-radius: 5px; border: 1px solid #ccc;" required />
            <button type="submit" style="padding:10px 20px; cursor: pointer; background-color: #ff0000; color: white; border: none; border-radius: 5px;">
                Play Video
            </button>
        </form>
    </div>
    """

@app.route("/download", methods=["POST"])
def download_video():
    url = request.form.get("url")
    if not url:
        return "URL দিন", 400

    filename = str(uuid.uuid4()) + ".mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    # FFmpeg কনফিগারেশন:
    # এটি সেরা ভিডিও এবং সেরা অডিও নামাবে এবং তারপর মার্জ করবে।
    ydl_opts = {
        "outtmpl": filepath,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",  # FFmpeg দিয়ে জোড়া লাগাবে
        "quiet": True,
        # ব্রাউজার কম্প্যাটিবিলিটির জন্য পোস্ট-প্রসেসর ব্যবহার করা যেতে পারে,
        # তবে সাধারণত ওপরের কনফিগারেশনই যথেষ্ট।
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except Exception as e:
        return f"<h3>Download failed:</h3><p>{e}</p>"

    return f"""
    <div style="font-family: sans-serif; text-align: center; padding-top: 20px;">
        <h3>ভিডিও তৈরি! এখন ব্রাউজারে চলবে 👍</h3>
        
        <video width="100%" max-width="800" controls autoplay style="border: 2px solid #333; border-radius: 8px;">
            <source src="/files/{filename}" type="video/mp4">
            আপনার ব্রাউজার ভিডিও ট্যাগ সাপোর্ট করছে না।
        </video>
        
        <br><br>
        
        <a href="/files/{filename}" download="video_{filename}">
            <button style="padding:10px 20px; background-color: green; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                📥 ডাউনলোড (High Quality)
            </button>
        </a>
        
        <br><br>
        <a href="/" style="text-decoration: none; color: #007bff;">🏠 নতুন ভিডিও</a>
    </div>
    """

@app.route("/files/<path:filename>")
def files(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=False)

if __name__ == "__main__":
    # Docker এ চালানোর জন্য host 0.0.0.0 হতে হবে
    app.run(host="0.0.0.0", port=3030)
