<div align="center">

# 🚀 Isterika Panel

### Modern Web Panel for Hysteria 2

<img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python">
<img src="https://img.shields.io/badge/Flask-3.0+-green.svg" alt="Flask">
<img src="https://img.shields.io/badge/Hysteria-2-purple.svg" alt="Hysteria 2">
<img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">

**Красивая, легковесная и функциональная панель управления для Hysteria 2**

[Возможности](#-возможности) • [Установка](#-установка) • [Документация](#-документация)

</div>

---

## ⚠️ Дисклеймер

> **ВНИМАНИЕ:** Этот проект предназначен исключительно для образовательных целей и легального использования в соответствии с законодательством вашей страны. Автор не несет ответственности за использование данного программного обеспечения в незаконных целях и не призывает к обходу блокировок или нарушению законодательства. Используйте на свой страх и риск.

---

## ✨ Возможности

- 🎨 **Современный дизайн** - Темная тема с градиентами, glassmorphism и плавными анимациями
- 👥 **Управление пользователями** - Добавление, удаление, редактирование и просмотр клиентов Hysteria 2
- 📅 **Система подписок** - Автоматическая блокировка истекших пользователей (cron), цветовая индикация срока
- ⏰ **Автоматическая очистка** - Ежедневная проверка и блокировка истекших подписок (пользователи остаются в панели)
- 📱 **QR-коды** - Быстрое подключение через сканирование QR-кода
- 📊 **Мониторинг в реальном времени** - CPU, RAM, Network и статус сервиса
- 🚀 **Speedtest** - Встроенная проверка скорости интернета с прогрессивным отображением
- 🔗 **Генерация ссылок** - Автоматическое создание hysteria2:// ссылок через команду `hysteria share`
- ⚙️ **Настройки** - Смена пароля, username, секретного URL пути
- 🔒 **Секретный URL** - Защита панели через случайный путь в URL
- 🔐 **HTTPS** - Автоматические ACME сертификаты через Hysteria 2
- ⚡ **Легковесность** - Минимальное потребление ресурсов (~15MB зависимостей)
- 🚀 **Установка одной командой** - Полная автоматизация на Ubuntu 24.04

## 📦 Установка

### Установка одной командой

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/install.sh)
```

### Альтернативный способ

```bash
wget -O - https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/install.sh | bash
```

Скрипт автоматически:
- ✅ Установит Hysteria 2 через официальный скрипт
- ✅ Настроит ACME сертификаты для вашего домена
- ✅ Создаст маскировочную nginx страницу
- ✅ Установит и запустит панель управления
- ✅ Создаст первого пользователя с автогенерацией пароля
- ✅ Настроит cron задачу для автоматической блокировки истекших пользователей (ежедневно в 3:00)

### Удаление

Полное удаление панели и всех компонентов:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/uninstall.sh)
```

Скрипт удалит:
- ❌ Hysteria 2 сервер и конфигурации
- ❌ Панель управления Isterika
- ❌ Базу данных и пользовательские данные
- ❌ SSL сертификаты ACME
- ❌ Systemd сервисы

### Требования

- Ubuntu 24.04 (рекомендуется)
- Root доступ
- Домен с A-записью на ваш сервер
- Открытые порты: 80, 443, 8443

### После установки

Панель будет доступна по адресу:
```
https://ваш-домен:8443/секретный-путь
```

Секретный путь будет показан в конце установки. Сохраните его!

Логин: `admin`  
Пароль: `admin123`

⚠️ **Обязательно смените пароль после первого входа!** Панель автоматически попросит это сделать.

## 🖼️ Интерфейс

### 🎨 Современный дизайн
- Темная тема с градиентами
- Плавные анимации и переходы
- Адаптивная верстка для всех устройств
- Интуитивно понятный интерфейс

### 📊 Панель управления
- Мониторинг ресурсов в реальном времени
- Управление пользователями одним кликом
- Быстрая генерация ссылок подключения
- Контроль статуса Hysteria 2 сервиса

