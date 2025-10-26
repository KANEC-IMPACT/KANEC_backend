# api/v1/services/hedera.py
import asyncio
from typing import Optional
from hiero_sdk_python import Client, AccountId, PrivateKey, Hbar, AccountCreateTransaction, AccountInfoQuery, Network, TransferTransaction, TransactionGetReceiptQuery
from api.utils.settings import settings
from api.v1.models.project import Project
from api.v1.models.donation import Donation
from sqlalchemy.orm import Session
import requests
from uuid import UUID
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def get_hedera_client() -> Client:
    """
    Get configured Hedera client for testnet or mainnet.
    """
    try:
        network = settings.HEDERA_NETWORK.lower()
        client = Client(Network(network='testnet' if network == 'testnet' else 'mainnet'))
        
        account_id = AccountId.from_string(settings.HEDERA_OPERATOR_ID)
        operator_key = PrivateKey.from_string(settings.HEDERA_OPERATOR_KEY)
        
        # Debug the actual key type
        pub_key = operator_key.public_key()
        logger.debug(f"Setting operator with ID: {account_id}")
        logger.debug(f"Operator key type: {type(pub_key)}")
        logger.debug(f"Operator public key: {pub_key}")
        
        client.set_operator(account_id, operator_key)
        return client
        
    except ValueError as e:
        logger.error(f"Invalid Hedera configuration: {str(e)}")
        raise ValueError(f"Invalid Hedera configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_hedera_client: {type(e).__name__}: {str(e)}")
        raise ValueError(f"Failed to initialize Hedera client: {type(e).__name__}: {str(e)}")
    

async def create_project_wallet(db: Session, project: Optional[Project] = None) -> str:
    """
    Create a new Hedera account for a project wallet.
    """
    client = await get_hedera_client()
    loop = asyncio.get_event_loop()

    def sync_create_account():
        try:
            # Generate ECDSA key
            new_key = PrivateKey.generate("ecdsa")
            logger.debug(f"Generating new ECDSA account with public key: {new_key.public_key()}")

            operator_key = PrivateKey.from_string(settings.HEDERA_OPERATOR_KEY)

            # Create account
            transaction = (
                AccountCreateTransaction()
                .set_key(new_key.public_key())
                .set_initial_balance(Hbar(1))
                .set_account_memo("Project donation wallet")
                .freeze_with(client)
                .sign(operator_key)
            )

            # Execute and get receipt
            receipt = transaction.execute(client)
            logger.debug(f"Transaction submitted: {receipt.transaction_id}")
            logger.debug(f"Transaction receipt status: {receipt.status}")

            # Check if account was created successfully
            if receipt.account_id is None:
                raise ValueError(f"Account creation failed. Status code: {receipt.status}")

            # Convert AccountId to string - use str() instead of to_string()
            account_id = str(receipt.account_id)
            logger.info(f"Successfully created Hedera account: {account_id}")
            return account_id

        except Exception as e:
            logger.error(f"Failed to create Hedera account: {type(e).__name__}: {str(e)}")
            raise

    try:
        account_id = await loop.run_in_executor(None, sync_create_account)
        if project:
            project.wallet_address = account_id
            db.commit()
        return account_id
    except Exception as e:
        logger.error(f"Failed to create Hedera wallet: {type(e).__name__}: {str(e)}")
        raise ValueError(f"Failed to create Hedera wallet: {type(e).__name__}: {str(e)}")
        

async def donate_hbar(donor_wallet: str, project_wallet: str, amount_hbar: float, donor_private_key: str) -> str:
    """
    Process an HBAR donation from donor to project wallet.
    """
    client = await get_hedera_client()
    loop = asyncio.get_event_loop()

    def sync_donate():
        try:
            donor_id = AccountId.from_string(donor_wallet)
            project_id = AccountId.from_string(project_wallet)
            donor_key = PrivateKey.from_string(donor_private_key)

            logger.debug(f"Processing donation: {amount_hbar} HBAR from {donor_wallet} to {project_wallet}")

            # Convert HBAR to tinybars (1 HBAR = 100,000,000 tinybars)
            amount_tinybars = int(amount_hbar * 100_000_000)
            
            # Create and execute transaction
            transaction = (
                TransferTransaction()
                .add_hbar_transfer(donor_id, -amount_tinybars)
                .add_hbar_transfer(project_id, amount_tinybars)
                .freeze_with(client)
                .sign(donor_key)
            )

            # Execute returns receipt directly
            receipt = transaction.execute(client)
            transaction_id = transaction.transaction_id
            
            logger.debug(f"Transaction ID: {transaction_id}")
            logger.debug(f"Transaction status: {receipt.status}")

            # Check if transaction was successful
            if receipt.status != 22:  # SUCCESS
                raise ValueError(f"Transaction failed with status: {receipt.status}")

            # Try different formats for mirror node
            tx_str = str(transaction_id)
            # Format 1: Replace @ with -
            tx_hash = tx_str.replace('@', '-')
            # Format 2: If that doesn't work, we'll try the original in verify_transaction
            
            logger.info(f"Donation transaction completed successfully: {tx_hash}")
            return tx_hash

        except Exception as e:
            logger.error(f"Failed to process donation: {type(e).__name__}: {str(e)}")
            raise

    tx_hash = await loop.run_in_executor(None, sync_donate)
    return tx_hash

