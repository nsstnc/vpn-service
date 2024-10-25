import tempfile

import paramiko
import subprocess
from wgconfig import WGConfig

import os


class Server:

    # todo добавить дополнительные команды настройки сервера
    def __init__(self, ip, password):
        self.ip = ip
        self.password = password
        self.interface_public_key = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username='root', password=password)
            self.connection = ssh
        except Exception as e:
            print(e)

    def execute_command(self, command):
        stdin, stdout, stderr = self.connection.exec_command(command)
        # выполняем подтверждение, при конфигурации файрволла
        if "ufw enable" in command:
            stdin.write('y\n')
            stdin.flush()

        return stdout.read().decode(), stderr.read().decode()

    def generate_keypair(self):
        # Генерация приватного ключа на удаленном сервере
        private_key, error = self.execute_command("wg genkey")
        if error:
            print(f"Ошибка генерации приватного ключа: {error}")
            return None, None

        # Генерация публичного ключа на основе приватного
        public_key, error = self.execute_command(f"echo {private_key.strip()} | wg pubkey")
        if error:
            print(f"Ошибка генерации публичного ключа: {error}")
            return None, None

        return private_key.strip(), public_key.strip()

    def install_wireguard(self):
        commands = [
            'sudo apt update',
            'sudo apt install wireguard -y',
            'sudo apt install wireguard-tools -y'
        ]
        for command in commands:
            stdout, stderr = self.execute_command(command)
            if stderr:
                print(f"Error: {stderr}")
            print(stdout)

    def read_file(self, file_path):
        stdout, stderr = self.execute_command(f'cat {file_path}')
        if stderr:
            print(f"Ошибка при чтении файла {file_path}: {stderr}")
            return None
        return stdout.strip()

    def write_file(self, content, file_path):
        write_command = f'echo "{content}" | sudo tee {file_path} > /dev/null'
        stdout, stderr = self.execute_command(write_command)
        if stderr:
            print(f"Ошибка при записи файла на сервер: {stderr}")
        else:
            print("Файл успешно записан на сервер")

    def setup_wireguard_interface(self):
        # добавляем на сервер IPv4 Forwarding
        self.execute_command('sudo echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf')
        # перезапускаем конфигурацию
        self.execute_command('sudo sysctl -p')

        # Генерация ключей для сервера
        server_private_key, server_public_key = self.generate_keypair()

        self.interface_public_key = server_public_key

        create_dir = "sudo mkdir -p /etc/wireguard"
        stdout, stderr = self.execute_command(create_dir)
        if stderr:
            print(f"Ошибка создания каталога: {stderr}")
        else:
            print("Каталог создан.")

            # Создание конфигурации сервера
            config_content = f"""[Interface]\nPrivateKey = {server_private_key}\nAddress = 10.0.0.1/24\nListenPort = 51820\nPostUp = ufw allow 51820/udp; iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\nPostDown = ufw delete allow 51820/udp; iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE"""

            # Запись конфигурации в файл
            self.write_file(config_content.strip(), "/etc/wireguard/wg0.conf")

            return server_public_key

    def add_client_to_wireguard(self, client_name, client_private_key, client_public_key, id=0):
        allowed_ips = f"10.0.0.{2 + id}/32"
        # Получаем содержимое конфигурационного файла
        config_content = self.read_file("/etc/wireguard/wg0.conf")
        if config_content is None:
            print("Не удалось получить содержимое конфигурационного файла.")
            return

        # Временное сохранение конфигурации в локальный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".conf") as temp_file:
            temp_file.write(config_content.encode())
            temp_file_path = temp_file.name

        try:
            # Создаем объект WGConfig с локальным файлом
            config = WGConfig(temp_file_path)
            config.read_file()

            # Добавляем нового клиента
            config.handle_leading_comment(f"#{client_name}")
            config.add_peer(client_public_key)
            config.add_attr(client_public_key, 'AllowedIPs', allowed_ips)

            # Запись изменений в локальный файл
            config.write_file()

            # Чтение обновленного содержимого и запись обратно на удаленный сервер
            with open(temp_file_path, 'r') as updated_file:
                updated_content = updated_file.read()
                self.write_file(updated_content.strip(), "/etc/wireguard/wg0.conf")
            # перезапускаем WG
            self.restart_wireguard()
            return self.get_peer_configuration(client_private_key, self.interface_public_key, allowed_ips)
        finally:
            # Удаление временного файла
            os.remove(temp_file_path)

    def get_peer_configuration(self, client_private_key, server_public_key, address):
        interface_content = f"""[Interface]\nPrivateKey = {client_private_key}\nAddress = {address}\nDNS = 8.8.8.8"""
        peer_content = f"""[Peer]\nPublicKey = {server_public_key}\nEndpoint = {self.ip}:51820\nAllowedIPs = 0.0.0.0/0\nPersistentKeepalive = 0"""
        config_content = interface_content + "\n\n\n" + peer_content
        return config_content

    def restart_wireguard(self):
        command = 'sudo systemctl restart wg-quick@wg0'
        stdout, stderr = self.execute_command(command)
        if stderr:
            print(f"Error: {stderr}")
        print(stdout)

    # def configure_firewall(self):
    #     commands = [
    #         'sudo ufw allow 51820/udp',
    #         'sudo ufw enable'
    #     ]
    #     for command in commands:
    #         stdout, stderr = self.execute_command(command)
    #         if stderr:
    #             print(f"Error: {stderr}")
    #         print(stdout)


server = Server("80.242.57.211", "gujmcY,+5De+N3")
server.install_wireguard()
server_public_key = server.setup_wireguard_interface()
client_private_key, client_public_key = server.generate_keypair()
print(client_private_key, client_public_key)
client_conf = server.add_client_to_wireguard("егор", client_private_key, client_public_key)
from scripts.qr import generate_qr_code

generate_qr_code(client_conf)
server.connection.close()
