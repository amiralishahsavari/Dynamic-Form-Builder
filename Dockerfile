FROM python:3.12-slim

# تنظیم دایرکتوری کاری
WORKDIR /app

# کپی کردن فایل‌های پروژه و فایل requirements
COPY . /app

# نصب پکیج‌ها از فایل requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# باز کردن پورت
EXPOSE 8000

# اجرای سرور جنگو
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
