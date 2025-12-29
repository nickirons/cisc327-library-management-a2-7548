import pytest
from unittest.mock import Mock, patch
from services.library_service import pay_late_fees, refund_late_fee_payment
from services.payment_service import PaymentGateway

# Pay late fees tests
#----------------

def stub_fee_and_book(mocker, fee_amount=5.0, book_title="Test Book", book_id=1):
    """Helper to stub database calls"""
    fee_stub = mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": fee_amount, "status": "Overdue"}
    )
    book_stub = mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": book_id, "title": book_title}
    )
    return fee_stub, book_stub

def test_pay_late_fees_successful_payment(mocker):
    fee_stub, book_stub = stub_fee_and_book(
        mocker, fee_amount=7.5, book_title="Mocked Book", book_id=42
    )
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (True, "txn_123", "Payment of $7.50 processed successfully")
    success, message, transaction_id = pay_late_fees("123456", 42, mock_gateway)
    assert success is True
    assert transaction_id == "txn_123"
    assert "successful" in message.lower()
    
    mock_gateway.process_payment.assert_called_once_with(
        patron_id="123456", 
        amount=7.5, 
        description="Late fees for 'Mocked Book'"
    )

def test_pay_late_fees_declined_by_gateway(mocker):
    fee_stub, book_stub = stub_fee_and_book(
        mocker, fee_amount=4.0, book_title="Declined Book", book_id=7
    )
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (False, None, "Card declined")
    success, message, transaction_id = pay_late_fees("123456", 7, mock_gateway)

    assert success is False
    assert transaction_id is None
    assert "failed" in message.lower()
    
    mock_gateway.process_payment.assert_called_once()

def test_pay_late_fees_invalid_patron_id_skips_gateway(mocker):
    fee_stub, book_stub = stub_fee_and_book(mocker, fee_amount=5.0)
    mock_gateway = Mock(spec=PaymentGateway)

    success, message, transaction_id = pay_late_fees("12AB56", 1, mock_gateway)
    assert success is False
    assert "invalid patron id" in message.lower()
    
    #Make sure external call swerent made
    mock_gateway.process_payment.assert_not_called()

def test_pay_late_fees_zero_amount_skips_payment(mocker):
    fee_stub, book_stub = stub_fee_and_book(mocker, fee_amount=0.0)
    mock_gateway = Mock(spec=PaymentGateway)

    success, message, transaction_id = pay_late_fees("123456", 1, mock_gateway)
    assert success is False
    assert "no late fees" in message.lower()
    
    mock_gateway.process_payment.assert_not_called()

def test_pay_late_fees_handles_network_error(mocker):
    fee_stub, book_stub = stub_fee_and_book(mocker, fee_amount=10.0, book_title="Network Book")
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.side_effect = Exception("Network outage")

    success, message, transaction_id = pay_late_fees("123456", 1, mock_gateway)

    assert success is False
    assert "processing error" in message.lower()
    assert "network outage" in message.lower()

#========================
# Refund late fee payment tests
# =================

def test_refund_late_fee_payment_success():
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (True, "Refund Processed")

    success, message = refund_late_fee_payment("txn_001", 10.0, mock_gateway)

    assert success is True
    assert "refund processed" in message.lower()
    mock_gateway.refund_payment.assert_called_once_with("txn_001", 10.0)

def test_refund_late_fee_payment_invalid_transaction():
    mock_gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("bad_id", 5.0, mock_gateway)

    assert success is False
    assert "invalid transaction" in message.lower()
    #Make sure we didn't call the gateway with bad data
    mock_gateway.refund_payment.assert_not_called()

@pytest.mark.parametrize("amount, expected_msg", [
    (-1, "greater than 0"),
    (0, "greater than 0"),
    (20, "exceeds maximum")
])
def test_refund_late_fee_payment_invalid_amounts(amount, expected_msg):
    mock_gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("txn_001", amount, mock_gateway)

    assert success is False
    assert expected_msg.lower() in message.lower()
    mock_gateway.refund_payment.assert_not_called()