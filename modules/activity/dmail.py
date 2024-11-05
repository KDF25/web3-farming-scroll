import asyncio
import random
import warnings
from hashlib import sha256
from sys import stderr

from loguru import logger
from web3 import Web3

import nltk
from nltk.corpus import words

from abi import load_abi
from config import all_proxies
from data.data import RPC
from database.main import update_send_dmail__message, current_wallet
from utils.utils import tx_type_eip_1559, check_status_tx, tx_type_eip_legacy

logger.remove()
custom_name = "Dmail"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<20}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)

nltk.download('words')
english_words = words.words()


class Dmail:
    def __init__(self, private_key: str, index: int = 0,  minuts: [int, float] = 0) -> None:
        proxy = random.choice(all_proxies)
        proxies = {'http': proxy}
        request_kwargs = {"proxies": proxies, "timeout": 120}
        self.web3 = Web3(Web3.HTTPProvider(RPC["SCROLL"]["rpcUrl"], request_kwargs=request_kwargs))
        self.private_key = private_key
        self.account = self.web3.eth.account.from_key(private_key)
        self.address_wallet = self.account.address
        self.index = index
        self.minuts = minuts

    async def _generate_message(self):
        breakers = ["", "!", ".", "?"]
        num_words = random.randint(1, 3)
        message = ' '.join(random.sample(english_words, num_words)) + random.choice(breakers)
        self.__message = message[0:30]

    async def _generate_mail(self):
        domain_list = ["@gmail.com", "@dmail.ai"]
        breakers = ["", "_", "."]
        num_words = random.randint(1, 2)
        mail = f'{random.choice(breakers)}'.join(random.sample(english_words, num_words))
        self.__mail = mail[0:20] + random.choice(domain_list)

    async def _random_parameters(self):
        await self._generate_message()
        await self._generate_mail()

    async def mail(self) -> None:
        try:
            await self._random_parameters()
            dmail_abi = await load_abi('dmail_abi')
            dmail_contract = self.web3.eth.contract(address=Web3.to_checksum_address(RPC['SCROLL']['dmail_router']), abi=dmail_abi)

            balance = self.web3.eth.get_balance(self.address_wallet, 'latest')
            logger.info(f'START    | index = {self.index} | {self.address_wallet} | Balance = {balance / 10 ** 18} ETH | {self.__mail} | {self.__message}')

            # email = sha256(str(self.__mail).encode()).hexdigest()
            # theme = sha256(str(self.__message).encode()).hexdigest()

            data = dmail_contract.encodeABI("send_mail", args=(self.__mail, self.__message))
            tx = await tx_type_eip_legacy(web3=self.web3, address_wallet=self.address_wallet)

            tx.update(
                {
                    "to": Web3.to_checksum_address(RPC['SCROLL']['dmail_router']),
                    "data": data
                }
            )

            gasLimit = self.web3.eth.estimate_gas(tx)
            tx.update({'gas': gasLimit})
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            raw_tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            balance = self.web3.eth.get_balance(self.address_wallet, 'latest')
            status = await check_status_tx(self.web3, raw_tx_hash)

            if status == 1:
                logger.success(f'FINISH   | index = {self.index} | {self.address_wallet} | Transaction: {RPC["SCROLL"]["tokenScan"]}/tx/{raw_tx_hash.hex()} | Balance = {balance / 10 ** 18} ETH | SLEEP = {round(self.minuts, 2)} min')
                await update_send_dmail__message(public_key=self.address_wallet, message=self.__message, mail=self.__mail)
                await asyncio.sleep(self.minuts * 60)

            elif status == 0:
                logger.error(f'FINISH   | index = {self.index} | {self.address_wallet} | Transaction: {RPC["SCROLL"]["tokenScan"]}/tx/{raw_tx_hash.hex()} | Balance = {balance / 10 ** 18} ETH | SLEEP = {round(self.minuts, 2)} min')

        except Exception as ex:
            logger.error(f'ERROR    | index = {self.index} | {self.address_wallet} | {ex}')
            await asyncio.sleep(5 * 60)


async def new():
    wallets = await current_wallet(public_key="")
    new_class = Dmail(
        private_key=wallets['private_key'],
    )
    await new_class.mail()

if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        logger.info(f'START')
        asyncio.run(new())
    except KeyboardInterrupt:
        pass


