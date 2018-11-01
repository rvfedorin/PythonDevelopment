def mark_used_ip(list_used_ip, list_all_ip):
    for ip in list_all_ip:
        if ip in list_used_ip:
            position_ip = list_all_ip.index(ip)
            list_all_ip[position_ip] = 'x'


def get_free_lan(list_ip_with_used):
    free_lan = []
    for lan in range(25, 33):
        count_subnet = 2**(lan - 24)
        count_ip_in_subnet = 2**(32 - lan)
        start_ip = 0
        end_ip = count_ip_in_subnet

        for subnet in range(count_subnet):
            if len(list_ip_with_used) >= end_ip and 'x' not in list_ip_with_used[start_ip:end_ip]:
                free_lan.append(f'{list_ip_with_used[start_ip]}/{lan}')
                all_ip_temp = [_ for _ in list_ip_with_used if _ not in list_ip_with_used[start_ip:end_ip]]
                list_ip_with_used = all_ip_temp[:]
            else:
                start_ip += count_ip_in_subnet
                end_ip += count_ip_in_subnet

            if len(list_ip_with_used) == 0:
                break
        if len(list_ip_with_used) == 0:
            break
    return free_lan


def get_only_fourth_octet(list_ip):
    list_octets = []
    for i in list_ip:
        octet = i.split('.')
        list_octets.append(int(octet[3]))
        lan = f'{octet[0]}.{octet[1]}.{octet[2]}.'
    return list_octets, lan


def get_all_ip_in_lan(list_lan):
    ip_of_all_lan = []
    for lan in list_lan:
        mask_lan = lan.split('/')
        lan_ip = mask_lan[0].split('.')
        for i in range(2**(32-int(mask_lan[1]))):
            four_octet = int(lan_ip[3])+i
            ip_of_all_lan.append(f'{lan_ip[0]}.{lan_ip[1]}.{lan_ip[2]}.{four_octet}')
    return ip_of_all_lan


if __name__ == '__main__':
    all_ip = []
    for i in range(256):
        all_ip.append(i)

    x = (get_all_ip_in_lan(['172.30.86.164/30', '172.30.86.216/30', '172.30.86.152/30', '172.30.86.156/30',
                            '172.30.86.160/30', '172.30.86.144/30', '172.30.86.140/30', '172.30.86.136/30',
                            '172.30.86.120/30', '172.30.86.116/30', '172.30.86.88/30', '172.30.86.92/30',
                            '172.30.86.96/30', '172.30.86.80/30', '172.30.86.20/30', '172.30.86.184/30',
                            '172.30.86.196/30', '172.30.86.212/30', '172.30.86.220/30', '172.30.86.224/30',
                            '172.30.86.232/30', '172.30.86.236/30', '172.30.86.240/30', '172.30.86.248/30',
                            '172.30.86.252/30', '172.30.86.132/30', '172.30.86.44/30', '172.30.86.148/30',
                            '172.30.86.76/30', '172.30.86.48/30', '172.30.86.40/30', '172.30.86.84/30',
                            '172.30.86.36/30', '172.30.86.72/30', '172.30.86.104/30', '172.30.86.108/30',
                            '172.30.86.24/30', '172.30.86.228/30', '172.30.86.204/30', '172.30.86.0/30',
                            '172.30.86.4/30', '172.30.86.8/30', '172.30.86.12/30', '172.30.86.244/30',
                            '172.30.86.192/30', '172.30.86.124/30', '172.30.86.112/30', '172.30.86.60/30',
                            '172.30.86.208/30', '172.30.86.176/30', '172.30.86.68/30', '172.30.86.28/30',
                            '172.30.86.32/30', '172.30.86.56/30', '172.30.86.100/30', '172.30.86.168/29',
                            '172.30.86.200/30', '172.30.86.188/30', '172.30.86.180/30']))

    list_used_ip = x
    list_used_ip_octet, lan24 = get_only_fourth_octet(list_used_ip)

    mark_used_ip(list_used_ip_octet, all_ip)
    free = get_free_lan(all_ip)
    for i in free:
        print(f'{lan24}{i}')

