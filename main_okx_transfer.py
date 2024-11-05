import asyncio
import random
import warnings
from sys import stderr

from loguru import logger

from database.main import current_wallet
from modules.okx_address import OkxDeposit

logger.remove()
custom_name = "MAIN Okx Transfer"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


async def okx_transfer(wallet: dict, index: int):
    logger.info(f"START    | index = {index} | {wallet['public_key']} |")
    await asyncio.sleep(int(0 + index * random.uniform(10, 15)) * 60)
    okx = OkxDeposit(wallet=wallet, index=index)
    await okx.start()


async def multithreading():
    wallets = []

    tasks = []
    for index, wallet in enumerate(wallets):
        wallet = await current_wallet(public_key=wallet)
        task = asyncio.create_task(okx_transfer(wallet=wallet, index=index))
        tasks.append(task)

    while len(tasks) > 0:
        tasks[:] = [task for task in tasks if not task.done()]
        await asyncio.sleep(60)


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        asyncio.run(multithreading())
    except KeyboardInterrupt:
        pass