## 🛠️ Технологии

| Компонент | Технология |
|-----------|-----------|
| Backend | Python 3.12 + Flask |
| Frontend | Alpine.js + Tailwind CSS |
| Database | SQLite |
| Proxy | Hysteria 2 |
| Auth | Bcrypt |
| Monitoring | psutil |

## 📁 Структура проекта

```
isterika/
├── install.sh              # Скрипт автоматической установки
├── app.py                  # Flask приложение с API endpoints
├── database.py             # SQLite модели и CRUD операции
├── hysteria.py             # Интеграция с Hysteria 2
├── auth.py                 # Аутентификация и безопасность
├── requirements.txt        # Python зависимости
├── templates/
│   ├── login.html         # Страница входа
│   └── dashboard.html     # Главная панель (SPA)
├── static/
│   └── css/
│       └── style.css      # Кастомные стили и анимации
└── systemd/
    └── isterika-panel.service  # Systemd сервис
```

## 🔧 API Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/stats` | GET | Статистика сервера (CPU, RAM, Network) |
| `/api/speedtest` | POST | Запуск теста скорости (download) |
| `/api/speedtest/upload` | POST | Запуск теста скорости (upload) |
| `/api/server/status` | GET | Статус Hysteria 2 сервиса |
| `/api/server/restart` | POST | Перезапуск Hysteria 2 |
| `/api/clients` | GET | Список всех клиентов |
| `/api/clients` | POST | Добавить нового клиента |
| `/api/clients/<username>` | DELETE | Удалить клиента |
| `/api/clients/<username>/expires` | PUT | Обновить дату истечения подписки |
| `/api/clients/<username>/share` | GET | Получить ссылку подключения |
| `/api/clients/<username>/qr` | GET | Получить QR-код для подключения |
| `/api/settings/password` | POST | Сменить пароль администратора |
| `/api/settings/username` | POST | Сменить username администратора |
| `/api/settings/secret-path` | POST | Сменить секретный URL путь |

## 🔐 Безопасность

- ✅ Пароли хешируются с помощью bcrypt
- ✅ Защита от CSRF атак
- ✅ Безопасные Flask сессии с secret key
- ✅ Валидация всех входных данных
- ✅ Изоляция процессов через systemd

## 📚 Документация

### Управление подписками

Панель автоматически блокирует пользователей с истекшими подписками:
- Cron задача запускается каждый день в 3:00
- Истекшие пользователи удаляются из конфига Hysteria (блокировка доступа)
- Пользователи остаются в панели со статусом "Expired"
- Для продления подписки используйте кнопку "Edit" и измените дату
- После продления пользователь автоматически разблокируется

### Просмотр логов автоматической очистки

```bash
sudo tail -f /var/log/isterika-cleanup.log
```

### Добавление пользователя вручную

```bash
# Генерация пароля
pwgen 40 1

# Редактирование конфига
sudo nano /etc/hysteria/config.yaml

# Добавьте в блок auth.userpass:
auth:
  type: userpass
  userpass:
    username: password

# Перезапуск сервиса
sudo systemctl restart hysteria-server.service
```

### Просмотр логов

```bash
# Логи Hysteria 2
sudo journalctl -u hysteria-server.service -f

# Логи панели
sudo journalctl -u isterika-panel.service -f
```

### Обновление панели

```bash
cd /opt/isterika
git pull
sudo systemctl restart isterika-panel.service
```

## 🤝 Вклад в проект

Приветствуются любые улучшения! Создавайте Issues и Pull Requests.

1. Fork проекта
2. Создайте ветку (`git checkout -b feature/amazing`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## ⭐ Поддержка

Если проект вам понравился, поставьте звезду ⭐

---

<div align="center">

**Сделано с ❤️ для сообщества Hysteria 2**

[GitHub](https://github.com/Th3K3rn3l/isterika) • [Issues](https://github.com/Th3K3rn3l/isterika/issues)

</div>
