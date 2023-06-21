L2TELEGRAPH_ABI = [
  {
    "name": "sendMessage",
    "inputs": [
      {
        "name": "message",
        "type": "string"
      },
      {
        "name": "destChainId",
        "type": "uint16"
      }
    ],
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "name": "crossChain",
    "inputs": [
      {
        "name": "_dstChainId",
        "type": "uint16"
      },
      {
        "name": "_destination",
        "type": "bytes"
      },
      {
        "name": "tokenId",
        "type": "uint256"
      }
    ],
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  }
]


class L2TelegraphContract:
    """Store checksummed contract addresses for known networks"""

    MESSAGES = "0xEb762C289c1A3BdF2375679c1c69b745F9CDc17f"
    CROSS_NFT = "0xD43A183C97dB9174962607A8b6552CE320eAc5aA"


class ChainId:
    """Store L0 (!!) chain ids for known networks"""

    ARBTRUM = 110
    ARBITRUM_NOVA = 175
    BSC = 102
    POLYGON_ZKEVM = 158


CHAINS_FOR_BRIDGE = [ChainId.ARBITRUM_NOVA, ChainId.BSC, ChainId.POLYGON_ZKEVM]

class TrustedRemoteAddress:
    BNB = "0x241704d8f874b1f0D7a7dE577BA10fAF004dc0ba"
    ARBITRUM_NOVA = "0x5B10aE182C297ec76fE6fe0E3Da7c4797ceDE02D"
    POLYGON_ZKEVM = "0xDC60fd9d2A4ccF97f292969580874De69E6c326E"


ADDRESSES_FOR_BRIDGE = {
    ChainId.BSC: TrustedRemoteAddress.BNB,
    ChainId.ARBITRUM_NOVA: TrustedRemoteAddress.ARBITRUM_NOVA,
    ChainId.POLYGON_ZKEVM: TrustedRemoteAddress.POLYGON_ZKEVM,
}

BRIDGE_NFT_FEES = {
    ChainId.BSC: 700000000000000,
    ChainId.ARBITRUM_NOVA: 100000000000000,
    ChainId.POLYGON_ZKEVM: 1300000000000000,
}
