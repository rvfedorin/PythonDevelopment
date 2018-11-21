# ver 1.0.1
# created by Roman Fedorin

import shelve
import os
import settings


def delete_from_db(db, key):
    # Remove START
    #     del db['Bryansk']
    # Remove END
    del db[key]


def add_to_db(db, key, kwargs):
    # # # NEW Data START
    #     temp = {'city': 'Bryansk', 'root_sw': '172.17.92.2', 'root_port': '1', 'col_sw': 2, 'unix': '79.175.53.254'}
    #     db['Br'] = temp
    # NEW Data END
    temp = kwargs
    db[key] = temp


def update_in_db(db, key, kwargs):
    # Update data START
    #     temp = db['Bryansk']
    #     temp.update({'unix': '79.175.53.254'})
    #     db['Bryansk'] = temp
    #     print(db['Bryansk'])
    # Update data END
    temp = db[key]
    temp.update(kwargs)
    db[key] = temp


def get_data_from_db(key):
    city_shelve = settings.city_shelve
    with shelve.open(city_shelve) as db:
        if key in db:
            result = db[key]
        else:
            result = None
    return result


def get_list_cities():
    """ Function reads all keys of cities from shelveDB """
    city_shelve = os.path.abspath(os.getcwd() + settings.city_shelve)
    cities_keys = {}
    with shelve.open(city_shelve) as db:
        for key in db:
            cities_keys[db[key]['city']] = key
    return cities_keys


if __name__ == '__main__':

    city_shelve = os.path.abspath(settings.city_shelve).replace('\\tools', '')

    with shelve.open(city_shelve) as db:
        for i in db:
            print(f'{i} => {db[i]}')
            # temp = db[i]
            # temp['Mobibox'] = 'None'
            # db[i] = temp

    # print(os.path.abspath(os.getcwd() + f'../{settings.city_shelve}'))
    # print(get_list_cities())




