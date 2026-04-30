# 🎉 Isterika Panel v2.0 - Major Update

## 🚀 Что нового в версии 2.0

### 🎨 Полный редизайн - 100% Glassmorphism
Панель полностью переделана с премиум глассморфизм дизайном:
- ✨ Анимированные градиентные фоны с плавающими частицами
- 💎 Стеклянные карточки с backdrop blur эффектами
- 🌈 Яркая цветовая палитра (purple, pink, blue, cyan)
- 🎭 Плавные анимации и hover эффекты
- 🔮 Градиентные кнопки и текст

### 🔒 Безопасность
- **IP блокировка**: Автоматическая блокировка после 5 неудачных попыток входа (15 минут)
- **CSRF защита**: На всех API endpoints
- **Мониторинг**: Отображение заблокированных IP в Settings с таймером
- **Rate limiting**: Ограничение запросов с Flask-Limiter

### 🔍 Управление пользователями
- **Поиск в реальном времени**: Мгновенная фильтрация пользователей
- **Улучшенная таблица**: Визуальное отображение всех параметров

### ⚡ Ограничение скорости (NEW!)
- **Индивидуальные лимиты**: Установка upload/download скорости для каждого пользователя
- **Гибкие единицы**: Поддержка Mbps и Gbps
- **Режим Unlimited**: Без ограничений скорости
- **Визуализация**: Иконки 🔼 upload и 🔽 download в таблице
- **Редактирование**: Изменение лимитов для существующих пользователей
- **Интеграция**: Полная поддержка Hysteria2

## 📦 Установка

### Быстрая установка (Ubuntu 24.04)

```bash
# Клонировать репозиторий
git clone https://github.com/Th3K3rn3l/isterika.git
cd isterika

# Запустить установку
sudo bash install.sh
```

Скрипт автоматически:
- Установит все зависимости
- Настроит Hysteria2
- Создаст базу данных
- Настроит systemd сервис
- Получит SSL сертификаты

### Требования
- Ubuntu 24.04 (рекомендуется)
- Python 3.10+
- Домен с A записью на ваш сервер
- Порты 443, 8443 открыты

## 🎯 Использование

### Первый вход
1. Откройте `https://your-domain.com:8443/SECRET_PATH`
2. Логин: `admin`
3. Пароль: `admin123`
4. **Обязательно смените пароль при первом входе!**

### Создание пользователя с ограничением скорости

1. Нажмите **"Add User"**
2. Введите имя пользователя и дату истечения
3. В секции **"Bandwidth Limits"**:
   - Нажмите **"Set Limits"** для установки ограничений
   - Или оставьте **"Unlimited"** для неограниченной скорости
4. Введите значения upload/download
5. Выберите единицу измерения (Mbps/Gbps)
6. Нажмите **"Add User"**

### Примеры тарифных планов

```
Basic:    50 Mbps  ↕️
Standard: 100 Mbps ↕️
Premium:  500 Mbps ↕️
Ultimate: 1 Gbps   ↕️
Unlimited: ∞
```

## 🔧 Технические детали

### Новые модули
- `ip_blocker.py` - Система блокировки IP
- `csrf_protection.py` - CSRF защита

### База данных
Автоматическая миграция добавляет поля:
- `bandwidth_up` - Ограничение upload
- `bandwidth_down` - Ограничение download

### API Endpoints

#### Создание пользователя с bandwidth
```bash
POST /api/clients
{
  "username": "user1",
  "expires_at": "2026-12-31",
  "bandwidth_up": "100 mbps",
  "bandwidth_down": "100 mbps"
}
```

#### Обновление bandwidth
```bash
PUT /api/clients/user1/bandwidth
{
  "bandwidth_up": "200 mbps",
  "bandwidth_down": "200 mbps"
}
```

#### Просмотр заблокированных IP
```bash
GET /api/security/blocked-ips
```

## 📚 Документация

- [BANDWIDTH_LIMITING_GUIDE.md](BANDWIDTH_LIMITING_GUIDE.md) - Руководство по ограничению скорости
- [BANDWIDTH_LIMITING_ANALYSIS.md](BANDWIDTH_LIMITING_ANALYSIS.md) - Технический анализ
- [GLASSMORPHISM_DESIGN.md](GLASSMORPHISM_DESIGN.md) - Описание дизайна
- [NEW_FEATURES.md](NEW_FEATURES.md) - Новые функции
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Инструкция по тестированию
- [SECURITY_FIXES.md](SECURITY_FIXES.md) - Исправления безопасности

## 🔄 Обновление с v1.x

```bash
cd isterika
git pull origin master
sudo systemctl restart isterika
```

База данных обновится автоматически при первом запуске.

## 🎨 Скриншоты

### Dashboard
- Анимированный градиентный фон
- Стеклянные stat cards
- Таблица пользователей с bandwidth
- Поиск в реальном времени

### Login
- Премиум стеклянная форма
- Пульсирующий логотип
- Градиентная кнопка входа

### Settings
- Управление паролем и username
- Секретный путь
- Мониторинг заблокированных IP

## 🛠️ Разработка

### Структура проекта
```
isterika/
├── app.py                 # Основное приложение Flask
├── database.py            # Работа с SQLite
├── hysteria.py            # Управление Hysteria2
├── auth.py                # Аутентификация
├── ip_blocker.py          # Блокировка IP
├── csrf_protection.py     # CSRF защита
├── templates/
│   ├── dashboard_v2.html  # Главная панель
│   ├── login.html         # Страница входа
│   └── settings.html      # Настройки
├── static/
│   ├── css/
│   └── logo.png
└── install.sh             # Скрипт установки
```

### Запуск в dev режиме
```bash
python app.py
```

## 🐛 Устранение проблем

### Ограничения скорости не работают
1. Проверьте конфигурацию: `cat /etc/hysteria/config.yaml`
2. Убедитесь что `ignoreClientBandwidth: false`
3. Перезапустите: `sudo systemctl restart hysteria-server`

### IP блокировка не работает
- Блокировки хранятся в памяти и сбрасываются при перезапуске
- Проверьте логи: `sudo journalctl -u isterika -f`

### Проблемы с дизайном
- Очистите кэш браузера (Ctrl+Shift+R)
- Проверьте поддержку backdrop-filter в браузере
- Используйте современный браузер (Chrome 76+, Firefox 103+)

## 📊 Статистика изменений

- **Файлов изменено**: 7
- **Новых файлов**: 11
- **Строк добавлено**: 2729
- **Строк удалено**: 230
- **Коммитов**: 1 major update

## 🤝 Вклад

Проект открыт для вклада! Создавайте issues и pull requests.

## 📝 Лицензия

MIT License

## 👨‍💻 Автор

**Th3K3rn3l**
- GitHub: [@Th3K3rn3l](https://github.com/Th3K3rn3l)

## 🙏 Благодарности

- Hysteria2 team за отличный протокол
- Claude AI за помощь в разработке
- Сообщество за фидбек и тестирование

---

**Версия**: 2.0.0  
**Дата релиза**: 28.04.2026  
**Статус**: Production Ready ✅

🌟 Если проект понравился - поставьте звезду на GitHub!
