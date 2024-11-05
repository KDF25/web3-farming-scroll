import asyncio
import base64
import datetime
import hmac
import random
import warnings
from sys import stderr

import requests
from loguru import logger

from config import OKX_KEYS
from database.main import update_first_withdraw

RETRY = 0
logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | " "<white>{message}</white>")



async def signature(timestamp: str, method: str, request_path: str, secret_key: str, body: str = "") -> str:
    if not body:
        body = ""

    message = timestamp + method.upper() + request_path + body
    mac = hmac.new(
        bytes(secret_key, encoding="utf-8"),
        bytes(message, encoding="utf-8"),
        digestmod="sha256",
    )
    d = mac.digest()
    return base64.b64encode(d).decode("utf-8")


async def okx_data(api_key, secret_key, passphras, request_path="/api/v5/account/balance?ccy=USDT", body='', meth="GET"):
    try:

        dt_now = datetime.datetime.utcnow()
        ms = str(dt_now.microsecond).zfill(6)[:3]
        timestamp = f"{dt_now:%Y-%m-%dT%H:%M:%S}.{ms}Z"

        base_url = "https://www.okex.com"
        headers = {
            "Content-Type": "application/json",
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-SIGN": await signature(timestamp, meth, request_path, secret_key, body),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": passphras,
            'x-simulated-trading': '0'
        }
        return base_url, request_path, headers
    except Exception as ex:
        logger.error(ex)


async def okx_withdraw(wallet: str, account: str, CHAIN: str, SYMBOL: str, AMOUNT: [int, float], FEE: float,
                       SUB_ACC: bool = True,  minuts: [int, float] = 0, index: int = 0):

    api_key = OKX_KEYS[account]['api_key']
    secret_key = OKX_KEYS[account]['api_secret']
    passphras = OKX_KEYS[account]['password']
    logger.info(f'OKX START       | index = {index} | {wallet} | {CHAIN} | {AMOUNT} {SYMBOL}')

    try:

        if SUB_ACC is True:

            list_sub = []
            try:

                _, _, headers = await okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/users/subaccount/list", meth="GET")
                list_sub = requests.get("https://www.okx.cab/api/v5/users/subaccount/list", timeout=10, headers=headers)
                list_sub = list_sub.json()

                for sub_data in list_sub['data']:
                    name_sub = sub_data['subAcct']

                    _, _, headers = await okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}", meth="GET")
                    sub_balance = requests.get(f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}", timeout=10, headers=headers)
                    sub_balance = sub_balance.json()
                    sub_balance = sub_balance['data'][0]['bal']

                    logger.info(f'{name_sub} | sub_balance : {sub_balance} {SYMBOL}')

                    body = {"ccy": f"{SYMBOL}", "amt": str(sub_balance), "from": 6, "to": 6, "type": "2", "subAcct": name_sub}
                    _, _, headers = await okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/transfer",
                                             body=str(body), meth="POST")
                    a = requests.post("https://www.okx.cab/api/v5/asset/transfer", data=str(body), timeout=10, headers=headers)
                    a = a.json()
                    await asyncio.sleep(1)

            except Exception as error:
                logger.error(f'ERROR1 | wallet = {wallet} | list_sub : {list_sub} | {error}')
                return "error"

        try:
            _, _, headers = await okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/account/balance?ccy={SYMBOL}")
            balance = requests.get(f'https://www.okx.cab/api/v5/account/balance?ccy={SYMBOL}', timeout=10, headers=headers)
            balance = balance.json()
            balance = balance["data"][0]["details"][0]["cashBal"]

            if balance != 0:
                body = {"ccy": f"{SYMBOL}", "amt": float(balance), "from": 18, "to": 6, "type": "0", "subAcct": "",
                        "clientId": "", "loanTrans": "", "omitPosRisk": ""}
                _, _, headers = await okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/transfer", body=str(body), meth="POST")
                a = requests.post("https://www.okx.cab/api/v5/asset/transfer", data=str(body), timeout=10, headers=headers)
        except Exception:
            pass

        body = {"ccy": SYMBOL, "amt": AMOUNT, "fee": FEE, "dest": "4", "chain": f"{SYMBOL}-{CHAIN}", "toAddr": wallet}
        _, _, headers = await okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/withdrawal", meth="POST", body=str(body))
        a = requests.post("https://www.okx.cab/api/v5/asset/withdrawal", data=str(body), timeout=10, headers=headers)
        result = a.json()

        if result['code'] == '0':
            logger.success(f'OKX FINISH      | index = {index} | {wallet} | {CHAIN} | {AMOUNT} {SYMBOL}')
            await asyncio.sleep(int(minuts * 60))
            return "success"

        else:
            error = result['msg']
            logger.error(f'OKX ERROR3       | index = {index} | {wallet} | {CHAIN} | {AMOUNT} {SYMBOL} | {error}')
            return "error"

    except Exception as error:
        logger.error(f'OKX ERROR4       | index = {index} | {wallet} | {CHAIN} | {AMOUNT} {SYMBOL} | {error}')
        return "error"


