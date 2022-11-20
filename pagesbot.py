#!/usr/bin/env python3

import re

from wikibaseintegrator import WikibaseIntegrator, wbi_login
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator.datatypes import Quantity, Item


CONSUMER_TOKEN = '00000000000000000000000000000000'
CONSUMER_SECRET = '0000000000000000000000000000000000000000'
USERNAME = ''
PASSWORD = ''

wbi_config['USER_AGENT'] = 'PagesBot/1.0 (https://www.wikidata.org/wiki/User:PagesBot)'
login_instance = wbi_login.OAuth2(consumer_token=CONSUMER_TOKEN, consumer_secret=CONSUMER_SECRET)
#login_instance = wbi_login.Clientlogin(user='USERNAME', password='PASSWORD')

wbi = WikibaseIntegrator(login=login_instance)  # is_bot=True


def get_page_range_str(wbi_item):
    # Try to get the pages() (P304) statement
    try:
        page_range_str = wbi_item.get_json()['claims']['P304'][0]['mainsnak']['datavalue']['value']
        return page_range_str

    except KeyError:
        return


def get_number_of_pages(wbi_item):
    # Try to get the number of pages (P1104) statement
    try:
        pages = int(wbi_item.get_json()['claims']['P1104'][0]['mainsnak']['datavalue']['value']['amount'])
        return pages

    except KeyError:
        return


def infer_pages(page_range_str):
    # Infer the number of pages from the range
    range_re = re.match(r'^(\d*)\s*(-|‐|‑|‒|–|—|―|−)\s*(\d*)$', page_range_str)
    first_page_num = int(range_re.group(1))
    last_page_num = int(range_re.group(3))
    return last_page_num - first_page_num + 1


# Get the item to work on
item = wbi.item.get(entity_id='Q4115189')

existing_number_of_pages = get_number_of_pages(item)
page_range_str = get_page_range_str(item)

if existing_number_of_pages:
    print(item.id + ': number of pages (P1104) statement is already present')

elif not page_range_str:
    print(item.id + ': pages() (P304) statement is not present')

else:
    number_of_pages = infer_pages(page_range_str)
    print(item.id + ': inferred {} pages from "{}"'.format(number_of_pages, page_range_str))

    number_of_pages_statement = Quantity(prop_nr='P1104',
                                         amount=number_of_pages,
                                         unit='Q1069725',
                                         references=[Item(prop_nr="P887", value='Q110768064')])

    summary = 'Inferred [[Property:P1104]]: {} from [[Property:P304]]: "{}"'\
              .format(number_of_pages, page_range_str)

    # Add the statement to the item
    item.claims.add([number_of_pages_statement])
    item.write(summary=summary)
