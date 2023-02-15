# Yatube - блог-платформа, социальная сеть

## О проекте
Платформа предоставляет возможность публиковать записи на личной странице, добавлять публикации в группы по темам, подписываться на других авторов и комментировать их записи. Реализована система регистрации и восстановления пароля.

## Автор

yatube - Захаров Данил

tests - Яндекс.Практикум

## Технологии

Python, Django, Django Rest Framework, SQLite, pytest.

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Dranbald/yatube/
```

```
cd yatube
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
. venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py makemigrations
```

```
python3 manage.py migrate
```

Создать суперпользователя:

```
python3 manage.py createsuperuser
```

Запустить проект:

```
python3 manage.py runserver
```
