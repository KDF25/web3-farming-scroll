import asyncio
import random
import time
import warnings
from sys import stderr

from eth_abi import encode
from loguru import logger
from web3 import Web3

from abi import load_abi
from config import all_proxies
from data.data import RPC
from database.main import update_swap, current_wallet
from utils.utils import create_amount, full_conversion, tx_type_eip_legacy, check_status_tx, approve_token

logger.remove()
custom_name = "SyncSwap"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<20}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)

slippage = 1


class SyncSwap:
    def __init__(self, private_key: str, from_token: str, to_token: str, amount: [float, int],
                 index: int = 0, minuts: [float, int] = 0) -> None:
        proxy = random.choice(all_proxies)
        proxies = {'http': proxy}
        request_kwargs = {"proxies": proxies, "timeout": 120}
        self.web3 = Web3(Web3.HTTPProvider(RPC["SCROLL"]["rpcUrl"], request_kwargs=request_kwargs))
        self.private_key = private_key
        self.from_token = from_token
        self.to_token = to_token
        self.amount_to_swap = amount
        self.account = self.web3.eth.account.from_key(private_key)
        self.address_wallet = self.account.address
        self.index = index
        self.minuts = minuts

    async def get_min_amount_out(self, pool_address: str, token_address: str, amount: int, slippage: float):
        sync_swap_factory_abi = await load_abi('sync_swap_classic_pool_data_abi')
        pool_contract = self.web3.eth.contract(address=Web3.to_checksum_address(pool_address), abi=sync_swap_factory_abi)
        min_amount_out = pool_contract.functions.getAmountOut(
            token_address,
            amount,
            self.address_wallet
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * slippage))

    async def swap(self) -> None:
        try:
            sync_swap_factory_abi = await load_abi('sync_swap_factory_abi')
            sync_swap_route_abi = await load_abi('sync_swap_router_abi')

            logger.info(f'START    | index = {self.index} | {self.address_wallet} | {self.from_token} --> {self.to_token}')

            to_token_address, from_token_address = RPC['SCROLL'][self.to_token], RPC['SCROLL'][self.from_token]

            classic_pool_factory = self.web3.eth.contract(address=Web3.to_checksum_address(RPC["SCROLL"]["sync_swap_factory"]), abi=sync_swap_factory_abi)
            pool_address = classic_pool_factory.functions.getPool(Web3.to_checksum_address(from_token_address),
                                                                  Web3.to_checksum_address(to_token_address)).call()

            value, token_contract = await create_amount(self.web3, from_token_address, self.amount_to_swap)

            balance = self.web3.eth.get_balance(self.address_wallet, 'latest')
            token_balance = token_contract.functions.balanceOf(self.address_wallet).call() if self.from_token.lower() != 'eth' else await full_conversion(balance=balance)
            decimals = token_contract.functions.decimals().call()
            value = token_balance if token_balance < value else value
            logger.info(f'START    | index = {self.index} | {self.address_wallet} | {self.from_token} --> {self.to_token} | {self.from_token} = {token_balance / 10 ** decimals} | Balance = {balance / 10 ** 18} ETH ')

            if pool_address == "0x0000000000000000000000000000000000000000":
                logger.error(f'There is no pool')
                return

            if token_balance == 0:
                logger.debug(f'NO {self.from_token}  | index = {self.index} | {self.address_wallet} | {self.from_token} --> {self.to_token} | {self.from_token} = {token_balance / 10 ** decimals} | Balance = {balance / 10 ** 18} ETH | sleep = 10 min')
                # await remove_no_token(from_token=self.from_token, public_key=self.address_wallet)
                return
                # await asyncio.sleep(60 * 10)
                # token_balance = token_contract.functions.balanceOf(self.address_wallet).call()

            min_amount_out = await self.get_min_amount_out(pool_address, from_token_address, value, slippage)

            swap_data = encode(
                ["address", "address", "uint8"],
                [Web3.to_checksum_address(from_token_address), self.address_wallet, 1]
            )
            native_eth_address = "0x0000000000000000000000000000000000000000"

            steps = [{
                "pool": pool_address,
                "data": swap_data,
                "callback": native_eth_address,
                "callbackData": '0x'
            }]

            tokenIn = Web3.to_checksum_address(from_token_address) if self.from_token.lower() != 'eth' else Web3.to_checksum_address(native_eth_address)

            paths = [{
                "steps": steps,
                "tokenIn": tokenIn,
                "amountIn": value,
            }]

            router = self.web3.eth.contract(address=Web3.to_checksum_address(RPC["SCROLL"]["sync_swap_router"]),
                                            abi=sync_swap_route_abi)

            deadline = int(time.time()) + 1000000
            if self.from_token.lower() != 'eth':
                await approve_token(amount=value,
                                    private_key=self.private_key,
                                    from_token_address=from_token_address,
                                    spender=RPC["SCROLL"]["sync_swap_router"],
                                    address_wallet=self.address_wallet,
                                    from_token=self.from_token,
                                    to_token=self.to_token,
                                    web3=self.web3,
                                    index=self.index)

            tx_type = await tx_type_eip_legacy(web3=self.web3, address_wallet=self.address_wallet)
            tx = router.functions.swap(paths,
                                       min_amount_out,
                                       deadline).build_transaction(tx_type)
            if self.from_token.lower() == 'eth':
                tx.update({'value': value})

            gasLimit = int(self.web3.eth.estimate_gas(tx) * 1.2)
            tx.update({'gas': gasLimit})
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            raw_tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            balance = self.web3.eth.get_balance(self.address_wallet, 'latest')
            status = await check_status_tx(self.web3, raw_tx_hash)

            if status == 1:
                logger.success(f'FINISH   | index = {self.index} | {self.address_wallet} | {self.from_token} --> {self.to_token} | Transaction: {RPC["SCROLL"]["tokenScan"]}/tx/{raw_tx_hash.hex()} | Balance = {balance / 10 ** 18} ETH | SLEEP = {round(self.minuts, 2)} min')
                await update_swap(public_key=self.address_wallet, amount=value / 10 ** decimals,
                                  balance=balance, from_token=self.from_token, to_token=self.to_token, Swap="sync_swap")
                await asyncio.sleep(self.minuts * 60)

            elif status == 0:
                logger.error(f'FINISH   | index = {self.index} | {self.address_wallet} | {self.from_token} --> {self.to_token} | Transaction: {RPC["SCROLL"]["tokenScan"]}/tx/{raw_tx_hash.hex()} | Balance = {balance / 10 ** 18} ETH | SLEEP = {round(self.minuts, 2)} min')
                
        except Exception as ex:
            logger.error(f'ERROR    | index = {self.index} | {self.address_wallet} | {self.from_token} --> {self.to_token} | {ex}')
            await asyncio.sleep(5 * 60)


async def new():
    from_token = 'DAI'
    to_token = 'ETH'
    amount_from = 1000
    wallets = await current_wallet(public_key="")
    new_class = SyncSwap(
        private_key=wallets['private_key'],
        from_token=from_token,
        to_token=to_token,
        amount=amount_from,
        index=0
    )
    await new_class.swap()

if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        logger.info(f'START')
        asyncio.run(new())
    except KeyboardInterrupt:
        pass

