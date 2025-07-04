 [![Home Assistant](https://img.shields.io/badge/Home%20Assistant-41BDF5?logo=home-assistant&logoColor=white)](https://www.home-assistant.io/) [![MQTT](https://img.shields.io/badge/MQTT-660066?logo=mqtt&logoColor=white)](https://mqtt.org/) [![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/license-MIT-blue)](./LICENSE) [![Último Commit](https://img.shields.io/github/last-commit/cateim/ha-lab)](https://github.com/cateim/ha-lab/commits/main)

# 🧠 Laboratório Home Assistant (ha-lab)

Bem-vindo ao meu repositório de automações e experimentos para o Home Assistant! Este é o meu "laboratório" pessoal, onde eu, **Gustavo Cateim**, documento e compartilho as soluções que crio para a minha casa inteligente.

Aqui você encontrará desde automações complexas até configurações de cards e integrações que fogem do comum. Sinta-se à vontade para explorar, se inspirar e adaptar as ideias para o seu próprio setup.

## 🚀 Projetos em Destaque

Atualmente, o laboratório conta com os seguintes projetos principais, cada um com sua própria documentação detalhada:

### 🚪 Monitoramento de Porta com Câmera e Notificação Inteligente
Um sistema de segurança completo que:
- Tira um **snapshot** da câmera no momento exato em que a porta é aberta.
- Envia uma **notificação com a foto** para múltiplos dispositivos (iOS e Android).
- A notificação é **clicável**, abrindo um popup com a câmera ao vivo.
- A foto gerada é **apagada automaticamente** após 5 minutos para economizar espaço.

> [**Ver documentação completa ➔**](./door_notification_pop_camera.md)

### 🧼 Controle Inteligente para Lavadora Electrolux (LWI13)
Uma interface e um conjunto de automações para controlar a lavadora Electrolux LWI13. O projeto inclui:
- **Cards customizados** (Mushroom e Bubble) que mostram status, tempo restante e programa ativo.
- **Automações e Scripts** para selecionar programas, níveis de água e opções como "Turbo Agitação" e "Enxágue Extra" diretamente pelo Home Assistant.
- Uma **ação inteligente** que executa o comando certo (iniciar/pausar) dependendo do estado atual da máquina.

> [**Ver documentação completa ➔**](./washing_machine.md)

### ❄️ Bridge MQTT para Ar Condicionado Gree (Wait..⚠️)
Uma solução robusta e estável para integrar Ar Condicionados da marca Gree, superando as limitações das integrações diretas.
- Utiliza um **bridge em Python** para traduzir os comandos do ar condicionado para o protocolo MQTT.
- Oferece **maior confiabilidade e flexibilidade**, desacoplando o Home Assistant do dispositivo.
- Inclui **descoberta automática** de dispositivos na rede e configuração via MQTT Discovery do Home Assistant.

> [**Ver documentação completa ➔**](./gree-mqtt-bridge/README.md)

## 💡 Filosofia do Laboratório

O objetivo deste repositório é ser um espaço de **experimentação prática**. Muitas soluções aqui nasceram de uma necessidade real ou da simples curiosidade de "será que dá pra fazer isso?". Acredito que compartilhar esses projetos pode ajudar e inspirar outras pessoas na comunidade Home Assistant.

## 🏗️ Planos Futuros (Work in Progress)

Este repositório está em constante evolução. Pretendo adicionar novos projetos e aprimorar os existentes. Algumas ideias na fila são:
- [ ] Monitoramento avançado de consumo de energia.
- [ ] Integração com assistentes de voz para rotinas complexas.
- [ ] Criação de painéis (dashboards) temáticos e dinâmicos.

Feito com ☕ e curiosidade por **Gustavo Cateim**.