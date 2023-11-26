from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
import mysql.connector
from tkinter import simpledialog

db = None
cursor = None

"""
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="pass",
    database="library"
)
cursor = db.cursor()
"""

FINE_RATE_PER_DAY = 5  
FINE_START_DAYS = 14 

def add_book(title, author):
    try:
        if(title=="" or author==""):
            messagebox.showinfo("Error", "Please enter all fields.")
            return
        cursor.callproc("AddBook", (title, author))
        db.commit()
        messagebox.showinfo("Success", "Book added successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add book: {e}")

def add_borrower(name):
    try:
        if(name==""):
            messagebox.showinfo("Error", "Please enter all fields.")
            return
        sql = "INSERT INTO borrowers (name) VALUES (%s)"
        values = (name,)
        cursor.execute(sql, values)
        db.commit()
        messagebox.showinfo("Success", "Borrower added successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add borrower: {e}")


def calculate_fine(borrow_date, return_date):
    overdue_days = (return_date - borrow_date).days - FINE_START_DAYS
    fine = max(0, overdue_days * FINE_RATE_PER_DAY)  
    return fine

def borrow_book(book_id, borrower_id, borrow_date_entry):
    try:
        borrow_date = datetime.strptime(borrow_date_entry, "%Y-%m-%d").date()
        due_date = borrow_date + timedelta(days=FINE_START_DAYS)

        cursor.execute("SELECT available FROM books WHERE id = %s", (book_id,))
        result = cursor.fetchone()

        if result and result[0] == 1:
            try:
                sql = "UPDATE books SET available = 0 WHERE id = %s"
                values = (book_id,)
                cursor.execute(sql, values)

                sql = "INSERT INTO transactions (book_id, borrower_id, borrow_date, due_date) VALUES (%s, %s, %s, %s)"
                values = (book_id, borrower_id, borrow_date, due_date)
                cursor.execute(sql, values)
                db.commit()
                messagebox.showinfo("Success", "Book borrowed successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to borrow book: {e}")
        else:
            add_to_waitlist(book_id, borrower_id,borrow_date)
    except ValueError:
        messagebox.showerror("Error", "Invalid date format. Please enter date in YYYY-MM-DD format.")

def add_to_waitlist(book_id, borrower_id, borrow_date_entry):
    try:
        sql = "INSERT INTO waitlist (book_id, borrower_id, date_added) VALUES (%s, %s, %s)"
        values = (book_id, borrower_id, borrow_date_entry)
        cursor.execute(sql, values)
        db.commit()
        messagebox.showinfo("Success", "Added to waitlist. You will be notified when the book is available.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add to waitlist: {e}")

def remove_from_waitlist(entry_id):
    try:
        sql = "DELETE FROM waitlist WHERE id = %s"
        values = (entry_id,)
        cursor.execute(sql, values)
        db.commit()
        messagebox.showinfo("Success", "Removed from waitlist.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to remove from waitlist: {e}")


def show_waitlist():
    cursor.execute("""
        SELECT 
            books.id,
            books.title,
            authors.name,
            COUNT(waitlist.id) AS waitlist_count,  
            books.available
        FROM
            waitlist
        JOIN
            books ON waitlist.book_id = books.id
        JOIN
            authors ON books.author_id = authors.id
        GROUP BY
            books.id, books.title, authors.name, books.available
    """)

    waitlist_entries = cursor.fetchall()

    waitlist_window = tk.Tk()
    waitlist_window.title("Wait List")

    list_books_label = tk.Label(waitlist_window, text="Waiting:")
    list_books_label.pack()

    for entry in waitlist_entries:
        book_id, book_title, author_name, waitlist_count, available = entry
        availability = 'Yes' if available == 1 else 'No'
        entry_info = f"Book ID: {book_id}, Title: {book_title}, Author: {author_name}, Waitlist Count: {waitlist_count}, Available: {availability}"
        entry_label = tk.Label(waitlist_window, text=entry_info)
        entry_label.pack()

    waitlist_window.mainloop()

def delete_book(book_id):
    try:
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE book_id = %s AND return_date IS NULL", (book_id,))
        borrow_count = cursor.fetchone()[0]

        if borrow_count == 0:
            cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
            db.commit()
            messagebox.showinfo("Success", "Book deleted successfully.")
        else:
            messagebox.showerror("Error", "Cannot delete the book. The book is currently borrowed.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete book: {e}")


 
