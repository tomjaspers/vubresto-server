#!/usr/bin/env python
import io
import os
import json
import logging
import datetime
import requests
import lxml.html
from lxml.cssselect import CSSSelector

# Path where the JSONs will get written. Permissions are your job.
SAVE_PATH = '/Users/tjs/Development/vubresto-server/'

# Urls of the pages that will get parsed
URL_ETTERBEEK = 'https://my.vub.ac.be/resto/etterbeek'
URL_JETTE = 'https://my.vub.ac.be/resto/jette'

# Mapping of colors for the menus.
COLOR_MAPPING = {}
COLOR_MAPPING['soep'] = '#fdb85b' # yellow
COLOR_MAPPING['menu 1'] = '#68b6f3' # blue
COLOR_MAPPING['dag menu'] = '#68b6f3' #blue
COLOR_MAPPING['dagmenu'] = '#68b6f3' #blue
COLOR_MAPPING['health'] = '#ff9861' # orange
COLOR_MAPPING['menu 2'] = '#cc93d5' # purple
COLOR_MAPPING['meals of the world'] = '#cc93d5' # purple
COLOR_MAPPING['veggie'] = '#87b164' # green
COLOR_MAPPING['veggiedag'] = '#87b164' # green
COLOR_MAPPING['pasta'] = '#de694a' # red
COLOR_MAPPING['pasta bar'] = '#de694a' # red
COLOR_MAPPING['wok'] = '#6c4c42' # brown

# Months in Dutch, to allow the parsing of the (Dutch) site
LOCAL_MONTHS = {}
LOCAL_MONTHS['januari'] = 1
LOCAL_MONTHS['februari'] = 2
LOCAL_MONTHS['maart'] = 3
LOCAL_MONTHS['april'] = 4
LOCAL_MONTHS['mei'] = 5
LOCAL_MONTHS['juni'] = 6
LOCAL_MONTHS['juli'] = 7
LOCAL_MONTHS['augustus'] = 8
LOCAL_MONTHS['september'] = 9
LOCAL_MONTHS['oktober'] = 10
LOCAL_MONTHS['november'] = 11
LOCAL_MONTHS['december'] = 12

def is_veggiedag_img(img):
    src = img.get('src', None) if img is not None else None
    if src is None:
        return False
    return "veggiedag" in src

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
        date_string = normalize_text(date_span[0].text_content()).lower()
        date_components = date_string.split()[1:] #  ['29', 'september', '2014']
        month_name = normalize_text(date_components[1]).lower()
        month = LOCAL_MONTHS.get(date_components[1], None)
        if month is not None:
            date = datetime.date(int(date_components[2]), # year
                                 month, # month
                                 int(date_components[0])) # day
        else:
            # If we couldn't find a month, we'll just try to use the previous date
            logging.warning(name + " - Failed to get a month for the month_name: " + month_name)
            try:
                prev_date_components = map(int, data[len(data) - 1]['date'].split('-'))
                prev_date = datetime.date(prev_date_components[0], # year
                                          prev_date_components[1], # month
                                          prev_date_components[2]) # day
                date = prev_date + datetime.timedelta(days=1)
            except Exception:
                # If the previous date doesn't exist or was bad aswell, we'll just skip this day
                logging.exception(name + " - Couldn't derive date from previous dates")
                continue

        # Get the table rows
        tablerows = sel_tablerows(day_div)
        for tr in tablerows:
            tds = tr.getchildren()
            menu_name = normalize_text(tds[0].text_content())
            menu_dish = normalize_text(tds[1].text_content())
            # Sometimes there is no menu name, but just an image (e.g., for "Veggiedag")
            if not menu_name:
                img = sel_img(tds[0])
                img = img[0] if img else None
                menu_name = 'Veggiedag' if is_veggiedag_img(img) else 'Menu'
            menu_color = COLOR_MAPPING.get(menu_name.lower(), None)
            if menu_color is None:
                logging.warning(name + " - Failed to get a color for the menu: '" +\
                                menu_name + "' (" + str(date) + ")")
                menu_color = '#ffffff'
            menus.append({'name': menu_name, 'dish': menu_dish, 'color': menu_color})
        data.append({'date': str(date), 'menus': menus})
    return data

def write_to_json(data, filename):
    with io.open(os.path.join(SAVE_PATH, filename), 'w', encoding='utf8') as f:
        f.write(unicode(json.dumps(data, ensure_ascii=False)))

def parse_and_save(name, url):
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
    parse_and_save("Etterbeek", URL_ETTERBEEK)
    parse_and_save("Jette", URL_JETTE)
    
    
if __name__ == "__main__":
    main()
