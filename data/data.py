from .model import RPCModel

SYNC_SWAP_TOKENS = [
    'USDC', 'USDT', "DAI", "WBTC"
]

ZEBRA_SWAP_TOKENS = [
    'USDC', 'USDT', "DAI"
]

zkstar_contracts = [
        "0x609c2f307940b8f52190b6d3d3a41c762136884e",
        "0x16c0baa8a2aa77fab8d0aece9b6947ee1b74b943",
        "0xc5471e35533e887f59df7a31f7c162eb98f367f7",
        "0xf861f5927c87bc7c4781817b08151d638de41036",
        "0x954e8ac11c369ef69636239803a36146bf85e61b",
        "0xa576ac0a158ebdcc0445e3465adf50e93dd2cad8",
        "0x17863384c663c5f95e4e52d3601f2ff1919ac1aa",
        "0x4c2656a6d1c0ecac86f5024e60d4f04dbb3d1623",
        "0x4e86532cedf07c7946e238bd32ba141b4ed10c12",
        "0x6b9db0ffcb840c3d9119b4ff00f0795602c96086",
        "0x10d4749bee6a1576ae5e11227bc7f5031ad351e4",
        "0x373148e566e4c4c14f4ed8334aba3a0da645097a",
        "0xdacbac1c25d63b4b2b8bfdbf21c383e3ccff2281",
        "0x2394b22b3925342f3216360b7b8f43402e6a150b",
        "0xf34f431e3fc0ad0d2beb914637b39f1ecf46c1ee",
        "0x6f1e292302dce99e2a4681be4370d349850ac7c2",
        "0xa21fac8b389f1f3717957a6bb7d5ae658122fc82",
        "0x1b499d45e0cc5e5198b8a440f2d949f70e207a5d",
        "0xec9bef17876d67de1f2ec69f9a0e94de647fcc93",
        "0x5e6c493da06221fed0259a49beac09ef750c3de1"
    ]

RPC: RPCModel = {
                    'ARBITRUM': {
                        # 'rpcUrl': 'https://rpc.ankr.com/arbitrum',
                        # 'rpcUrl': 'https://endpoints.omniatech.io/v1/arbitrum/one/public',
                        'rpcUrl': 'https://rpc.ankr.com/arbitrum',
                        # 'tokenScan': 'https://arbiscan.io',
                        'tokenScan': 'https://arbitrum.llamarpc.com',
                    },

                    'OPTIMISM': {
                        'USDC': '0x7f5c764cbc14f9669b88837ca1490cca17c31607',
                        # 'rpcUrl': 'https://endpoints.omniatech.io/v1/op/mainnet/public',
                        # 'rpcUrl': 'https://1rpc.io/op',
                        'rpcUrl': 'https://optimism-mainnet.public.blastapi.io',
                        'tokenScan': 'https://optimistic.etherscan.io',
                    },

                    'BASE': {
                        # 'rpcUrl': 'https://base.llamarpc.com',
                        'rpcUrl': 'https://base-pokt.nodies.app',
                        'tokenScan': 'https://basescan.org',
                    },

                    'LINEA': {
                        'rpcUrl': 'https://linea.decubate.com',
                        'tokenScan': 'https://lineascan.build',
                    },

                    'ZKSYNC': {
                        'rpcUrl': "https://mainnet.era.zksync.io",
                        # 'rpcUrl': "https://zksync.drpc.org",
                        # 'rpcUrl': 'https://rpc.ankr.com/zksync_era',
                        'tokenScan': 'https://explorer.zksync.io',
                    },

                    'SCROLL': {
                        'rpcUrl': 'https://rpc.ankr.com/scroll',
                        'tokenScan': 'https://scrollscan.com',

                        "ETH": "0x5300000000000000000000000000000000000004",
                        "USDC": "0x06eFdBFf2a14a7c8E15944D1F4A48F9F95F663A4",
                        "USDT": "0xf55BEC9cafDbE8730f096Aa55dad6D22d44099Df",
                        "WBTC": "0x3C1BCa5a656e69edCD0D4E36BEbb3FcDAcA60Cf1",
                        "DAI": "0xcA77eB3fEFe3725Dc33bccB54eDEFc3D9f764f97",

                        'dmail_router': '0x47fbe95e981c0df9737b6971b451fb15fdc989d9',
                        'sync_swap_factory': '0x37BAc764494c8db4e54BDE72f6965beA9fa0AC2d',
                        'sync_swap_router': '0x80e38291e06339d10aab483c65695d004dbd5c69',
                        "zebra_swap_router": "0x0122960d6e391478bfe8fb2408ba412d5600f621",
                        'aevo_landing': "0x11fCfe756c05AD438e312a7fd934381537D3cFfe"
                    },



}
