#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Isterika Panel - Установка         ║${NC}"
echo -e "${BLUE}║   Hysteria 2 Management Panel          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Ошибка: Запустите скрипт с правами root (sudo)${NC}"
    exit 1
fi

if [ ! -f /etc/os-release ]; then
    echo -e "${RED}Ошибка: Не удалось определить ОС${NC}"
    exit 1
fi

. /etc/os-release
if [[ "$ID" != "ubuntu" ]] || [[ "$VERSION_ID" != "24.04" ]]; then
    echo -e "${YELLOW}Предупреждение: Рекомендуется Ubuntu 24.04${NC}"
    read -p "Продолжить? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}[1/10]${NC} Запрос конфигурации..."
read -p "Введите домен (например, example.com): " DOMAIN
read -p "Введите email для ACME: " EMAIL

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo -e "${RED}Ошибка: Домен и email обязательны${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Проверка DNS записи для ${DOMAIN}...${NC}"
SERVER_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)

if [ -z "$DOMAIN_IP" ]; then
    echo -e "${RED}⚠️  Предупреждение: Не удалось разрешить домен ${DOMAIN}${NC}"
    echo -e "${YELLOW}Убедитесь, что A-запись домена указывает на ${SERVER_IP}${NC}"
    read -p "Продолжить установку? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
