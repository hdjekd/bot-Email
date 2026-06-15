FROM python:3.10-slim

# إعداد الصلاحيات للمستخدم العادي داخل بيئة Hugging Face
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# تحويل المنفذ بشكل إجباري ليتوافق مع السيرفر
ENV MONITOR_PORT=7860

# نسخ وتثبيت المكتبات
COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# نسخ ملفات البوت
COPY --chown=user . .

# أمر التشغيل لملف البايثون الخاص بك تماماً
CMD ["python", "MR_Email_Bot_Ultimate.py"]
