import unittest

from src.atm_controller import (
    Account,
    ATMController,
    BankServer,
    Card,
    HardwareInterface,
    SessionStatus,
)


class TestATMController(unittest.TestCase):
    def test_successful_withdrawal(self):
        hw = HardwareInterface()
        bank = BankServer()
        atm = ATMController(hw, bank)

        card = Card(card_id="CARD-1", pin="1234")
        account = Account(account_id="ACC-1", balance=200.0)

        status = atm.run_withdrawal_session(
            card_reader_simulator=lambda attempt: card,
            pin_inputs=["1234"],
            account=account,
            desired_amounts=[50],
        )

        self.assertEqual(status, SessionStatus.SUCCESS)
        self.assertEqual(account.balance, 150.0)
        self.assertEqual(account.withdrawn_today, 50.0)

    def test_card_read_retry_and_recovery(self):
        hw = HardwareInterface()
        bank = BankServer()
        atm = ATMController(hw, bank)

        card = Card(card_id="CARD-2", pin="5678")
        account = Account(account_id="ACC-2", balance=300.0)

        attempts_logged = []

        def flaky_reader(attempt):
            attempts_logged.append(attempt)
            if attempt == 0:
                return None
            return card

        status = atm.run_withdrawal_session(
            card_reader_simulator=flaky_reader,
            pin_inputs=["5678"],
            account=account,
            desired_amounts=[100],
        )

        self.assertEqual(status, SessionStatus.SUCCESS)
        self.assertEqual(attempts_logged, [0, 1])

    def test_pin_lockout_security_interlock(self):
        hw = HardwareInterface()
        bank = BankServer()
        atm = ATMController(hw, bank)

        card = Card(card_id="CARD-3", pin="9999")
        account = Account(account_id="ACC-3", balance=500.0)

        status = atm.run_withdrawal_session(
            card_reader_simulator=lambda attempt: card,
            pin_inputs=["0000", "1111", "2222"],
            account=account,
            desired_amounts=[50],
        )

        self.assertEqual(status, SessionStatus.CARD_RETAINED_SECURITY)
        self.assertTrue(hw.card_retained)

    def test_mechanical_jam_triggers_atomic_rollback(self):
        hw = HardwareInterface()
        hw.jam_next_dispense = True
        bank = BankServer()
        atm = ATMController(hw, bank)

        card = Card(card_id="CARD-4", pin="4321")
        account = Account(account_id="ACC-4", balance=400.0)

        status = atm.run_withdrawal_session(
            card_reader_simulator=lambda attempt: card,
            pin_inputs=["4321"],
            account=account,
            desired_amounts=[100],
        )

        self.assertEqual(status, SessionStatus.HARDWARE_ERROR)
        self.assertEqual(account.balance, 400.0)
        self.assertTrue(hw.maintenance_flag)

    def test_insufficient_funds_cancels_session(self):
        hw = HardwareInterface()
        bank = BankServer()
        atm = ATMController(hw, bank)

        card = Card(card_id="CARD-5", pin="1111")
        account = Account(account_id="ACC-5", balance=50.0)

        status = atm.run_withdrawal_session(
            card_reader_simulator=lambda attempt: card,
            pin_inputs=["1111"],
            account=account,
            desired_amounts=[100],
        )

        self.assertEqual(status, SessionStatus.USER_CANCELLED)
        self.assertEqual(account.balance, 50.0)


if __name__ == "__main__":
    unittest.main()