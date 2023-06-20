from eth_account import Account
from loguru import logger
from web3 import Web3
from web3.contract import Contract
from web3.eth import AsyncEth
from web3.exceptions import ContractLogicError
from web3.types import TxParams

from l2_telegraph.const import L2TELEGRAPH_ABI, L2TelegraphContract


def load_telegraph_contract() -> Contract:
    return Web3().eth.contract(
        address=L2TelegraphContract.ZK_SYNC,
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
    ) -> str:
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

        return (await self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)).hex()


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
    ) -> None:
        gas_price = await self.web3.eth.gas_price

        maxPriorityFeePerGas = gas_price
        maxFeePerGas = maxPriorityFeePerGas

        return await self.estimate_and_send_transaction({
            "from": self.account.address,
            "chainId": await self.web3.eth.chain_id,
            "to": self.contract.address,
            "data": self.get_send_message_data(message, dest_chain_id),
            "maxPriorityFeePerGas": maxPriorityFeePerGas,
            "maxFeePerGas": maxFeePerGas,
            "nonce": await self.web3.eth.get_transaction_count(self.account.address, "pending"),
            # 0.0007 ETH ETH fee
            "value": 700000000000000
        })