def list_books():
    cursor.execute("""
        SELECT
            books.id,
            books.title,
            authors.name,
            IFNULL(transaction_count, 0) AS transaction_count,
            books.available,
            IFNULL(borrowers.name, 'N/A') AS borrower
        FROM
            books
        LEFT JOIN
            authors
        ON
            books.author_id = authors.id
        LEFT JOIN (
            SELECT
                book_id,
                COUNT(id) AS transaction_count
            FROM
                transactions
            GROUP BY
                book_id
        ) AS transaction_counts
        ON
            books.id = transaction_counts.book_id
        LEFT JOIN (
            SELECT
                transactions.book_id,
                GROUP_CONCAT(DISTINCT borrowers.name) AS name
            FROM
                transactions
            JOIN
                borrowers
            ON
                transactions.borrower_id = borrowers.id
            WHERE
                (transactions.book_id, transactions.borrow_date) IN (
                    SELECT
                        book_id,
                        MAX(borrow_date) AS max_borrow_date
                    FROM
                        transactions
                    GROUP BY
                        book_id
                )
            GROUP BY
                transactions.book_id
        ) AS borrowers
        ON
            books.id = borrowers.book_id
    """)


    books = cursor.fetchall()

    list_books_window = tk.Tk()
    list_books_window.title("List Books")

    list_books_label = tk.Label(list_books_window, text="Books in the library:")
    list_books_label.pack()

    for book in books:
        book_id, title, author, transaction_count, available, borrower = book
        availability = 'Yes' if available == 1 else 'No'
        borrower_name = borrower if available == 0 and borrower else 'N/A'
        book_info = f"Book ID: {book_id}, Title: {title}, Author: {author}, Available: {availability}, Borrower: {borrower_name}"
        book_label = tk.Label(list_books_window, text=book_info)
        book_label.pack()

        delete_button = tk.Button(list_books_window, text="Delete", command=lambda b=book_id: delete_book(b))
        delete_button.pack()

    list_books_window.mainloop()

def list_borrowers():
    cursor.execute("SELECT * FROM borrowers")
    borrowers = cursor.fetchall()
    
    list_borrowers_window = tk.Tk()
    list_borrowers_window.title("List Borrowers")
    
    list_borrowers_label = tk.Label(list_borrowers_window, text="Borrowers:")
    list_borrowers_label.pack()
    
    for borrower in borrowers:
        borrower_id, name = borrower
        borrower_info = f"Borrower ID: {borrower_id}, Name: {name}"
        borrower_label = tk.Label(list_borrowers_window, text=borrower_info)
        borrower_label.pack()
    
    list_borrowers_window.mainloop()

def borrow_book_with_date(book_id, borrower_id, borrow_date):
    sql = "UPDATE books SET available = 0 WHERE id = %s"
    values = (book_id,)
    cursor.execute(sql, values)

    due_date = borrow_date + timedelta(days=FINE_START_DAYS)

    sql = "INSERT INTO transactions (book_id, borrower_id, borrow_date, due_date) VALUES (%s, %s, %s, %s)"
    values = (book_id, borrower_id, borrow_date, due_date)
    cursor.execute(sql, values)
    db.commit()
    messagebox.showinfo("Success", "Book borrowed successfully.")
    return due_date

