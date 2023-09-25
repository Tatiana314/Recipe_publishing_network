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
pip install -r foodgram-project-react/requirements.txt
```
Выполнить миграции, создать суперюзера:
```
python manage.py migrate
python manage.py createsuperuser
```
## Запуск проекта на удаленном сервере:
Подключиться к удаленному серверу и создать директорию foodgram:

```
ssh -i путь_до_файла_с_SSH_ключом/название_файла_с_SSH_ключом имя_пользователя@ip_адрес_сервера
mkdir kittygram
```
Установка docker compose на сервер:
```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin
```
В директорию foodgram/ скопируйте файл docker-compose.production.yml:
```
scp -i path_to_SSH/SSH_name docker-compose.production.yml username@server_ip:/home/username/foodgram/docker-compose.production.yml
```
Проект использует базу данных PostgreSQL.
В директории foodgram/ необходимо создать и заполнить ".env" с переменными окружения.
```
POSTGRES_DB=foodgram
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY='Секретный ключ'
ALLOWED_HOSTS='Имя или IP хоста'
DEBUG=True
DB_SQLITE=True
```
Запустите docker compose в режиме демона:
```
sudo docker compose -f docker-compose.production.yml up -d
```
Выполните миграции, загрузите данные в БД, соберите статику бэкенда и скопируйте их в /backend_static/static/:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py loaddata dump.json
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```
На сервере в редакторе nano откройте конфиг Nginx:

sudo nano /etc/nginx/sites-enabled/default
Добавте настройки location в секции server:

location / {
    proxy_set_header Host $http_host;
    proxy_pass http://127.0.0.1:9000;
}
Проверьте работоспособность конфигураций и перезапустите Nginx:

sudo nginx -t 
sudo service nginx reload
