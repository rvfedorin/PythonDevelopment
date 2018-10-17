from os import urandom

from Cryptodome.Cipher import Blowfish
# from work.tools.customers import Customer
#
# cl = Customer('Orel', 'Orel-Test', '356', '172.17.237.126', '12', 'T')
# print(cl)


#################################
iv = b'\x88\xc3p\\\xd6\xb8\xcb\xa3'
data = b'xxxx'
k = b'xxxxx'

cipher = Blowfish.new(k, Blowfish.MODE_CBC, iv)
text = cipher.encrypt(data)
print(text)

# cipher = Blowfish.new(k, Blowfish.MODE_CBC, iv)
# print(cipher.decrypt(b'\xd4\xab\x8e!\xd5\xac\xcd\xc9\x1d\x8c/\xa1U\xf8\xdf\xfe'))
#################################