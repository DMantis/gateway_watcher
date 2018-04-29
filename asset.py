from bitshares.asset import Asset as BTSAsset
import logging

logger = logging.getLogger('gateway_watcher')


class Asset:
    assets_table = {}

    def __init__(self, asset_id, raw_amount=0):
        self.id = asset_id
        if not Asset.assets_table.get(asset_id):
            logger.info('asset {} not found in assets_table, download.'.format(asset_id))
            Asset.add_asset(asset_id)
        self.symbol = Asset.assets_table[asset_id]['symbol']
        self.precision = Asset.assets_table[asset_id]['precision']
        self.raw_amount = int(raw_amount)

    @classmethod
    def add_asset(cls, asset_id):
        asset = BTSAsset(asset_id)
        cls.assets_table[asset_id] = {}
        # more checks?
        cls.assets_table[asset_id]['symbol'] = asset['symbol']
        cls.assets_table[asset_id]['precision'] = int(asset['precision'])

    @property
    def amount(self):
        # raw_amount = str(self.raw_amount)
        # a = "{0}.{1}".format(raw_amount[:-self.precision],
        #                      raw_amount[-self.precision:])
        # a = a.rstrip('0')
        # if a[-1] == '.':
        #     a += '0'
        return self.raw_amount / (10 ** self.precision)
