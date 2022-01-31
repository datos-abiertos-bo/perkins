import time
import random
import requests
import functools

from bs4 import BeautifulSoup

import perkins.constants


PROXY_TIMEOUT = 30
REQUEST_RETRY = 5
REQUEST_SLEEP = 2


def do_request(URL, data=None, _try=0, **kwargs):
    if data is not None:
        req_fn = requests.post
    else:
        req_fn = requests.get

    try:
        return req_fn(URL, data=data, **kwargs)

    except Exception as e:
        if _try > REQUEST_RETRY:
            raise(e)

    time.sleep(_try * REQUEST_SLEEP)
    return do_request(URL, data=data, _try=_try + 1, **kwargs)


@functools.cache
def _get_proxy_list(country):
    req = requests.get(
        'https://www.proxydocker.com/es/proxylist/country/{}'.format(country),
        headers=perkins.constants.DEFAULT_HEADERS
    )
    html = BeautifulSoup(req.content, 'html.parser')

    meta = html.findChild('meta', attrs={'name': '_token'})
    token = meta.attrs['content']

    cookies = req.headers['Set-Cookie']
    cookies = [cookie.split(';')[0] for cookie in cookies.split(',')]
    cookies = [_ for _ in cookies if '=' in _]

    PROXY_TYPES = {
        '1': 'http',
        '2': 'https',
        '12': 'https',
        '3': 'socks4',
        '4': 'socks5'
    }

    proxy_data = {
        'token': token,
        'country': country,
        'city': 'all',
        'state': 'all',
        'port': 'all',
        'type': 'all',
        'anonymity': 'all',
        'need': 'all',
        'page': 1
    }
    proxies = []

    for page in range(1, 3):
        proxy_data['page'] = page
        req = requests.post(
            'https://www.proxydocker.com/es/api/proxylist/',
            data=proxy_data,
            headers={
                'Cookie': ';'.join(cookies),
                **perkins.constants.DEFAULT_HEADERS
            }
        )

        payload = req.json()
        if 'proxies' in payload and len(payload['proxies']) > 0:
            proxies.extend(payload['proxies'])
        else:
            break

    proxies = [(
        'https' if '2' in _['type'] else 'http',
        '{}://{}:{}'.format(PROXY_TYPES[_['type']], _['ip'], _['port'])
    ) for _ in  proxies if _['type'] in PROXY_TYPES.keys()]

    return proxies


def setup_proxy(base_url, country='Bolivia', banned=[], timeout=PROXY_TIMEOUT):
    proxies = _get_proxy_list(country)
    random.shuffle(proxies)

    for proxy in proxies:
        if proxy in banned:
            continue

        proxy = dict([proxy])

        try:
            requests.get(
                base_url,
                timeout=timeout,
                proxies=proxy,
                headers=perkins.constants.DEFAULT_HEADERS
            )

        except Exception as e:
            continue

        return proxy
