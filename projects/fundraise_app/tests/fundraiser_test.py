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
        PayParams(sender=dispenser.address, receiver=acct.address, amount=10_000_000)
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
    