async def okx_to_main(account: str, SYMBOL: str):

    api_key = OKX_KEYS[account]['api_key']
    secret_key = OKX_KEYS[account]['api_secret']
    passphras = OKX_KEYS[account]['password']
    logger.info(f'OKX to main START')

    try:
        _, _, headers = await okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/users/subaccount/list", meth="GET")
        list_sub = requests.get("https://www.okx.cab/api/v5/users/subaccount/list", timeout=10, headers=headers)
        list_sub = list_sub.json()

        for sub_data in list_sub['data']:
            name_sub = sub_data['subAcct']

            _, _, headers = await okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}", meth="GET")
            sub_balance = requests.get(f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}", timeout=10, headers=headers)
            sub_balance = sub_balance.json()
            sub_balance = sub_balance['data'][0]['bal']

            logger.info(f'{name_sub} | sub_balance : {sub_balance} {SYMBOL}')

            body = {"ccy": f"{SYMBOL}", "amt": str(sub_balance), "from": 6, "to": 6, "type": "2", "subAcct": name_sub}
            _, _, headers = await okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/transfer",
                                     body=str(body), meth="POST")
            a = requests.post("https://www.okx.cab/api/v5/asset/transfer", data=str(body), timeout=10, headers=headers)
            await asyncio.sleep(1)
        logger.success(f'OKX to main FINISH')

    except Exception as error:
        logger.error(f'OKX to main      | {error}')

async def scroll_withdraw():
    NETS = [
        {"name": "Optimism", "fee": 0.0001},
        {"name": "Arbitrum One", "fee": 0.0001},
        {"name": "Base", "fee": 0.0002},
        {"name": "Base", "fee": 0.0002},
        {"name": "Linea", "fee": 0.0002},
        {"name": "Linea", "fee": 0.0002},
    ]

    wallets = []

    random.shuffle(wallets)
    random.shuffle(wallets)

    all_len = len(wallets)
    for index, wallet in enumerate(wallets):
        CHAIN = random.choice(NETS)
        AMOUNT = round(random.uniform(0.031, 0.035), 6)
        # AMOUNT = round(random.uniform(0.002, 0.003), 6)
        status = await okx_withdraw(wallet=wallet, account="Account_1", CHAIN=CHAIN["name"], SYMBOL="ETH",
                                    AMOUNT=AMOUNT, FEE=CHAIN["fee"], SUB_ACC=False, index=index + 1)
        if status == "success":
            await update_first_withdraw(public_key=wallet, currency=AMOUNT, Mainnet=CHAIN["name"])
        minuts = random.randint(10, 17)
        logger.success(f'index = {index + 1} | {all_len} | sleep = {minuts} min')
        await asyncio.sleep(60 * minuts)


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        asyncio.run(scroll_withdraw())
    except KeyboardInterrupt:
        pass