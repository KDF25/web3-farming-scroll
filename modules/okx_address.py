import asyncio
import random
import warnings
from sys import stderr

from loguru import logger
from web3 import Web3

from config import all_proxies
from data.data import RPC
from database.main import current_wallet
from utils.utils import check_status_tx

logger.remove()
custom_name = "Okx Deposit"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<20}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)
slippage = 1


class OkxDeposit:

    def __init__(self, wallet: dict, index: int = 0) -> None:
        proxy = random.choice(all_proxies)
        self.__proxies = {'http': proxy}
        request_kwargs = {"proxies": self.__proxies, "timeout": 120}
        self.__web3 = Web3(Web3.HTTPProvider(RPC["ARBITRUM"]["rpcUrl"], request_kwargs=request_kwargs))
        self.__wallet = wallet
        self.__ETH = wallet['ETH']
        self.__private_key = wallet['private_key']
        self.__account = self.__web3.eth.account.from_key(self.__private_key)
        self.__address_wallet = self.__account.address
        self.__index = index

    async def start(self):
        try:
            balance = self.__web3.eth.get_balance(self.__address_wallet, 'latest')
            gas_price = self.__web3.eth.gas_price
            logger.info(
                f'START TRANSFER  | index = {self.__index} | {self.__address_wallet} | Balance = {balance / 10 ** 18} native token | Gas price = {gas_price / 10 ** 9}')
            to = self.__web3.to_checksum_address(self.__wallet['okx_address'])
            # value = await okx_deposit_balance2(balance=balance, ETH=self.__ETH)
            value = 0
            tx = {
                "chainId": self.__web3.eth.chain_id,
                'nonce': self.__web3.eth.get_transaction_count(self.__address_wallet),
                'maxFeePerGas': self.__web3.eth.gas_price,
                'maxPriorityFeePerGas': self.__web3.eth.gas_price,
                'gas': 0,
                "from": self.__address_wallet,
                "to": to,
                "value": value,
                "data": "0x"
            }
            # print(tx)
            gasLimit = self.__web3.eth.estimate_gas(tx)
            value = balance - gasLimit * gas_price
            tx.update({'gas': gasLimit})
            tx.update({'value': value})
            signed_transfer_txn = self.__web3.eth.account.sign_transaction(tx, self.__private_key)
            transfer_txn_hash = self.__web3.eth.send_raw_transaction(signed_transfer_txn.rawTransaction)

            status = await check_status_tx(self.__web3, transfer_txn_hash)

            if status == 1:
                logger.success(
                    f'FINISH TRANSFER | index = {self.__index} | {self.__address_wallet} | Transaction: {RPC["ARBITRUM"]["tokenScan"]}/tx/{transfer_txn_hash.hex()} | Balance = {balance / 10 ** 18} native token |')
                balance = self.__web3.eth.get_balance(self.__address_wallet, 'latest')

            elif status == 0:
                logger.error(
                    f'FINISH TRANSFER | index = {self.__index} | {self.__address_wallet} | Transaction: {RPC["ARBITRUM"]["tokenScan"]}/tx/{transfer_txn_hash.hex()} | Balance = {balance / 10 ** 18} native token |')

        except Exception as ex:
            logger.error(f'ERROR TRANSFER  | index = {self.__index} | {self.__address_wallet} | {ex}')


async def new():
    wallet = await current_wallet(public_key="")
    new_class = OkxDeposit(
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

