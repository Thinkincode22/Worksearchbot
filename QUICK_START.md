# 🚀 Швидкий старт розгортання

## Локальна розробка (SQLite)

### 1. Встановлення
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Налаштування
```bash
cp env.example .env
# Додай свій TELEGRAM_BOT_TOKEN в .env
```

### 3. Запуск
```bash
python main.py
```

---

## Production розгортання (Render.com + PostgreSQL)

📖 **Детальна інструкція:** [DEPLOY.md](DEPLOY.md)

### Коротко:
1. Push на GitHub
2. Підключити Render.com
3. Додати PostgreSQL БД
4. Встановити `TELEGRAM_BOT_TOKEN` у Environment

✅ **Готово! Бот працює 24/7** 🎉

---

## 📚 Документація

- [SETUP.md](SETUP.md) - Локальне налаштування
- [DEPLOY.md](DEPLOY.md) - Розгортання на сервер
- [PLAN.md](PLAN.md) - План розробки
- [README.md](README.md) - Основна документація

---

## 🔐 Security

Ніколи не комітьте `.env` файл! Він вже в `.gitignore`.

Використовуйте Environment Variables на сервері для всіх секретних даних.
