import asyncio
import random

from loguru import logger
from web3.contract import Contract

from l2_telegraph.const import CHAINS_FOR_BRIDGE
from l2_telegraph.utils import Config, init_logger, load_config
from l2_telegraph.web3 import (L2Telegraph, get_web3, load_cross_nft_contract,
                               load_messages_contract)


async def worker(
    q: asyncio.Queue,
    config: Config,
    msg_contract: Contract,
    cross_nft_contract: Contract,
    is_bridge: bool
) -> None:
    while not q.empty():
        private_key, message, dest_chain_id = await q.get()

        try:
            telegraph = L2Telegraph(get_web3(config.zksync_rpc), private_key, msg_contract)

            logger.info(f"[{telegraph.account.address}] Trying to send {message=}.")

            tx_hash = await telegraph.send_telegraph_message(message, dest_chain_id)

            logger.success(f"[{telegraph.account.address}] Sent {message=} with tx hash {tx_hash}")

            if is_bridge and random.randint(0, 1) == 1:
                telegraph.contract = cross_nft_contract

                nft_id = await telegraph.mint()

                logger.success(f"[{telegraph.account.address}] Minted NFT with id {nft_id}")

                tx_hash = await telegraph.bridge_nft(102989, chain_id := random.choice(CHAINS_FOR_BRIDGE))

                logger.success(f"[{telegraph.account.address}] Bridged NFT with id {102989} to chain {chain_id} with tx hash {tx_hash.hex()}")

        except Exception as e:
            logger.error(f"[{telegraph.account.address}] Failed with error: {e}")


async def main():
    init_logger()

    config = load_config("settings.yaml")

    msg_contract = load_messages_contract()
    nft_contract = load_cross_nft_contract()

    with open("accounts.txt", "r") as f:
        accounts = f.read().splitlines()

    logger.info(f"Loaded {config=}, contracts and {len(accounts)=}")

    is_bridge = input("Is this a mint and bridge with a 50% chance? (y/n): ").lower() == "y"

    q = asyncio.Queue()
    for account in accounts:
        q.put_nowait(account.split(":", maxsplit=3))

    workers = [
        asyncio.create_task(worker(q, config, msg_contract, nft_contract, is_bridge))
        for _ in range(5)
    ]

    await asyncio.gather(*workers)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Exiting...")
