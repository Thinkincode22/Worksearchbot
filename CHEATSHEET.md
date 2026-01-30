# 📋 ШПАРГАЛКА: GitHub + Render розгортання

## 🔐 1. Вперше на GitHub?

### Реєстрація (2 хв):
1. Відкрити [github.com/signup](https://github.com/signup)
2. Вписати email, пароль, username
3. Підтвердити email
4. Готово!

### Налаштування Git (1 хв):
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
git config --global init.defaultBranch main
```

---

## 📤 2. Завантажити проект на GitHub

```bash
cd .

# Ініціалізуємо git
git init

# Додаємо всі файли
git add .

# Перша commit
git commit -m "Initial commit: WorkSearchBot"

# Замінити YOUR_USERNAME на свій GitHub username
git remote add origin https://github.com/YOUR_USERNAME/WorkSearchBot.git

# Встановлюємо гілку main
git branch -M main

# Завантажуємо (push)
git push -u origin main
```

**Відповідь повинна бути:**
```
Enumerating objects: ...
Writing objects: ...
remote: Create a pull request ...
```

---

## 🚀 3. Розгорнути на Render.com

### Реєстрація (2 хв):
1. Відкрити [render.com](https://render.com)
2. Натиснути **Sign up**
3. Вибрати **Sign up with GitHub**
4. Підтвердити дозвіл
5. Готово!

### Розгортання (8 хв):

#### 3.1 Web Service (Бот):
1. Натиснути **New +** → **Web Service**
2. Вибрати **Connect your GitHub repository**
3. Шукати `WorkSearchBot`
4. Натиснути **Connect**
5. Заповнити форму:
   - **Name:** `worksearchbot`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Plan:** Free
6. Натиснути **Create Web Service**
7. Чекай... (хвилину)

#### 3.2 PostgreSQL Database:
1. На Render Dashboard натиснути **New +** → **PostgreSQL**
2. Заповнити:
   - **Name:** `worksearchbot-db`
   - **Database:** `worksearchbot`
   - **User:** `worksearchbot`
   - **Plan:** Free
3. Натиснути **Create Database**
4. Чекай 2-3 хвилини...

#### 3.3 Підключити БД до бота:
1. Відкрити сторінку боту (Web Service)
2. Вкладка **Environment**
3. Натиснути **Add Environment Variable**
4. **Key:** `DATABASE_URL`
5. **Value:** Скопіювати з PostgreSQL сторінки (Connection String)
6. Натиснути **Save**

#### 3.4 Додати токен:
1. На сторінці боту вкладка **Environment**
2. Натиснути **Add Environment Variable**
3. **Key:** `TELEGRAM_BOT_TOKEN`
4. **Value:** (Твій токен з `.env` файлу - НЕ ПУБЛІКУВАТИ!)
5. Натиснути **Save**

---

## ✅ 4. Перевіри що все працює:

1. На сторінці бота натиснути **Logs**
2. Шукати рядки:
   ```
   Application started
   Scheduler started
   ```
3. Якщо є - 🎉 **Успіх!**

4. Відкрити Telegram, напиши @SzukaczPracy_bot:
   ```
   /start
   ```
5. Якщо бот відповів - 🎉 **ВСЕ ПРАЦЮЄ!**

---

## 🆘 Якщо щось не працює:

| Проблема | Рішення |
|----------|---------|
| Git не розпізнає | Встановити git: `brew install git` |
| `.git: command not found` | Встановити Git for macOS |
| Push не працює | Перевірити username в remote: `git remote -v` |
| Render не бачить repo | Дати дозвіл GitHub у Render settings |
| БД не підключується | Перевірити Connection String на PostgreSQL сторінці |
| Бот не відповідає | Перевірити TELEGRAM_BOT_TOKEN та логи |

---

## 📞 Посилання:

- GitHub username: https://github.com/settings/profile
- Render dashboard: https://render.com/dashboard
- Telegram @SzukaczPracy_bot
- Логи: Dashboard → Web Service → Logs

---

**ГОТОВО! Бот буде запущено 24/7 після розгортання! 🚀**
