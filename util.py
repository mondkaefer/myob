import os
import time
import functools
from typing import Dict, List
from enum import Enum, auto, unique

secure_config_file = 'config.yml.gpg'


@unique
class PaymentType(Enum):
    DANA = auto(),
    DHARMA_GEAR_MEMBER = auto(),
    DHARMA_GEAR_NON_MEMBER = auto(),
    OTHER = auto()


ITEM_NAMES: Dict[PaymentType, str] = {
    PaymentType.DANA: "Dana",
    PaymentType.DHARMA_GEAR_MEMBER: "Dharmagear sales: members",
    PaymentType.DHARMA_GEAR_NON_MEMBER: "Dharmagear sales: non-members"
}


def read_contact_map(path_to_file: str):
    contact_map: Dict[str, str] = {}

    assert os.path.isfile(path_to_file), f'File {path_to_file} does not exist'
    with open(path_to_file) as f:
        lines = [line for line in f.readlines() if line.strip()]

    assert 1 < len(lines), f'no records found in {path_to_file}'
    for line in lines:
        ref, name = line.split('|')
        contact_map[ref] = name.strip()
    return contact_map


def read_bank_feed_csv(path_to_file: str, memo_blacklist: list):
    payments: List[Dict[str, str]] = []

    assert os.path.isfile(path_to_file), f'File {path_to_file} does not exist'
    with open(path_to_file) as f:
        lines = [line for line in f.readlines() if line.strip()]

    assert 0 < len(lines), f'{path_to_file} has not content'
    assert 1 < len(lines), f'no records found in {path_to_file}'

    # read header line
    col_names: List[str] = lines[0].strip().split(',')
    header_num_cols: int = len(col_names)

    blacklist_count: int = 0
    # read payment lines
    for i in range(1, len(lines)):
        cols = lines[i].strip().split(',')
        if len(cols) != header_num_cols:
            raise Exception(f'number of fields in a line in {path_to_file} does not match header line')
        elif cols[2] in memo_blacklist:
            blacklist_count += 1
            print(f'--> ignoring memo/description "{cols[2]} (on blacklist)')
        else:
            d = {}
            for j in range(0, len(cols)):
                d[col_names[j]] = cols[j]
            # col_of_interest = 'OP code'
            col_of_interest = 'Dana'
            assert col_of_interest in d
            if d[col_of_interest] == ITEM_NAMES[PaymentType.DANA]:
                d['payment_type'] = PaymentType.DANA
            elif d[col_of_interest] == ITEM_NAMES[PaymentType.DHARMA_GEAR_MEMBER]:
                d['payment_type'] = PaymentType.DHARMA_GEAR_MEMBER
            elif d[col_of_interest] == ITEM_NAMES[PaymentType.DHARMA_GEAR_NON_MEMBER]:
                d['payment_type'] = PaymentType.DHARMA_GEAR_NON_MEMBER
            else:
                d['payment_type'] = PaymentType.OTHER
            payments.append(d)

    assert len(lines) == (1 + len(payments) + blacklist_count), f'line count in {path_to_file} does not match up'

    return col_names, payments


def read_cash_payments_csv(path_to_file: str):
    payments: List[Dict[str, str]] = []

    assert os.path.isfile(path_to_file), f'File {path_to_file} does not exist'
    with open(path_to_file) as f:
        lines = [line for line in f.readlines() if line.strip()]

    assert 0 < len(lines), f'{path_to_file} has not content'
    assert 1 < len(lines), f'no records found in {path_to_file}'

    # read header line
    col_names: List[str] = lines[0].strip().split(',')
    header_num_cols: int = len(col_names)

    # read payment lines
    for i in range(1, len(lines)):
        cols = lines[i].strip().split(',')
        if len(cols) != header_num_cols:
            raise Exception(f'number of fields in a line in {path_to_file} does not match header line')
        d = {}
        for j in range(0, len(cols)):
            d[col_names[j]] = cols[j]
        if d['Item'] == ITEM_NAMES[PaymentType.DANA]:
            d['payment_type'] = PaymentType.DANA
        elif d['Item'] == ITEM_NAMES[PaymentType.DHARMA_GEAR_MEMBER]:
            d['payment_type'] = PaymentType.DHARMA_GEAR_MEMBER
        elif d['Item'] == ITEM_NAMES[PaymentType.DHARMA_GEAR_NON_MEMBER]:
            d['payment_type'] = PaymentType.DHARMA_GEAR_NON_MEMBER
        else:
            d['payment_type'] = PaymentType.OTHER
        payments.append(d)

    assert len(lines) == (1 + len(payments)), f'line count in {path_to_file} does not match up'

    return col_names, payments


def wait_for_enter_before_execution(func):
    """
    Decorator to wait for keyboard input before proceeding
    """

    @functools.wraps(func)
    def wrapper_wait_for_enter(*args, **kwargs):
        input('Hit ENTER to continue...')
        return func(*args, **kwargs)

    return wrapper_wait_for_enter


def wait_before_execution(wait_s):
    """
    Decorator to wait for 2 seconds before proceeding
    """

    def decorator_wait_before_execution(func):
        @functools.wraps(func)
        def wrapper_wait_for_enter(*args, **kwargs):
            time.sleep(wait_s)
            return func(*args, **kwargs)

        return wrapper_wait_for_enter
    return decorator_wait_before_execution