DROP database if EXISTS library;
CREATE DATABASE IF NOT EXISTS library;
USE library;

CREATE TABLE authors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author_id INT,
    available INT DEFAULT 0,
    FOREIGN KEY (author_id) REFERENCES authors(id)
);

CREATE TABLE borrowers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT,
    borrower_id INT,
    borrow_date DATE,
    due_date DATE,
    return_date DATE,
    fine DECIMAL(10, 2) DEFAULT 0,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (borrower_id) REFERENCES borrowers(id)
);

CREATE TABLE waitlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT,
    borrower_id INT,
    date_added DATE,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (borrower_id) REFERENCES borrowers(id)
);

DELIMITER $$
CREATE PROCEDURE AddBook(IN p_title VARCHAR(255), IN p_author VARCHAR(255))
BEGIN
    DECLARE author_id INT;
    SELECT id INTO author_id FROM authors WHERE name = p_author;
    
    IF author_id IS NULL THEN
        INSERT INTO authors (name) VALUES (p_author);
        SET author_id = LAST_INSERT_ID();
    END IF;
    
    INSERT INTO books (title, author_id, available) VALUES (p_title, author_id, 1);
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER update_available_status AFTER INSERT ON transactions
FOR EACH ROW
BEGIN
    DECLARE available_status INT;
    SELECT available INTO available_status FROM books WHERE id = NEW.book_id;
    IF available_status = 1 THEN
        UPDATE books SET available = 0 WHERE id = NEW.book_id;
    END IF;
END$$
DELIMITER ;



-- Create user 'library_user' with password 'password' and grant privileges
-- DROP USER 'library_user'@'localhost';
-- CREATE USER 'library_user'@'localhost' IDENTIFIED BY 'password';
-- GRANT SELECT, UPDATE ON library.books TO 'library_user'@'localhost';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON library.waitlist TO 'library_user'@'localhost';
-- GRANT SELECT, INSERT, UPDATE ON library.transactions TO 'library_user'@'localhost';
-- GRANT SELECT, INSERT, UPDATE ON library.books TO 'library_user'@'localhost';
-- GRANT TRIGGER ON library.* TO 'library_user'@'localhost';



-- -- CREATE TABLE books (
-- --     id INT AUTO_INCREMENT PRIMARY KEY,
-- --     title VARCHAR(255) NOT NULL,
-- --     author VARCHAR(255),
-- --     available INT DEFAULT 0
-- -- );

-- -- CREATE TABLE borrowers (
-- --     id INT AUTO_INCREMENT PRIMARY KEY,
-- --     name VARCHAR(255) NOT NULL
-- -- );

-- -- CREATE TABLE transactions (
-- --     id INT AUTO_INCREMENT PRIMARY KEY,
-- --     book_id INT,
-- --     borrower_id INT,
-- --     borrow_date DATE,
-- --     due_date DATE,  
-- --     return_date DATE,
-- --     fine DECIMAL(10, 2) DEFAULT 0
-- -- );

-- -- CREATE TABLE waitlist (
-- --     id INT AUTO_INCREMENT PRIMARY KEY,
-- --     book_id INT,
-- --     borrower_id INT,
-- --     date_added DATE
-- -- );