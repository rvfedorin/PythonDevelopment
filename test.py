import re

ip_pattern = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
text = '172.17.152.222'

res = re.findall(ip_pattern, text)
if res:
    print(res[0])
else:
    print(res)