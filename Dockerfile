# ১. বেস ইমেজ হিসেবে পাইথন স্লিম ভার্সন ব্যবহার করছি (হালকা এবং ফাস্ট)
FROM python:3.9-slim

# ২. সিস্টেম আপডেট করা এবং FFmpeg ইনস্টল করা
# এটি আপনার কন্টেইনারের ভেতরে FFmpeg সেটআপ করে দেবে
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ৩. ওয়ার্কিং ডিরেক্টরি সেট করা
WORKDIR /app

# ৪. রিকোয়ারমেন্টস ফাইল কপি এবং ইনস্টল করা
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ৫. বাকি সব ফাইল কপি করা
COPY . .

# ৬. পোর্ট এক্সপোজ করা (আপনার ৫৪৭৭)
EXPOSE 5477

# ৭. অ্যাপ রান করা
CMD ["python", "app.py"]
