# Sử dụng image Python phiên bản slim để tối ưu kích thước
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các công cụ biên dịch cần thiết cho bitarray và mmh3 (yêu cầu C/C++)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Sao chép file requirements.txt trước để tận dụng cache của Docker
COPY requirements.txt .

# Cài đặt các thư viện trong requirements.txt và các thư viện web cần thiết
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir Flask flask-cors requests

# Sao chép toàn bộ mã nguồn của dự án vào container
COPY . .

# Biến môi trường mặc định
ENV PYTHONUNBUFFERED=1
ENV SITE_B_URL=http://localhost:5001

# Lệnh chạy mặc định (sẽ được ghi đè bởi docker-compose)
CMD ["python", "app.py"]
