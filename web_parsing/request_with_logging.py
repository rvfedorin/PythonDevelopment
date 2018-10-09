import requests
import bs4


def get_url_login(site, headers=None):
    link = None
    if headers is None:
        r = requests.get(site)
    else:
        r = requests.get(site, headers=headers)

    soup = bs4.BeautifulSoup(r.text, "html.parser")
    for a_link in soup.find_all('a'):
        if 'Войти' in str(a_link):
            link = a_link['href']
    # print(link)
    return link

if __name__ == '__main__':
    # get_url_login('https://yandex.ru/')
    headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    }

    SITE = 'https://yandex.ru/'
    USERNAME = 'rv.fedorin'
    PASSWORD = 'xxxxxx'
    LOGIN_URL = get_url_login(SITE, headers=headers)  # Страница Логина
    URL = "https://mail.yandex.ru/lite"  # Страница самого контента для парсинга

    payload = {
        "login": USERNAME,
        "passwd": PASSWORD
    }

    session_requests = requests.session()
    session_requests.headers.update(headers)

    # Perform login
    result = session_requests.post(LOGIN_URL, data=payload, headers=dict(referer=LOGIN_URL))
    result = session_requests.get(URL, headers=dict(referer=URL))
    soup_login = bs4.BeautifulSoup(result.content, "html.parser")

    span_message = soup_login.find_all('div', class_='b-messages__message')
    print(span_message)

    # for mes in span_message:
    #     print(mes)
    #     # print(mes.text)

    print(soup_login.prettify())

