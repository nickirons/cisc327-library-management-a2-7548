import pytest

from services.payment_service import PaymentGateway


@pytest.fixture(autouse=True)
def no_sleep(mocker):
    """Prevent test delays from simulated network calls."""
    mocker.patch("services.payment_service.time.sleep", return_value=None)


def test_process_payment_success(mocker):
    mocker.patch("services.payment_service.time.time", return_value=1700)
    gateway = PaymentGateway()

    success, txn_id, message = gateway.process_payment("123456", 25.0, "Late fees")

    assert success is True
    assert txn_id == "txn_123456_1700"
    assert "processed successfully" in message.lower()


@pytest.mark.parametrize(
    "amount, expected_msg",
    [
        (0, "invalid amount"),
        (-5, "invalid amount"),
        (1001, "declined"),
    ],
)
def test_process_payment_invalid_amounts(mocker, amount, expected_msg):
    mocker.patch("services.payment_service.time.time", return_value=1700)
    gateway = PaymentGateway()

    success, txn_id, message = gateway.process_payment("123456", amount, "Late fees")

    assert success is False
    assert txn_id == ""
    assert expected_msg in message.lower()


def test_process_payment_invalid_patron_id(mocker):
    mocker.patch("services.payment_service.time.time", return_value=1700)
    gateway = PaymentGateway()

    success, txn_id, message = gateway.process_payment("123", 10.0, "Late fees")

    assert success is False
    assert txn_id == ""
    assert "invalid patron id" in message.lower()


def test_refund_payment_success(mocker):
    mocker.patch("services.payment_service.time.time", return_value=42)
    gateway = PaymentGateway()

    success, message = gateway.refund_payment("txn_abc_1700", 5.0)

    assert success is True
    assert "refund of $5.00 processed successfully" in message.lower()
    assert "refund_txn_abc_1700_42" in message


@pytest.mark.parametrize(
    "transaction_id, amount, expected_msg",
    [
        ("", 5.0, "invalid transaction id"),
        ("txn_abc_1700", 0, "invalid refund amount"),
        ("txn_abc_1700", -1, "invalid refund amount"),
    ],
)
def test_refund_payment_invalid_inputs(transaction_id, amount, expected_msg):
    gateway = PaymentGateway()

    success, message = gateway.refund_payment(transaction_id, amount)

    assert success is False
    assert expected_msg in message.lower()


def test_verify_payment_status_not_found():
    gateway = PaymentGateway()

    status = gateway.verify_payment_status("")

    assert status["status"] == "not_found"
    assert "not found" in status["message"].lower()


def test_verify_payment_status_completed(mocker):
    mocker.patch("services.payment_service.time.time", return_value=1700)
    gateway = PaymentGateway()

    status = gateway.verify_payment_status("txn_123456_1700")

    assert status["status"] == "completed"
    assert status["transaction_id"] == "txn_123456_1700"
    assert status["amount"] == 10.50
