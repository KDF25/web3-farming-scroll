import asyncio
import random
from sys import stderr

from eth_typing import Address
from loguru import logger
from web3 import Web3
from web3.contract import Contract

from abi import load_abi
from config import *
from data.data import RPC

logger.remove()
custom_name = "Utils"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<20}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


async def tx_type_eip_1559(web3: Web3, address_wallet: Address):
    return {
        "chainId": web3.eth.chain_id,
        'nonce': web3.eth.get_transaction_count(address_wallet),
        'from': address_wallet,
        'maxFeePerGas': web3.eth.gas_price,
        'maxPriorityFeePerGas': web3.eth.gas_price,
        'gas': 0,
        'value': 0,
    }


async def tx_type_eip_legacy(web3: Web3, address_wallet: Address):
    return {
        "chainId": web3.eth.chain_id,
        'nonce': web3.eth.get_transaction_count(address_wallet),
        'from': address_wallet,
        'gasPrice': web3.eth.gas_price,
        'gas': 0,
        'value': 0,
    }


async def check_status_tx(web3: Web3, tx_hash):
    while True:
        try:
            await asyncio.sleep(10)
            status_ = web3.eth.get_transaction_receipt(tx_hash)
            status = status_["status"]
            if status in [0, 1]:
                return status

        except Exception as ex:
            await asyncio.sleep(15)


async def load_contract(address, web3, abi_name) -> Contract | None:
    if address is None:
        return

    address = web3.to_checksum_address(address)
    return web3.eth.contract(address=address, abi=await load_abi(abi_name))


async def full_conversion(balance: int):
    usd_remainder = 5   # gas price for 2 transction
    current_eth_prise = 3300  # current eth price
    if FULL_CONVERSION:
        amount = balance - (usd_remainder/current_eth_prise) * 10 ** 18
    else:
        remainder = random.randint(REMAINDER[0], REMAINDER[1])
        amount = balance - (remainder / current_eth_prise) * 10 ** 18
    return int(amount)


async def create_amount(web3: Web3, token_contract, amount: float) -> tuple[int, Contract | None]:
    token_contract = RPC['SCROLL']["ETH"] if token_contract == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE" else token_contract
    token_contract = RPC['SCROLL']["ETH"] if token_contract == "0x0000000000000000000000000000000000000000" else token_contract
    stable_contract = await load_contract(token_contract, web3, 'erc20')
    amount = int(amount * 10 ** stable_contract.functions.decimals().call())
    return amount, stable_contract


async def approve_token(amount: float, private_key: str, from_token: str, to_token: str,
                        from_token_address: str, spender: str,
                        address_wallet: Address, web3: Web3, index: int = 0):
    try:
        spender = web3.to_checksum_address(spender)
        contract = await get_contract(web3, from_token_address)
        allowance_amount = await check_allowance(web3, from_token_address, address_wallet, spender)

        if amount > allowance_amount:
            tx_type = await tx_type_eip_legacy(web3=web3, address_wallet=address_wallet)
            tx = contract.functions.approve(
                                        spender,
                                        2**128
                                        ).build_transaction(tx_type)

            tx['chainId'] = web3.eth.chain_id
            gas_limit = await add_gas_limit(web3, tx)
            tx['gas'] = gas_limit
            signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)
            raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            await asyncio.sleep(1 * 60)
            logger.info(f'APPROVED | index = {index} | {address_wallet} | {from_token} --> {to_token} | APPROVED   : {RPC["SCROLL"]["tokenScan"]}/tx/{raw_tx_hash.hex()}')

    except Exception:
        pass


async def check_allowance(web3: Web3, from_token_address: str, address_wallet: Address, spender: str) -> float:
    contract = web3.eth.contract(address=web3.to_checksum_address(from_token_address),
                                 abi=await load_abi('erc20'))
    amount_approved = contract.functions.allowance(address_wallet, spender).call()
    return amount_approved


async def add_gas_limit(web3: Web3, tx: dict) -> int:
    tx['value'] = 0
    gas_limit = web3.eth.estimate_gas(tx)
    return gas_limit


async def get_contract(web3: Web3, from_token_address: str) -> Contract:
    return web3.eth.contract(address=web3.to_checksum_address(from_token_address),
                             abi=await load_abi('erc20'))





def all_dex(modules: dict):
    ALL_DEX = {}
    if modules['sync_swap']:
        ALL_DEX.update({"sync_swap": 1})
    if modules['zebra_swap']:
        ALL_DEX.update({"zebra_swap": 2})
    return ALL_DEX


