import asyncio
import random
import warnings
from sys import stderr

from loguru import logger
from web3 import Web3

from abi import load_abi
from config import all_proxies
from data.data import RPC, zkstar_contracts
from database.main import current_wallet, update_zkstars
from utils.utils import tx_type_eip_legacy, check_status_tx

logger.remove()
custom_name = "ZkStars"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<20}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


class ZkStars:
    def __init__(self, private_key: str,  contracts: [list, None], index: int = 0,  minuts: [int, float] = 0,) -> None:
        proxy = random.choice(all_proxies)
        proxies = {'http': proxy}
        request_kwargs = {"proxies": proxies, "timeout": 120}
        self.web3 = Web3(Web3.HTTPProvider(RPC["SCROLL"]["rpcUrl"], request_kwargs=request_kwargs))
        self.private_key = private_key
        self.account = self.web3.eth.account.from_key(private_key)
        self.address_wallet = self.account.address
        self.index = index
        self.minuts = minuts
        self.contracts = contracts if contracts is not None  else []

    async def mint(self) -> None:
        try:
            zkstars_abi = await load_abi('zkstars_abi')
            difference = set(zkstar_contracts) - set(self.contracts)
            contract = random.choice(list(difference))
            zkstars_contract = self.web3.eth.contract(address=Web3.to_checksum_address(contract), abi=zkstars_abi)

            balance = self.web3.eth.get_balance(self.address_wallet, 'latest')
            logger.info(f'START    | index = {self.index} | {self.address_wallet} | Balance = {balance / 10 ** 18} ETH ')

            tx_type = await tx_type_eip_legacy(web3=self.web3, address_wallet=self.address_wallet)

            mint_price = zkstars_contract.functions.getPrice().call()

            tx = zkstars_contract.functions.safeMint(
                Web3.to_checksum_address("0x1C7FF320aE4327784B464eeD07714581643B36A7")
            ).build_transaction(tx_type)

            tx.update({"value": mint_price})

            gasLimit = self.web3.eth.estimate_gas(tx)
            tx.update({'gas': gasLimit})
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            raw_tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            balance = self.web3.eth.get_balance(self.address_wallet, 'latest')
            status = await check_status_tx(self.web3, raw_tx_hash)

            if status == 1:
                logger.success(f'FINISH   | index = {self.index} | {self.address_wallet} | Transaction: {RPC["SCROLL"]["tokenScan"]}/tx/{raw_tx_hash.hex()} | Balance = {balance / 10 ** 18} ETH | SLEEP = {round(self.minuts, 2)} min')
                await update_zkstars(public_key=self.address_wallet, contract=contract)
                await asyncio.sleep(self.minuts * 60)

            elif status == 0:
                logger.error(f'FINISH   | index = {self.index} | {self.address_wallet} | Transaction: {RPC["SCROLL"]["tokenScan"]}/tx/{raw_tx_hash.hex()} | Balance = {balance / 10 ** 18} ETH | SLEEP = {round(self.minuts, 2)} min')

        except Exception as ex:
            logger.error(f'ERROR    | index = {self.index} | {self.address_wallet} | {ex}')
            await asyncio.sleep(5 * 60)


async def new():
    wallets = await current_wallet(public_key="")
    new_class = ZkStars(
        private_key=wallets['private_key'],
        contracts=[]
    )
    await new_class.mint()


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        logger.info(f'START')
        asyncio.run(new())
    except KeyboardInterrupt:
        pass


