# 🚀 Инструкции по загрузке проекта на GitHub

## 📋 Проблема
GitHub больше не принимает пароли для API запросов, требуется **Personal Access Token**.

## 🛠️ Решение 1: Создать репозиторий вручную (рекомендуется)

### Шаг 1: Создайте репозиторий на сайте GitHub
1. Перейдите на https://github.com
2. Войдите под аккаунтом **PavelVM209**
3. Нажмите **"+"** → **"New repository"**
4. Назовите репозиторий: **MultiAgent-Content-Creator**
5. Описание: **🤖 Мультиагентная система с интеллектуальным оркестратором для создания контента через цепочку нейросетей**
6. Выберите **Public**
7. НЕ ставьте галочки "Add README", "Add .gitignore", "Choose license"
8. Нажмите **"Create repository"**

### Шаг 2: Подключите и загрузите проект
После создания репозитория GitHub покажет команды. Выполните в терминале:

```bash
# Добавляем remote (указанный GitHub)
git remote add origin https://github.com/PavelVM209/MultiAgent-Content-Creator.git

# Переименовываем ветку в main (стандарт GitHub)
git branch -M main

# Отправляем код на GitHub
git push -u origin main
```

---

## 🛠️ Решение 2: Personal Access Token

### Шаг 1: Создайте Personal Access Token
1. Перейдите на https://github.com/settings/tokens
2. Нажмите **"Generate new token"** → **"Generate new token (classic)"**
3. Назовите токен: **MultiAgent Project**
4. Выберите срок действия
5. Отметьте права: **repo**, **public_repo**
6. Нажмите **"Generate token"**
7. **СКОПИРУЙТЕ ТОКЕН** (он больше не будет показан!)

### Шаг 2: Используйте токен вместо пароля
При выполнении команды `git push` система попросит пароль:
- **Login:** PavelVM209
- **Password:** [вставьте Personal Access Token]

---

## 🛠️ Решение 3: Использовать GitHub CLI с токеном

```bash
# Прерываем текущий процесс (Ctrl+C)
# Выполняем вход с токеном
echo "your_personal_access_token" | gh auth login --with-token

# Создаем репозиторий
gh repo create MultiAgent-Content-Creator --public --description "🤖 Мультиагентная система с интеллектуальным оркестратором для создания контента через цепочку нейросетей"

# Отправляем код
git push -u origin main
```

---

## ✅ Проверка результата

После успешной загрузки проверьте:
1. Перейдите на https://github.com/PavelVM209/MultiAgent-Content-Creator
2. Убедитесь что все файлы загружены
3. Проверьте что README.md отображается корректно

---

## 🆘 Если что-то пошло не так

### Ошибка "Authentication failed"
- Убедитесь что используете Personal Access Token, а не пароль
- Проверьте что токен имеет права `repo`

### Ошибка "Repository not found"
- Убедитесь что репозиторий создан
- Проверьте правильность имени репозитория

### Ошибка "Permission denied"
- Проверьте что вы владелец репозитория
- Убедитесь что токен не просрочен

---

## 🎯 Рекомендуемый путь

**Используйте Решение 1 (ручное создание)** - это самый надежный и простой способ:

1. Создайте репозиторий на сайте GitHub (2 минуты)
2. Выполните 3 команды в терминале (30 секунд)
3. Готово! 🎉

Проект будет доступен по адресу:
https://github.com/PavelVM209/MultiAgent-Content-Creator