def return_book(book_id, return_date_entry):
    try:
        return_date = datetime.strptime(return_date_entry, "%Y-%m-%d").date()
        cursor.execute("SELECT available, borrow_date, borrower_id FROM books JOIN transactions ON books.id = transactions.book_id WHERE books.id = %s AND return_date IS NULL", (book_id,))
        result = cursor.fetchone()

        if result and result[0] == 0:
            borrow_date = result[1]
            borrower_id = result[2]
            if return_date >= borrow_date:
                
                sql_update_books = "UPDATE books SET available = 1 WHERE id = %s"
                values_update_books = (book_id,)
                cursor.execute(sql_update_books, values_update_books)

                sql_update_transactions = "UPDATE transactions SET return_date = %s WHERE book_id = %s AND return_date IS NULL"
                values_update_transactions = (return_date, book_id)
                cursor.execute(sql_update_transactions, values_update_transactions)

                fine = calculate_fine(borrow_date, return_date)
                sql_update_fine = "UPDATE transactions SET fine = %s WHERE book_id = %s AND return_date = %s"
                values_update_fine = (fine, book_id, return_date)
                cursor.execute(sql_update_fine, values_update_fine)
                
                db.commit()

                if fine > 0:
                    messagebox.showinfo("Success", "Book returned successfully.")
                    messagebox.showinfo("Fine", f"Please pay fine: {fine}")
                else:
                    messagebox.showinfo("Success", "Book returned successfully. No fine!")

                cursor.execute("SELECT * FROM waitlist WHERE book_id = %s ORDER BY date_added", (book_id,))
                waitlist = cursor.fetchall()

                if waitlist:
                    next_borrower = waitlist[0]

                    borrow_date = return_date
                    due_date = borrow_book_with_date(book_id, next_borrower[2], borrow_date)
                    messagebox.showinfo("Success", f"Book assigned to borrower ID {next_borrower[2]}.")
                    remove_from_waitlist(next_borrower[0])

                    cursor.execute("UPDATE transactions SET borrow_date = %s WHERE book_id = %s AND borrower_id = %s AND borrow_date IS NULL", (borrow_date, book_id, next_borrower[2]))
                    db.commit()

                else:
                    messagebox.showinfo("Success", "Book returned successfully. No one in the waitlist for this book.")
            else:
                messagebox.showerror("Error", "Invalid return date. Return date cannot be before the borrow date.")
        else:
            if result and result[0] == 1:
                messagebox.showerror("Error", "Book is already available. Cannot return again.")
            else:
                messagebox.showerror("Error", "No active borrow record found for the given book ID.")
    except ValueError:
        messagebox.showerror("Error", "Invalid date format. Please enter date in YYYY-MM-DD format.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


def on_closing():
    app.destroy()

def create_user():
    global db, cursor

    try:
        cursor.execute("SELECT user()")
        result = cursor.fetchone()
        current_user_info = result[0]
        if "root" not in current_user_info:
            messagebox.showerror("Error", "Only the root user can create users.")
            return
        
        new_user = simpledialog.askstring("Create New User", "Enter new username:")
        new_password = simpledialog.askstring("Create New User", "Enter password for the new user:")
        try:
            cursor.execute(f"CREATE USER '{new_user}'@'localhost' IDENTIFIED BY '{new_password}'")
            cursor.execute(f"GRANT SELECT, UPDATE ON library.books TO '{new_user}'@'localhost'")
            cursor.execute(f"GRANT SELECT, UPDATE ON library.borrowers TO '{new_user}'@'localhost'")
            cursor.execute(f"GRANT SELECT, UPDATE, INSERT, DELETE ON library.waitlist TO '{new_user}'@'localhost'")
            cursor.execute(f"GRANT SELECT ON library.authors TO '{new_user}'@'localhost'")
            cursor.execute(f"GRANT SELECT, INSERT, UPDATE ON library.transactions TO '{new_user}'@'localhost'")
            cursor.execute(f"GRANT TRIGGER ON library.* TO '{new_user}'@'localhost'")
            db.commit()
            messagebox.showinfo("Success", f"User '{new_user}' created successfully with the privileges as a borrower.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create a new user: {e}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to create user: {e}")


def switch_user():
    global db, cursor

    current_user = simpledialog.askstring("Switch User", "Enter admin/borrower username: ")
    current_password = simpledialog.askstring("Switch User", "Enter admin/borrower password: ")

    try:
        if db:
            db.close()

        db = mysql.connector.connect(
            host="localhost",
            user=current_user,
            password=current_password,
            database="library"
        )

        cursor = db.cursor()

        print(f"User switched successfully. Current user: {current_user}") #log
        messagebox.showinfo("Success", f"User switched to {current_user} successfully.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to switch user: {e}")


def on_closing():
    app.destroy()

app = tk.Tk()

def main():
    
    app.title("Library Management System")
    app.geometry("800x600")  
    app.minsize(800, 600)

    app.protocol("WM_DELETE_WINDOW", on_closing)

    selected_option = tk.StringVar()
    selected_option.set("1")  

    frame = None  

    menu_frame = tk.Frame(app, width=200, bg="light gray")
    menu_frame.pack(side="left", fill="y")

    def on_option_selected():
        nonlocal frame  
        choice = selected_option.get()
        if frame:
            frame.pack_forget()  

        if choice == "1":
            frame = add_book_frame
            frame.pack(fill="both", expand=True)
        elif choice == "2":
            frame = add_borrower_frame
        elif choice == "3":
            frame = borrow_book_frame
        elif choice == "4":
            frame = return_book_frame
        elif choice == "5":
            frame = list_books_frame
            list_books()  
        elif choice == "6":
            frame = list_borrowers_frame
            list_borrowers() 
        elif choice == "7":
            frame = list_waitlist_frame
            show_waitlist()

        frame.pack(fill="both", expand=True)  
    tk.Radiobutton(menu_frame, text="Add Book", variable=selected_option, value="1", command=on_option_selected).pack(anchor="w")
    tk.Radiobutton(menu_frame, text="Add Borrower", variable=selected_option, value="2", command=on_option_selected).pack(anchor="w")
    tk.Radiobutton(menu_frame, text="Borrow Book", variable=selected_option, value="3", command=on_option_selected).pack(anchor="w")
    tk.Radiobutton(menu_frame, text="Return Book", variable=selected_option, value="4", command=on_option_selected).pack(anchor="w")
    tk.Radiobutton(menu_frame, text="List Books", variable=selected_option, value="5", command=on_option_selected).pack(anchor="w")
    tk.Radiobutton(menu_frame, text="List Borrowers", variable=selected_option, value="6", command=on_option_selected).pack(anchor="w")
    tk.Radiobutton(menu_frame, text="Show Waitlist", variable=selected_option, value="7", command=on_option_selected).pack(anchor="w")

    add_book_frame = tk.Frame(app)
    add_borrower_frame = tk.Frame(app)
    borrow_book_frame = tk.Frame(app)
    return_book_frame = tk.Frame(app)
    list_books_frame = tk.Frame(app)
    list_borrowers_frame = tk.Frame(app)
    list_waitlist_frame = tk.Frame(app)

    add_book_label = tk.Label(add_book_frame, text="Add Book Frame")
    add_book_label.pack()

    title_label = tk.Label(add_book_frame, text="Title:")  
    title_label.pack()
    title_entry = tk.Entry(add_book_frame)  
    title_entry.pack()

    author_label = tk.Label(add_book_frame, text="Author:")
    author_label.pack()
    author_entry = tk.Entry(add_book_frame)
    author_entry.pack()

    add_book_button = tk.Button(add_book_frame, text="Add Book", command=lambda: add_book(title_entry.get(), author_entry.get()))
    add_book_button.pack()


    add_borrower_label = tk.Label(add_borrower_frame, text="Add Borrower Frame")
    add_borrower_label.pack()

    borrower_label = tk.Label(add_borrower_frame, text="Borrower Name:")
    borrower_label.pack()
    borrower_entry = tk.Entry(add_borrower_frame)
    borrower_entry.pack()

    add_borrower_button = tk.Button(add_borrower_frame, text="Add Borrower", command=lambda: add_borrower(borrower_entry.get()))
    add_borrower_button.pack()

    borrow_book_label = tk.Label(borrow_book_frame, text="Borrow Book Frame")
    borrow_book_label.pack()

    book_id_label = tk.Label(borrow_book_frame, text="Book ID:")
    book_id_label.pack()
    book_id_entry = tk.Entry(borrow_book_frame)
    book_id_entry.pack()

    borrower_id_label = tk.Label(borrow_book_frame, text="Borrower ID:")
    borrower_id_label.pack()
    borrower_id_entry = tk.Entry(borrow_book_frame)
    borrower_id_entry.pack()

    borrow_date_label = tk.Label(borrow_book_frame, text="Borrow Date (YYYY-MM-DD):")
    borrow_date_label.pack()
    borrow_date_entry = tk.Entry(borrow_book_frame)
    borrow_date_entry.pack()

    borrow_book_button = tk.Button(borrow_book_frame, text="Borrow Book", command=lambda: borrow_book(book_id_entry.get(), borrower_id_entry.get(), borrow_date_entry.get()))
    borrow_book_button.pack()


    return_book_label = tk.Label(return_book_frame, text="Return Book Frame")
    return_book_label.pack()

    return_book_id_label = tk.Label(return_book_frame, text="Book ID:")
    return_book_id_label.pack()
    return_book_id_entry = tk.Entry(return_book_frame)
    return_book_id_entry.pack()

    return_date_label = tk.Label(return_book_frame, text="Return Date (YYYY-MM-DD):")
    return_date_label.pack()
    return_date_entry = tk.Entry(return_book_frame)
    return_date_entry.pack()

    return_book_button = tk.Button(return_book_frame, text="Return Book", command=lambda: return_book(return_book_id_entry.get(), return_date_entry.get()))
    return_book_button.pack()

    list_books_button = tk.Button(list_books_frame, text="List Books", command=list_books)
    list_books_button.pack()

    switch_user_button = tk.Button(menu_frame, text="Switch User", command=switch_user)
    switch_user_button.pack(anchor="w")

    create_user_button = tk.Button(menu_frame, text="Create User", command=create_user)
    create_user_button.pack(anchor="w")


    frame = add_book_frame
    frame.pack(fill="both", expand=True)

    app.mainloop()

try:
    main()
except KeyboardInterrupt:
        print("Exiting...")