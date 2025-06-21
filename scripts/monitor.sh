#!/bin/bash

# Script de monitoreo del sistema MANUS-like
# Verifica el estado de todos los servicios y componentes

echo "🔍 MANUS-like System - Monitor de Estado"
echo "========================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para verificar servicio
check_service() {
    local service_name=$1
    local check_command=$2
    local expected_output=$3
    
    echo -n "Verificando $service_name... "
    
    if eval "$check_command" &>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ ERROR${NC}"
        return 1
    fi
}

# Función para verificar puerto
check_port() {
    local service_name=$1
    local port=$2
    local host=${3:-localhost}
    
    echo -n "Verificando $service_name (puerto $port)... "
    
    if nc -z "$host" "$port" 2>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ ERROR${NC}"
        return 1
    fi
}

# Función para verificar URL
check_url() {
    local service_name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Verificando $service_name ($url)... "
    
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ OK (HTTP $response_code)${NC}"
        return 0
    else
        echo -e "${RED}✗ ERROR (HTTP $response_code)${NC}"
        return 1
    fi
}

# Verificar dependencias del sistema
echo -e "${BLUE}📋 Verificando Dependencias del Sistema${NC}"
echo "----------------------------------------"

check_service "Docker" "docker --version"
check_service "Docker Compose" "docker-compose --version"
check_service "Ollama" "ollama --version"
check_service "Node.js" "node --version"
check_service "Python" "python3 --version"

echo ""

# Verificar servicios Docker
echo -e "${BLUE}🐳 Verificando Servicios Docker${NC}"
echo "--------------------------------"

# Verificar que los contenedores estén ejecutándose
containers=("manus-postgres" "manus-backend" "manus-frontend" "manus-redis" "manus-nginx")

for container in "${containers[@]}"; do
    echo -n "Verificando contenedor $container... "
    
    if docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
        status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
        if [ "$status" = "running" ]; then
            echo -e "${GREEN}✓ Ejecutándose${NC}"
        else
            echo -e "${YELLOW}⚠ Estado: $status${NC}"
        fi
    else
        echo -e "${RED}✗ No encontrado${NC}"
    fi
done

echo ""

# Verificar puertos
echo -e "${BLUE}🌐 Verificando Puertos${NC}"
echo "----------------------"

check_port "Frontend" 3000
check_port "Backend API" 5000
check_port "PostgreSQL" 5432
check_port "Redis" 6379
check_port "Nginx" 80
check_port "Ollama" 11434

echo ""

# Verificar URLs
echo -e "${BLUE}🔗 Verificando URLs${NC}"
echo "------------------"

check_url "Frontend" "http://localhost:3000"
check_url "Backend API" "http://localhost:5000/api/health"
check_url "Nginx Proxy" "http://localhost/health"

echo ""

# Verificar modelos de Ollama
echo -e "${BLUE}🧠 Verificando Modelos de Ollama${NC}"
echo "-------------------------------"

if command -v ollama &> /dev/null; then
    echo "Modelos instalados:"
    ollama list 2>/dev/null | tail -n +2 | while read -r line; do
        if [ -n "$line" ]; then
            model_name=$(echo "$line" | awk '{print $1}')
            echo -e "  ${GREEN}✓${NC} $model_name"
        fi
    done
    
    # Verificar que al menos un modelo esté disponible
    model_count=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
    if [ "$model_count" -eq 0 ]; then
        echo -e "${YELLOW}⚠ No hay modelos instalados${NC}"
        echo "  Ejecuta: ollama pull llama2"
    fi
else
    echo -e "${RED}✗ Ollama no está disponible${NC}"
fi

echo ""

# Verificar espacio en disco
echo -e "${BLUE}💾 Verificando Espacio en Disco${NC}"
echo "------------------------------"

disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
available_space=$(df -h . | tail -1 | awk '{print $4}')

echo "Uso del disco: $disk_usage%"
echo "Espacio disponible: $available_space"

if [ "$disk_usage" -gt 90 ]; then
    echo -e "${RED}⚠ Advertencia: Poco espacio en disco${NC}"
elif [ "$disk_usage" -gt 80 ]; then
    echo -e "${YELLOW}⚠ Espacio en disco limitado${NC}"
else
    echo -e "${GREEN}✓ Espacio en disco suficiente${NC}"
fi

echo ""

# Verificar logs recientes
echo -e "${BLUE}📝 Verificando Logs Recientes${NC}"
echo "----------------------------"

if [ -d "logs" ]; then
    echo "Últimos errores en logs:"
    find logs -name "*.log" -type f -exec grep -l "ERROR\|CRITICAL" {} \; 2>/dev/null | head -3 | while read -r logfile; do
        echo -e "  ${YELLOW}⚠${NC} Errores encontrados en: $logfile"
        tail -3 "$logfile" | grep -E "ERROR|CRITICAL" | head -1 | sed 's/^/    /'
    done
    
    if ! find logs -name "*.log" -type f -exec grep -l "ERROR\|CRITICAL" {} \; 2>/dev/null | head -1 | grep -q .; then
        echo -e "  ${GREEN}✓ No se encontraron errores recientes${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Directorio de logs no encontrado${NC}"
fi

echo ""

# Resumen final
echo -e "${BLUE}📊 Resumen del Estado${NC}"
echo "-------------------"

# Contar servicios funcionando
services_ok=0
total_services=8

# Verificar servicios críticos
critical_services=("docker" "ollama" "3000" "5000" "5432")
for service in "${critical_services[@]}"; do
    case $service in
        "docker")
            docker --version &>/dev/null && ((services_ok++))
            ;;
        "ollama")
            ollama --version &>/dev/null && ((services_ok++))
            ;;
        *)
            nc -z localhost "$service" 2>/dev/null && ((services_ok++))
            ;;
    esac
done

# Calcular porcentaje
percentage=$((services_ok * 100 / ${#critical_services[@]}))

echo "Servicios funcionando: $services_ok/${#critical_services[@]} ($percentage%)"

if [ "$percentage" -eq 100 ]; then
    echo -e "${GREEN}🎉 Sistema completamente operativo${NC}"
elif [ "$percentage" -ge 80 ]; then
    echo -e "${YELLOW}⚠ Sistema mayormente operativo${NC}"
else
    echo -e "${RED}❌ Sistema con problemas críticos${NC}"
fi

echo ""
echo "Para más detalles, ejecuta:"
echo "  docker-compose logs [servicio]"
echo "  docker stats"
echo "  ollama list"

echo ""
echo "URLs de acceso:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:5000"
echo "  Admin:    http://localhost:3000/admin"

