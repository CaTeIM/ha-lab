#!/usr/bin/env python3
"""
Gree HVAC MQTT Bridge for Home Assistant
Integração robusta para ar condicionados Gree via MQTT

Autor: Claude AI Assistant
Data: 2025-06-09
"""

import asyncio
import json
import logging
import socket
import struct
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import paho.mqtt.client as mqtt
import yaml
import argparse
import signal
import sys

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class GreeDevice:
    """Representa um dispositivo Gree AC"""
    name: str
    ip: str
    port: int = 7000
    mac: str = ""
    key: Optional[str] = None
    last_seen: Optional[datetime] = None
    available: bool = False
    brand: str = "gree"
    model: str = ""
    version: str = ""

@dataclass
class GreeState:
    """Estado atual do ar condicionado Gree"""
    power: int = 0          # 0=off, 1=on
    mode: int = 0           # 0=auto, 1=cool, 2=dry, 3=fan, 4=heat
    temp_set: int = 25      # Temperatura desejada
    temp_current: int = 25  # Temperatura atual
    fan_speed: int = 0      # 0=auto, 1-5=velocidade
    swing_vertical: int = 0 # 0=off, 1=on
    swing_horizontal: int = 0 # 0=off, 1=on
    quiet: int = 0          # 0=off, 1=on
    turbo: int = 0          # 0=off, 1=on
    light: int = 1          # 0=off, 1=on
    health: int = 0         # 0=off, 1=on
    sleep: int = 0          # 0=off, 1=on

