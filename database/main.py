import asyncio
import json
import random
from typing import Literal

import psycopg2
from sqlalchemy import create_engine
import pandas as pd
from config import  *


async def main_database_create():
    pg_host_url = f'postgresql://{pg_user}:{pg_password}@{pg_host}:5432/{database}'
    engine = create_engine(pg_host_url)
    df = pd.read_excel('../wallet_generator/scroll_evm_wallets.xlsx')
    df = df.rename(columns={'Unnamed: 0': 'id'})
    df[['route', 'Tokens']] = '{}'
    df[["ETH"]] = 0
    df['comment'] = None
    df.to_sql('wallets', engine, index=False, if_exists="replace")


async def all_wallets_to_withdraw(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT * FROM public.wallets WHERE mainnet is null ORDER BY id LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df


async def all_wallets_to_bridge(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT * FROM public.wallets WHERE mainnet is not null and (comment != 'BRIDGED' or comment is null)
                         ORDER BY RANDOM() LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df

async def update_first_withdraw(public_key: str, currency: [float, int], Mainnet: Literal["ARBITRUM", "OPTIMISM"]):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set "ETH" = {currency}, mainnet = '{Mainnet}'  WHERE public_key = '{public_key}'"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def update_bridge(public_key: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set comment = 'BRIDGED'  WHERE public_key = '{public_key}'"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def current_wallet(public_key: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT * FROM public.wallets WHERE public_key = '{public_key}' """, con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df[0]


async def update_aevo(public_key: str, aevo: dict):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = """UPDATE public.wallets SET "aevo" = %s, "aevo_count" = "aevo_count" + 1 WHERE public_key = %s"""
    cursor = conn.cursor()
    aevo_json = json.dumps(aevo)
    cursor.execute(sql, (aevo_json, public_key))
    cursor.close()
    conn.close()


async def current_swaps(public_key: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""  SELECT  "sync_swap", "zebra_swap" FROM public.wallets WHERE public_key = '{public_key}' """, con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df[0]


async def all_wallets_to_swap(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT * FROM public.wallets  
                         WHERE id >= 0 and all_swaps < 10 and id < 300  
                         ORDER BY Random() LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df



async def update_send_dmail__message(public_key: str, message: str, mail: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set 
              dmail_count = dmail_count + 1 
              WHERE public_key = '{public_key}'"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def update_swap(public_key: str, from_token: str,  to_token: str, balance: [float, int], amount: [float, int],
                      Swap: Literal["sync_swap", "zebra_swap"] = "OtherSwap"):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    balance /= 10 ** 18

    sql = f"""  update public.wallets 
                set "ETH" = '{balance}', 
                "Tokens" = CASE
                WHEN '{from_token}' = 'ETH' THEN ARRAY_APPEND("Tokens", '{to_token}')
                WHEN '{to_token}' = 'USDC' AND 'USDC' <> ALL ("Tokens") THEN ARRAY_APPEND(ARRAY_REMOVE("Tokens", '{from_token}'), '{to_token}')
                ELSE ARRAY_REMOVE("Tokens", '{from_token}')
                 END,
                route = ARRAY_APPEND(route, '{from_token}-->{to_token}|{Swap}|{amount}'), 
                "{Swap}" = "{Swap}" + 1,  
                all_swaps = all_swaps + 1  
                WHERE public_key = '{public_key}'"""

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def all_wallets_to_action(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT * FROM public.wallets  
                         WHERE "ETH" != 0 and id >= 0 and id < 300
                         ORDER BY RANDOM() LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df


async def update_zkstars(public_key: str, contract: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set 
              zkstars_count = zkstars_count + 1, 
              zkstar_contracts = ARRAY_APPEND(zkstar_contracts, '{contract}') 
              WHERE public_key = '{public_key}'"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.get_event_loop().run_until_complete(main_database_create())