elif [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo -e "${RED}⚠️  Предупреждение: Домен указывает на ${DOMAIN_IP}, но IP сервера ${SERVER_IP}${NC}"
    echo -e "${YELLOW}ACME сертификат может не выдаться!${NC}"
    read -p "Продолжить установку? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ DNS настроен правильно${NC}"
fi

echo ""
echo -e "${GREEN}[2/10]${NC} Установка Hysteria 2..."
bash <(curl -fsSL https://get.hy2.sh/)

echo -e "${GREEN}[3/10]${NC} Установка зависимостей..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv pwgen curl dnsutils

echo -e "${GREEN}[4/10]${NC} Проверка портов..."
PORTS_TO_CHECK="80 443 8443"
PORTS_IN_USE=""

for port in $PORTS_TO_CHECK; do
    if ss -tuln | grep -q ":$port "; then
        PORTS_IN_USE="$PORTS_IN_USE $port"
    fi
done

if [ ! -z "$PORTS_IN_USE" ]; then
    echo -e "${YELLOW}⚠️  Предупреждение: Порты уже используются:${PORTS_IN_USE}${NC}"
    echo -e "${YELLOW}Hysteria 2 требует порты 80, 443. Панель использует 8443.${NC}"
    read -p "Продолжить? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Все необходимые порты свободны${NC}"
fi

echo -e "${GREEN}[5/10]${NC} Создание маскировочной страницы..."
mkdir -p /var/www/masq
cat > /var/www/masq/index.html << 'EOF'
<!DOCTYPE html><html><head><title>Welcome to nginx!</title><style>html { color-scheme: light dark; }body { width: 35em; margin: 0 auto;font-family: Tahoma, Verdana, Arial, sans-serif; }</style></head><body><h1>Welcome to nginx!</h1><p>If you see this page, the nginx web server is successfully installed andworking. Further configuration is required.</p><p>For online documentation and support please refer to<a href="http://nginx.org/">nginx.org</a>.<br/>Commercial support is available at<a href="http://nginx.com/">nginx.com</a>.</p><p><em>Thank you for using nginx.</em></p></body></html>
EOF

echo -e "${GREEN}[6/10]${NC} Генерация пароля для user1..."
USER1_PASSWORD=$(pwgen 40 1)

echo -e "${GREEN}[7/10]${NC} Создание конфигурации Hysteria 2..."
rm -f /etc/hysteria/config.yaml

# Create and set permissions for Hysteria working directory
mkdir -p /var/lib/hysteria
chown -R hysteria:hysteria /var/lib/hysteria 2>/dev/null || chmod -R 777 /var/lib/hysteria

cat > /etc/hysteria/config.yaml << EOF
listen: 0.0.0.0:443

acme:
  type: http
  domains:
    - ${DOMAIN}
  email: ${EMAIL}

auth:
  type: userpass
  userpass:
    user1: ${USER1_PASSWORD}

masquerade:
  type: file
  file:
    dir: /var/www/masq
  listenHTTP: :80
  listenHTTPS: :443
  forceHTTPS: true
EOF

echo -e "${GREEN}[8/10]${NC} Запуск Hysteria 2..."
systemctl start hysteria-server.service
sleep 5

if systemctl is-active --quiet hysteria-server.service; then
    echo -e "${GREEN}✓ Hysteria 2 запущен${NC}"

    # Wait for ACME certificates to be generated
    echo "Ожидание генерации SSL сертификатов..."
    for i in {1..30}; do
        if [ -f /var/lib/hysteria/acme/certificates/acme-v02.api.letsencrypt.org-directory/*/*.crt ]; then
            echo -e "${GREEN}✓ SSL сертификаты получены${NC}"
            break
        fi
        sleep 1
    done
else
    echo -e "${RED}✗ Ошибка запуска Hysteria 2${NC}"
    echo ""
    echo -e "${YELLOW}Возможные причины:${NC}"
    echo -e "  1. ${YELLOW}Не удалось получить ACME сертификат${NC}"
    echo -e "     - Проверьте, что домен ${DOMAIN} правильно указывает на этот сервер"
    echo -e "     - Убедитесь, что порты 80 и 443 открыты и доступны"
    echo -e "     - Попробуйте другой домен"
    echo ""
    echo -e "  2. ${YELLOW}Порты 80 или 443 уже заняты${NC}"
    echo -e "     - Остановите другие веб-серверы (nginx, apache)"
    echo -e "     - Проверьте: ${GREEN}ss -tuln | grep ':80\\|:443'${NC}"
    echo ""
    echo -e "${BLUE}Логи Hysteria 2:${NC}"
    journalctl -u hysteria-server.service -n 20 --no-pager
    echo ""
    echo -e "${YELLOW}Для повторной попытки запустите скрипт снова с другим доменом${NC}"
    exit 1
fi

echo -e "${GREEN}[9/10]${NC} Настройка автозапуска Hysteria 2..."
systemctl enable hysteria-server.service > /dev/null 2>&1

echo -e "${GREEN}[10/11]${NC} Установка панели управления..."
INSTALL_DIR="/opt/isterika"
mkdir -p $INSTALL_DIR

echo "Загрузка файлов проекта..."
cd $INSTALL_DIR

# Add timestamp to bypass GitHub cache
TIMESTAMP=$(date +%s)

curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/app.py?t=$TIMESTAMP" -o app.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/database.py?t=$TIMESTAMP" -o database.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/auth.py?t=$TIMESTAMP" -o auth.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/hysteria.py?t=$TIMESTAMP" -o hysteria.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/ip_blocker.py?t=$TIMESTAMP" -o ip_blocker.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/csrf_protection.py?t=$TIMESTAMP" -o csrf_protection.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/cleanup_expired.py?t=$TIMESTAMP" -o cleanup_expired.py
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/requirements.txt?t=$TIMESTAMP" -o requirements.txt

chmod +x cleanup_expired.py

mkdir -p templates static/css systemd
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/templates/login.html?t=$TIMESTAMP" -o templates/login.html
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/templates/dashboard_v2.html?t=$TIMESTAMP" -o templates/dashboard_v2.html
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/templates/settings.html?t=$TIMESTAMP" -o templates/settings.html
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/static/css/style.css?t=$TIMESTAMP" -o static/css/style.css
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/static/logo.png?t=$TIMESTAMP" -o static/logo.png
curl -fsSL "https://raw.githubusercontent.com/Th3K3rn3l/isterika/master/systemd/isterika-panel.service?t=$TIMESTAMP" -o systemd/isterika-panel.service

python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"

python3 << PYEOF
import database
import auth

database.init_db()

# Check if admin already exists
existing_admin = database.get_admin_by_username('${ADMIN_USERNAME}')
if not existing_admin:
    password_hash = auth.hash_password('${ADMIN_PASSWORD}')
    database.create_admin('${ADMIN_USERNAME}', password_hash)
    print("Admin user created")
else:
    print("Admin user already exists, skipping")

# Check if user1 already exists
existing_client = database.get_client_by_username('user1')
if not existing_client:
    database.create_client('user1', '${USER1_PASSWORD}')
    print("User1 created")
else:
    print("User1 already exists, skipping")

print("Database initialized")
PYEOF

cp systemd/isterika-panel.service /etc/systemd/system/
systemctl daemon-reload

# Stop panel if already running to reload with new code
systemctl stop isterika-panel.service 2>/dev/null || true

systemctl start isterika-panel.service
systemctl enable isterika-panel.service > /dev/null 2>&1

echo -e "${GREEN}[11/12]${NC} Настройка автоматической очистки истекших пользователей..."
# Add cron job to cleanup expired users daily at 3 AM
(crontab -l 2>/dev/null | grep -v "cleanup_expired.py"; echo "0 3 * * * cd /opt/isterika && /opt/isterika/venv/bin/python3 /opt/isterika/cleanup_expired.py >> /var/log/isterika-cleanup.log 2>&1") | crontab -
echo -e "${GREEN}✓ Cron задача добавлена (запуск каждый день в 3:00)${NC}"

echo -e "${GREEN}[12/12]${NC} Проверка установки..."
sleep 3

if systemctl is-active --quiet isterika-panel.service; then
    echo -e "${GREEN}✓ Панель запущена${NC}"
else
    echo -e "${RED}✗ Ошибка запуска панели${NC}"
    systemctl status isterika-panel.service
    exit 1
fi

SERVER_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')

# Extract secret path from database
SECRET_PATH=$(python3 << PYEOF
import sys
sys.path.insert(0, '/opt/isterika')
import database
secret = database.get_setting('secret_path')
print(secret if secret else '')
PYEOF
)

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Установка завершена!            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📱 Панель управления${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  🌐 URL (IP):     ${GREEN}https://${SERVER_IP}:8443/${SECRET_PATH}${NC}"
echo -e "  🌐 URL (Домен):  ${GREEN}https://${DOMAIN}:8443/${SECRET_PATH}${NC}"
echo -e "  👤 Логин:        ${GREEN}${ADMIN_USERNAME}${NC}"
echo -e "  🔑 Пароль:       ${GREEN}${ADMIN_PASSWORD}${NC}"
echo -e "  ${YELLOW}⚠️  Смените пароль после первого входа!${NC}"
echo -e "  ${YELLOW}⚠️  Сохраните секретный путь: /${SECRET_PATH}${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 Hysteria 2 Server${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  🌍 Домен:        ${GREEN}${DOMAIN}${NC}"
echo -e "  🔌 Порт:         ${GREEN}443${NC}"
echo -e "  ✅ Статус:       ${GREEN}Запущен${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}👤 Первый пользователь${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Имя:             ${GREEN}user1${NC}"
echo -e "  Пароль:          ${GREEN}${USER1_PASSWORD}${NC}"
echo ""
echo -e "${YELLOW}⚠️  ВАЖНО: Сохраните эти данные в безопасном месте!${NC}"
echo ""
echo -e "${BLUE}📝 Следующие шаги:${NC}"
echo -e "  1. Откройте панель в браузере"
echo -e "  2. Войдите с логином ${GREEN}admin${NC}"
echo -e "  3. Добавьте новых пользователей через UI"
echo -e "  4. Скопируйте ссылки подключения для клиентов"
echo ""
echo -e "${BLUE}🔧 Полезные команды:${NC}"
echo -e "  Статус Hysteria:  ${GREEN}systemctl status hysteria-server${NC}"
echo -e "  Статус панели:    ${GREEN}systemctl status isterika-panel${NC}"
echo -e "  Логи Hysteria:    ${GREEN}journalctl -u hysteria-server -f${NC}"
echo -e "  Логи панели:      ${GREEN}journalctl -u isterika-panel -f${NC}"
echo ""
