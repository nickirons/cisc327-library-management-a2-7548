"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_db_connection, get_patron_borrowed_books
)
from services.payment_service import PaymentGateway

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13 or not isbn.isdigit():
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed >= 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    
    TODO: Implement R4 as per requirements
    """

    # Validate patron id
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check ifthe book exists
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    # Check if THIS patron actually borrowed this book
    conn = get_db_connection()
    borrow_record = conn.execute('''
        SELECT * FROM borrow_records 
        WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
    ''', (patron_id, book_id)).fetchone()
    conn.close()

    if not borrow_record:
        return False, "This book was not borrowed by this patron."
    
    # Update the borrow record
    return_date = datetime.now()
    return_success = update_borrow_record_return_date(patron_id, book_id, return_date)
    
    if not return_success:
        return False, "No active borrow record found for this book and patron."
    
    # Increase available copies cause were returning
    availability_success = update_book_availability(book_id, 1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."

    # Calculate late fee after setting the return date
    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    fee_amount = fee_info.get('fee_amount', 0.0)
    if fee_amount > 0:
        return True, f'Successfully returned "{book["title"]}". Late fee: ${fee_amount:.2f}.'
    return True, f'Successfully returned "{book["title"]}". No late fee.'

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.
    
    TODO: Implement R5 as per requirements 
    """
    
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Invalid patron ID'
        }
    
    # Get the most recent borrow record directly
    conn = get_db_connection()
    record = conn.execute('''
        SELECT * FROM borrow_records 
        WHERE patron_id = ? AND book_id = ? 
        ORDER BY borrow_date DESC 
        LIMIT 1
    ''', (patron_id, book_id)).fetchone()
    conn.close()
    
    if not record:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'No borrow record found'
        }
    
    # Determine check date
    if record['return_date']:
        check_date = datetime.fromisoformat(record['return_date'])
    else:
        check_date = datetime.now()
    
    due_date = datetime.fromisoformat(record['due_date'])
    
    # num of days overdue
    if check_date > due_date:
        days_overdue = (check_date - due_date).days
        
        # Calculate the fee
        if days_overdue <= 7:
            fee_amount = days_overdue * 0.50
        else:
            fee_amount = (7 * 0.50) + ((days_overdue - 7) * 1.00)
        
        # $15 max
        fee_amount = min(fee_amount, 15.00)
        
        return {
            'fee_amount': round(fee_amount, 2),
            'days_overdue': days_overdue,
            'status': 'Overdue'
        }
    else:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Not overdue'
        }

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    
    TODO: Implement R6 as per requirements
    """
    valid_types = ['title', 'author', 'isbn']

    if search_type not in valid_types:
        return []
    
    if not search_term or not search_term.strip():
        return []
    
    conn = get_db_connection()
    
    if search_type == 'isbn':
        #exact match
        books = conn.execute('''
            SELECT * FROM books 
            WHERE isbn = ?
        ''', (search_term.strip(),)).fetchall()
    elif search_type == 'title':
        books = conn.execute('''
            SELECT * FROM books 
            WHERE LOWER(title) LIKE LOWER(?)
        ''', (f'%{search_term.strip()}%',)).fetchall()
    elif search_type == 'author':
        books = conn.execute('''
            SELECT * FROM books 
            WHERE LOWER(author) LIKE LOWER(?)
        ''', (f'%{search_term.strip()}%',)).fetchall()
    else:
        books = []
    
    conn.close()
    
    # Converts to list of dictionaries
    return [dict(book) for book in books]

def get_patron_status_report(patron_id: str) -> Dict:
    """
    Get status report for a patron.
    
    TODO: Implement R7 as per requirements
    """

    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            'patron_id': patron_id,
            'currently_borrowed': [],
            'total_late_fees': 0.00,
            'books_borrowed_count': 0,
            'borrowing_history': [],
            'status': 'Invalid patron ID. Must be exactly 6 digits.'
        }
    
    # Use existing function to get currently borrowed books
    currently_borrowed = get_patron_borrowed_books(patron_id)
    
    # Calculate total late fees
    total_late_fees = 0.00
    for book in currently_borrowed:
        fee_info = calculate_late_fee_for_book(patron_id, book['book_id'])
        book['late_fee'] = fee_info['fee_amount']
        book['days_overdue'] = fee_info['days_overdue']
        book['is_overdue'] = fee_info['status'] == 'Overdue'
        total_late_fees += fee_info['fee_amount']
    
    #Borrow history
    conn = get_db_connection()
    history = conn.execute('''
        SELECT br.*, b.title, b.author, b.isbn
        FROM borrow_records br
        JOIN books b ON br.book_id = b.id
        WHERE br.patron_id = ?
        ORDER BY br.borrow_date DESC
    ''', (patron_id,)).fetchall()
    conn.close()
    
    borrowing_history = [dict(record) for record in history]
    
    return {
        'patron_id': patron_id,
        'currently_borrowed': currently_borrowed,
        'total_late_fees': round(total_late_fees, 2),
        'books_borrowed_count': len(currently_borrowed),
        'borrowing_history': borrowing_history,
        'status': 'Success'
    }

def refund_late_fee_payment(transaction_id: str, amount: float, payment_gateway: PaymentGateway = None) -> Tuple[bool, str]:
    """
    Refund a late fee payment (e.g., if book was returned on time but fees were charged in error).
    
    NEW FEATURE FOR ASSIGNMENT 3: Another function requiring mocking
    
    Args:
        transaction_id: Original transaction ID to refund
        amount: Amount to refund
        payment_gateway: Payment gateway instance (injectable for testing)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate inputs
    if not transaction_id or not transaction_id.startswith("txn_"):
        return False, "Invalid transaction ID."
    
    if amount <= 0:
        return False, "Refund amount must be greater than 0."
    
    if amount > 15.00:  # Maximum late fee per book
        return False, "Refund amount exceeds maximum late fee."
    
    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()
    
    # Process refund through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN YOUR TESTS!
    try:
        success, message = payment_gateway.refund_payment(transaction_id, amount)
        
        if success:
            return True, message
        else:
            return False, f"Refund failed: {message}"
            
    except Exception as e:
        return False, f"Refund processing error: {str(e)}"
    
