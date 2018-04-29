#!/usr/bin/env python3
"""
    Simple API Interface written to Blockchair which has been written on Hackathon.

    I don't recommend to use it in any productional enviroment.
"""

# https://api.blockchair.com/bitcoin/outputs?q=time(2018-04-28+13:00:00..2018-04-28+13:30:00),
# value(199960000..210000000)&s=value(asc)

import requests
from datetime import datetime, timedelta

base_url = "https://api.blockchair.com/{currency}"


class BlockchairException(Exception):
    pass


class TransactionSearchException(Exception):
    pass


class TransactionNotFoundError(TransactionSearchException):
    pass


class TooMuchTransactionMatchesError(TransactionSearchException):
    pass


class BlockhairBitcoinAPI:
    url = base_url.format(currency='bitcoin')

    def __init__(self):
        pass


class Transactions(BlockhairBitcoinAPI):
    url = "{base}/transactions".format(base=BlockhairBitcoinAPI.url)

    def __init__(self):
        super().__init__()

    def query(self, hash):
        """
            hash: transcation hash
        """
        q = "hash({})".format(hash)
        params = {'q': q}

        # urlencode api bug
        payload_str = "&".join("%s=%s" % (k, v) for k, v in params.items())
        resp = requests.get(self.url, params=payload_str)
        return resp.json()


class Outputs(BlockhairBitcoinAPI):
    url = "{base}/outputs".format(base=BlockhairBitcoinAPI.url)

    def __init__(self):
        super().__init__()

    def query(self, value=None, time=None, s="value(asc)"):
        """
            value: dict with params 'from' (int or string) and 'to' (int or string)
            time: dict with params 'from' and 'to'
        """
        if time:
            if isinstance(time['from'], datetime):
                time['from'] = datetime.strftime(time['from'], "%Y-%m-%d+%H:%M:%S")
            if isinstance(time['to'], datetime):
                time['to'] = datetime.strftime(time['to'], "%Y-%m-%d+%H:%M:%S")

        q = ','.join(['value({}..{})'.format(value.get('from', ''),value.get('to')),
                      'time({}..{})'.format(time.get('from'), time.get('to'))])
        params = {'q': q, 's': s}

        # urlencode api bug
        payload_str = "&".join("%s=%s" % (k, v) for k, v in params.items())
        resp = requests.get(self.url, params=payload_str)
        data = resp.json()
        if data['total'] == 0:
            raise TransactionNotFoundError()
        if data['total'] == 1:
            return data['data'][0]
        else:
            raise TooMuchTransactionMatchesError("Too much transactions match the criteria: {}".format(data['total']))



transactions = Transactions()
outputs = Outputs()

if __name__ == '__main__':
    # DEBUG
    amount_from = 0.25214442
    satoshi_mupltiplier = 100000000
    value_from_ol = {
        'from': str(int(satoshi_mupltiplier * amount_from)),
        'to': str(int(satoshi_mupltiplier * (amount_from + amount_from * openledger_commision)))
    }
    value_to_ol = {
        'from': str(int(satoshi_mupltiplier * (amount_from - amount_from * 3 * openledger_commision))),
        'to': str(int(satoshi_mupltiplier * amount_from))
    }
    time_from_ol = {
        'from': datetime.utcnow() - timedelta(minutes=30),
        'to': datetime.utcnow() - timedelta(minutes=0)
    }
    time_to_ol = {
        'from': datetime.utcnow() - timedelta(minutes=60),
        'to': datetime.utcnow() - timedelta(minutes=0)
    }

    outputs.query(value=value_to_ol, time=time_to_ol)