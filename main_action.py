import asyncio
import random
import warnings
from sys import stderr

from loguru import logger

from data.data import *
from database.main import all_wallets_to_action, current_wallet
from modules.activity.dmail import Dmail
from modules.activity.zkstars import ZkStars

logger.remove()
custom_name = "MAIN Action"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<20}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


class RandomAction:
    def __init__(self, wallet: dict,  index: int = 0,  minuts: [int, float] = 0) -> None:
        self.__wallet = wallet
        self.__private_key = wallet["private_key"]
        self.__index = index
        self.__minuts = minuts

    async def action(self):
        TYPE = [2, 2]

        if self.__wallet['dmail_count'] == 0:
            TYPE.append(2)

        if self.__wallet['zkstars_count'] < len(zkstar_contracts):
            TYPE.append(9)

        _type = random.choice(TYPE)

        if _type == 2:
            start = Dmail(private_key=self.__private_key, index=self.__index, minuts=self.__minuts)
            await start.mail()

        elif _type == 9:
            start = ZkStars(private_key=self.__private_key, index=self.__index, contracts=self.__wallet['zkstar_contracts'], minuts=self.__minuts)
            await start.mint()
async def one_wallet_swaps(wallet: dict, index: int):
    logger.info(f"START ACTION  | index = {index} | {wallet['public_key']}")
    await asyncio.sleep(int(0 + index * random.uniform(5, 10)) * 60)
    num_of_action = random.randint(2, 3)
    for num in range(0, num_of_action):
        coefficient = 1 if num_of_action - 1 > num else 0
        start = RandomAction(wallet=wallet, index=index, minuts=random.uniform(15, 35) * coefficient)
        await start.action()
        wallet = await current_wallet(wallet['public_key'])
    logger.success(f"FINISH ACTION    | index = {index} | {wallet['public_key']}")


async def multithreading(limit: int, offset: int = 0):
    wallets = await all_wallets_to_action(limit=limit, offset=offset)
    random.shuffle(wallets)
    random.shuffle(wallets)
    random.shuffle(wallets)

    tasks = []
    for index, wallet in enumerate(wallets):
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
