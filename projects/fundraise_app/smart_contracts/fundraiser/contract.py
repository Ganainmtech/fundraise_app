from algopy import (
    Global,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
)

class FundraiserApp(arc4.ARC4Contract):
    goal_amount: UInt64 # Campaign goal in microAlgos
    total_raised: UInt64 # Total amount raised

    @arc4.abimethod(
        allow_actions=["NoOp"],  # Allow only NoOp actions
        create="require",        # Require this method for contract creation
    )
    def create_campaign(self, goal_amount: UInt64) -> None:
        """Create a new fundraising campaign with the specified goal amount."""
        self.goal_amount = goal_amount
        self.total_raised = UInt64(0)

    @arc4.abimethod
    def contribute(self, contribution: gtxn.PaymentTransaction) -> None:
        """Contribute funds to the campaign."""
        assert contribution.receiver == Global.current_application_address
        self.total_raised += contribution.amount

    @arc4.abimethod
    def check_goal(self) -> UInt64:
        """Check the total amount raised so far."""
        return self.total_raised

    @arc4.abimethod
    def withdraw_funds(self) -> None:
        """Withdraw funds when the goal is met and sender is the creator."""
        assert Txn.sender == Global.creator_address
        assert self.total_raised >= self.goal_amount

        itxn.Payment(
            receiver=Global.creator_address,
            amount=self.total_raised,
            close_remainder_to=Global.creator_address,
        ).submit()
