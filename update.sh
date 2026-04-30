#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Isterika Panel - Обновление        ║${NC}"
echo -e "${BLUE}║   Hysteria 2 Management Panel          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Ошибка: Запустите скрипт с правами root (sudo)${NC}"
    exit 1
fi

INSTALL_DIR="/opt/isterika"

if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}Ошибка: Isterika Panel не установлена${NC}"
    echo -e "${YELLOW}Используйте install.sh для первой установки${NC}"
    exit 1
fi

echo -e "${YELLOW}Обновление Isterika Panel до версии 2.0${NC}"
echo ""

echo -e "${GREEN}[1/7]${NC} Остановка панели..."
systemctl stop isterika-panel.service

echo -e "${GREEN}[2/7]${NC} Создание резервной копии..."
BACKUP_DIR="/opt/isterika-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp "$INSTALL_DIR/isterika.db" "$BACKUP_DIR/" 2>/dev/null || true
cp "/etc/hysteria/config.yaml" "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓ Резервная копия создана: $BACKUP_DIR${NC}"

echo -e "${GREEN}[3/7]${NC} Загрузка обновлений..."
cd "$INSTALL_DIR"
TIMESTAMP=$(date +%s)

# Download all Python modules
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/app.py?t=$TIMESTAMP" -o app.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/database.py?t=$TIMESTAMP" -o database.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/auth.py?t=$TIMESTAMP" -o auth.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/hysteria.py?t=$TIMESTAMP" -o hysteria.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/ip_blocker.py?t=$TIMESTAMP" -o ip_blocker.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/csrf_protection.py?t=$TIMESTAMP" -o csrf_protection.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/cleanup_expired.py?t=$TIMESTAMP" -o cleanup_expired.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/requirements.txt?t=$TIMESTAMP" -o requirements.txt

chmod +x cleanup_expired.py

# Download templates
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/templates/login.html?t=$TIMESTAMP" -o templates/login.html
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/templates/dashboard_v2.html?t=$TIMESTAMP" -o templates/dashboard_v2.html
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/templates/settings.html?t=$TIMESTAMP" -o templates/settings.html
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/static/css/style.css?t=$TIMESTAMP" -o static/css/style.css
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/static/logo.png?t=$TIMESTAMP" -o static/logo.png

echo -e "${GREEN}✓ Файлы обновлены${NC}"

echo -e "${GREEN}[4/7]${NC} Обновление зависимостей..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
deactivate
echo -e "${GREEN}✓ Зависимости обновлены${NC}"

echo -e "${GREEN}[5/7]${NC} Проверка конфигурации Hysteria2..."
if ! grep -q "ignoreClientBandwidth" /etc/hysteria/config.yaml; then
    echo "ignoreClientBandwidth: false" >> /etc/hysteria/config.yaml
    echo -e "${GREEN}✓ Добавлен параметр ignoreClientBandwidth${NC}"
else
    # Update existing value
    sed -i 's/ignoreClientBandwidth:.*/ignoreClientBandwidth: false/' /etc/hysteria/config.yaml
    echo -e "${GREEN}✓ Обновлен параметр ignoreClientBandwidth${NC}"
fi

echo -e "${GREEN}[6/7]${NC} Перезапуск служб..."
systemctl restart hysteria-server.service
systemctl restart isterika-panel.service

echo -e "${GREEN}[7/7]${NC} Проверка установки..."
sleep 3

if systemctl is-active --quiet isterika-panel.service; then
    echo -e "${GREEN}✓ Панель запущена${NC}"
else
    echo -e "${RED}✗ Ошибка запуска панели${NC}"
    echo -e "${YELLOW}Восстановление из резервной копии...${NC}"
    cp "$BACKUP_DIR/isterika.db" "$INSTALL_DIR/" 2>/dev/null || true
    cp "$BACKUP_DIR/config.yaml" "/etc/hysteria/" 2>/dev/null || true
    systemctl restart isterika-panel.service
    echo -e "${RED}Обновление отменено. Проверьте логи: journalctl -u isterika-panel -n 50${NC}"
    exit 1
fi

if systemctl is-active --quiet hysteria-server.service; then
    echo -e "${GREEN}✓ Hysteria2 запущен${NC}"
else
    echo -e "${YELLOW}⚠️  Hysteria2 не запущен, проверьте конфигурацию${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      Обновление завершено!             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}🎉 Isterika Panel обновлена до версии 2.0${NC}"
echo ""
echo -e "${BLUE}Что нового:${NC}"
echo -e "  ✨ Полный glassmorphism дизайн"
echo -e "  🔒 IP блокировка после неудачных попыток входа"
echo -e "  ⚡ Ограничение скорости для пользователей"
echo -e "  🔍 Поиск пользователей в реальном времени"
echo -e "  🛡️  CSRF защита на всех API endpoints"
echo ""
echo -e "${BLUE}Резервная копия сохранена в: ${GREEN}$BACKUP_DIR${NC}"
echo ""
echo -e "${YELLOW}Рекомендации:${NC}"
echo -e "  1. Откройте панель и проверьте работу"
echo -e "  2. Смените пароль администратора"
echo -e "  3. Проверьте существующих пользователей"
echo ""
