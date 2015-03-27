#!/usr/bin/env python26
import io
import os
import json
import logging
import datetime
import requests
import lxml.html
from lxml.cssselect import CSSSelector
from multiprocessing.dummy import Pool as ThreadPool


# Path where the JSONs will get written. Permissions are your job.
SAVE_PATH = '.'


# Urls of the pages that will get parsed
URL_ETTERBEEK_NL = 'https://my.vub.ac.be/resto/etterbeek'
URL_ETTERBEEK_EN = 'https://my.vub.ac.be/restaurant/etterbeek'
URL_JETTE_NL = 'https://my.vub.ac.be/resto/jette'
URL_JETTE_EN = 'https://my.vub.ac.be/restaurant/jette'


# Mapping of colors for the menus.
DEFAULT_COLOR = '#f0eb93'  # very light yellow
COLOR_MAPPING = {
    'soep': '#fdb85b',  # yellow
    'soup': '#fdb85b',  # yellow
    'menu 1': '#68b6f3',  # blue
    'dag menu': '#68b6f3',  # blue
    'dagmenu': '#68b6f3',  # blue
    'health': '#ff9861',  # orange
    'menu 2': '#cc93d5',  # purple
    'meals of the world': '#cc93d5',  # purple
    'fairtrade': '#cc93d5',  # purple
    'fairtrade menu': '#cc93d5',  # purple
    'veggie': '#87b164',  # green
    'veggiedag': '#87b164',  # green
    'pasta': '#de694a',  # red
    'pasta bar': '#de694a',  # red
    'wok': '#6c4c42',  # brown
}


# Months in Dutch, to allow the parsing of the (Dutch) site
MONTHS = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli',
          'augustus', 'september', 'oktober', 'november', 'december']
LOCAL_MONTHS = {month: i for i, month in enumerate(MONTHS, 1)}


def is_veggiedag_img(img):
    return img and 'veggiedag' in img.get('src', '')


def normalize_text(text):
    return text.replace(u'\xa0', u' ').strip()


def parse_restaurant(name, url):
    data = []

    # Construct CSS Selectors
    sel_day_divs = CSSSelector('#content .views-row')
    sel_date_span = CSSSelector('.date-display-single')
    sel_tablerows = CSSSelector('table tr')
    sel_img = CSSSelector('img')

    # Request and build the DOM Tree
    r = requests.get(url)
    tree = lxml.html.fromstring(r.text)

    # Apply selector to get divs representing 1 day
    day_divs = sel_day_divs(tree)
    for day_div in day_divs:
        menus = []
        # Apply selector to get date span (contains date string of day)
        date_span = sel_date_span(day_div)
        # date string should be format '29 september 2014', normally
        date_string = normalize_text(date_span[0].text_content()).lower()
        date_components = date_string.split()[1:]
        month_name = normalize_text(date_components[1]).lower()
        month = LOCAL_MONTHS.get(date_components[1], None)
        if month:
            date = datetime.date(int(date_components[2]),  # year
                                 month,  # month
                                 int(date_components[0]))  # day
        else:
            # If we couldn't find a month, we try to use the previous date
            logging.warning("{0} - Failed to get a month \
                             for the month_name {1} ".format(name, month_name))
            try:
                prev_date_components = map(int, data[-1]['date'].split('-'))
                prev_date = datetime.date(prev_date_components[0],  # year
                                          prev_date_components[1],  # month
                                          prev_date_components[2])  # day
                date = prev_date + datetime.timedelta(days=1)
            except Exception:
                # If we can't find any date, we'll skip the day
                logging.exception("{0} - Couldn't derive date \
                                  from previous dates".format(name))
                continue

        # Get the table rows
        tablerows = sel_tablerows(day_div)
        for tr in tablerows:
            tds = tr.getchildren()
            menu_name = normalize_text(tds[0].text_content())
            menu_dish = normalize_text(tds[1].text_content())
            # Sometimes there is no menu name,
            # but just an image (e.g., for "Veggiedag")
            if not menu_name:
                img = sel_img(tds[0])
                img = img[0] if img else None
                menu_name = 'Veggiedag' if is_veggiedag_img(img) else 'Menu'
            menu_color = COLOR_MAPPING.get(menu_name.lower(), None)
            if menu_color is None:
                logging.warning(name + " - No color found for the menu: '" +
                                menu_name + "' (" + str(date) + ")")
                menu_color = DEFAULT_COLOR
            if menu_dish:
                menus.append({'name': menu_name,
                              'dish': menu_dish,
                              'color': menu_color})
        data.append({'date': str(date), 'menus': menus})
    return data


def write_to_json(data, filename):
    with io.open(os.path.join(SAVE_PATH, filename), 'w', encoding='utf8') as f:
        f.write(unicode(json.dumps(data, ensure_ascii=False)))


def parse_and_save((name, url)):
    try:
        data = parse_restaurant(name, url)
    except Exception:
        logging.exception(name + " - Failed to parse")
        data = []
    try:
        write_to_json(data, name.lower() + '.json')
    except Exception:
        logging.exception(name + " - Failed to save to json")


def main():
    # Configure the logger
    logging.basicConfig(filename='menuparser.log', level='WARNING')

    # Parse and save the 2 restaurants
    pool = ThreadPool(4)
    pool.map(parse_and_save, [
        ('Etterbeek.nl', URL_ETTERBEEK_NL),
        ('Jette.nl', URL_JETTE_NL),
        ('Etterbeek.en', URL_ETTERBEEK_EN),
        ('Jette.en', URL_JETTE_EN),
    ])


if __name__ == "__main__":
    main()
