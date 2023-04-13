import re
import json
import requests
import unidecode

import pandas as pd

PREFIX = [
    'departamento', 'departament',
    'provincia', 'province',
    'estado', 'state',
    'region'
]
RE_PREFIX = re.compile(r'\b(?:{})\b'.format('|'.join(PREFIX)))
RE_ARTICLE = re.compile(r'^ *(de|del|of) ')
GEO_URL = 'https://raw.githubusercontent.com/esosedi/3166/master/data/iso3166-2.json'
def fetch_geocodes(trim_admin_level=True):
    geo_data = requests.get(GEO_URL)
    geo_data = json.loads(geo_data.content)

    # Patch Ñuble
    geo_data['CL']['regions'].append(
        {'name': 'Ñuble Region', 'iso': 'NB', 'names': {'geonames': 'Ñuble'}}
    )
    # Patch CABA - AR
    caba_region = next(_ for _ in geo_data['AR']['regions'] if _['iso'] == 'C')
    caba_region['names'] = {
        'geonames': 'CABA',
        'es': 'Ciudad Autonoma de Buenos Aires',
        'en': 'Autonomous City of Buenos Aires'
    }
    # Patch Lima - PE
    geo_data_pe = geo_data['PE']
    lima_province_idx = next(
        _ for _, __ in enumerate(geo_data_pe['regions']) if __['iso'] == 'LMA'
    )
    lima_province = geo_data_pe['regions'].pop(lima_province_idx)
    lima_province['names'] = {
        'geonames': 'Lima Metropolitana',
        'es': 'Provincia de Lima',
        'en': 'Lima Province'
    }
    geo_data_pe['regions'].append(lima_province)

    lima_region = next(_ for _ in geo_data['PE']['regions'] if _['iso'] == 'LIM')
    lima_region['names']['geonames'] = 'Lima'
    # Patch Puerto Rico
    geo_data['US']['regions'].append(
        {'name': 'Puerto Rico', 'iso': 'PR', 'names': {'geonames': 'Puerto Rico'}}
    )

    # Patch Kosovo
    geo_data['XK'] = {
        'iso': 'XK',
        'iso3': 'XKX',
        'names': {
            'geonames': 'Kosovo',
            'en': 'Republic of Kosovo'
        },
        'regions': []
    }

    iso_level_0 = {}
    iso_level_1 = pd.DataFrame([])

    for geo_key in geo_data.keys():
        iso_level_0[geo_key] = geo_data[geo_key]['names'].values()

        geo_names_level_1 = {
            '{}-{}'.format(geo_key, _['iso']): [*_['names'].values()] for _ in geo_data[geo_key]['regions']
        }
        geo_names_level_1 = pd.DataFrame.from_dict(geo_names_level_1, orient='index')
        geo_names_level_1 = geo_names_level_1.fillna('')

        iso_level_1 = pd.concat([iso_level_1, geo_names_level_1])

    iso_level_0 = pd.DataFrame.from_dict(iso_level_0, orient='index')
    iso_geo_names = iso_level_1.fillna('')
    geo_names = iso_geo_names.stack().droplevel(1).reset_index()

    geo_names.columns = ['geocode', 'name']
    geo_names['name'] = geo_names['name'].map(
        unidecode.unidecode
    ).str.lower()

    if trim_admin_level:
        geo_names['name'] = geo_names['name'].str.replace(
            RE_PREFIX, '', regex=True
        ).str.replace(
            RE_ARTICLE, '', regex=True
        )

    geo_names['name'] = geo_names['name'].str.strip()
    geo_names = geo_names[geo_names['name'] != ''].set_index('name')

    return iso_level_0, iso_geo_names, geo_names


__all__ = [
    'RE_PREFIX',
    'RE_ARTICLE',
    'fetch_geocodes'
]
