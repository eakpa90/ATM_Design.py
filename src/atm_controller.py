from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional


class SessionStatus(Enum):
    SUCCESS = "SUCCESS"
    INVALID_CARD = "INVALID_CARD"
    CARD_RETAINED_SECURITY = "CARD_RETAINED_SECURITY"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    NETWORK_ERROR = "NETWORK_ERROR"
    HARDWARE_ERROR = "HARDWARE_ERROR"
    USER_CANCELLED = "USER_CANCELLED"


class ServerStatus(Enum):
    APPROVED = "APPROVED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"


@dataclass
class Card:
    card_id: str
    pin: str
    is_expired: bool = False
    is_blacklisted: bool = False

    def verify_pin(self, input_pin: str) -> bool:
        return self.pin == input_pin


@dataclass
class Account:
    account_id: str
    balance: float
    daily_limit: float = 4000.0
    withdrawn_today: float = 0.0


class HardwareInterface:
    def __init__(self) -> None:
        self.card_retained = False
        self.cash_retracted = False
        self.maintenance_flag = False
        self.jam_next_dispense = False

    def eject_card(self) -> None:
        print("[HARDWARE] Card ejected.")

    def retain_card(self, reason: str) -> None:
        self.card_retained = True
        print(f"[HARDWARE] Card retained for security. Reason: {reason}")

    def can_dispense_denominations(self, amount: int) -> bool:
        return amount > 0 and amount % 10 == 0

    def dispense_cash(self, amount: int) -> bool:
        if self.jam_next_dispense:
            self.maintenance_flag = True
            print("[HARDWARE ERROR] Mechanical cash jam detected mid-dispense!")
            return False
        print(f"[HARDWARE] Dispensing ${amount} in bills...")
        return True

    def retract_cash(self) -> None:
        self.cash_retracted = True
        print("[HARDWARE] Abandoned cash retracted into secure cassette.")


class BankServer:
    def __init__(self) -> None:
        self.simulate_timeout = False
        self.held_funds: dict[str, int] = {}

    def request_authorization(self, account: Account, amount: int) -> ServerStatus:
        if self.simulate_timeout:
            return ServerStatus.NETWORK_TIMEOUT
        if account.balance < amount:
            return ServerStatus.INSUFFICIENT_FUNDS

        self.held_funds[account.account_id] = amount
        return ServerStatus.APPROVED

    def commit_transaction(self, account: Account, amount: int) -> None:
        self.held_funds.pop(account.account_id, None)
        account.balance -= amount
        account.withdrawn_today += amount
        print(f"[BANK] Ledger updated. New balance: ${account.balance:.2f}")

    def rollback_transaction(self, account: Account) -> None:
        self.held_funds.pop(account.account_id, None)
        print(f"[BANK] Rollback executed! Hold released for account {account.account_id}.")


class ATMController:
    MAX_PIN_ATTEMPTS = 3
    MAX_READ_ATTEMPTS = 2

    def __init__(self, hardware: HardwareInterface, bank_server: BankServer) -> None:
        self.hardware = hardware
        self.bank_server = bank_server

    def run_withdrawal_session(
        self,
        card_reader_simulator: Callable[[int], Optional[Card]],
        pin_inputs: List[str],
        account: Account,
        desired_amounts: List[int],
        user_took_card: bool = True,
        user_took_cash: bool = True,
    ) -> SessionStatus:
        read_attempts = 0
        card: Optional[Card] = None

        while read_attempts < self.MAX_READ_ATTEMPTS and card is None:
            card = card_reader_simulator(read_attempts)
            if card is None:
                read_attempts += 1
                print(
                    f"[UI] Card read error (Attempt {read_attempts}/{self.MAX_READ_ATTEMPTS}). "
                    "Please wipe chip and re-insert."
                )

        if card is None or card.is_expired or card.is_blacklisted:
            if card:
                self.hardware.eject_card()
            print("[UI] Session terminated: Card unreadable or invalid.")
            return SessionStatus.INVALID_CARD

        authenticated = False
        attempts = 0
        for pin in pin_inputs:
            if attempts >= self.MAX_PIN_ATTEMPTS:
                break
            attempts += 1
            if card.verify_pin(pin):
                authenticated = True
                break
            remaining = self.MAX_PIN_ATTEMPTS - attempts
            if remaining > 0:
                print(f"[UI] Incorrect PIN. {remaining} tries remaining.")

        if not authenticated:
            self.hardware.retain_card("Max PIN attempts exceeded")
            print("[UI] Security Lock: Card retained due to repeated incorrect PINs.")
            return SessionStatus.CARD_RETAINED_SECURITY

        valid_amount: Optional[int] = None
        for amount in desired_amounts:
            if not self.hardware.can_dispense_denominations(amount):
                print(f"[UI] ATM cannot dispense ${amount}. Enter a multiple of $10.")
                continue
            if amount > account.balance:
                print(
                    f"[UI] Insufficient funds. Balance is ${account.balance:.2f}. "
                    "Try a lower amount."
                )
                continue
            if (account.withdrawn_today + amount) > account.daily_limit:
                print("[UI] Exceeds daily withdrawal limit.")
                continue
            valid_amount = amount
            break

        if valid_amount is None:
            print("[UI] Transaction cancelled or no valid amount entered.")
            self.hardware.eject_card()
            return SessionStatus.USER_CANCELLED

        auth_status = self.bank_server.request_authorization(account, valid_amount)
        if auth_status == ServerStatus.NETWORK_TIMEOUT:
            print("[UI] Connection error with bank server. Please try another machine.")
            self.hardware.eject_card()
            return SessionStatus.NETWORK_ERROR
        if auth_status == ServerStatus.INSUFFICIENT_FUNDS:
            print("[UI] Server rejected transaction: Insufficient funds.")
            self.hardware.eject_card()
            return SessionStatus.INSUFFICIENT_FUNDS

        if not self.hardware.dispense_cash(valid_amount):
            self.bank_server.rollback_transaction(account)
            self.hardware.eject_card()
            print("[UI] Mechanical error occurred. Transaction cancelled. No funds deducted.")
            return SessionStatus.HARDWARE_ERROR

        self.bank_server.commit_transaction(account, valid_amount)
        self.hardware.eject_card()

        if not user_took_card:
            self.hardware.retain_card("Card abandoned by user")
        if not user_took_cash:
            self.hardware.retract_cash()

        print("[UI] Please take your cash and receipt. Thank you!")
        return SessionStatus.SUCCESS