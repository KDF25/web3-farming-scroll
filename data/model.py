from typing import TypedDict


class ChainModel(TypedDict, total=False):
    chainId: str
    router: str
    sushi_router: str
    mute_router: str
    space_router: str
    sync_swap_factory: str
    sync_swap_router: str
    zebra_swap_router: str
    woofi_router: str
    pancake_router: str
    velocore_router: str
    zkswap_router: str
    ezkalibur_router: str
    xyswap_router: str
    openocean_router: str
    maverick_router: str
    vesync_router: str
    izumi_router: str
    l2telegraph_message: str
    l2telegraph_mint_nft: str
    omnisea_router: str
    omnisea_router2: str
    odos_router: str
    dmail_router: str
    tavaera_router: str
    tavaera_id_router: str
    zerolend: str
    zerolend_weth: str
    aevo_landing: str
    eralend_collateral: str
    USDC: str
    USDT: str
    USD_plus: str
    LUSD: str
    ZkUSD: str
    TiUSD: str
    slUSDT: str
    crvUSD: str
    BUSD: str
    WBTC: str
    DAI: str
    ZKDOGE: str
    WISP: str
    ZKLOTTO: str
    ZKPAD: str
    ZKFLOKI: str
    ZKSHIB: str
    ZKCULT: str
    BOLT: str
    PANDA: str
    AVAX: str
    BNB: str
    MATIC: str
    CHEEMS: str
    SPACE: str
    MAV: str
    ETH: str
    frETH: str
    MUTE: str
    agEUR: str
    rpcUrl: str
    tokenScan: str
    nativeToken: str
    endpoint: str


class RPCModel(TypedDict, total=False):
    ETHERIUM: ChainModel
    OPTIMISM: ChainModel
    ARBITRUM: ChainModel
    ZKSYNC: ChainModel
    BASE: ChainModel
    LINEA: ChainModel
    SCROLL: ChainModel


