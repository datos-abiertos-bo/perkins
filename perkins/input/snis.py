import demjson

from bs4 import BeautifulSoup

import perkins.requests


SNIS_TIMEOUT = 90


def get_inputs(soup):
    form_inputs = soup.select('input') + soup.select('select')

    return {
        finput.get('name'):finput.get('value', '') for finput in form_inputs if (
            finput.get('name')
        )
    }


def process_request(URL, soup, cookies, data, proxy=None, raw=False):
    form_imputs = get_inputs(soup)
    form_imputs.update(data)
    form_imputs = {_:__ for _, __ in form_imputs.items() if __ is not None}

    req = perkins.requests.do_request(URL, data=form_imputs, headers={
        'Cookie': ';'.join(cookies)
    }, timeout=SNIS_TIMEOUT, proxies=proxy)

    if raw:
        return req.content

    try:
        content = req.content
        content = demjson.decode(content[int(content[:3]) + 4:][7:-1])

        content = content['result'][0]
        content = content.split('|', 2)

        content_offset = int(content[1].split(',')[0])
        content_name = content[2][:content_offset]
        content = content[2][content_offset:]

        soup_update = BeautifulSoup(content, 'html.parser')

        parent_el = soup.select_one('#' + content_name)
        parent_el = parent_el.select_one(
            '#' + next(soup_update.children).get('id')
        ).parent

        form_inputs = soup_update.select('input') + soup_update.select('select')
        for input_update in form_inputs:
            input_id = input_update.get('id')

            if not input_id:
                continue

            target_el = soup.select_one('#' + input_id)

            if not target_el:
                target_el = soup.new_tag(name='input')
                parent_el.append(target_el)

            target_el.attrs = input_update.attrs

    except Exception as e:
        soup = BeautifulSoup(req.content, 'html.parser')

    return soup
