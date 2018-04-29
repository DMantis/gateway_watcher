import logging
import redis
import time
import threading
import pymongo
import yaml
from datetime import datetime, timedelta
from bitshares.account import Account as BTSAccount

from asset import Asset
import blockchair

mongo_lock = threading.Lock()

logger = logging.getLogger('gateway_watcher')
# debug
logging.basicConfig(level=logging.INFO)

with open('app.conf') as f:
    config = yaml.safe_load(f.read())

r = redis.Redis(db=config['redis_db_num'])
mongo_client = pymongo.MongoClient()


def task_loop():
    """
        Так как при выводе с OL транзакция появляется на BitShares раньше блокчейна биткоина, необоходимо подождать
        несколько блоков до проверки.

        Таблица tasks хранит объекты заведенных задач на исполнение.

        Статусы:
         0 - новая задача
         1 - задача выполнена успешна
         2 - ошибка при выполнении, отправлена на доработку с новыми параметрами
         3 - ошибка при выполении, закрыта

        Таблица txs хранит соотношение транзакций на блокчейне биткоина и аккаунтов BitShares.
    """
    logger.info('task loop started')
    while True:
        time.sleep(5)
        now = datetime.utcnow()
        task = mongo_client.app.tasks.find_one({"dt": {"$lt": now}, "status": {"$in": [0, 2]}})
        result = {}

        if not task:
            continue
        try:
            tx_info = find_bitcoin_tx(task['amount'], task['commision'], task['lookup_time_min'], task['direction'])
            logger.info(tx_info)
        except blockchair.TransactionNotFoundError:
            logger.info('Transaction not found')
            if task['status'] == 0:
                update_data = {'$set': {'status': 2, 'commision': task['commision'] * 3}}
            else:
                update_data = {'$set': {'status': 3}}
        except blockchair.TooMuchTransactionMatchesError as err:
            logger.info(err)
            update_data = {'$set': {'status': 3}}
        else:
            update_data = {'$set': {'status': 1}}
            result = {
                'account': task['account'],
                'tx': tx_info['transaction_hash'],
                'value': tx_info['value'],
                'direction': task['direction']
            }

        with mongo_lock:
            if result:
                mongo_client.app.txs.insert_one(result)
            mongo_client.app.tasks.update_one({'_id': task['_id']}, update_data)


class RequiredFieldMissedError(Exception):
    pass


def format_amount(amount):
    msg = format(amount, '.9f').rstrip('0')
    if msg[-1] == '.':
        msg += '0'
    return msg


# find_bitcoin_tx(amount, commision=0.0006, lookup_time_min=60, direction=1) для вывода с DEX
# find_bitcoin_tx(amount, commision=0.0002, lookup_time_min=30, direction=0) для ввода на DEX
def find_bitcoin_tx(amount, commision=0.0002, lookup_time_min=30, direction=0):
    satoshi_multiplier = 100000000

    # диапазон искомых значений зависит от того, происходит вывод или ввод средств на DEX/Graphene Blockchain.
    if direction == 0:
        value = {
            'from': str(int(satoshi_multiplier * amount)),
            'to': str(int(satoshi_multiplier * (amount + amount * commision)))
        }
    else:
        value = {
            'from': str(int(satoshi_multiplier * (amount - amount * commision))),
            'to': str(int(satoshi_multiplier * amount))
        }

    time = {
        'from': datetime.utcnow() - timedelta(minutes=lookup_time_min),
        'to': datetime.utcnow()
    }
    return blockchair.outputs.query(time=time, value=value)


def transfer_handler(op_info):
    for field in ['from', 'to', 'amount']:
        if field not in op_info:
            raise RequiredFieldMissedError("Missed required field {} in op_info".format(field))

    account_from = BTSAccount(op_info['from']).name
    account_to = BTSAccount(op_info['to']).name
    asset = Asset(op_info['amount']['asset_id'], op_info['amount']['amount'])

    if asset.symbol != 'OPEN.BTC':
        return None
    logging.info("Transfer {0} {1} from *{2}* to *{3}*".format(
        format_amount(asset.amount), asset.symbol, account_from, account_to))

    task = {'amount': asset.amount, 'status': 0}

    if account_from == 'openledger-dex':
        task.update({
            'account': account_to,
            'lookup_time_min': 30,
            'commision': 0.0002,
            'direction': 0,
            'dt': datetime.utcnow() + timedelta(minutes=0)
        })
        # find_bitcoin_tx(asset.amount)
    elif account_to == 'openledger-dex':
        task.update({
            'account': account_from,
            'lookup_time_min': 60,
            'commision': 0.0006,
            'direction': 1,
            'dt': datetime.utcnow() + timedelta(minutes=60)
        })

    with mongo_lock:
        mongo_client.app.tasks.insert_one(task)


def account_updates(account_name, stop_block):
    bts_account = BTSAccount(account_name)
    bts_history = bts_account.history(limit=100)

    first_entry = bts_history.__next__()
    first_block_num = first_entry['block_num']
    if stop_block is None:
        r.set(account_name, first_block_num)
        stop_block = first_block_num
        logger.info('last_processed_block for account {} not found. set {} as '
                    'last_processed_block'.format(account_name, first_block_num))
    stop_block = int(stop_block)

    if first_entry['block_num'] <= stop_block:
        #  logger.debug('{}, {}'.format(first_entry['block_num'], stop_block))
        r.set(account_name, first_block_num)
        raise StopIteration
    yield process_history_entry(first_entry)

    for history_entry in bts_history:
        if history_entry['block_num'] <= stop_block:
            r.set(account_name, first_block_num)
            raise StopIteration
        yield process_history_entry(history_entry)
    r.set(account_name, first_block_num)


def process_history_entry(history_entry):
    """ Process account's history entry. """
    logger.debug('process history entry {}'.format(history_entry))
    operation = history_entry.get('op')
    if not operation:
        logger.warning('no operations found: {}'.format(history_entry))
    op_code, op_info = operation[0], operation[1]

    # 0 - transfer opcode
    if op_code != 0:
        return

    try:
        return transfer_handler(op_info)
    except RequiredFieldMissedError:
        logger.error('required field missed in {}'.format(history_entry))
        return None


def process_account(account_name):
    logger.debug('process account {}'.format(account_name))
    stop_block = r.get(account_name)
    update_msgs = []
    for update_msg in account_updates(account_name, stop_block):
        if update_msg:
            msg = str(datetime.now()) + ": " + update_msg
            print(msg)


def process_loop(check_interval=15):
    while True:
        process_account('openledger-dex')
        time.sleep(check_interval)


if __name__ == '__main__':
    logger.info('service has been started')
    threading.Thread(target=task_loop).start()
    process_loop(10)