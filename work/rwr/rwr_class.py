import telnetlib

# my
import settings
import intranet


class CreateRwr:
    def __init__(self, ip, passw, login='root'):
        self.ip = ip
        self.login = login.encode()
        self.passw = passw.encode()

    @property
    def sector(self):
        return self.ip

    # заглушка для служебных telnet ответов
    def _bulk(self, _self, cmd, opt):
        pass

    def connect(self)->list:
        print(f"Connecting to rwr {self.ip}")
        try:
            tn = telnetlib.Telnet(self.ip, timeout=5)
            tn.set_option_negotiation_callback(self._bulk)
        except Exception as e:
            text = f"Error connect to RWR {self.ip}.\n{e}"
            print(text)
            return [False, e]
        else:
            print("Autorization ...")
            tn.read_until(b"Login:", timeout=1)
            tn.write(self.login + b"\r")
            tn.read_until(b":", timeout=1)
            tn.write(self.passw + b"\r")
            tn.read_until(b'>', timeout=1)
            tn.write(b"\n\n")
            tn.read_until(b'>', timeout=1)

            response = tn.read_until(b'>', timeout=1).decode(errors='ignore')
            print(response)
            if "Sorry" in response:
                return [False, f"RWR {self.ip} -> auth error: {response} "]

            print(f"Подключение к {self.ip} установлено.")

            return [True, tn]

    def send_command(self, command_list):
        res = []
        tn = self.connect()
        if tn[0]:
            tn = tn[1]
        else:
            return tn  # [False, "Error"]

        try:
            for com in command_list:
                text = ''
                text += tn.read_until(b'>', timeout=1).decode()
                tn.write(com.encode()+b'\r')
                text += tn.read_until(b'>', timeout=1).decode()
                res.append(text)
            tn.write(b"exit\r")

        except Exception as e:
            print(f"Ошибка отправки комманды на rwr {self.ip}. \n {e}")
        finally:
            tn.close()

        return res


if __name__ == '__main__':
    import settings
    from Cryptodome.Cipher import Blowfish

    key = b"12341234"
    cipher = Blowfish.new(key, Blowfish.MODE_CBC, settings.iv)
    p_rwr_cl = cipher.decrypt(settings.p_rwr_cl).decode().split('1111')[0]

    rwr = CreateRwr("172.16.44.230", passw=p_rwr_cl)
    response = rwr.send_command(["co sh mint"])
    print(response[0])

