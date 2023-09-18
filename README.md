# [foodgram-project-react](https://animalworld.zapto.org) - продуктовый помошник. Учебный проект Яндекс.Практикум.
[![Main Foodgram workflow](https://github.com/Tatiana314/foodgram-project-react/actions/workflows/main.yml/badge.svg)](https://github.com/Tatiana314/foodgram-project-react/actions/workflows/main.yml)

 Сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Технологии
Python3, Django3, HTML, CSS, JavaScript

## Запуск проекта локально:
Клонировать репозиторий:
```
git clone https://github.com/Tatiana314/foodgram-project-react.git
```
В директории foodgram-project-react/backend создать и активировать виртуальное окружение:
```
python -m venv venv
Linux/macOS: source env/bin/activate
windows: source env/scripts/activate
```
Установить зависимости из файла requirements.txt:
```
python -m pip install --upgrade pip
pip install -r kittygram_final/requirements.txt
```
Выполнить миграции, создать суперюзера:
```
python manage.py migrate
python manage.py createsuperuser
```
