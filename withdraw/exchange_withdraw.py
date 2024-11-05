import asyncio
import random
import warnings
from math import ceil, floor
from sys import stderr
from typing import Union, Literal

from binance.error import ClientError
from binance.spot import Spot as Client
from loguru import logger

from config import *
from database.main import update_first_withdraw

logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | " "<white>{message}</white>")

network = {
    'ARBITRUM': {'coin': 'ETH', 'currency': 0.0008},
    'OPTIMISM': {'coin': 'ETH', 'currency': 0.001},
}


async def withdraw_from_binance(coin: str, network: Literal["ARBITRUM", "OPTIMISM"], wallet: str,
                                AmountFrom: Union[int, float], AmountTo: Union[int, float], stream: int = None):
    AmountToWithdraw = round(random.uniform(AmountFrom, AmountTo), 6)

    for attempt in range(max_tries):

        try:
            logger.info(f'STREAM {stream} | START  | {wallet} | Network = {network} | Coin = {coin} | Amount = {AmountToWithdraw}')
            spot_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, )
            withdraw = spot_client.withdraw(coin=coin, amount=AmountToWithdraw, network=network, address=wallet)
            logger.success(f'STREAM {stream} | FINISH | {wallet} | Network = {network} | Coin = {coin} | Amount = {AmountToWithdraw} | {withdraw}')
            await update_first_withdraw(public_key=wallet, currency=AmountToWithdraw, Mainnet=network)
            break

        except ClientError as ex:
            logger.error(f'STREAM {stream} | ERROR | {wallet} | Network = {network} | Coin = {coin} | Amount = {AmountToWithdraw} | {ex}')


async def withdraw_wallets_random(stream: int, wallets: list):
    NETS = ["OPTIMISM", "ARBITRUM"]
    for index, wallet in enumerate(wallets):
        wallet = wallet['public_key']
        net = random.choice(NETS)
        try:
            await withdraw_from_binance(coin=network[net]['coin'], network=net, wallet=wallet, stream=stream,
                                        AmountFrom=network[net]['currency'], AmountTo=network[net]['currency'] * 1.05)

            await asyncio.sleep(random.randint(5 * 60, 10 * 60))

        except BaseException as ex:
            logger.error(f'GLOBAL ERROR | {wallet} | {ex}')

        logger.success(f'STREAM {stream} | FINISH {index + 1} / {len((wallets))}')

    logger.success(f'STREAM {stream} | FINISH ALL WITHDRAW ')


async def multithreading():
    stream_num = 1
    wallets = await all_wallets_to_withdraw(limit=10, offset=201)
    """

    ALWAYS CHECK DATABASE

    """
    wallets_len = len(wallets)
    tasks = []
    end = 0
    for stream in range(0, stream_num):
        if stream < wallets_len % stream_num:
            num = ceil(wallets_len / stream_num)

        elif stream >= wallets_len:
            break

        else:
            num = floor(wallets_len / stream_num)

        stream_wallets = wallets[end:end + num]
        end += num
        task = asyncio.create_task(withdraw_wallets_random(stream=stream, wallets=stream_wallets))
        tasks.append(task)

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    try:
        warnings.filterwarnings("ignore")
        loop = asyncio.new_event_loop()
        loop.run_until_complete(multithreading())
    except KeyboardInterrupt:
        pass

# MATIC | MATIC
# FTM | FTM
# AVAX | AVAXC
# ETH | ARBITRUM
# ETH | OPTIMISM




