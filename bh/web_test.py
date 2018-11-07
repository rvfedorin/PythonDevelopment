import urllib.request as urlib

url = "http://localhost:8000"
header = dict()

header['User-Agent'] = 'Googlebot'

request = urlib.Request(url, headers=header)
response = urlib.urlopen(request)

print(response.read().decode())
response.close()
