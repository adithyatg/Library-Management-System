Library Management System

Overview
The Library Management System is a Python-based application designed to streamline library operations. It provides functionalities for adding books, managing borrowers, handling book transactions, and maintaining a waitlist.

Key Features
Add Book: Admins can add new books, and authors are dynamically added if not present.
Add Borrower: Admins can add new borrowers to the system.
Borrow & Return: Borrowers can borrow and return books, with automatic fine calculation.
List Books & Borrowers: Admins can view lists of books and registered borrowers.
Show Waitlist: Admins can see a list of individuals waiting for currently unavailable books.
Switch/Create User: Admins can switch user roles (admin/borrower) and create new borrower users.

Database Structure
The database includes tables for Authors, Books, Borrowers, Transactions and Waitlist, with defined relationships and keys for data integrity.

Setup
Install dependencies: pip install mysql-connector-python
Configure database credentials in dbms.py.
Run struct.py to set up the database and tables.

Usage
Run dbms.py to launch the application. Use the provided menu for easy navigation between functionalities.

SQL Queries
The application includes SQL queries for set operations, joins, aggregate functions, and complex queries to manage and retrieve data.

Deliverables
Conceptual Model: ER diagram illustrating the relationships between entities.
Relational Schema: Database structure outlining tables, attributes, and keys.
Procedures/Triggers: Implemented procedures, functions, and triggers for specific functionalities.
