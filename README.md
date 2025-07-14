# Telegram Realty Bot

## 🚀 Быстрый старт

1. Клонируйте проект и настройте `.env`
2. Поместите `credentials.json` (Google API)
3. Запустите в Docker:

```bash
docker-compose up --build -d
```

4. Убедитесь, что SSL-сертификаты размещены в `/etc/nginx/certs/`
5. Установите webhook у бота:

```bash
curl -F "url=https://yourdomain.com" https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook
```

## 📁 Структура

- `bot.py` — основной файл бота
- `Dockerfile`, `docker-compose.yml` — для развёртывания
- `nginx.conf` — SSL-прокси для Telegram webhook
- `.env` — переменные окружения
- `requirements.txt` — зависимости Python

---
Проект включает анкету, конкурс, учёт рефералов и интеграцию с Google Sheets.