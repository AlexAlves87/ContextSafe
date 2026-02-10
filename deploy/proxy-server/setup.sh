#!/bin/bash
# ContextSafe Proxy Server Setup
# ===============================

set -e

echo "=== ContextSafe Proxy Server Setup ==="

# Verificar .env
if [ ! -f .env ]; then
    echo "Error: Crear .env desde .env.example"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

source .env

if [ -z "$DOMAIN" ] || [ -z "$BACKEND_HOST" ] || [ -z "$GOOGLE_CLIENT_ID" ]; then
    echo "Error: Configurar DOMAIN, BACKEND_HOST y GOOGLE_CLIENT_ID en .env"
    exit 1
fi

echo "Dominio: $DOMAIN"
echo "Backend: $BACKEND_HOST:$BACKEND_PORT"

# Configurar nginx con valores reales
echo "Configurando nginx..."
sed -i "s/BACKEND_IP/$BACKEND_HOST/g" nginx.conf
sed -i "s/DOMAIN/$DOMAIN/g" nginx.conf

# Crear directorios certbot
mkdir -p certbot/conf certbot/www

# Certificado temporal para arrancar nginx
echo "Creando certificado temporal..."
mkdir -p "certbot/conf/live/$DOMAIN"
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "certbot/conf/live/$DOMAIN/privkey.pem" \
    -out "certbot/conf/live/$DOMAIN/fullchain.pem" \
    -subj "/CN=localhost" 2>/dev/null

# Build frontend
echo "Building frontend..."
docker compose build frontend

# Arrancar nginx
echo "Arrancando nginx..."
docker compose up -d frontend
sleep 5

# Verificar que el backend responde
echo "Verificando conexión al backend..."
if curl -sf "http://$BACKEND_HOST:$BACKEND_PORT/health" > /dev/null; then
    echo "✓ Backend accesible"
else
    echo "✗ Backend no responde en $BACKEND_HOST:$BACKEND_PORT"
    echo "  Verificar que el servidor GPU está encendido y el API corriendo"
fi

# Obtener certificado real
echo ""
echo "Obteniendo certificado SSL..."
rm -rf "certbot/conf/live/$DOMAIN"

docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $LETSENCRYPT_EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Reiniciar nginx
docker compose restart frontend

echo ""
echo "=== Setup Completado ==="
echo ""
echo "URL: https://$DOMAIN"
echo ""
echo "Google Cloud Console - Añadir:"
echo "  Authorized JavaScript origins: https://$DOMAIN"
echo "  Authorized redirect URIs: https://$DOMAIN"
