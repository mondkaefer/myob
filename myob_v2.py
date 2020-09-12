import json
import requests
import util
import authenticate_v2
from secureconfig import SecureConfig

api_base_url = 'https://api.myob.com/accountright'
config = SecureConfig().decrypt(util.secure_config_file)


def _create_headers():
    return {
        'x-myobapi-version': 'v2',
        'x-myobapi-key': config['myob_client_id'],
        'Authorization': f'Bearer {authenticate_v2.get_access_token()}'
    }


def _do_get(url: str):
    try:
        r = requests.get(url, headers=_create_headers())
        r.raise_for_status()
        return r
    except requests.exceptions.HTTPError:
        raise


def _do_post(url: str, body: dict, dryrun: bool):
    if dryrun:
        print(f'POST {url}')
        print(f'{body}')
        return None
    else:
        try:
            r = requests.post(url, headers=_create_headers(), json=body)
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError:
            raise


def get_company_file_url():
    url = f'{api_base_url}/'
    return json.loads(_do_get(url).content)[0]['Uri']


def get_statement():
    url = f'{get_company_file_url()}/Banking/Statement?$orderby=Date%20desc'
    return json.loads(_do_get(url).content)['Items']


def get_items():
    url = f'{get_company_file_url()}/Sale/Invoice/Service?$orderby=Date%20desc'
    return json.loads(_do_get(url).content)['Items']

