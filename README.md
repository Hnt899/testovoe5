# Django + Stripe Checkout

Тестовое задание: Django-бэкенд с интеграцией Stripe для оплаты товаров и заказов.

## Реализованный функционал

### Обязательное
- Модель `Item` (`name`, `description`, `price`, `currency`)
- `GET /item/{id}` — HTML-страница товара с кнопкой **Buy**
- `GET /buy/{id}` — создание Stripe Checkout Session, возвращает `{"id": "cs_..."}`

### Бонусные задачи
- Docker (`Dockerfile`, `docker-compose.yml`)
- Переменные окружения (`.env`)
- Django Admin для всех моделей
- Модель `Order` — оплата нескольких `Item` одним платежом (`/order/{id}`, `/buy-order/{id}`)
- Модели `Discount` и `Tax`, привязка к `Order` и передача в Stripe Checkout
- Поле `Item.currency` + отдельные Stripe keypair для USD и EUR
- Payment Intent flow (`/item-intent/{id}`, `/buy-intent/{id}`, `/buy-order-intent/{id}`)

## Быстрый старт (локально)

### 1. Клонировать и перейти в проект

```bash
git clone https://github.com/Hnt899/testovoe5.git
cd testovoe5
```

### 2. Создать виртуальное окружение и установить зависимости

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Настроить переменные окружения

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux / macOS
```

Заполните `.env` тестовыми ключами из [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys):

- `STRIPE_PUBLISHABLE_KEY_USD` / `STRIPE_SECRET_KEY_USD`
- `STRIPE_PUBLISHABLE_KEY_EUR` / `STRIPE_SECRET_KEY_EUR`

Для одного Stripe-аккаунта можно временно указать одни и те же ключи в обе пары переменных.

### 4. Миграции и демо-данные

```bash
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

### 5. Проверка

| URL | Описание |
|-----|----------|
| http://localhost:8000/item/1 | Страница товара (USD) |
| http://localhost:8000/buy/1 | JSON с session id |
| http://localhost:8000/order/1 | Страница заказа |
| http://localhost:8000/item-intent/1 | Payment Intent (бонус) |
| http://localhost:8000/admin/ | Админка |

**Админка (после `seed_demo_data`):**
- Логин: `admin`
- Пароль: `admin123`

## Запуск через Docker

```bash
copy .env.example .env
# заполните Stripe keys в .env

docker compose up --build
```

Приложение будет доступно на http://localhost:8000

## API

### Товар — Checkout Session

```bash
curl http://localhost:8000/buy/1
# {"id": "cs_test_..."}

curl http://localhost:8000/item/1
# HTML с кнопкой Buy
```

### Заказ — Checkout Session

```bash
curl http://localhost:8000/buy-order/1
curl http://localhost:8000/order/1
```

### Payment Intent (бонус)

```bash
curl http://localhost:8000/buy-intent/1
# {"clientSecret": "pi_..."}
```

## Структура проекта

```
testovoe5/
├── config/              # Django settings, urls
├── payments/
│   ├── models.py        # Item, Order, Discount, Tax
│   ├── views.py         # HTTP endpoints
│   ├── admin.py         # Django Admin
│   ├── services/
│   │   └── stripe_service.py
│   └── templates/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Деплой (Render / Railway / VPS)

1. Залейте репозиторий на GitHub
2. Создайте Web Service, укажите:
   - Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Start: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
3. Добавьте переменные окружения из `.env.example`
4. Установите `DJANGO_DEBUG=False`, сгенерируйте `DJANGO_SECRET_KEY`
5. Добавьте домен в `DJANGO_ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`
6. Обновите `STRIPE_SUCCESS_URL` и `STRIPE_CANCEL_URL` на ваш домен
7. Выполните миграции и создайте суперпользователя:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data
```

## Тестовая карта Stripe

- Номер: `4242 4242 4242 4242`
- Срок: любой будущий
- CVC: любой 3-значный

Документация: https://stripe.com/docs/testing

## Что нужно сделать вручную перед отправкой

1. **Получить Stripe test keys** на https://dashboard.stripe.com/test/apikeys
2. **Заполнить `.env`** своими ключами (не коммитить `.env` в git)
3. **Задеплоить** на Render/Railway/Fly.io/VPS и дать ссылку проверяющим
4. **Создать суперпользователя** на проде (или сменить пароль `admin123`)
5. **Указать в ответе на тестовое:**
   - Ссылка на GitHub: https://github.com/Hnt899/testovoe5
   - Ссылка на живое приложение
   - Логин/пароль админки
