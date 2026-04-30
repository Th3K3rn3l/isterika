# Анализ: Ограничение скорости для отдельных пользователей в Hysteria2

## Возможности Hysteria2

### 1. Глобальные ограничения (уже реализовано)
В конфигурации Hysteria2 есть глобальные настройки bandwidth:
```yaml
bandwidth:
  up: 1 gbps
  down: 1 gbps
```

Эти настройки применяются ко всему серверу, а не к отдельным пользователям.

### 2. Ограничения для отдельных пользователей

**Хорошая новость:** Hysteria2 **ПОДДЕРЖИВАЕТ** индивидуальные ограничения скорости для каждого пользователя!

#### Способ реализации:

В конфигурации можно указать bandwidth для каждого пользователя отдельно:

```yaml
auth:
  type: userpass
  userpass:
    user1: password1
    user2: password2

# Индивидуальные ограничения
trafficStats:
  listen: :9999

# Для каждого пользователя можно задать лимиты через ACL
acl:
  inline:
    - user(user1) && bandwidth(up:100mbps,down:100mbps)
    - user(user2) && bandwidth(up:500mbps,down:500mbps)
```

**Альтернативный способ (более простой):**

Hysteria2 поддерживает расширенный формат userpass с дополнительными параметрами:

```yaml
auth:
  type: userpass
  userpass:
    user1:
      password: password1
      bandwidth:
        up: 100 mbps
        down: 100 mbps
    user2:
      password: password2
      bandwidth:
        up: 500 mbps
        down: 500 mbps
```

## Реализация в панели Isterika

### Необходимые изменения:

#### 1. База данных
Добавить поля в таблицу `hysteria_clients`:
- `bandwidth_up` (TEXT) - например "100 mbps"
- `bandwidth_down` (TEXT) - например "100 mbps"

#### 2. Модуль hysteria.py
Обновить функции:
- `add_user()` - принимать параметры bandwidth
- `read_config()` / `write_config()` - поддержка расширенного формата userpass

#### 3. API endpoints (app.py)
Добавить/обновить:
- `POST /api/clients` - принимать bandwidth параметры
- `PUT /api/clients/<username>/bandwidth` - изменение лимитов

#### 4. UI (dashboard_v2.html)
Добавить:
- Поля для ввода bandwidth при создании пользователя
- Отображение текущих лимитов в таблице
- Модальное окно для редактирования bandwidth

### Пример структуры конфига с лимитами:

```yaml
listen: :443

acme:
  domains:
    - example.com
  email: admin@example.com

auth:
  type: userpass
  userpass:
    premium_user:
      password: "abc123"
      bandwidth:
        up: 1 gbps
        down: 1 gbps
    standard_user:
      password: "def456"
      bandwidth:
        up: 100 mbps
        down: 100 mbps
    basic_user:
      password: "ghi789"
      bandwidth:
        up: 50 mbps
        down: 50 mbps

bandwidth:
  up: 10 gbps
  down: 10 gbps

ignoreClientBandwidth: false  # ВАЖНО: должно быть false
```

## Важные моменты

### 1. ignoreClientBandwidth
Параметр `ignoreClientBandwidth` должен быть `false` (по умолчанию), чтобы индивидуальные лимиты работали.

### 2. Глобальный лимит
Глобальный `bandwidth` - это максимум для всего сервера. Индивидуальные лимиты не могут его превышать.

### 3. Формат значений
Поддерживаемые форматы:
- `100 mbps` или `100mbps`
- `1 gbps` или `1gbps`
- `500 kbps` или `500kbps`

### 4. Динамическое изменение
При изменении лимитов нужно:
1. Обновить конфиг файл
2. Перезапустить Hysteria сервис
3. Активные соединения будут переподключены с новыми лимитами

## Преимущества реализации

1. **Тарифные планы** - можно создавать разные уровни подписки
2. **Контроль нагрузки** - предотвращение перегрузки сервера одним пользователем
3. **Монетизация** - возможность продавать разные скорости
4. **Справедливость** - равномерное распределение ресурсов

## Рекомендуемые тарифы

```
Basic:    50 mbps  / 50 mbps
Standard: 100 mbps / 100 mbps
Premium:  500 mbps / 500 mbps
Ultimate: 1 gbps   / 1 gbps
```

## Вывод

✅ **Ограничение скорости для отдельных пользователей ВОЗМОЖНО и ПОДДЕРЖИВАЕТСЯ Hysteria2**

Реализация потребует:
- Миграция базы данных (добавить поля bandwidth)
- Обновление модуля hysteria.py
- Новые API endpoints
- Обновление UI для управления лимитами

Сложность реализации: **Средняя**
Время реализации: **2-3 часа**
