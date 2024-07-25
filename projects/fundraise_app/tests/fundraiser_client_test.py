import algokit_utils
import algosdk
import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import (
    AlgorandClient,
    PayParams,
)
from algosdk.atomic_transaction_composer import TransactionWithSigner


from smart_contracts.artifacts.fundraiser.fundraiser_app_client import (
    FundraiserAppClient,
)


@pytest.fixture(scope="session")
def algorand() -> AlgorandClient:
    """Fixture to provide an AlgorandClient instance."""
    return AlgorandClient.default_local_net()

@pytest.fixture(scope="session")
def dispenser(algorand: AlgorandClient) -> AddressAndSigner:
    """Fixture to provide a dispenser account."""
    return algorand.account.dispenser()

@pytest.fixture(scope="session")
def creator(algorand: AlgorandClient, dispenser: AddressAndSigner) -> AddressAndSigner:
    """Fixture to provide a random account funded by the dispenser."""
    acct = algorand.account.random()
    algorand.send.payment(
        PayParams(sender=dispenser.address, receiver=acct.address, amount=15_000_000)
    )
    return acct

@pytest.fixture(scope="session")
def fundraiser_client(algorand: AlgorandClient, creator: AddressAndSigner) -> FundraiserAppClient:
    """Fixture to instantiate a FundraiserAppClient for testing."""
    client = FundraiserAppClient(
        algod_client=algorand.client.algod,
        sender=creator.address,
        signer=creator.signer,
    )
    # Create an instance of the application on the network
    client.create_create_campaign(goal_amount=5_000_000)  # Setting the goal amount to 5 ALGO
    
    return client

def test_create_campaign(fundraiser_client: FundraiserAppClient):
    """Test function to verify campaign creation."""
    goal_amount = 5_000_000
    result = fundraiser_client.create_create_campaign(goal_amount=goal_amount)
    assert result.confirmed_round

    # Print information for verification
    print(f"Created campaign with goal amount: {goal_amount}")
    print(f"Transaction ID: {result.tx_id}")
    print(f"Confirmed round: {result.confirmed_round}")
    

def test_contribute(fundraiser_client: FundraiserAppClient, creator: AddressAndSigner, algorand: AlgorandClient):
    # Send a contribution to the fundraiser
    contribution_txn = algorand.transactions.payment(
        PayParams(
            sender=creator.address,
            receiver=fundraiser_client.app_address,
            amount=1_000_000,  # 1 ALGO contribution
        )
    )

    result = fundraiser_client.contribute(contribution=TransactionWithSigner(txn=contribution_txn, signer=creator.signer))

    assert result.confirmed_round

    # Get the total raised amount from check_goal
    total_raised = fundraiser_client.check_goal().return_value

    assert total_raised == 1_000_000
    
def test_goal_achievement(fundraiser_client: FundraiserAppClient, creator: AddressAndSigner, algorand: AlgorandClient):
    goal_amount = 5_000_000  # Goal set to 5 ALGO

    contribution_amount = goal_amount  # Directly contribute enough to meet the goal

    contribution_txn = algorand.transactions.payment(
        PayParams(
            sender=creator.address,
            receiver=fundraiser_client.app_address,
            amount=contribution_amount,
        )
    )

    # Contribute the amount that meets the goal
    result = fundraiser_client.contribute(
        contribution=TransactionWithSigner(txn=contribution_txn, signer=creator.signer)
    )

    # Check if the goal is reached
    assert fundraiser_client.check_goal().return_value >= goal_amount

def test_withdraw_funds(fundraiser_client: FundraiserAppClient, creator: AddressAndSigner, algorand: AlgorandClient):
    goal_amount = 5_000_000  # Goal set to 5 ALGO

    # Check if the goal is already reached 
    assert fundraiser_client.check_goal().return_value >= goal_amount

    # Withdraw the funds
    withdrawal_txn = fundraiser_client.withdraw_funds()

    # Send the withdrawal transaction
    result = algorand.send.payment(
        PayParams(
            sender=fundraiser_client.app_address,
            receiver=creator.address,
            amount=goal_amount,
            close_remainder_to=creator.address,
            fee=1000, 
        )
    )

    # Check transaction confirmation
    assert result.confirmed_round

    print(f"Withdrawal transaction confirmed: {result.txid}")
