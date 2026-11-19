import random

from src.atm_controller import Account, BankServer, Card, HardwareInterface, ServerStatus


class InteractiveATMController:
    MAX_PIN_ATTEMPTS = 3
    MAX_READ_ATTEMPTS = 2

    def __init__(self, hardware: HardwareInterface, bank_server: BankServer) -> None:
        self.hardware = hardware
        self.bank_server = bank_server

    def run_interactive_session(self, user_card: Card, user_account: Account) -> None:
        print("\n" + "=" * 40)
        print("      WELCOME TO PYTHON VIRTUAL ATM      ")
        print("=" * 40)

        read_attempts = 0
        card = None
        while read_attempts < self.MAX_READ_ATTEMPTS and card is None:
            input("\nPress [Enter] to insert/swipe your card...")
            if read_attempts == 0 and random.random() < 0.3:
                print("Read error: Chip unreadable. Please wipe your card and try again.")
                read_attempts += 1
            else:
                card = user_card
                print("Card read successfully!")

        if card is None or card.is_expired or card.is_blacklisted:
            print("Session terminated: Invalid or unreadable card.")
            return

        attempts = 0
        authenticated = False
        while attempts < self.MAX_PIN_ATTEMPTS and not authenticated:
            attempts += 1
            pin_input = input(
                f"\n[PIN Entry - Attempt {attempts}/{self.MAX_PIN_ATTEMPTS}] Enter your 4-digit PIN: "
            )
            if card.verify_pin(pin_input):
                authenticated = True
                print("PIN Verified Successfully.")
            else:
                remaining = self.MAX_PIN_ATTEMPTS - attempts
                if remaining > 0:
                    print(f"Incorrect PIN. You have {remaining} tries remaining.")

        if not authenticated:
            self.hardware.retain_card("Exceeded maximum PIN attempts")
            print("Access Denied. Your card has been retained for security.")
            return

        valid_amount = None
        while valid_amount is None:
            remaining_limit = user_account.daily_limit - user_account.withdrawn_today
            print(f"\nCurrent Account Balance: ${user_account.balance:.2f}")
            print(f"Daily Limit Remaining: ${remaining_limit:.2f}")

            amount_str = input(
                "Enter withdrawal amount (multiples of $10, or type 'cancel' to exit): "
            )
            if amount_str.lower() == "cancel":
                self.hardware.eject_card()
                print("Transaction cancelled by user.")
                return

            try:
                amount = int(amount_str)
            except ValueError:
                print("Please enter a valid numerical amount.")
                continue

            if not self.hardware.can_dispense_denominations(amount):
                print("Invalid amount: ATM can only dispense multiples of #10.")
                continue

            if amount > user_account.balance:
                print(
                    f"Insufficient funds! You requested #{amount} "
                    f"but only have ${user_account.balance:.2f}."
                )
                choice = input("Would you like to try a different amount? (y/n): ")
                if choice.lower() != "y":
                    self.hardware.eject_card()
                    return
                continue

            if amount > remaining_limit:
                print("Amount exceeds remaining daily limit.")
                continue

            valid_amount = amount

        print("\nCommunicating with bank server...")
        auth_status = self.bank_server.request_authorization(user_account, valid_amount)
        if auth_status != ServerStatus.APPROVED:
            print("Transaction declined by server.")
            self.hardware.eject_card()
            return

        if not self.hardware.dispense_cash(valid_amount):
            self.bank_server.rollback_transaction(user_account)
            self.hardware.eject_card()
            print("Dispense failed. Your funds have been safely restored.")
            return

        self.bank_server.commit_transaction(user_account, valid_amount)
        self.hardware.eject_card()
        print("\nTHANK YOU FOR BANKING WITH US!")


def main() -> None:
    hw = HardwareInterface()
    bank = BankServer()
    atm = InteractiveATMController(hw, bank)

    my_card = Card(card_id="CARD-777", pin="1234")
    my_account = Account(account_id="ACC-001", balance=5000.00)

    while True:
        atm.run_interactive_session(my_card, my_account)
        again = input("\nWould you like to start another ATM session? (y/n): ")
        if again.lower() != "y":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()