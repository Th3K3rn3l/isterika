#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}╔════════════════════════════════════════╗${NC}"
echo -e "${RED}║     Isterika Panel - Удаление          ║${NC}"
echo -e "${RED}║   Hysteria 2 Management Panel          ║${NC}"
echo -e "${RED}╚════════════════════════════════════════╝${NC}"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Ошибка: Запустите скрипт с правами root (sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Это удалит:${NC}"
echo -e "  - Hysteria 2 сервер и все его конфигурации"
echo -e "  - Панель управления Isterika"
echo -e "  - Все пользовательские данные и базу данных"
echo -e "  - SSL сертификаты ACME"
echo ""
read -p "Вы уверены? Введите 'yes' для подтверждения: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${GREEN}Отменено${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}[1/8]${NC} Остановка служб..."
systemctl stop isterika-panel.service 2>/dev/null || true
systemctl stop hysteria-server.service 2>/dev/null || true

echo -e "${GREEN}[2/8]${NC} Отключение автозапуска..."
systemctl disable isterika-panel.service 2>/dev/null || true
systemctl disable hysteria-server.service 2>/dev/null || true

echo -e "${GREEN}[3/8]${NC} Удаление systemd сервисов..."
rm -f /etc/systemd/system/isterika-panel.service
rm -f /etc/systemd/system/hysteria-server.service
rm -f /etc/systemd/system/hysteria-server@.service
systemctl daemon-reload

echo -e "${GREEN}[4/8]${NC} Удаление панели управления..."
rm -rf /opt/isterika

echo -e "${GREEN}[5/8]${NC} Удаление Hysteria 2..."
rm -f /usr/local/bin/hysteria
rm -rf /etc/hysteria
rm -rf /var/lib/hysteria/*
# Keep /var/lib/hysteria directory for future installations

echo -e "${GREEN}[6/8]${NC} Удаление маскировочной страницы..."
rm -rf /var/www/masq

echo -e "${GREEN}[7/9]${NC} Удаление cron задачи..."
crontab -l 2>/dev/null | grep -v "cleanup_expired.py" | crontab - 2>/dev/null || true
rm -f /var/log/isterika-cleanup.log

echo -e "${GREEN}[8/9]${NC} Удаление зависимостей (опционально)..."
read -p "Удалить Python зависимости? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    apt-get remove -y python3-pip python3-venv pwgen 2>/dev/null || true
    apt-get autoremove -y 2>/dev/null || true
fi

echo -e "${GREEN}[9/9]${NC} Очистка..."
# Remove any leftover files
find /tmp -name "hysteria*" -delete 2>/dev/null || true
find /tmp -name "isterika*" -delete 2>/dev/null || true

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Удаление завершено!             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Все компоненты Isterika Panel и Hysteria 2 удалены.${NC}"
echo ""
echo -e "${YELLOW}Примечание:${NC}"
echo -e "  - Порты 80, 443, 8443 теперь свободны"
echo -e "  - Для повторной установки используйте install.sh"
echo ""
