import asyncio
import random
import warnings
from sys import stderr

from loguru import logger

from database.main import all_wallets_to_bridge, current_wallet
from modules.bridge import OrbiterBridge

logger.remove()
custom_name = "MAIN Bridge"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<20}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


async def start_abuse_bridge(wallet: dict, index: int = 0):
    logger.info(f"ROUTE  {wallet['mainnet']} -- Scroll | index = {index} | {wallet['public_key']}")
    bridge = OrbiterBridge(
        private_key=wallet['private_key'],
        from_chain="SCROLL",
        to_chain="ARBITRUM",
        index=index
    )
    await bridge.bridge()


async def multithreading(limit: int, offset: int = 0):
    wallets = []
    random.shuffle(wallets)
    random.shuffle(wallets)
    for index, wallet in enumerate(wallets):
        logger.info(f"ROUTE | index = {index} | {wallet}")

    for index, wallet in enumerate(wallets):
        wallet = await current_wallet(public_key=wallet)
        await start_abuse_bridge(wallet=wallet, index=index)
        await asyncio.sleep(random.uniform(5, 15) * 60)


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        logger.info(f'START BRIDGE')
        asyncio.run(multithreading(40, 0))
    except KeyboardInterrupt:
        pass