async def verify_transaction(tx_hash: str) -> dict:
    """
    Verify a transaction using Hedera Mirror Node API.
    Try multiple transaction ID formats.
    """
    import httpx
    import asyncio
    
    network = settings.HEDERA_NETWORK.lower()
    mirror_node_url = f"https://{'testnet' if network == 'testnet' else 'mainnet'}.mirrornode.hedera.com"
    
    # Wait a bit for transaction to be indexed by mirror node
    await asyncio.sleep(5)
    
    # Try multiple transaction ID formats
    formats_to_try = [
        tx_hash,  # Original format with -
        tx_hash.replace('-', '@'),  # Replace - with @
        tx_hash.split('-')[0] + '@' + tx_hash.split('-')[1].split('.')[0] + '.' + tx_hash.split('-')[1].split('.')[1][:6],  # Limited precision
    ]
    
    max_retries = 3
    for tx_format in formats_to_try:
        for attempt in range(max_retries):
            try:
                url = f"{mirror_node_url}/api/v1/transactions/{tx_format}"
                logger.debug(f"Verifying transaction attempt {attempt + 1} with format: {tx_format}")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        result = response.json()
                        transactions = result.get("transactions", [])
                        if not transactions:
                            continue
                        
                        tx = transactions[0]
                        transfers = tx.get("transfers", [])
                        
                        # Find the transfer amounts
                        positive_transfers = [t for t in transfers if t.get("amount", 0) > 0]
                        negative_transfers = [t for t in transfers if t.get("amount", 0) < 0]
                        
                        return {
                            "valid": tx.get("result") == "SUCCESS",
                            "amount": sum(t.get("amount", 0) for t in positive_transfers) / 100_000_000,
                            "from_account": negative_transfers[0].get("account") if negative_transfers else None,
                            "to_account": positive_transfers[0].get("account") if positive_transfers else None,
                            "timestamp": tx.get("consensus_timestamp"),
                            "transaction_id": tx.get("transaction_id"),
                            "transfers": transfers
                        }
                    elif response.status_code == 404:
                        # Transaction not yet indexed, wait and retry
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            logger.debug(f"Transaction not indexed yet with format {tx_format}, waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                    else:
                        # Other HTTP error, try next format
                        break
                        
            except Exception as e:
                logger.debug(f"Failed with format {tx_format} attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
    
    # If all formats fail, check if we can get transaction info another way
    logger.warning(f"Could not verify transaction {tx_hash} with mirror node using any format")
    return {
        "valid": False,
        "amount": 0,
        "from_account": None,
        "to_account": None,
        "timestamp": None,
        "transaction_id": tx_hash,
        "error": "Transaction not found in mirror node after trying multiple formats"
    }

async def trace_transaction(tx_hash: str, db: Session) -> dict:
    """
    Trace a donation by transaction hash.
    
    Args:
        tx_hash: Hedera transaction ID
        db: SQLAlchemy session
    
    Returns:
        dict: Transaction details with linked donation/project
    """
    verification = await verify_transaction(tx_hash)
    donation = db.query(Donation).filter(Donation.tx_hash == tx_hash).first()
    
    result = {
        "transaction_id": tx_hash,
        "valid": verification["valid"],
        "amount": verification["amount"],
        "from_account": verification["from_account"],
        "to_account": verification["to_account"],
        "timestamp": verification["timestamp"]
    }
    
    if donation:
        result.update({
            "donation_id": donation.id,
            "project_id": donation.project_id,
            "donor_id": donation.donor_id,
            "status": donation.status.value
        })
    
    return result

async def update_raised_amount(db: Session, project_id: UUID, amount: float):
    """
    Update project's amount_raised.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.amount_raised += amount
        db.commit()