# Сервис "Электронное голосование" для акционеров
 
**Веб-сервис, который позволит акционерам голосовать удаленно** (серверная часть сервиса)

## Структура

```
E-VOTING
│
├── evoting/               # Папка проекта
│   ├── settings.py        # Настройки проекта
│   ├── urls.py            # URL проекта
│
├── meeting/               # Приложение собрания             
│   ├── ballot/            # Для создания тестовых данных
│   ├── services/          # Бизнес-логика
│   ├── views/             # Представления
│   ├── admin.py           # Настройка админ-панели
│   ├── models.py          # Модели
│   ├── permissions.py     # Права редактирования для администратора
│   ├── serializers.py     # Сериализаторы
│   ├── urls.py            # URL адреса собрания
│
├── users/                 # Приложение пользователей
|
├── .gitignore             # Игнорируемые файлы
├── manage.py              # Исполняемый файл
└── requirements.txt       # Зависимости
```

## Установка проекта 

1. Клонирование репозитория
```
git clone https://github.com/noktis1707/E-voting.git
```
2. Создание и активация виртуального окружения
  - Создание
```
python -m venv venv
```
  - Активация
```
venv\Scripts\activate
```

3. Установка зависимостей
```
pip install -r requirements.txt
```
  
4. Настройка базы данных
   
  - Для работы с бд необходимо в evoting/settings.py изменить данные:
```py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':'your name',           # Название бд
        'USER':'your user name',      # Имя пользователя
        'PASSWORD':'your password',   # Пароль
        'HOST':'localhost',
        'PORT':'5432',
    }
}
```
  - Затем выполнить миграции
```
python manage.py migrate
```
  - И создать суперпользователя для работы в админке
```
python manage.py createsuperuser
```

5. Запуск сервера
```
python manage.py runserver
```

## Документация

Документация API доступна в [postman](https://documenter.getpostman.com/view/27977053/2sAYkLkGJt#fa6d2abf-fdf0-494d-ba53-8e15fcb07fb9)
