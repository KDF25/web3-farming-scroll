import asyncio
import random
import warnings
from sys import stderr

from loguru import logger
from web3 import Web3, HTTPProvider

from data.data import *
from database.main import all_wallets_to_swap, current_wallet, current_swaps
from modules.swap import *
from modules.swap.zebra_swap import zebraSwap
from utils.utils import all_dex

logger.remove()
custom_name = "MAIN Remaining Swap"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<20}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)

SELL_TO_TOKEN = ["ETH", "ETH"]
NUM_OF_TOKENS = 4
ORDER_TYPE = ["sell", "sell"]
MAX_AMOUNT = int(10 ** 200)
GAS_MAX = 50

MODULES = {
    'sync_swap': True,
    'zebra_swap': True,
}

ALL_DEX = all_dex(modules=MODULES)
SELL_ANYWAY = True


async def _gas():
    while True:
        try:
            mainnet_w3 = Web3(HTTPProvider(endpoint_uri='https://eth.meowrpc.com'))
            return int(mainnet_w3.eth.gas_price / 10 ** 9)
        except Exception:
            pass


async def _gas_check() -> bool:
    while True:
        gas = await _gas()
        if gas > GAS_MAX:
            logger.info(f"GAS = {gas} GWEI")
            await asyncio.sleep(2 * 60)
        else:
            return True


class RandomSwaps:
    def __init__(self, wallet: dict,  index: int = 0,  minuts: [int, float] = 0) -> None:
        self._Swap = None
        self.__from_token = None
        self.__eth_equivalent = round(random.uniform(1, 1.7) * 0.02, 6)
        self.__wallet = wallet
        self.__private_key = wallet["private_key"]
        self.__Tokens = wallet["Tokens"]
        self.__order = random.choice(ORDER_TYPE)
        self.__index = index
        self.__minuts = minuts

    async def _get_amount_buy(self, SWAP_TOKENS: list):
        try:
            tokens = list(set(SWAP_TOKENS) - set(self.__Tokens))
            self.__to_token = random.choice(tokens)
            self.__amount = self.__eth_equivalent

        except Exception as ex:
            logger.warning(f"TOKENS ERROR    | index = {self.__index} | {self.__wallet['public_key']} | SWAP_TOKENS = {SWAP_TOKENS} | TOKENS = {self.__Tokens} | {ex}")

    async def _get_amount_sell(self):
        try:
            self.__Tokens.remove("ETH")
        except Exception:
            pass

        self.__from_token = random.choice(self.__Tokens)
        try:
            SELL_TO_TOKEN.remove(self.__from_token)

        except Exception:
            pass

        self.__to_token = random.choice(SELL_TO_TOKEN)
        self.__amount = MAX_AMOUNT

    async def _get_dex_buy(self):
        if len(self.__zeroSwaps) != 0:
            self.__dex = random.choice(self.__zeroSwaps)
        else:
            self.__dex = random.choice(list(ALL_DEX.values())) if SELL_ANYWAY else 0
            logger.warning(f"TOKEN BUY  ERROR| index = {self.__index} | {self.__wallet['public_key']} | {self.__from_token} --> XXX | SELL ANYWAY = {SELL_ANYWAY} | {self.__dex} | zeroSwaps = {self.__zeroSwaps} | AllDex = {ALL_DEX}")

    async def _get_dex_sell(self):
        zeroSwaps = list(set(self.__zeroSwaps) & set(self.__Random))
        if len(zeroSwaps) != 0:
            self.__dex = random.choice(zeroSwaps)

        else:
            self.__dex = random.choice(self.__Random) if SELL_ANYWAY else 0
            logger.warning(f"TOKEN SELL ERROR| index = {self.__index} | {self.__wallet['public_key']} | {self.__from_token} --> {self.__to_token} | SELL ANYWAY = {SELL_ANYWAY} | {self.__dex} | zeroSwaps = {self.__zeroSwaps} | Random = {self.__Random}")

    async def _get_zero_swaps(self):
        self.__zeroSwaps = []
        # need request from database
        dex = await current_swaps(public_key=self.__wallet['public_key'])
        for i in dex:
            try:
                if dex[i] == 0:
                    self.__zeroSwaps.append(ALL_DEX[i])
            except Exception:
                pass

    async def start_swaps(self):
        await self._get_zero_swaps()

        if len(self.__Tokens) == 1 or (len(self.__Tokens) < NUM_OF_TOKENS and self.__order == "buy"):
            # random - buy on random DEX it random token for eth equivalent
            await self._buy_token()

        elif len(self.__Tokens) >= NUM_OF_TOKENS or self.__order == "sell":
            # only sell token all currency except ETH for ETH or USDC
            await self._sell_token()

        else:
            return

        await self._choose_dex()

    async def _buy_token(self):
        self.__from_token = "ETH"
        await self._get_dex_buy()

        if self.__dex == 1:
            await self._get_amount_buy(SYNC_SWAP_TOKENS)

        if self.__dex == 2:
            await self._get_amount_buy(ZEBRA_SWAP_TOKENS)

    async def _sell_token(self):
        self.__Random = []
        await self._get_amount_sell()

        if self.__from_token in SYNC_SWAP_TOKENS:
            self.__Random.append(1)

        if self.__from_token in ZEBRA_SWAP_TOKENS:
            self.__Random.append(2)

        await self._get_dex_sell()

    async def _choose_dex(self):

        if self.__dex == 0:
            return

        elif self.__dex == 1:
            Swap = SyncSwap(private_key=self.__private_key, index=self.__index, minuts=self.__minuts,
                            from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif self.__dex == 2:
            Swap = zebraSwap(private_key=self.__private_key, index=self.__index, minuts=self.__minuts,
                                from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        await Swap.swap()


async def one_wallet_swaps(wallet: dict, index: int):
    num_of_swaps = 1
    logger.info(f"SWAPS | index = {index} | {wallet['public_key']} | num = {num_of_swaps} |")
    await asyncio.sleep(int(0 + index * random.uniform(15, 45)) * 60)

    for num in range(num_of_swaps):
        coefficient = 1 if num_of_swaps - 1 > num else 0
        await _gas_check()
        start = RandomSwaps(wallet=wallet, index=index, minuts=random.uniform(20, 30) * coefficient)
        await start.start_swaps()
        wallet = await current_wallet(public_key=wallet['public_key'])

    logger.success(f"FINISH SWAPS    | index = {index} | {wallet['public_key']} |  num = {num_of_swaps} | ")


async def multithreading(limit: int, offset: int = 0):
    wallets = await all_wallets_to_swap(limit=limit, offset=offset)
    tasks = []
    for index, wallet in enumerate(wallets):
        wallet = await current_wallet(public_key=wallet)
        task = asyncio.create_task(one_wallet_swaps(wallet=wallet, index=index))
        tasks.append(task)

    while len(tasks) > 0:
        tasks[:] = [task for task in tasks if not task.done()]
        await asyncio.sleep(60)


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        asyncio.run(multithreading(100, 0))
    except KeyboardInterrupt:
        pass
