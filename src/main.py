import asyncio

from loguru import logger
from web3.contract import Contract

from l2_telegraph.utils import Config, init_logger, load_config
from l2_telegraph.web3 import L2Telegraph, load_telegraph_contract, get_web3


async def worker(q: asyncio.Queue, config: Config, contract: Contract) -> None:
    while not q.empty():
        private_key, message, dest_chain_id = await q.get()

        try:
            telegraph = L2Telegraph(get_web3(config.zksync_rpc), private_key, contract)

            logger.info(f"[{telegraph.account.address}] Trying to send {message=}.")

            tx_hash = await telegraph.send_telegraph_message(message, int(dest_chain_id))

            logger.success(f"[{telegraph.account.address}] Sent {message=} with tx hash {tx_hash}")
        except Exception as e:
            logger.error(f"[{telegraph.account.address}] Failed to send {message=} with error: {e}")


async def main():
    init_logger()

    config = load_config("settings.yaml")

    contract = load_telegraph_contract()

    with open("accounts.txt", "r") as f:
        accounts = f.read().splitlines()

    logger.info(f"Loaded {config=}, {contract.address=} and {len(accounts)=}")
    input()
    q = asyncio.Queue()
    for account in accounts:
        q.put_nowait(account.split(":", maxsplit=3))

    workers = [asyncio.create_task(worker(q, config, contract)) for _ in range(5)]

    await asyncio.gather(*workers)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Exiting...")
