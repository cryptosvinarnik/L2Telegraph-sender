import asyncio

from eth_abi import encode_abi
from eth_account import Account
from loguru import logger
from web3 import Web3
from web3.contract import Contract
from web3.eth import AsyncEth
from web3.exceptions import ContractLogicError
from web3.types import HexBytes, TxParams

from l2_telegraph.const import (ADDRESSES_FOR_BRIDGE, BRIDGE_NFT_FEES,
                                L2TELEGRAPH_ABI, L2TelegraphContract)


def load_messages_contract() -> Contract:
    return Web3().eth.contract(
        address=L2TelegraphContract.MESSAGES,
        abi=L2TELEGRAPH_ABI
    )


def load_cross_nft_contract() -> Contract:
    return Web3().eth.contract(
        address=L2TelegraphContract.CROSS_NFT,
        abi=L2TELEGRAPH_ABI
    )


def get_web3(rpc_url: str) -> Web3:
    return Web3(
        Web3.AsyncHTTPProvider(
            rpc_url,
        ),
        middlewares=[],
        modules={"eth": (AsyncEth,)}
    )


class Web3Wrapper:
    def __init__(self, web3: Web3, private_key: str) -> None:
        self.web3 = web3
        self.account = Account.from_key(private_key)

    async def estimate_and_send_transaction(
        self,
        tx_params: TxParams,
        gas_buffer: int = 1.05
    ) -> HexBytes:
        """Estimate gas, add a buffer, and send a transaction"""

        for _ in range(3):
            try:
                estimated_gas = await self.web3.eth.estimate_gas(tx_params)
                break
            except ContractLogicError as e:
                # If the estimate fails, try again for up to 3 times
                logger.error(f"Failed to estimate gas for {tx_params=} with error: {e}")
                continue
        else:
            # If the estimate fails for 3 times, raise the error
            raise ContractLogicError("Failed to estimate gas for transaction")

        if (
            ("gas" not in tx_params) or
            (tx_params["gas"] is None) or
            (tx_params["gas"] < estimated_gas)
        ):
            tx_params["gas"] = tx_params["gas"] = int(estimated_gas * gas_buffer)

        signed_tx = self.account.sign_transaction(tx_params)

        return await self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    @property
    async def eip_1559_gas(self) -> dict:
        gas_price = await self.web3.eth.gas_price

        maxPriorityFeePerGas = gas_price
        maxFeePerGas = maxPriorityFeePerGas

        return {
            "maxPriorityFeePerGas": maxPriorityFeePerGas,
            "maxFeePerGas": maxFeePerGas
        }


class L2Telegraph(Web3Wrapper):
    def __init__(self, web3: Web3, private_key: str, telegraph_contract: Contract) -> None:
        super().__init__(web3, private_key)

        self.contract = telegraph_contract

    def get_send_message_data(self, message: str, dest_chain_id: int) -> str:
        """Get the data for a sendMessage transaction"""

        return self.contract.encodeABI(
            fn_name="sendMessage",
            args=[message, dest_chain_id]
        )
    
    async def send_telegraph_message(
        self,
        message: str,
        dest_chain_id: int,
    ) -> HexBytes:
        return await self.estimate_and_send_transaction({
            "from": self.account.address,
            "chainId": await self.web3.eth.chain_id,
            "to": self.contract.address,
            "data": self.get_send_message_data(message, dest_chain_id),
            "nonce": await self.web3.eth.get_transaction_count(self.account.address, "pending"),
            # 0.0007 ETH ETH fee
            "value": 700000000000000,
            **(await self.eip_1559_gas)
        })
    
    def get_trusted_remote(self, address: str) -> str:
        addresses = [address, "0xD43A183C97dB9174962607A8b6552CE320eAc5aA"]

        trusted_remote = encode_abi(
            ["address", "address"],
            [address for address in addresses]
        ).hex().replace("0" * 24, "")

        return trusted_remote

    async def mint(self) -> int:
        """
        Mint test NFT
        
        :return: NFT id
        """

        tx_hash = await self.estimate_and_send_transaction({
            "from": self.account.address,
            "chainId": await self.web3.eth.chain_id,
            "to": self.contract.address,
            "data": "0x1249c58b",
            "nonce": await self.web3.eth.get_transaction_count(self.account.address, "pending"),
            # 0.0005 ETH ETH fee
            "value": 500000000000000,
            **(await self.eip_1559_gas)
        })

        while True:
            receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt["logs"]:
                break

            await asyncio.sleep(2)
        
        nft_minted_log = receipt["logs"][2]

        nft_id = int(nft_minted_log["topics"][-1].hex(), 16)

        return nft_id
    
    async def bridge_nft(self, nft_id: int, dest_chain_id: int) -> HexBytes:
        birdge_data = self.contract.functions.crossChain(
            _dstChainId=dest_chain_id,
            _destination=self.get_trusted_remote(ADDRESSES_FOR_BRIDGE[dest_chain_id]),
            tokenId=nft_id
        )._encode_transaction_data()

        return await self.estimate_and_send_transaction({
            "from": self.account.address,
            "chainId": await self.web3.eth.chain_id,
            "to": self.contract.address,
            "data": birdge_data,
            "nonce": await self.web3.eth.get_transaction_count(self.account.address, "pending"),
            "value": BRIDGE_NFT_FEES[dest_chain_id],
            **(await self.eip_1559_gas)
        })
