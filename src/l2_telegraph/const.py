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
  }
]


class L2TelegraphContract:
    """Store checksummed contract addresses for known networks"""

    ZK_SYNC = "0xEb762C289c1A3BdF2375679c1c69b745F9CDc17f"


class ChainId:
    """Store L0 (!!) chain ids for known networks"""

    ARBTRUM = 110
