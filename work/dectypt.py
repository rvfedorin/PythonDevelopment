# ver 1.0.1
# created by Roman Fedorin

from Cryptodome.Cipher import Blowfish

import settings


class DecryptPass:
    key_pass = None
    p_un_sup = None
    p_sw = None
    p_mb_sec = None
    p_rwr_sec = None
    p_rwr_cl = None
    my_key = None
    my_key_e = None

    @classmethod
    def decrypt_pass(cls):
        if cls.key_pass:
            try:
                cipher = Blowfish.new(cls.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                cls.p_un_sup = cipher.decrypt(settings.p_un_sup).decode().split('1111')[0]

                cipher = Blowfish.new(cls.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                cls.p_sw = cipher.decrypt(settings.p_sw).decode().split('1111')[0]

                cipher = Blowfish.new(cls.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                cls.my_key = cipher.decrypt(settings.my_key).decode().split('1111')[0]

                cipher = Blowfish.new(cls.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                cls.my_key_e = cipher.decrypt(settings.my_key_e).decode().split('1111')[0]

                cipher = Blowfish.new(cls.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                cls.p_mb_sec = cipher.decrypt(settings.p_mb_sec).decode().split('1111')[0]

            except Exception as e:
                print(f"Error while encoded passwords. {e}")
                cls.key_pass = None
            finally:
                return True