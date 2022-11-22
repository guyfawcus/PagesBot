#!/usr/bin/env python3

import sys
import re

from wikibaseintegrator import WikibaseIntegrator, wbi_login
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator.datatypes import Quantity, Item


CONSUMER_TOKEN = ''
CONSUMER_SECRET = ''
USERNAME = ''
PASSWORD = ''

wbi_config['USER_AGENT'] = 'PagesBot/1.0 (https://www.wikidata.org/wiki/User:PagesBot)'

try:
    if CONSUMER_TOKEN and CONSUMER_SECRET:
        login_instance = wbi_login.OAuth2(consumer_token=CONSUMER_TOKEN, consumer_secret=CONSUMER_SECRET)
    elif USERNAME and PASSWORD:
        login_instance = wbi_login.Clientlogin(user=USERNAME, password=PASSWORD)
    else:
        print('Please supply a token and secret, or a username and password')
        sys.exit()
except wbi_login.LoginError as error_msg:
    print(error_msg)
    sys.exit()

wbi = WikibaseIntegrator(login=login_instance)  # is_bot=True


def get_page_range_str(wbi_item):
    # Try to get the page(s) (P304) statement
    try:
        wbi_item.get_json()['claims']['P304']
    except KeyError:
        print(wbi_item.id + ': no page(s) (P304) statements present')
        return

    if len(wbi_item.get_json()['claims']['P304']) > 1:
        print(wbi_item.id + ': aborting, more than one page(s) (P304) statements present')
        return
    else:
        page_range_str = wbi_item.get_json()['claims']['P304'][0]['mainsnak']['datavalue']['value']
        return page_range_str


def get_number_of_pages(wbi_item):
    # Try to get a number of pages (P1104) statement
    try:
        pages = int(wbi_item.get_json()['claims']['P1104'][0]['mainsnak']['datavalue']['value']['amount'])
        return pages

    except KeyError:
        return


def infer_pages(page_range_str, qid='Q?'):
    # Infer the number of pages from the range
    range_re = re.match(r'^([a-zA-Z]*)(\d+)\s*(-|‐|‑|‒|–|—|―|−)\s*([a-zA-Z]*)(\d+)$', page_range_str)

    if not range_re:
        print(qid + ': Bad number of pages (P1104) statement, does not match regex')
        return

    first_page_char = range_re.group(1)
    first_page_num = int(range_re.group(2))
    hyphen_char = range_re.group(3)
    last_page_char = range_re.group(4)
    last_page_num = int(range_re.group(5))

    # Allow prepended characters, but only where the letters do not differ
    # A1-2 is okay, A1-B2 is ambiguous so should be looked at by a human
    if (last_page_char != '') and (last_page_char != first_page_char):
        print(qid + ': Bad number of pages (P1104) statement, ambiguous range')
        return

    # Allow ranges where the second number is only made up of the digits that change
    # 100-4 is the same as 100-104
    if last_page_num < first_page_num:
        number_of_pages = (first_page_num + last_page_num) - first_page_num
    else:
        number_of_pages = last_page_num - first_page_num + 1

    return number_of_pages


def parse_item(qid, write_changes=True):
    # Get the item to work on
    item = wbi.item.get(entity_id=qid)

    existing_number_of_pages = get_number_of_pages(item)
    page_range_str = get_page_range_str(item)

    if existing_number_of_pages:
        print(item.id + ': number of pages (P1104) statement is already present')

    elif page_range_str:
        number_of_pages = infer_pages(page_range_str, qid)

        if number_of_pages:
            print(item.id + ': inferred {} pages from "{}"'.format(number_of_pages, page_range_str))

            number_of_pages_statement = Quantity(prop_nr='P1104',
                                                 amount=number_of_pages,
                                                 unit='Q1069725',
                                                 references=[Item(prop_nr="P887", value='Q110768064')])

            summary = 'Inferred [[Property:P1104]]: {} from [[Property:P304]]: "{}"'\
                      .format(number_of_pages, page_range_str)

            if write_changes == True:
                # Add the statement to the item
                item.claims.add([number_of_pages_statement])
                item.write(summary=summary)


if __name__ == '__main__':
    sandbox_qid = 'Q4115189'
    parse_item(sandbox_qid, write_changes=False)
