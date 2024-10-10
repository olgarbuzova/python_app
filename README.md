# Сервис микроблогов, аналогичный Twitter
Проект реализующий бэкенд приложения для микроблогов.
Функциональные возможности:
1. Пользователь может добавить/удалить твит.
2. Пользователь может подписаться/отписаться от другого пользователя.
3. Пользователь может поставить/удалить отметку "Нравится".
4. Пользователь может получить ленту из твитов.
5. Твит может содержать картинку.

## Установка и запуск
Перед началом убедитесь, что у вас установлены:
- Docker
- Docker-compose

1. Клонируйте репозиторий

2. Сборка и запуск контейнеров с приложением и базой данных:
```bash
docker-compose build
docker-compose up
```

## Использование приложения
- Открыть в браузере <http://localhost> для загрузки стартовой страницы
- Документация доступна <http://localhost/docs>

## Используются:
- [Python](https://www.python.org/) основной язык программирования бэкенд части
- [FastAPI](https://fastapi.tiangolo.com/) веб-фреймворк для бэкенд части
- [SQLAlchemy 2.0](https://www.sqlalchemy.org) для ORM
- [PostgreSQL](https://www.postgresql.org) для базы данных

## Автор
Ольга Кривопишина
Каналы связи:
- [Telegram](https://t.me/okrivopishina)
- email: o.a.krivopishina.gmail.com