# World of Games

### Страницы

- `base.html` - базовый шаблон страницы: хедер, сайдбар и футер
- `index.html` - страница со списком вопросов
- `ask.html` - страница с формой создания нового вопроса
- `login.html` - страница с формой авторизации
- `signup.html` - страница с формой регистрации
- `profile.html` - страница настроек профиля аккаунта
- `question.html` - страница вопроса и ответов к нему

### Как запустить верстку

##### Вариант 1. Локальный запуск

1. Создайте виртуальное окружение
```shell
python3 -m venv venv
```

2. Активируйте его
- Для Linux/Mac:
```shell
source venv/bin/activate
```
- Для Windows:
```shell
venv\Scripts\activate
```

3. Установите зависимости
```shell
pip install -r requirements.txt
```

4. Запустите сервер
```shell
python3 manage.py runserver
```

Проект запущен по адресу `http://127.0.0.1:8000`. Для остановки нажмите `Ctrl + C`.

##### Вариант 2. Запуск через Docker Compose

1. Установите `Docker` и `Docker Compose`.

2. Запустите сервер
```shell
docker compose up --build
```

Проект запущен по адресу `http://127.0.0.1:8000`. Для остановки нажмите `Ctrl + C` и выполните:
```shell
docker compose down
```
