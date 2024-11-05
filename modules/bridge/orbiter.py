import asyncio
import random
import warnings
from sys import stderr
from typing import Literal

import requests
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from loguru import logger
from web3 import Web3

from config import all_proxies
from data.data import RPC
from database.main import current_wallet, update_bridge

from utils.utils import tx_type_eip_1559, check_status_tx

logger.remove()
custom_name = "Orbiter Bridge"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<20}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


class OrbiterBridge:
    def __init__(self,
                 private_key: str,
                 from_chain: Literal["ARBITRUM", "OPTIMISM", "ZKSYNC", "SCROLL", "BASE", "LINEA"],
                 to_chain: Literal["ARBITRUM", "OPTIMISM", "ZKSYNC", "SCROLL", "BASE", "LINEA"],
                 index: int = 0) -> None:

        self.__amount = 0
        proxy = random.choice(all_proxies)
        self.__proxies = {'http': proxy}
        request_kwargs = {"proxies": self.__proxies, "timeout": 120}
        self.__private_key = private_key
        self.__from_chain = from_chain
        self.__to_chain = to_chain
        self.__web3 = Web3(Web3.HTTPProvider(RPC[from_chain]["rpcUrl"], request_kwargs=request_kwargs))
        self.__account = self.__web3.eth.account.from_key(private_key)
        self.__address_wallet = self.__account.address
        self.__index = index
        self.__fee = {
            "ARBITRUM": 0.0013,
            "OPTIMISM": 0.0013,
            "BASE": 0.0015,
            "LINEA": 0.0013,
            "SCROLL": 0.00045,
        }
        self.chain_ids = {
            "ETH": "1",
            "ARBITRUM": "42161",
            "OPTIMISM": "10",
            "ZKSYNC": "324",
            "SCROLL": "534352",
            "BASE": "8453",
            "LINEA": "59144",
        }

    async def get_bridge_amount(self):
        url = "https://openapi.orbiter.finance/explore/v3/yj6toqvwh1177e1sexfy0u1pxx5j8o47"

        data = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "orbiter_calculatedAmount",
            "params": [f"{self.chain_ids[self.__from_chain]}-{self.chain_ids[self.__to_chain]}:ETH-ETH", float(self.__amount)]
        }
        # connector = ProxyConnector.from_url(random.choice(all_proxies))
        # async with ClientSession(connector=connector) as session:
        response = requests.post(
            url=url,
            headers={"Content-Type": "application/json"},
            json=data,
        )

        response_data = response.json()
        # print(response_data)
        if response_data.get("result").get("error", None) is None:
            # print(int(response_data.get("result").get("_sendValue")))
            return int(response_data.get("result").get("_sendValue"))

        else:
            error_data = response_data.get("result").get("error")

            logger.error(f"[{self.__index}][{self.__address_wallet}] Orbiter error | {error_data}")

            return False

    async def bridge(self) -> None:
        try:

            balance = self.__web3.eth.get_balance(self.__address_wallet, 'latest')
            logger.info(f'START    | index = {self.__index} | {self.__address_wallet} | {self.__from_chain} --> {self.__to_chain} | Balance = {balance / 10 ** 18} ETH ')
            BALANCE = round(balance / 10 ** 18, 5) - 0.00002
            self.__amount = BALANCE - self.__fee[self.__from_chain]
            bridge_amount = await self.get_bridge_amount()

            if bridge_amount is False:
                return

            if bridge_amount > balance:
                logger.error(f'ERROR    | index = {self.__index} | {self.__address_wallet} | {self.__from_chain} --> {self.__to_chain} | Balance = {balance / 10 ** 18} ETH | BRIDGE AMOUNT = {bridge_amount / 10 ** 18} ETH | Insufficient funds!')
                return

            tx = {
                'chainId': self.__web3.eth.chain_id,
                # 'maxFeePerGas': self.__web3.eth.gas_price,
                # 'maxPriorityFeePerGas': self.__web3.eth.max_priority_fee,
                'gasPrice': self.__web3.eth.gas_price,
                'nonce': self.__web3.eth.get_transaction_count(self.__address_wallet),
                'to': '0x80C67432656d59144cEFf962E8fAF8926599bCF8',
                'gas': 0,
                'value': 0
            }

            gasLimit = self.__web3.eth.estimate_gas(tx)
            tx.update({'gas': gasLimit})
            tx.update({'value': bridge_amount})
            signed_tx = self.__web3.eth.account.sign_transaction(tx, self.__private_key)
            raw_tx_hash = self.__web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            status = await check_status_tx(self.__web3, raw_tx_hash)
            balance = self.__web3.eth.get_balance(self.__address_wallet, 'latest')

            if status == 1:
                logger.success(f'FINISH   | index = {self.__index} | {self.__address_wallet} | {self.__from_chain} --> {self.__to_chain} | Transaction: {RPC[self.__from_chain]["tokenScan"]}/tx/{raw_tx_hash.hex()} | Balance = {balance / 10 ** 18} ETH')
                await update_bridge(public_key=self.__address_wallet)

            elif status == 0:
                logger.error(f'FINISH   | index = {self.__index} | {self.__address_wallet} | {self.__from_chain} --> {self.__to_chain} | Transaction: {RPC[self.__to_chain]["tokenScan"]}/tx/{raw_tx_hash.hex()} | Balance = {balance / 10 ** 18} ETH')

        except Exception as ex:
            logger.error(f'ERROR    | index = {self.__index} | {self.__address_wallet} | {self.__from_chain} --> {self.__to_chain} | {ex}')


async def new():
    wallets = await current_wallet(public_key="")
    new_class = OrbiterBridge(
        private_key=wallets['private_key'],
        from_chain="SCROLL",
        to_chain="ARBITRUM",
        index=0,
    )
    await new_class.bridge()

if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        logger.info(f'START')
        asyncio.run(new())
    except KeyboardInterrupt:
        pass










