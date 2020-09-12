import json
import requests
import util
import authenticate_v0
from secureconfig import SecureConfig
import template

api_base_url = 'https://api.myob.com/nz/essentials'
config = SecureConfig().decrypt(util.secure_config_file)


def _create_headers():
    return {
        'x-myobapi-version': 'v0',
        'x-myobapi-key': config['myob_client_id'],
        'Authorization': f'Bearer {authenticate_v0.get_access_token()}'
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


def get_contacts():

    url = f'{api_base_url}/businesses/{config["myob_business_uid"]}/contacts'
    return json.loads(_do_get(url).content)['items']


def get_invoices():
    url = f'{api_base_url}/businesses/{config["myob_business_uid"]}/sale/invoices'
    return json.loads(_do_get(url).content)['items']


def get_items():
    url = f'{api_base_url}/businesses/{config["myob_business_uid"]}/inventory/items'
    return json.loads(_do_get(url).content)['items']


def get_item_by_name(name: str):
    items = get_items()
    for i in items:
        if i['name'] == name:
            return i
    return None


def get_invoice(invoice_uid):
    url = f'{api_base_url}/businesses/{config["myob_business_uid"]}/sale/invoices/{invoice_uid}'
    return json.loads(_do_get(url).content)


def get_next_invoice_number():
    url = f'{api_base_url}/businesses/{config["myob_business_uid"]}/sale/invoices/nextReference'
    return json.loads(_do_get(url).content)['reference']


def get_next_payment_reference():
    url = f'{api_base_url}/businesses/{config["myob_business_uid"]}/sale/payments/nextReference'
    return json.loads(_do_get(url).content)['reference']


def get_accounts():
    url = f'{api_base_url}/businesses/{config["myob_business_uid"]}/generalledger/accounts'
    return json.loads(_do_get(url).content)


def get_account_types():
    url = f'{api_base_url}/account/types'
    return json.loads(_do_get(url).content)


def get_account_classifications():
    url = f'{api_base_url}/account/classifications'
    return json.loads(_do_get(url).content)


def create_invoice(json_template_file: str, parameter_dict: dict, dryrun: bool):
    url = f'{api_base_url}/businesses/{config["myob_business_uid"]}/sale/invoices'
    invoice_str = template.text_from_template_file(json_template_file, parameter_dict)
    return _do_post(url, json.loads(invoice_str), dryrun=dryrun)
