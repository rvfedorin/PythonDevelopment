from bs4 import BeautifulSoup
import requests
import fake_useragent


line = '-'*80

#  Random user-agent
ua = fake_useragent.UserAgent()
user = ua.random
header = {'User-Agent': str(user)}


#  Connection to the ip site
ip_site = 'http://icanhazip.com'
address = requests.get(ip_site, headers=header)

#  Check yor IP address
print(line + "\n[*] IP your network:\n" + address.text + line)

#  Proxy
# proxies = {
#     'http': 'socks5h://127.0.0.1:9050',
#     'https': 'socks5h://127.0.0.1:9050'
# }
# address_proxy = requests.get(ip_site, proxies=proxies, headers=header)

#  Parse site
url = input('Site: http://')

page = requests.get("http://" + url.split()[0], headers=header)
soup = BeautifulSoup(page.text, "html.parser")

#  Default parse HTML
if url.split()[0] == url.split()[-1]:
    code = ""
    for tag in soup.findAll("html"):
        code += str(tag)
        with open('index.html', 'w') as html:
            html.write(code)
else:
    #  Parse tag
    if url.split()[1] == url.split()[-1]:
        for tag in soup.findAll(url.split()[1]):
            print(tag)
    else:
        for tag in soup.findAll(url.split()[1]):
            print(tag[url.split()[2]])
print(line)
