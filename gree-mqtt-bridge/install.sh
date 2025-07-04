#!/bin/bash

echo "=== Gree MQTT Bridge - Instalação ==="
echo

# Detecta sistema operacional
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "✓ Sistema Linux detectado"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✓ Sistema macOS detectado"
else
    echo "⚠️  Sistema não reconhecido, continuando..."
fi

# Verifica se Python 3.8+ está instalado
python_version=$(python3 --version 2>/dev/null | cut -d" " -f2)
if [[ -z "$python_version" ]]; then
    echo "❌ Python 3 não encontrado!"
    echo "Instale Python 3.8+ antes de continuar"
    exit 1
fi

echo "✓ Python $python_version encontrado"

# Cria ambiente virtual
echo "📦 Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

# Atualiza pip
echo "📦 Atualizando pip..."
pip install --upgrade pip

# Instala dependências
echo "📦 Instalando dependências Python..."
cat > requirements.txt << EOF
paho-mqtt>=1.6.0
cryptography>=3.4.8
PyYAML>=6.0
asyncio-mqtt>=0.11.0
EOF

pip install -r requirements.txt

# Cria configuração inicial
echo "⚙️  Criando configuração inicial..."
python3 gree_mqtt_bridge.py --create-config

# Verifica se o arquivo foi criado
if [[ -f "config.yaml" ]]; then
    echo "✓ Arquivo config.yaml criado"
else
    echo "❌ Erro ao criar config.yaml"
    exit 1
fi

# Descobre dispositivos Gree na rede
echo "🔍 Descobrindo dispositivos Gree na rede..."
echo "   (Aguarde 10 segundos...)"
python3 gree_mqtt_bridge.py --discover

echo
echo "=== Instalação Concluída! ==="
echo
echo "Próximos passos:"
echo "1. Edite o arquivo config.yaml com suas configurações MQTT"
echo "2. Configure dispositivos manualmente se necessário"
echo "3. Execute: python3 gree_mqtt_bridge.py"
echo
echo "Para ajuda: python3 gree_mqtt_bridge.py --help"