import json
import requests
import util
import template
import authenticate_v2
import base64
from secureconfig import SecureConfig

api_base_url = 'https://api.myob.com/accountright'
config = SecureConfig().decrypt(util.secure_config_file)


def _create_headers():
    username_password = f'{config["myob_username"]}:{config["myob_password"]}'
    u_p_decoded = base64.b64encode(username_password.encode("utf-8")).decode("utf-8")
    return {
        'Authorization': f'Bearer {authenticate_v2.get_access_token()}',
        'x-myobapi-cftoken': u_p_decoded,
        'x-myobapi-key': config['myob_client_id'],
        'x-myobapi-version': 'v2'
    }


def _do_get(url: str):
    try:
        r = requests.get(url, headers=_create_headers())
        print(r.text)
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


def get_contacts():
    url = f'{api_base_url}/businesses/{config["myob_business_uid"]}/contacts'
    return json.loads(_do_get(url).content)['items']


def get_items():
    url = f'{get_company_file_url()}/Inventory/Item'
    print(json.loads(_do_get(url).content))
    #return json.loads(_do_get(url).content)['Items']


def get_item_by_name(name: str):
    items = get_items()
    for i in items:
        if i['name'] == name:
            return i
    return None


def create_invoice(json_template_file: str, parameter_dict: dict, dryrun: bool):
    url = f'{api_base_url}/businesses/{config["myob_business_uid"]}/Sale/Invoice/Item'
    invoice_str = template.text_from_template_file(json_template_file, parameter_dict)
    return _do_post(url, json.loads(invoice_str), dryrun=dryrun)


def get_next_invoice_number():
    url = f'{api_base_url}/businesses/{config["myob_business_uid"]}/sale/invoices/nextReference'
    return json.loads(_do_get(url).content)['reference']
