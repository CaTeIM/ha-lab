# Gree MQTT Bridge para Home Assistant

Este `README.md` fornece instruções detalhadas para configurar a integração `gree-mqtt-bridge` com o Home Assistant, utilizando o protocolo MQTT para controle de ar condicionados Gree. Esta abordagem é recomendada devido à sua robustez e flexibilidade, superando as limitações das integrações diretas.

## Sumário

1.  [Por que MQTT?](#por-que-mqtt)
2.  [Pré-requisitos](#pré-requisitos)
3.  [Instalação](#instalação)
    *   [Opção 1: Diretamente no Host do Home Assistant (Recomendado)](#opção-1-diretamente-no-host-do-home-assistant-recomendado)
    *   [Opção 2: Container Docker Separado](#opção-2-container-docker-separado)
    *   [Opção 3: Máquina Separada na Mesma Rede](#opção-3-máquina-separada-na-mesma-rede)
4.  [Configuração do config.yaml](#configuração-do-configyaml)
5.  [Execução e Teste](#execução-e-teste)
6.  [Monitoramento no Home Assistant](#monitoramento-no-home-assistant)

## Por que MQTT?

A integração de ar condicionados Gree com o Home Assistant tem sido um desafio devido à instabilidade das integrações diretas e ao protocolo proprietário da Gree. A abordagem via MQTT bridge oferece uma solução mais confiável e flexível, conforme detalhado na análise crítica [1].

### Vantagens do MQTT:

*   **Desacoplamento:** Cria uma camada de abstração entre o Home Assistant e o dispositivo, tornando a comunicação mais resiliente a mudanças no firmware do AC.
*   **Confiabilidade:** Protocolo robusto com Quality of Service (QoS) e reconexão automática, garantindo que as mensagens sejam entregues mesmo em condições de rede instáveis.
*   **Debugging:** Facilita o monitoramento das mensagens trocadas entre o bridge e o Home Assistant através de ferramentas como o MQTT Explorer.
*   **Flexibilidade:** Permite que múltiplos clientes se conectem ao broker MQTT simultaneamente, possibilitando outras automações ou visualizações.
*   **Padronização:** Segue as convenções do Home Assistant para MQTT Discovery, o que simplifica a adição automática de dispositivos.

### Desvantagens do MQTT:

*   **Complexidade Adicional:** Requer a instalação e manutenção de um broker MQTT (como o Mosquitto).
*   **Latência:** Adiciona uma camada extra de comunicação, o que pode introduzir uma pequena latência, embora geralmente imperceptível para controle de AC.
*   **Dependência:** Mais um serviço para manter em sua infraestrutura.
*   **Overhead:** Consome mais recursos do sistema em comparação com uma integração direta, mas o benefício da estabilidade geralmente compensa.

## Pré-requisitos

Antes de iniciar a instalação, certifique-se de ter os seguintes pré-requisitos:

*   **Home Assistant:** Instância do Home Assistant funcionando.
*   **Mosquitto Broker:** Add-on Mosquitto Broker instalado e configurado no Home Assistant.
*   **Integração MQTT:** A integração MQTT do Home Assistant deve estar configurada e conectada ao Mosquitto Broker.
*   **Acesso SSH:** Acesso SSH ao host do Home Assistant (recomendado) ou ambiente Linux/Docker para hospedar o bridge.

## Instalação

Você pode escolher uma das seguintes opções para instalar o `gree-mqtt-bridge`:

### Opção 1: Diretamente no Host do Home Assistant (Recomendado)

Esta opção é ideal se você tem acesso SSH ao seu Home Assistant e deseja que o bridge seja executado diretamente no mesmo ambiente.

1.  **Conecte-se via SSH:**

    ```bash
    ssh root@seu-ip-homeassistant
    ```

2.  **Crie o diretório do projeto:**

    ```bash
    mkdir -p /config/gree-mqtt-bridge
    cd /config/gree-mqtt-bridge
    ```

3.  **Copie os arquivos:**

    Você precisará copiar os seguintes arquivos do repositório `gree-mqtt-bridge` para o diretório `/config/gree-mqtt-bridge`:

    *   `gree_mqtt_bridge.py` (o script principal)
    *   `config.yaml` (arquivo de configuração)
    *   `install.sh` (script de instalação)
    *   `gree-mqtt-bridge.service` (arquivo de serviço Systemd para execução automática)

    Você pode fazer isso manualmente via SFTP/SCP ou, se tiver o add-on "File Editor" no Home Assistant, criar a pasta e colar o conteúdo dos arquivos.

4.  **Torne o script de instalação executável e execute-o:**

    ```bash
    cd /config/gree-mqtt-bridge
    chmod +x install.sh
    ./install.sh
    ```

    Este script instalará as dependências Python necessárias e configurará o serviço Systemd.

### Opção 2: Container Docker Separado

Se você prefere isolar o bridge em um container Docker, pode criar um `Dockerfile` e construir sua própria imagem. Esta opção oferece maior portabilidade e isolamento de dependências.

### Opção 3: Máquina Separada na Mesma Rede

Você pode executar o `gree-mqtt-bridge` em qualquer máquina Linux (como um Raspberry Pi ou outro servidor) que esteja na mesma rede que seus ar condicionados Gree e seu Mosquitto Broker. Os passos de cópia de arquivos e execução do `install.sh` seriam similares à Opção 1, mas adaptados ao seu ambiente Linux.

## Configuração do `config.yaml`

O arquivo `config.yaml` é crucial para o funcionamento do bridge. Você precisará ajustá-lo com suas credenciais MQTT e, opcionalmente, os IPs dos seus ar condicionados Gree.

Um exemplo básico de `config.yaml` pode ser:

```yaml
mqtt:
  host: 127.0.0.1  # Ou o IP do seu Mosquitto Broker
  port: 1883
  username: mqtt
  password: mqtt

devices:
  # Se a descoberta automática falhar, adicione os dispositivos manualmente aqui
  # - id: "gree_sala"
  #   name: "AC Sala"
  #   ip: "192.168.1.XXX"  # Substitua pelo IP do seu AC
```

**Atenção:** As credenciais MQTT (`username` e `password`) devem corresponder às configuradas no seu Mosquitto Broker. O `host` pode ser `127.0.0.1` se o bridge estiver no mesmo host que o Mosquitto, ou o IP do seu broker se estiver em uma máquina separada.

## Execução e Teste

Após a instalação e configuração, você pode testar o bridge:

1.  **Teste a descoberta de dispositivos (opcional):**

    ```bash
    cd /config/gree-mqtt-bridge
    source venv/bin/activate  # Ative o ambiente virtual criado pelo install.sh
    python3 gree_mqtt_bridge.py --discover
    ```

    Este comando tentará descobrir os ar condicionados Gree na sua rede e exibir suas informações. Se a descoberta for bem-sucedida, os dispositivos serão automaticamente adicionados ao Home Assistant via MQTT Discovery.

2.  **Execute o bridge em modo debug (para testes iniciais):**

    ```bash
    python3 gree_mqtt_bridge.py --debug
    ```

    Isso iniciará o bridge e exibirá logs detalhados no terminal, o que é útil para depuração.

3.  **Execute o bridge em modo normal (para operação contínua):**

    ```bash
    python3 gree_mqtt_bridge.py
    ```

    Para que o bridge inicie automaticamente com o sistema, o script `install.sh` já deve ter configurado um serviço Systemd. Você pode verificar o status do serviço com `sudo systemctl status gree-mqtt-bridge`.

## Monitoramento no Home Assistant

Uma vez que o `gree-mqtt-bridge` esteja em execução e conectado ao seu Mosquitto Broker, você verá os seguintes resultados no Home Assistant:

*   **Entidades:** Novos dispositivos `climate` (clima) aparecerão automaticamente na sua lista de Entidades, representando seus ar condicionados Gree.
*   **MQTT:** Você pode monitorar as mensagens MQTT no Home Assistant acessando `Ferramentas do Desenvolvedor` > `MQTT` e ouvindo tópicos relacionados a `gree` ou `homeassistant/#`.

## Referências

[1] Análise crítica da integração Gree com Home Assistant via Claude.ai: [https://claude.ai/share/03160025-68c4-411e-bf4b-622a4ec70981](https://claude.ai/share/03160025-68c4-411e-bf4b-622a4ec70981)
