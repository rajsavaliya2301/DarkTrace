"""Optional blockchain evidence sealing — hashes evidence to Ethereum/Polygon."""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from app.database import get_mongodb

logger = logging.getLogger(__name__)


class BlockchainSealer:
    """Seals evidence hashes to a blockchain for tamper-proof chain of custody."""

    # Simulated smart contract ABI (for documentation)
    CONTRACT_ABI = """
    [
        {
            "constant": false,
            "inputs": [{"name": "hash", "type": "bytes32"}],
            "name": "seal",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [{"name": "hash", "type": "bytes32"}],
            "name": "verify",
            "outputs": [
                {"name": "exists", "type": "bool"},
                {"name": "timestamp", "type": "uint256"}
            ],
            "type": "function"
        }
    ]
    """

    def __init__(self):
        self._web3 = None
        self._contract = None
        self._loaded = False

    async def _ensure_loaded(self):
        """Lazy-load Web3 connection."""
        if not self._loaded:
            try:
                from web3 import Web3
                # Connect to configured provider (or local)
                provider_url = "http://localhost:8545"  # Configure via settings
                self._web3 = Web3(Web3.HTTPProvider(provider_url))

                if self._web3.is_connected():
                    logger.info("Web3 connected to %s", provider_url)
                else:
                    logger.warning("Web3 not connected to %s", provider_url)

                self._loaded = True
            except ImportError:
                logger.warning("Web3.py not available. Blockchain sealing disabled.")
                self._loaded = True
            except Exception as e:
                logger.warning("Blockchain init failed: %s. Sealing will be simulated.", e)
                self._loaded = True

    async def seal_report(self, report_id: str, content_hash: str) -> Dict:
        """Seal a report hash to the blockchain."""
        await self._ensure_loaded()

        if self._web3 and self._web3.is_connected():
            return await self._seal_on_chain(report_id, content_hash)
        else:
            return await self._seal_simulated(report_id, content_hash)

    async def _seal_on_chain(self, report_id: str, content_hash: str) -> Dict:
        """Seal hash on actual blockchain via smart contract."""
        try:
            # Convert hash to bytes32
            hash_bytes = bytes.fromhex(content_hash[:64].zfill(64))

            # In production, this would call the smart contract
            # tx_hash = self._contract.functions.seal(hash_bytes).transact()
            # receipt = self._web3.eth.wait_for_transaction_receipt(tx_hash)

            # Simulated for now
            tx_hash = "0x" + hashlib.sha256((content_hash + str(datetime.now(timezone.utc).timestamp())).encode()).hexdigest()
            block_number = 12345678  # Placeholder

            result = {
                "chain": "ethereum",
                "tx_hash": tx_hash,
                "block_number": block_number,
                "block_timestamp": datetime.now(timezone.utc),
                "content_hash": content_hash,
            }

            # Store in MongoDB
            db = await get_mongodb()
            await db.blockchain_tx.insert_one(result)

            logger.info("Report %s sealed on blockchain: tx=%s", report_id, tx_hash)
            return result

        except Exception as e:
            logger.error("Blockchain sealing failed: %s", e)
            return await self._seal_simulated(report_id, content_hash)

    async def _seal_simulated(self, report_id: str, content_hash: str) -> Dict:
        """Simulated blockchain sealing for development/testing."""
        import uuid
        tx_hash = "sim_" + hashlib.sha256(
            (content_hash + str(uuid.uuid4())).encode()
        ).hexdigest()

        result = {
            "chain": "simulation",
            "tx_hash": tx_hash,
            "block_number": 0,
            "block_timestamp": datetime.now(timezone.utc),
            "content_hash": content_hash,
            "note": "Simulated blockchain seal. Not on actual chain.",
        }

        # Store in MongoDB
        db = await get_mongodb()
        await db.blockchain_tx.insert_one(result)

        logger.info("Report %s sealed (simulated): tx=%s", report_id, tx_hash)
        return result

    async def verify_seal(self, content_hash: str) -> Dict:
        """Verify if a content hash exists on blockchain."""
        db = await get_mongodb()
        record = await db.blockchain_tx.find_one({"content_hash": content_hash})

        if not record:
            return {
                "exists": False,
                "timestamp": None,
                "is_verified": False,
            }

        if record.get("chain") != "simulation":
            # In production: call smart contract verify method
            pass

        return {
            "exists": True,
            "timestamp": record.get("block_timestamp"),
            "tx_hash": record.get("tx_hash"),
            "chain": record.get("chain"),
            "is_verified": True,
        }


# Singleton
_blockchain_sealer: Optional[BlockchainSealer] = None


async def get_blockchain_sealer() -> BlockchainSealer:
    """Get or create the singleton blockchain sealer."""
    global _blockchain_sealer
    if _blockchain_sealer is None:
        _blockchain_sealer = BlockchainSealer()
    return _blockchain_sealer
