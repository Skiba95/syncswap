import json
from web3 import Web3
from eth_abi import encode
from web3.auto import w3
import random
import time
import math
from datetime import datetime
from colorama import Fore, Style
from web3.exceptions import ContractLogicError


# -------------------------------- CONFIG -------------------------------- #

# Флаг для включения/выключения рандомизации кошельков
randomize_wallets = True

# Установите диапазон количества транзакций для каждого кошелька
min_transactions = 1
max_transactions = 2

# Установка диапазона задержки между транзакциями в секундах
min_delay = 300
max_delay = 1200

# ------------------------------------------------------------------------ #

zero_address = '0x0000000000000000000000000000000000000000'
router_addr = '0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295'

endpoint_uri = 'https://rpc.ankr.com/zksync_era'
w3 = Web3(Web3.HTTPProvider(endpoint_uri))

# Чтение приватных ключей из файла
private_keys_file = open('wallets.txt')
private_keys = private_keys_file.read().splitlines()

# Определите пары токенов и соответствующие адреса пулов
with open('token_pairs.json') as f:
    token_pairs = json.load(f)

# Получение ABI контракта маршрутизатора
with open('router-abi.json') as f:
    router_abi = json.load(f)

# Выполняет обмен с ETH в заданных парах
def perform_swap(private_key, token_pair):
    account = w3.eth.account.from_key(private_key)
    caller = account.address

    token_in = token_pair['token_in']
    token_in_addr = token_pair['token_in_addr']
    token_out = token_pair['token_out']
    token_out_addr = token_pair['token_out_addr']
    pool_addr = token_pair['pool_addr']

    # Генерация случайной суммы в заданном диапазоне для каждой транзакции
    amount_eth = random.uniform(0.00005, 0.0004)  # Сумма в ETH (случайное значение между 0,001 и 0,01 ETH)
    amount = int(amount_eth * 10 ** 18)  # Количество десятичных знаков в ETH

    withdraw_mode = 1  # 1 - возвращает ETH, 2 - возвращает wETH

    swapData = encode(['address', 'address', 'uint8'], [token_in_addr, token_out_addr, withdraw_mode])

    # Построение шагов
    steps = [
        {
            'pool': pool_addr,
            'data': swapData,
            'callback': zero_address,
            'callbackData': '0x'
        }
    ]

    # Построение путей
    native_eth_address = zero_address

    paths = [
        {
            'steps': steps,
            'tokenIn': native_eth_address,
            'amountIn': amount
        }
    ]

    # Вызов swap()
    router = w3.eth.contract(address=router_addr, abi=router_abi)

    amountOutMin = 0
    deadline = math.floor(time.time() + 60 * 30)

    tx = router.functions.swap(paths, amountOutMin, deadline).build_transaction(
        {
            "from": caller,
            "nonce": w3.eth.get_transaction_count(caller),
            "value": amount,
            "gasPrice": w3.eth.gas_price,
            "gas": 1500000,
        }
    )

    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.BLUE}{timestamp}{Style.RESET_ALL} | {Fore.GREEN} success {Style.RESET_ALL} | {Fore.MAGENTA}{token_in} -> {token_out}{Style.RESET_ALL} | {Fore.GREEN}transaction: https://explorer.zksync.io/tx/{tx_hash.hex()}{Style.RESET_ALL}")

if randomize_wallets:
    random.shuffle(private_keys)  # Перемешиваем список приватных ключей

for private_key in private_keys:
    account = w3.eth.account.from_key(private_key)
    caller = account.address

    print('')
    print('')
    print(f"{Fore.BLUE}Wallet: {Style.RESET_ALL}{caller}")
    print('')
    
    # Генерация случайного количества транзакций для данного кошелька
    num_transactions = random.randint(min_transactions, max_transactions)

    # Выполнение статических транзакций
    tx_count = 0
    while tx_count < num_transactions:
        random.shuffle(token_pairs)  # Перемешиваем список пар токенов

        # Выбор случайной пары токенов
        token_pair = token_pairs[0]

        try:
            perform_swap(private_key, token_pair)
        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{Fore.BLUE}{timestamp}{Style.RESET_ALL} |{Fore.RED}  error swaping: {e} {Style.RESET_ALL} ")

        if tx_count < num_transactions - 1:
            wait_time = random.randint(min_delay, max_delay)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{Fore.BLUE}{timestamp}{Style.RESET_ALL} | {Fore.CYAN} waiting before next transaction {wait_time} sec{Style.RESET_ALL}")
            time.sleep(wait_time)

        tx_count += 1

    # Добавление задержки перед переходом к следующему кошельку
    wait_time = random.randint(min_delay, max_delay)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.BLUE}{timestamp}{Style.RESET_ALL} | {Fore.CYAN} waiting before next wallet {wait_time} sec{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}-------------------------------------------------------------------------------------------------------------------------------------------------------------{Style.RESET_ALL}")
    time.sleep(wait_time)

# Закрытие файла приватных ключей
private_keys_file.close()