# Гайд розгортання на Render.com

## 📋 Вимоги перед розгортанням

1. **GitHub аккаунт** - [Зареєструйтеся тут](https://github.com/signup)
2. **Render.com аккаунт** - [Зареєструйтеся тут](https://render.com)
3. **Telegram Bot Token** - вже у тебе є: `8503931691:AAHCn6piqnLoudFzvzaC2IV1WAMqvrZa-cI`

---

## 🚀 Крок 1: Завантажити проект на GitHub

### 1.1 Створити новий репозиторій на GitHub:
1. Відкрити [github.com/new](https://github.com/new)
2. Вписати ім'я: `WorkSearchBot`
3. Опис: `Telegram bot for job search in Poland`
4. Вибрати **Public** (щоб був доступний)
5. Натиснути **Create repository**

### 1.2 Завантажити проект в локальному терміналі:

```bash
cd /Users/denyssadovoi/Desktop/Projects/WorkSearchBot

# Ініціалізуємо git (якщо не було)
git init
git add .
git commit -m "Initial commit: WorkSearchBot setup"

# Додаємо GitHub репозиторій (замінити на свій)
git remote add origin https://github.com/YOUR_USERNAME/WorkSearchBot.git
git branch -M main
git push -u origin main
```

---

## 🎯 Крок 2: Розгорнути на Render.com

### 2.1 Підключити репозиторій:
1. Відкрити [render.com/dashboard](https://render.com/dashboard)
2. Натиснути **New +** → **Web Service**
3. Вибрати **Deploy existing repository**
4. Додати репозиторій GitHub `WorkSearchBot`
5. Дати Render.com дозвіл на доступ до GitHub

### 2.2 Налаштування сервісу:
1. **Name:** `worksearchbot`
2. **Runtime:** Python 3
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `python main.py`
5. **Plan:** Free
6. Натиснути **Create Web Service**

### 2.3 Додати PostgreSQL БД:
1. На сторінці Render Dashboard натиснути **New +** → **PostgreSQL**
2. **Name:** `worksearchbot-db`
3. **Database:** `worksearchbot`
4. **User:** `worksearchbot`
5. **Plan:** Free
6. **Region:** Ohio (або найближчий до тебе)
7. Натиснути **Create Database**

### 2.4 Підключити БД до бота:
1. На сторінці бота натиснути **Environment**
2. Додати змінну оточення:
   - **Key:** `DATABASE_URL`
   - **Value:** Скопіювати з PostgreSQL сервісу (Connection String)
3. Натиснути **Save**

### 2.5 Додати Telegram Bot Token:
1. На сторінці бота натиснути **Environment**
2. Додати змінну:
   - **Key:** `TELEGRAM_BOT_TOKEN`
   - **Value:** `8503931691:AAHCn6piqnLoudFzvzaC2IV1WAMqvrZa-cI`
3. Натиснути **Save**

---

## ✅ Крок 3: Перевірити розгортання

1. На сторінці бота проглянути **Logs**
2. Мають бути рядки типу:
   ```
   2026-01-28 10:30:45 | INFO | Bot initialized
   2026-01-28 10:30:46 | INFO | Application started
   ```

3. Якщо помилки - проглянути логи й додати `DEBUG=true` в Environment

---

## 🧪 Крок 4: Тестування

1. Відкрити Telegram та напиши @SzukaczPracy_bot:
   ```
   /start
   ```
2. Бот повинен відповісти з приватною меню

---

## 🛠️ Розв'язання проблем

### БД не підключується:
- Перевірити `DATABASE_URL` в Environment
- Впевниться, що PostgreSQL сервіс запущено

### Бот не відповідає:
- Перевірити логи в **Logs** розділі
- Перевірити `TELEGRAM_BOT_TOKEN`

### Скрапінг не працює:
- Перевірити скрапери в `scraper/scrapers/`
- Вмикти `SCRAPING_ENABLED=true` в Environment

---

## 📝 Корисні команди

```bash
# Переглянути логи локально
tail -f logs/bot.log

# Тестувати на локальній PostgreSQL
DATABASE_URL="postgresql://user:pass@localhost/worksearchbot" python main.py

# Оновити на GitHub
git add .
git commit -m "Update description"
git push
```

---

## 🎉 Результат

✅ Бот запущено 24/7 на Render.com
✅ PostgreSQL БД в хмарі
✅ Доступ для всіх користувачів
✅ Безплатно!

**Бот готовий до використання!** 🚀