class GreeProtocol:
    """Protocolo de comunicação com dispositivos Gree"""
    
    # Mapeamentos de comandos
    MODE_MAP = {
        'auto': 0, 'cool': 1, 'dry': 2, 'fan': 3, 'heat': 4
    }
    MODE_MAP_REVERSE = {v: k for k, v in MODE_MAP.items()}
    
    FAN_MAP = {
        'auto': 0, 'low': 1, 'medium-low': 2, 'medium': 3, 
        'medium-high': 4, 'high': 5
    }
    FAN_MAP_REVERSE = {v: k for k, v in FAN_MAP.items()}

    def __init__(self):
        self.generic_key = "a3K8Bx%2r8Y7#xDh"
        
    def encrypt(self, data: str, key: str) -> str:
        """Criptografa dados usando AES"""
        try:
            cipher = Cipher(
                algorithms.AES(key.encode('utf-8')[:16].ljust(16, b'\0')),
                modes.ECB(),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Padding PKCS7
            pad_len = 16 - (len(data) % 16)
            padded_data = data + chr(pad_len) * pad_len
            
            encrypted = encryptor.update(padded_data.encode('utf-8')) + encryptor.finalize()
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Erro na criptografia: {e}")
            return ""

    def decrypt(self, data: str, key: str) -> str:
        """Descriptografa dados usando AES"""
        try:
            cipher = Cipher(
                algorithms.AES(key.encode('utf-8')[:16].ljust(16, b'\0')),
                modes.ECB(),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            encrypted_data = base64.b64decode(data)
            decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Remove padding
            pad_len = decrypted[-1]
            return decrypted[:-pad_len].decode('utf-8')
        except Exception as e:
            logger.error(f"Erro na descriptografia: {e}")
            return ""

    def create_request(self, device: GreeDevice, command: Dict, encrypted: bool = True) -> str:
        """Cria uma requisição para o dispositivo Gree"""
        timestamp = int(time.time())
        
        if encrypted and device.key:
            pack_data = json.dumps(command, separators=(',', ':'))
            encrypted_pack = self.encrypt(pack_data, device.key)
            
            request = {
                "cid": "app",
                "i": 0,
                "t": "pack",
                "uid": 0,
                "tcid": device.mac or "",
                "pack": encrypted_pack
            }
        else:
            request = {
                "cid": "app",
                "i": 1,
                "t": "scan",
                "uid": 0
            }
            
        return json.dumps(request, separators=(',', ':'))

class GreeDiscovery:
    """Descoberta automática de dispositivos Gree na rede"""
    
    def __init__(self, protocol: GreeProtocol):
        self.protocol = protocol
        self.discovered_devices: List[GreeDevice] = []
        
    async def discover_devices(self, timeout: int = 5) -> List[GreeDevice]:
        """Descobre dispositivos Gree na rede local"""
        logger.info("Iniciando descoberta de dispositivos Gree...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        
        try:
            # Requisição de descoberta
            scan_request = self.protocol.create_request(
                GreeDevice("scan", ""), {}, encrypted=False
            )
            
            # Envia broadcast
            sock.sendto(scan_request.encode(), ('255.255.255.255', 7000))
            logger.info("Pacote de descoberta enviado")
            
            devices = []
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                    response = json.loads(data.decode())
                    
                    if response.get('t') == 'dev':
                        device_info = response.get('pack', {})
                        device = GreeDevice(
                            name=device_info.get('name', f"Gree AC {addr[0]}"),
                            ip=addr[0],
                            mac=device_info.get('mac', ''),
                            brand=device_info.get('brand', 'gree'),
                            model=device_info.get('model', ''),
                            version=device_info.get('ver', ''),
                            available=True,
                            last_seen=datetime.now()
                        )
                        devices.append(device)
                        logger.info(f"Dispositivo encontrado: {device.name} ({device.ip})")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.debug(f"Erro ao processar resposta: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erro na descoberta: {e}")
        finally:
            sock.close()
            
        logger.info(f"Descoberta finalizada. {len(devices)} dispositivos encontrados.")
        self.discovered_devices = devices
        return devices

class GreeController:
    """Controlador principal para dispositivos Gree"""
    
    def __init__(self, device: GreeDevice, protocol: GreeProtocol):
        self.device = device
        self.protocol = protocol
        self.state = GreeState()
        self.sock = None
        
    async def bind_device(self) -> bool:
        """Realiza bind com o dispositivo para obter chave de criptografia"""
        if self.device.key:
            return True
            
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(10)
            
            # Requisição de bind
            bind_request = {
                "mac": self.device.mac,
                "t": "bind",
                "uid": 0
            }
            
            request = self.protocol.create_request(self.device, bind_request, encrypted=False)
            sock.sendto(request.encode(), (self.device.ip, self.device.port))
            
            data, _ = sock.recvfrom(1024)
            response = json.loads(data.decode())
            
            if response.get('t') == 'bindok':
                # Extrai chave do response
                pack = response.get('pack', {})
                if 'key' in pack:
                    self.device.key = pack['key']
                    logger.info(f"Bind realizado com sucesso para {self.device.name}")
                    return True
                else:
                    # Usa chave genérica como fallback
                    self.device.key = self.protocol.generic_key
                    logger.warning(f"Usando chave genérica para {self.device.name}")
                    return True
                    
        except Exception as e:
            logger.error(f"Erro no bind com {self.device.name}: {e}")
            return False
        finally:
            if sock:
                sock.close()
                
        return False
    
    async def get_status(self) -> Optional[GreeState]:
        """Obtém status atual do dispositivo"""
        if not await self.bind_device():
            return None
            
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            # Comando para obter status
            status_cmd = {
                "cols": ["Pow", "Mod", "SetTem", "TemUn", "TemSen", "WdSpd", 
                        "SwUpDn", "SwingLfRig", "Quiet", "Tur", "Lig", "Health", "SwhSlp"],
                "mac": self.device.mac,
                "t": "status"
            }
            
            request = self.protocol.create_request(self.device, status_cmd)
            sock.sendto(request.encode(), (self.device.ip, self.device.port))
            
            data, _ = sock.recvfrom(1024)
            response = json.loads(data.decode())
            
            if response.get('t') == 'pack':
                encrypted_data = response.get('pack', '')
                decrypted_data = self.protocol.decrypt(encrypted_data, self.device.key)
                
                if decrypted_data:
                    status_data = json.loads(decrypted_data)
                    dat = status_data.get('dat', [])
                    
                    if len(dat) >= 13:
                        self.state = GreeState(
                            power=dat[0],
                            mode=dat[1],
                            temp_set=dat[2],
                            temp_current=dat[4],
                            fan_speed=dat[5],
                            swing_vertical=dat[6],
                            swing_horizontal=dat[7],
                            quiet=dat[8],
                            turbo=dat[9],
                            light=dat[10],
                            health=dat[11],
                            sleep=dat[12]
                        )
                        
                        self.device.available = True
                        self.device.last_seen = datetime.now()
                        return self.state
                        
        except Exception as e:
            logger.error(f"Erro ao obter status de {self.device.name}: {e}")
            self.device.available = False
            
        finally:
            if sock:
                sock.close()
                
        return None
    
    async def send_command(self, commands: Dict[str, Any]) -> bool:
        """Envia comando para o dispositivo"""
        if not await self.bind_device():
            return False
            
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            # Converte comandos para formato Gree
            gree_commands = self._convert_commands(commands)
            
            cmd = {
                "opt": list(gree_commands.keys()),
                "p": list(gree_commands.values()),
                "t": "cmd"
            }
            
            request = self.protocol.create_request(self.device, cmd)
            sock.sendto(request.encode(), (self.device.ip, self.device.port))
            
            data, _ = sock.recvfrom(1024)
            response = json.loads(data.decode())
            
            if response.get('t') == 'res':
                logger.info(f"Comando enviado com sucesso para {self.device.name}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao enviar comando para {self.device.name}: {e}")
            
        finally:
            if sock:
                sock.close()
                
        return False
    
    def _convert_commands(self, commands: Dict[str, Any]) -> Dict[str, Any]:
        """Converte comandos MQTT para protocolo Gree"""
        gree_cmd = {}
        
        if 'power' in commands:
            gree_cmd['Pow'] = 1 if commands['power'] == 'ON' else 0
            
        if 'mode' in commands:
            mode_str = commands['mode'].lower()
            if mode_str in self.protocol.MODE_MAP:
                gree_cmd['Mod'] = self.protocol.MODE_MAP[mode_str]
                
        if 'temperature' in commands:
            gree_cmd['SetTem'] = int(commands['temperature'])
            
        if 'fan_mode' in commands:
            fan_str = commands['fan_mode'].lower()
            if fan_str in self.protocol.FAN_MAP:
                gree_cmd['WdSpd'] = self.protocol.FAN_MAP[fan_str]
                
        if 'swing_mode' in commands:
            swing = commands['swing_mode'].lower()
            if swing == 'both':
                gree_cmd['SwUpDn'] = 1
                gree_cmd['SwingLfRig'] = 1
            elif swing == 'vertical':
                gree_cmd['SwUpDn'] = 1
                gree_cmd['SwingLfRig'] = 0
            elif swing == 'horizontal':
                gree_cmd['SwUpDn'] = 0
                gree_cmd['SwingLfRig'] = 1
            else:
                gree_cmd['SwUpDn'] = 0
                gree_cmd['SwingLfRig'] = 0
                
        return gree_cmd

class MQTTBridge:
    """Ponte MQTT para Home Assistant"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.mqtt_config = config.get('mqtt', {})
        self.client = mqtt.Client()
        self.controllers: Dict[str, GreeController] = {}
        self.protocol = GreeProtocol()
        self.discovery = GreeDiscovery(self.protocol)
        self.running = False
        
        # Configuração MQTT
        self.client.on_connect = self._on_mqtt_connect
        self.client.on_message = self._on_mqtt_message
        self.client.on_disconnect = self._on_mqtt_disconnect
        
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback de conexão MQTT"""
        if rc == 0:
            logger.info("Conectado ao broker MQTT")
            # Subscreve aos comandos
            for device_id in self.controllers:
                command_topic = f"homeassistant/climate/{device_id}/set"
                client.subscribe(command_topic)
                logger.info(f"Subscrito a: {command_topic}")
        else:
            logger.error(f"Falha na conexão MQTT. Código: {rc}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Callback de mensagem MQTT recebida"""
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 3 and topic_parts[-1] == 'set':
                device_id = topic_parts[-2]
                
                if device_id in self.controllers:
                    commands = json.loads(msg.payload.decode())
                    asyncio.create_task(
                        self.controllers[device_id].send_command(commands)
                    )
                    logger.info(f"Comando recebido para {device_id}: {commands}")
                    
        except Exception as e:
            logger.error(f"Erro ao processar mensagem MQTT: {e}")
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """Callback de desconexão MQTT"""
        logger.warning(f"Desconectado do MQTT. Código: {rc}")
    
    async def setup_mqtt(self):
        """Configura conexão MQTT"""
        try:
            # Autenticação se configurada
            if self.mqtt_config.get('username'):
                self.client.username_pw_set(
                    self.mqtt_config['username'],
                    self.mqtt_config.get('password', '')
                )
            
            # Conecta ao broker
            host = self.mqtt_config.get('host', 'localhost')
            port = self.mqtt_config.get('port', 1883)
            
            self.client.connect(host, port, 60)
            self.client.loop_start()
            
            # Aguarda conexão
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Erro ao configurar MQTT: {e}")
            raise
    
    def publish_discovery(self, device: GreeDevice, device_id: str):
        """Publica configuração de discovery do Home Assistant"""
        discovery_topic = f"homeassistant/climate/{device_id}/config"
        
        discovery_config = {
            "name": device.name,
            "unique_id": f"gree_{device.mac or device_id}",
            "device": {
                "identifiers": [f"gree_{device.mac or device_id}"],
                "name": device.name,
                "manufacturer": "Gree",
                "model": device.model or "Air Conditioner",
                "sw_version": device.version or "Unknown"
            },
            "modes": ["off", "auto", "cool", "heat", "dry", "fan_only"],
            "fan_modes": ["auto", "low", "medium-low", "medium", "medium-high", "high"],
            "swing_modes": ["off", "vertical", "horizontal", "both"],
            "temperature_unit": "C",
            "min_temp": 16,
            "max_temp": 30,
            "temp_step": 1,
            "current_temperature_topic": f"homeassistant/climate/{device_id}/current_temperature",
            "temperature_state_topic": f"homeassistant/climate/{device_id}/temperature",
            "temperature_command_topic": f"homeassistant/climate/{device_id}/set",
            "mode_state_topic": f"homeassistant/climate/{device_id}/mode",
            "mode_command_topic": f"homeassistant/climate/{device_id}/set",
            "fan_mode_state_topic": f"homeassistant/climate/{device_id}/fan_mode",
            "fan_mode_command_topic": f"homeassistant/climate/{device_id}/set",
            "swing_mode_state_topic": f"homeassistant/climate/{device_id}/swing_mode",
            "swing_mode_command_topic": f"homeassistant/climate/{device_id}/set",
            "availability_topic": f"homeassistant/climate/{device_id}/availability"
        }
        
        self.client.publish(
            discovery_topic,
            json.dumps(discovery_config),
            retain=True
        )
        logger.info(f"Discovery publicado para {device.name}")
    
    def publish_state(self, device_id: str, controller: GreeController):
        """Publica estado atual do dispositivo"""
        state = controller.state
        device = controller.device
        
        # Estado base
        base_topic = f"homeassistant/climate/{device_id}"
        
        # Disponibilidade
        availability = "online" if device.available else "offline"
        self.client.publish(f"{base_topic}/availability", availability)
        
        if not device.available:
            return
        
        # Modo de operação
        mode = "off" if state.power == 0 else self.protocol.MODE_MAP_REVERSE.get(state.mode, "auto")
        self.client.publish(f"{base_topic}/mode", mode)
        
        # Temperaturas
        self.client.publish(f"{base_topic}/temperature", state.temp_set)
        self.client.publish(f"{base_topic}/current_temperature", state.temp_current)
        
        # Velocidade do ventilador
        fan_mode = self.protocol.FAN_MAP_REVERSE.get(state.fan_speed, "auto")
        self.client.publish(f"{base_topic}/fan_mode", fan_mode)
        
        # Modo swing
        if state.swing_vertical and state.swing_horizontal:
            swing_mode = "both"
        elif state.swing_vertical:
            swing_mode = "vertical"
        elif state.swing_horizontal:
            swing_mode = "horizontal"
        else:
            swing_mode = "off"
        self.client.publish(f"{base_topic}/swing_mode", swing_mode)
    
    async def discover_and_setup_devices(self):
        """Descobre e configura dispositivos"""
        # Adiciona dispositivos configurados manualmente
        manual_devices = self.config.get('devices', [])
        for device_config in manual_devices:
            device = GreeDevice(
                name=device_config['name'],
                ip=device_config['ip'],
                port=device_config.get('port', 7000),
                mac=device_config.get('mac', ''),
                key=device_config.get('key')
            )
            
            device_id = device_config.get('id', device.ip.replace('.', '_'))
            controller = GreeController(device, self.protocol)
            self.controllers[device_id] = controller
            
            logger.info(f"Dispositivo manual adicionado: {device.name}")
        
        # Descoberta automática se habilitada
        if self.config.get('discovery', {}).get('enabled', True):
            discovered = await self.discovery.discover_devices()
            
            for device in discovered:
                # Evita duplicatas
                device_id = device.ip.replace('.', '_')
                if device_id not in self.controllers:
                    controller = GreeController(device, self.protocol)
                    self.controllers[device_id] = controller
        
        # Configura MQTT Discovery para todos os dispositivos
        for device_id, controller in self.controllers.items():
            self.publish_discovery(controller.device, device_id)
    
    async def monitor_devices(self):
        """Loop principal de monitoramento"""
        while self.running:
            for device_id, controller in self.controllers.items():
                try:
                    # Atualiza status
                    await controller.get_status()
                    
                    # Publica estado
                    self.publish_state(device_id, controller)
                    
                except Exception as e:
                    logger.error(f"Erro ao monitorar {device_id}: {e}")
            
            # Intervalo de polling
            await asyncio.sleep(self.config.get('polling_interval', 30))
    
    async def run(self):
        """Executa a ponte MQTT"""
        logger.info("Iniciando Gree MQTT Bridge...")
        
        try:
            # Configura MQTT
            await self.setup_mqtt()
            
            # Descobre dispositivos
            await self.discover_and_setup_devices()
            
            if not self.controllers:
                logger.warning("Nenhum dispositivo encontrado!")
                return
            
            logger.info(f"Configurados {len(self.controllers)} dispositivos")
            
            # Inicia monitoramento
            self.running = True
            await self.monitor_devices()
            
        except KeyboardInterrupt:
            logger.info("Interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro na execução: {e}")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()

def load_config(config_file: str) -> Dict:
    """Carrega configuração do arquivo"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                return yaml.safe_load(f)
            else:
                return json.load(f)
    except FileNotFoundError:
        logger.error(f"Arquivo de configuração não encontrado: {config_file}")
        return {}
    except Exception as e:
        logger.error(f"Erro ao carregar configuração: {e}")
        return {}

def create_default_config() -> Dict:
    """Cria configuração padrão"""
    return {
        "mqtt": {
            "host": "localhost",
            "port": 1883,
            "username": "",
            "password": ""
        },
        "discovery": {
            "enabled": True,
            "timeout": 10
        },
        "polling_interval": 30,
        "devices": [
            # Exemplo de dispositivo manual
            # {
            #     "id": "sala_ac",
            #     "name": "AC Sala",
            #     "ip": "192.168.1.100",
            #     "port": 7000,
            #     "mac": "aabbccddeeff",
            #     "key": "optional_custom_key"
            # }
        ]
    }

async def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Gree HVAC MQTT Bridge')
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Arquivo de configuração (default: config.yaml)'
    )
    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Cria arquivo de configuração de exemplo'
    )
    parser.add_argument(
        '--discover',
        action='store_true',
        help='Apenas descobre dispositivos e sai'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Ativa modo debug'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.create_config:
        config = create_default_config()
        with open('config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print("Arquivo config.yaml criado com configuração padrão")
        return
    
    if args.discover:
        protocol = GreeProtocol()
        discovery = GreeDiscovery(protocol)
        devices = await discovery.discover_devices(timeout=10)
        
        if devices:
            print(f"\n{len(devices)} dispositivos encontrados:")
            for device in devices:
                print(f"  - Nome: {device.name}")
                print(f"    IP: {device.ip}")
                print(f"    MAC: {device.mac}")
                print(f"    Marca: {device.brand}")
                print(f"    Modelo: {device.model}")
                print()
        else:
            print("Nenhum dispositivo encontrado")
        return
    
    # Carrega configuração
    config = load_config(args.config)
    if not config:
        logger.error("Configuração inválida ou não encontrada")
        logger.info("Use --create-config para criar um arquivo de exemplo")
        return
    
    # Inicia bridge
    bridge = MQTTBridge(config)
    
    # Handler para SIGINT
    def signal_handler(sig, frame):
        logger.info("Parando...")
        bridge.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await bridge.run()

if __name__ == "__main__":
    asyncio.run(main())