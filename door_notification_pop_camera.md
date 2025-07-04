# 📝 Automações e Cards: Monitoramento da Porta Paraíso

**Autor:** Gustavo Cateim (com uma ajudinha do Gemini)
**Status:** 🟢 Testado e Aprovado

## 🚀 Descrição Geral

Este documento detalha um sistema de monitoramento completo para a porta de entrada ("Paraíso"). O sistema é composto por um card de popup no painel (Lovelace) e duas automações complementares que trabalham juntas para fornecer notificações ricas e visualização instantânea da câmera.

## 🔧 Pré-requisitos de Configuração

Para que este sistema funcione, as seguintes configurações devem estar presentes no seu Home Assistant:

* **Entidades:**
    * Sensor da Porta: `binary_sensor.paraiso_porta`
    * Câmera (HD e SD): `camera.im3c_hd`, `camera.im3c_sd`
    * Dispositivos Notificáveis: `notify.mobile_app_iphone_de_gustavo`, `notify.mobile_app_motorola`.
* **Integrações:**
    * `browser_mod` (para os popups e navegação)
    * `custom:bubble-card` (instalado via HACS)
* **Comando de Apagar (`configuration.yaml`):** É **obrigatório** ter o `shell_command` abaixo no seu arquivo `configuration.yaml` e reiniciar o Home Assistant para que a função de apagar a foto funcione.

    ```yaml
    # configuration.yaml
    shell_command:
      delete_snapshot: "rm /config/www/tmp/{{ filename }}"
    ```

## 🎨 Configuração do Painel (Frontend/Lovelace)

Esta é a configuração do card que cria o popup da câmera no seu painel. Ele fica escondido e é "chamado" pelas automações através do `hash: "#entrada"`.

### Card do Popup da Câmera (`#entrada`)

**Observação:** A estrutura foi ajustada para que o card da câmera (`picture-glance`) apareça *dentro* do popup do Bubble Card, como deve ser.

```yaml
# Adicione este card no seu painel Lovelace
type: vertical-stack
cards:
  - type: custom:bubble-card
    card_type: pop-up
    hash: "#entrada"
    show_header: true
    slide_to_close_distance: "200"
    margin: 8px
    bg_opacity: "75"
    entity: binary_sensor.paraiso_porta
    show_name: true
    show_state: true
    show_attribute: false
    show_last_changed: true
    show_icon: true
    scrolling_effect: true
    name: Porta Paraíso
    tap_action:
      action: none
    button_type: state
    button_action:
      tap_action:
        action: none
      hold_action:
        action: none
    card_layout: normal
    modules: []
  - camera_view: live
    fit_mode: cover
    type: picture-glance
    image: /local/tmp/snapshot_porta.jpg
    entities: []
    camera_image: camera.im3c_hd
    entity: camera.im3c_sd
    hold_action:
      action: none
    tap_action:
      action: none
```

## 🤖 Automações

Aqui estão as duas automações que controlam o sistema.

### Automação 1: Notificação com Foto, Ação e Auto-Delete

Esta é a automação principal. Ela envia uma notificação com uma foto do momento, que é clicável para abrir o popup acima, e depois se auto-limpa.

```yaml
alias: "Notificação: Porta Paraiso Aberta"
description: Gera uma foto com nome único, notifica e apaga após 5 minutos.
triggers:
  - entity_id:
      - binary_sensor.paraiso_porta
    to: "on"
    trigger: state
conditions: []
actions:
  # PASSO 1: Cria uma variável com o nome do arquivo único para esta execução
  - variables:
      snapshot_filename: snapshot_porta_{{ now().strftime('%Y%m%d_%H%M%S') }}.jpg

  # PASSO 2: Tira a foto com o nome que acabamos de criar
  - data:
      filename: /config/www/tmp/{{ snapshot_filename }}
    target:
      entity_id: camera.im3c_hd
    action: camera.snapshot

  # PASSO 3: Pausa para garantir que o arquivo foi salvo no disco
  - delay:
      seconds: 2

  # PASSO 4: Envia as notificações com a lógica corrigida para iOS e Android
  - data:
      message: Porta do Paraíso foi aberta!
      title: Atenção!
	  # iOS: Use a chave 'url' para imagem e clique
      data:
        attachment:
          url: /local/tmp/{{ snapshot_filename }}
          content-type: jpeg
        url: /lovelace/0#entrada
    action: notify.mobile_app_iphone_de_gustavo
  - data:
      message: Porta do Paraíso foi aberta!
      title: Atenção!
	  # Android: Use a chave 'image' para imagem e 'clickAction' para clique
      data:
        image: /local/tmp/{{ snapshot_filename }}
        clickAction: /lovelace/0#entrada
    action: notify.mobile_app_motorola
  - delay:
      minutes: 5
  - data:
      filename: "{{ snapshot_filename }}"
    action: shell_command.delete_snapshot
mode: single
```

### Automação 2: Popup Instantâneo ao Abrir a Porta

Esta automação é opcional e serve para abrir o popup da câmera *imediatamente* em dispositivos específicos (como um tablet na parede) assim que a porta é aberta, sem precisar de notificação.

```yaml
alias: "Popup: Câmera ao Abrir Porta da Entrada"
description: Mostra a câmera da entrada em um popup quando a porta abre.
trigger:
  - entity_id:
      - binary_sensor.paraiso_porta
    to: "on"
    platform: state
condition: []
action:
  - service: browser_mod.navigate
    data:
      path: /lovelace/0#entrada
      browser_id:
        - c948ac8887e5822ab4f7f9ab838ccf00
        - bfa9a304209de81c6c3e4d5ecc53bfeb
mode: single
```
