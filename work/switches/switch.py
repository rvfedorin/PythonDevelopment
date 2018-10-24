# Created by Fedorint Roman
# Script create switch
# ver 1.0.0

from telnetlib import Telnet
from socket import timeout

from bs4 import BeautifulSoup
import requests
import fake_useragent

from re import search


class NewSwitch:
    def __init__(self, ip, sw_login='admin', sw_passw='pass'):
        self.ip = ip
        if sw_login is None:
            sw_login = 'admin'
        self.login = sw_login.encode()
        self.passw = sw_passw.encode()

    # заглушка для служебных telnet ответов
    def _bulk(self, _self, cmd, opt):
        pass

    #  в основном для защиты от подключения к 2108
    def get_model_sw(self, url):
        # for 2108
        ua = fake_useragent.UserAgent()
        user = ua.random
        header = {'User-Agent': str(user)}
        try:
            page = requests.get("http://" + url, headers=header)
        except:
            return False
        else:
            soup = BeautifulSoup(page.text, "html.parser")
            if len(soup.title.contents) > 0:
                _title = soup.title.contents[0]
            else:
                _title = 'Unknown'
            model = _title.strip()[:8]
            return model

    # зателнетиться к свитчу и получить дескрптор
    def connect(self):
        model = self.get_model_sw(self.ip)
        if model == 'DES-2108':
            message = f'{sw} is DES-2108  \n ERROR \n'
            return [False, message]

        try:
            print(f'Try connect to sw {self.ip}')
            tn = Telnet(self.ip, 23, 5)
            tn.set_option_negotiation_callback(self._bulk)
        except Exception as e:
            message = f"Error telnet to {self.ip} \n ERROR \n {e}"
            return [False, message]

        tn.read_until(b":", timeout=1)
        tn.write(self.login + b"\r")
        tn.read_until(b":", timeout=1)
        tn.write(self.passw + b"\r")
        tn.read_until(b"#", timeout=2)
        tn.write(b"\n\n")
        tn.read_until(b'#')

        print(f"Подключеник к {self.ip} установлено.")
        return [True, tn]

    # из сообщения от свитча выясняем есть ли влан на порту
    def has_vlan(self, msg):
        """ has it vlan """
        _trace = False
        data_list = msg.split('\n')
        start_read = 7 if 'DGS-1210' in str(data_list) else 6
        if _trace: print(f"----data_list-----\n{data_list}\n----data_list END-----")
        vlan_on_port = []

        for line in data_list[start_read:-1]:
            line = line[4:].strip() if start_read == 6 else line.strip()
            if _trace: print(f"----line-----\n{line}\n----line END-----")
            vlan = search('^\d{1,4}', line)
            if _trace: print(f"----vlan-----\n{vlan}\n----vlan END-----")
            if vlan is not None:
                vlan_on_port.append(vlan.group())
        if not len(vlan_on_port) == 0 and (len(vlan_on_port) > 1 or int(vlan_on_port[0]) != 1):
            print('True, has vlan', vlan_on_port)
            return True
        else:
            print('False, has no vlan')
            return False

    # собераем порты без линков
    def port_without_link(self, msg):
        data_list = msg.split('\n')
        ports_down = []
        for line in data_list:
            if 'Link Down' in line or 'LinkDown' in line:
                line = line.strip()
                port_line = line.split(' ')
                port = search('^\d{1,2}', port_line[0])
                if port is not None and port.group() not in ports_down:
                    ports_down.append(port.group())
        return ports_down

    # ищем порты на свитче без линков и вланов
    def find_free_port(self):
        all_free_ports = []
        tn = self.connect()
        if tn[0] is False:
            return False
        else:
            tn = tn[1]
        tn.write(b"sh ports\n")
        tn.write(b"n\n")
        tn.write(b"n\n")
        tn.write(b"n\n")
        tn.write(b"q\n")
        msg = (tn.read_until(b'#').decode())
        p = self.port_without_link(msg)
        msg = (tn.read_until(b'#').decode())

        for port in p:
            print(f'checked the port {port} without link')
            command = f"show vlan ports {port}\n"
            # msg = (tn.read_until(b'#').decode())
            tn.write(b"\n")
            tn.write(command.encode())
            msg += (tn.read_until(b'#', timeout=1).decode())
            msg += (tn.read_until(b'#', timeout=1).decode())
            port_has_vlan = self.has_vlan(msg)
            if port_has_vlan is False:
                all_free_ports.append(port)

            msg = ''

        tn.write(b"logout\n")
        tn.close()
        return all_free_ports

    # выполнить список комманд на свитче
    def send_command(self, command_list, _dict_done=None):
        res = []
        tn = self.connect()
        if tn[0] is False:
            return [False]
        else:
            tn = tn[1]
        try:
            for com in command_list:
                text = ''
                text += tn.read_until(b'#', timeout=1).decode()
                tn.write(com.encode())
                text += tn.read_until(b'#', timeout=1).decode()
                res.append(text)
            tn.write(b"logout\n")

        except Exception as e:
            print(f"Ошибка отправки комманды на свитч {self.ip}. \n {e}")
        finally:
            tn.close()

        if _dict_done:
            _dict_done[self.ip] = res
        else:
            return res


if __name__ == '__main__':
    passw = input("pass: ")
    sw = NewSwitch('172.16.48.254', b'admin', passw)
    print(sw.send_command(['show ports\nq\n', 'show vlan po 2\nq\n', 'show ports 2\n']))
