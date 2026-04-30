# 🔄 Руководство по обновлению Isterika Panel

## Обновление с v1.x до v2.0

### Автоматическое обновление (Рекомендуется)

```bash
cd /opt/isterika
sudo bash <(curl -fsSL https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/update.sh)
```

### Ручное обновление

#### 1. Остановите панель
```bash
sudo systemctl stop isterika-panel
```

#### 2. Создайте резервную копию
```bash
sudo cp /opt/isterika/isterika.db /opt/isterika/isterika.db.backup
sudo cp /etc/hysteria/config.yaml /etc/hysteria/config.yaml.backup
```

#### 3. Загрузите новые файлы
```bash
cd /opt/isterika
TIMESTAMP=$(date +%s)

# Основные модули
sudo curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/app.py?t=$TIMESTAMP" -o app.py
sudo curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/database.py?t=$TIMESTAMP" -o database.py
sudo curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/auth.py?t=$TIMESTAMP" -o auth.py
sudo curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/hysteria.py?t=$TIMESTAMP" -o hysteria.py

# Новые модули безопасности
sudo curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/ip_blocker.py?t=$TIMESTAMP" -o ip_blocker.py
sudo curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/csrf_protection.py?t=$TIMESTAMP" -o csrf_protection.py

# Обновленные шаблоны
sudo curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/templates/login.html?t=$TIMESTAMP" -o templates/login.html
sudo curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/templates/dashboard_v2.html?t=$TIMESTAMP" -o templates/dashboard_v2.html
sudo curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/templates/settings.html?t=$TIMESTAMP" -o templates/settings.html

# Обновить requirements.txt
sudo curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/requirements.txt?t=$TIMESTAMP" -o requirements.txt
```

#### 4. Установите новые зависимости
```bash
cd /opt/isterika
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
deactivate
```

#### 5. Обновите базу данных
База данных обновится автоматически при первом запуске панели.

#### 6. Обновите конфигурацию Hysteria2 (если нужно)
```bash
# Убедитесь, что ignoreClientBandwidth установлен в false
sudo nano /etc/hysteria/config.yaml
```

Добавьте или измените:
```yaml
ignoreClientBandwidth: false
```

#### 7. Перезапустите службы
```bash
sudo systemctl restart hysteria-server
sudo systemctl restart isterika-panel
```

#### 8. Проверьте статус
```bash
sudo systemctl status isterika-panel
sudo systemctl status hysteria-server
```

## Что нового в v2.0

### 🎨 Дизайн
- Полный редизайн с glassmorphism эффектами
- Анимированные градиентные фоны
- Улучшенная визуализация данных

### 🔒 Безопасность
- **IP блокировка**: Автоматическая блокировка после 5 неудачных попыток входа
- **CSRF защита**: На всех API endpoints
- **Rate limiting**: Ограничение запросов

### ⚡ Новые функции
- **Ограничение скорости**: Индивидуальные лимиты upload/download для каждого пользователя
- **Поиск в реальном времени**: Мгновенная фильтрация пользователей
- **Мониторинг безопасности**: Отображение заблокированных IP в Settings

## Откат к предыдущей версии

Если что-то пошло не так:

```bash
# Остановите панель
sudo systemctl stop isterika-panel

# Восстановите базу данных
sudo cp /opt/isterika/isterika.db.backup /opt/isterika/isterika.db

# Восстановите конфигурацию Hysteria
sudo cp /etc/hysteria/config.yaml.backup /etc/hysteria/config.yaml

# Переустановите старую версию
cd /tmp
git clone -b v1.0 https://github.com/Th3K3rn3l/isterika.git isterika-old
sudo cp -r isterika-old/* /opt/isterika/

# Перезапустите
sudo systemctl restart hysteria-server
sudo systemctl restart isterika-panel
```

## Проверка версии

После обновления откройте панель и проверьте версию в футере страницы входа:
```
Isterika Panel v2.0
```

## Устранение проблем

### Панель не запускается
```bash
# Проверьте логи
sudo journalctl -u isterika-panel -n 50

# Проверьте наличие всех файлов
ls -la /opt/isterika/*.py
```

### Ошибка "ModuleNotFoundError"
```bash
# Переустановите зависимости
cd /opt/isterika
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl restart isterika-panel
```

### Ограничения скорости не работают
```bash
# Проверьте конфигурацию Hysteria
cat /etc/hysteria/config.yaml | grep ignoreClientBandwidth

# Должно быть: ignoreClientBandwidth: false
# Если нет, добавьте и перезапустите
sudo systemctl restart hysteria-server
```

### CSRF ошибки
```bash
# Очистите кэш браузера (Ctrl+Shift+R)
# Или откройте панель в режиме инкогнито
```

## Поддержка

Если у вас возникли проблемы:
1. Проверьте логи: `sudo journalctl -u isterika-panel -f`
2. Создайте issue на GitHub: https://github.com/Th3K3rn3l/isterika/issues
3. Включите подробную информацию: версия ОС, логи ошибок, шаги воспроизведения

---

**Версия документа**: 2.0.0  
**Дата**: 28.04.2026
