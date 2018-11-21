
data_path = '/data/'
help_file = data_path+'help.txt'
intranet_path = 'C:/Intranets/'
clients_conf_path = '/etc/Clients.conf'
local_clients_conf = f"C:/Intranets/Clients.conf"
client_to_change_speed = f'{data_path}cl_to_change_speed.txt'
client_to_multi_vlan = f'{data_path}client_to_multi_vlan.txt'
city_shelve = f'./{data_path}city.shelve'
# log = '../log/'
ico = "ico.jpg"

iv = b'\x88\xc3p\\\xd6\xb8\xcb\xa3'
p_un_sup = b'a&7\x89\xeca\x99%p!_\xef\xdd\xb9\x8f\x16'
p_sw = b"@\xea\x88\xc0\xe9'y\xa0"
p_rwr_cl = b'\x0b\x87\xaf\x99\x86\xd2[\x9c#4\xcb\xd0\xe7\xcc\x14\x93'
p_rwr_sec = b'\xd4\xab\x8e!\xd5\xac\xcd\xc9'
p_mb_sec = b'C\x00\xd2\xee\x02\xdf\x0c\x1a'
my_key = b'\xd4\xab\x8e!\xd5\xac\xcd\xc9\x1d\x8c/\xa1U\xf8\xdf\xfe'
my_key_e = b'u\x97f\x1b\xa8\xc7-\x99\xa9\x9cP\xad\xc4\xd6<\x11'


if __name__ == '__main__':
    from Cryptodome.Cipher import Blowfish

    key = b"12345678"
    passw = b"12345678"
    vect = b'12345678'

    cipher = Blowfish.new(key, Blowfish.MODE_CBC, vect)
    res = cipher.encrypt(passw)
    print(res)


