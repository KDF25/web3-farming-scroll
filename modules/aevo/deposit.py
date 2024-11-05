import asyncio
import random
import warnings
from sys import stderr

from loguru import logger
from web3 import Web3

from abi import load_abi
from config import all_proxies
from data.data import RPC
from database.main import current_wallet, update_aevo
from utils.utils import tx_type_eip_legacy, check_status_tx

logger.remove()
custom_name = "aevo Deposit"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<20}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


class AevoDeposit:
    def __init__(self, wallet: dict,  index: int = 0, minuts: [float, int] = 0) -> None:
        proxy = random.choice(all_proxies)
        proxies = {'http': proxy}
        request_kwargs = {"proxies": proxies, "timeout": 120}
        self.web3 = Web3(Web3.HTTPProvider(RPC["SCROLL"]["rpcUrl"], request_kwargs=request_kwargs))
        self.wallet = wallet
        self.private_key = wallet['private_key']
        self.account = self.web3.eth.account.from_key(self.private_key)
        self.address_wallet = self.account.address
        self.index = index
        self.minuts = minuts

    async def start(self) -> None:
        try:
            aevo = self.web3.to_checksum_address(RPC["SCROLL"]["aevo_landing"])
            balance = self.web3.eth.get_balance(self.address_wallet, 'latest')
            aevo_abi = await load_abi('aevo_abi')
            aevo_contract = self.web3.eth.contract(address=aevo, abi=aevo_abi)
            amountIn = int(random.randint(60, 85) * balance)

            logger.info(f'START    | index = {self.index} | {self.address_wallet} | Balance = {balance / 10 ** 18} ETH ')

            tx_type = await tx_type_eip_legacy(web3=self.web3, address_wallet=self.address_wallet)

            tx = aevo_contract.functions.depositETH(
                self.web3.to_checksum_address("0x4d9429246EA989C9CeE203B43F6d1C7D83e3B8F8"),
                self.address_wallet,
                0
            ).build_transaction(tx_type)

            tx.update({'value': amountIn})
            gasLimit = self.web3.eth.estimate_gas(tx)
            tx.update({'gas': gasLimit})

            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            raw_tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            balance = self.web3.eth.get_balance(self.address_wallet, 'latest')
            status = await check_status_tx(self.web3, raw_tx_hash)

            if status == 1:
                logger.success(f'FINISH   | index = {self.index} | {self.address_wallet} | Transaction: {RPC["SCROLL"]["tokenScan"]}/tx/{raw_tx_hash.hex()} | Balance = {balance / 10 ** 18} ETH | SLEEP = {round(self.minuts, 2)} min')
                route: list = self.wallet['aevo'].get("route", [])
                route.append(f"{custom_name}|ETH|{round(amountIn / 10 ** 18, 6)}")
                self.wallet['aevo']["deposit_count"] = self.wallet['aevo'].get("deposit_count", 0) + 1
                self.wallet['aevo']["total_volume"] = self.wallet['aevo'].get("total_volume", 0) + amountIn
                self.wallet['aevo'].update({"deposit": amountIn, "route": route})
                await update_aevo(public_key=self.wallet['public_key'], aevo=self.wallet['aevo'])
                await asyncio.sleep(self.minuts * 60)

            elif status == 0:
                logger.error(f'FINISH   | index = {self.index} | {self.address_wallet} | Transaction: {RPC["SCROLL"]["tokenScan"]}/tx/{raw_tx_hash.hex()} | Balance = {balance / 10 ** 18} ETH | SLEEP = {round(self.minuts, 2)} min')

        except Exception as ex:
            logger.error(f'ERROR    | index = {self.index} | {self.address_wallet} | {ex}')


async def new():
    wallet = await current_wallet(public_key="")
    new_class = AevoDeposit(
        wallet=wallet,
        index=0
    )
    await new_class.start()


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        logger.info(f'START')
        asyncio.run(new())
    except KeyboardInterrupt:
        pass

