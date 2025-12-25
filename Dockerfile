# পাইথনের হালকা ভার্সন ব্যবহার করছি
FROM python:3.9-slim

# ১. সিস্টেম আপডেট করা এবং FFmpeg ইনস্টল করা
# (এটিই আপনার মূল সমস্যার সমাধান করবে)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ২. ওয়ার্কিং ডিরেক্টরি সেট করা
WORKDIR /app

# ৩. রিকোয়ারমেন্টস ফাইল কপি এবং ইনস্টল করা
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ৪. বাকি কোড কপি করা
COPY . .

# ৫. ডাউনলোড ফোল্ডার তৈরি করা (পারমিশন ঠিক রাখার জন্য)
RUN mkdir -p downloads

# ৬. পোর্ট এক্সপোজ করা
EXPOSE 3030

# ৭. অ্যাপ রান করা
CMD ["python", "app.py"]
