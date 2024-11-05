import json
import os


async def load_abi(name: str) -> str:
    abi_folder = os.path.join(os.path.dirname(__file__))
    abi = json.load(open(os.path.join(abi_folder, f'{name}.json')))
    return abi