def pay_late_fees(patron_id: str, book_id: int, payment_gateway: PaymentGateway = None) -> Tuple[bool, str, Optional[str]]:
    """
    Process payment for late fees using external payment gateway.
    
    NEW FEATURE FOR ASSIGNMENT 3: Demonstrates need for mocking/stubbing
    This function depends on an external payment service that should be mocked in tests.
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book with late fees
        payment_gateway: Payment gateway instance (injectable for testing)
        
    Returns:
        tuple: (success: bool, message: str, transaction_id: Optional[str])
        
    Example for you to mock:
        # In tests, mock the payment gateway:
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (True, "txn_123", "Success")
        success, msg, txn = pay_late_fees("123456", 1, mock_gateway)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits.", None
    
    # Calculate late fee first
    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    
    # Check if there's a fee to pay
    if not fee_info or 'fee_amount' not in fee_info:
        return False, "Unable to calculate late fees.", None
    
    fee_amount = fee_info.get('fee_amount', 0.0)
    
    if fee_amount <= 0:
        return False, "No late fees to pay for this book.", None
    
    # Get book details for payment description
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found.", None
    
    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()
    
    # Process payment through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN THEIR TESTS!
    try:
        success, transaction_id, message = payment_gateway.process_payment(
            patron_id=patron_id,
            amount=fee_amount,
            description=f"Late fees for '{book['title']}'"
        )
        
        if success:
            return True, f"Payment successful! {message}", transaction_id
        else:
            return False, f"Payment failed: {message}", None
            
    except Exception as e:
        # Handle payment gateway errors
        return False, f"Payment processing error: {str(e)}", None
