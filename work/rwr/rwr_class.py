import telnetlib

# my
import settings
import intranet


class CreateRwr:
    def __init__(self, ip, passw, login='root'):
        self.ip = ip
        self.login = login
        self.passw = passw

    @property
    def sector(self):
        return self.ip

    # заглушка для служебных telnet ответов
    def _bulk(self, _self, cmd, opt):
        pass

    def connect(self)->list:
        try:
            tn = telnetlib.Telnet(self.ip, timeout=5)
            tn.set_option_negotiation_callback(self._bulk)
        except Exception as e:
            text = f"Error connect to RWR {self.ip}.\n{e}"
            print(text)
            return [False, e]
        else:

            tn.read_until(b":", timeout=1)
            tn.write(self.login + b"\r")
            tn.read_until(b":", timeout=1)
            tn.write(self.passw + b"\r")
            tn.read_until(b">", timeout=2)
            tn.write(b"\n\n")
            tn.read_until(b'>')

            print(f"Подключеник к {self.ip} установлено.")

            return [True, tn]


if __name__ == '__main__':
    import settings

    rwr = CreateRwr("172.16.44.230", passw=settings.p_rwr_cl)

