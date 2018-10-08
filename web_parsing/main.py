import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


def get_page(url):
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    return requests.get(url, headers=headers).text


def get_url_from_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for link in soup.find_all('a'):
        links.append(link.get('href'))
    return links


def main():
    url = 'https://2ip.ru/'
    html = get_page(url)
    soup = BeautifulSoup(html, 'html.parser')
    info = soup.find('div', class_='ip-info-entry')
    my_ip = f'Ваш IP адрес: {info.find("big", id="d_clip_button").text}'
    links = get_url_from_page(html)
    for link in links:
        if 'https' in link:
            print(link)


if __name__ == '__main__':
    main()
