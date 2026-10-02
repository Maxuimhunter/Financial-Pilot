import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_connection():
    """Create a database connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD') or None,
            database=os.getenv('DB_NAME')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    """Initialize the database with required tables."""
    # First connect without specifying a database
    try:
        temp_conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD') or None
        )
        cursor = temp_conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_NAME')}")
        cursor.close()
        temp_conn.close()
        
        # Now connect to the specific database
        connection = create_connection()
        if connection is None:
            return False
            
        cursor = connection.cursor()
        cursor.execute(f"USE {os.getenv('DB_NAME')}")
        
        # Create months table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS months (
            id INT AUTO_INCREMENT PRIMARY KEY,
            month_name VARCHAR(20) NOT NULL UNIQUE,
            month_number INT NOT NULL UNIQUE
        )""")
        
        # Insert months if not exists
        months = [
            ('January', 1), ('February', 2), ('March', 3), ('April', 4),
            ('May', 5), ('June', 6), ('July', 7), ('August', 8),
            ('September', 9), ('October', 10), ('November', 11), ('December', 12)
        ]
        
        cursor.executemany("""
        INSERT IGNORE INTO months (month_name, month_number)
        VALUES (%s, %s)
        """, months)
        
        # Create budget table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            id INT AUTO_INCREMENT PRIMARY KEY,
            month_id INT NOT NULL,
            category VARCHAR(50) NOT NULL,
            budgeted DECIMAL(10, 2) DEFAULT 0.00,
            actual DECIMAL(10, 2) DEFAULT 0.00,
            year INT NOT NULL DEFAULT 2026,
            FOREIGN KEY (month_id) REFERENCES months(id),
            UNIQUE KEY unique_month_category_year (month_id, category, year)
        )""")
        
        # Create expenses table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            month_id INT NOT NULL,
            category VARCHAR(50) NOT NULL,
            description VARCHAR(255) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            expense_date DATE NOT NULL,
            year INT NOT NULL DEFAULT 2026,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (month_id) REFERENCES months(id),
            INDEX idx_month_category_year (month_id, category, year)
        )""")
        
        # Create a trigger to update the actual amount in the budget table
        cursor.execute("""
        DROP TRIGGER IF EXISTS after_expense_insert
        """)

        cursor.execute("""
        CREATE TRIGGER after_expense_insert
        AFTER INSERT ON expenses
        FOR EACH ROW
        BEGIN
            INSERT INTO budget (month_id, category, budgeted, actual, year)
            VALUES (NEW.month_id, NEW.category, 0, NEW.amount, NEW.year)
            ON DUPLICATE KEY UPDATE
                actual = actual + NEW.amount;
        END
        """)

        cursor.execute("""
        DROP TRIGGER IF EXISTS after_expense_delete
        """)

        cursor.execute("""
        CREATE TRIGGER after_expense_delete
        AFTER DELETE ON expenses
        FOR EACH ROW
        BEGIN
            UPDATE budget
            SET actual = (
                SELECT COALESCE(SUM(amount), 0)
                FROM expenses
                WHERE month_id = OLD.month_id
                AND category = OLD.category
                AND year = OLD.year
            )
            WHERE month_id = OLD.month_id
            AND category = OLD.category
            AND year = OLD.year;
        END
        """)
        
        # Initialize actual amounts for existing expenses
        cursor.execute("""
        INSERT INTO budget (month_id, category, budgeted, actual)
        SELECT month_id, category, 0, SUM(amount)
        FROM expenses
        GROUP BY month_id, category
        ON DUPLICATE KEY UPDATE 
            actual = VALUES(actual)
        """)
        
        connection.commit()
        return True
        
    except Error as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        if 'connection' in locals() and connection is not None and connection.is_connected():
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
            connection.close()

def get_month_budget(month_id, year=2026):
    """Get budget data for a specific month and year."""
    connection = create_connection()
    if connection is None:
        return None

    try:
        month_id = int(month_id)  # Ensure month_id is an integer
        year = int(year)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
        SELECT category,
               CAST(budgeted AS DECIMAL(10,2)) as budgeted,
               CAST(COALESCE(actual, 0) AS DECIMAL(10,2)) as actual
        FROM budget
        WHERE month_id = %s AND year = %s
        ORDER BY category
        """, (month_id, year))

        # Convert Decimal to float for consistency
        result = []
        for row in cursor.fetchall():
            row['budgeted'] = float(row['budgeted'])
            row['actual'] = float(row['actual'])
            result.append(row)

        return result

    except (Error, ValueError) as e:
        print(f"Error fetching budget data: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_budget(month_id, category, budgeted, is_income=False, year=2026):
    """
    Update or insert budget data for a specific month, category, and year.
    If is_income is True, updates both budgeted and actual amounts for income.
    """
    connection = create_connection()
    if connection is None:
        return False

    try:
        # Ensure values are of correct type
        month_id = int(month_id)
        budgeted = float(budgeted)
        year = int(year)

        cursor = connection.cursor()

        if is_income:
            # For income, update both budgeted and actual amounts
            cursor.execute("""
            INSERT INTO budget (month_id, category, budgeted, actual, year)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                budgeted = VALUES(budgeted),
                actual = VALUES(actual)
            """, (month_id, str(category), budgeted, budgeted, year))
        else:
            # For regular categories, update only budgeted amount
            cursor.execute("""
            INSERT INTO budget (month_id, category, budgeted, year)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                budgeted = VALUES(budgeted)
            """, (month_id, str(category), budgeted, year))

        connection.commit()
        return True

    except Error as e:
        print(f"Error updating budget: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_expense(month_id, category, description, amount, expense_date, year=2026):
    """Add a new expense to the database."""
    connection = create_connection()
    if connection is None:
        return False

    try:
        # Ensure amount is a float
        amount = float(amount)
        year = int(year)

        cursor = connection.cursor()
        cursor.execute("""
        INSERT INTO expenses (month_id, category, description, amount, expense_date, year)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (int(month_id), str(category), str(description), float(amount), expense_date, year))

        connection.commit()
        return True

    except (Error, ValueError) as e:
        print(f"Error adding expense: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_expenses(month_id, category=None, year=2026):
    """Get expenses for a specific month and year, optionally filter by category."""
    connection = create_connection()
    if connection is None:
        return []

    try:
        year = int(year)
        cursor = connection.cursor(dictionary=True)
        if category:
            cursor.execute("""
            SELECT id, description, amount, expense_date, created_at
            FROM expenses
            WHERE month_id = %s AND category = %s AND year = %s
            ORDER BY expense_date DESC
            """, (month_id, category, year))
        else:
            cursor.execute("""
            SELECT id, category, description, amount, expense_date, created_at
            FROM expenses
            WHERE month_id = %s AND year = %s
            ORDER BY category, expense_date DESC
            """, (month_id, year))

        return cursor.fetchall()

    except Error as e:
        print(f"Error fetching expenses: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_expense(expense_id):
    """Delete an expense by ID."""
    connection = create_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        connection.commit()
        return cursor.rowcount > 0
        
    except Error as e:
        print(f"Error deleting expense: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_annual_budget(year=2026):
    """Get budget data for all months in a specific year."""
    connection = create_connection()
    if connection is None:
        return None

    try:
        year = int(year)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
        SELECT
            m.month_name,
            m.month_number,
            b.category,
            CAST(COALESCE(b.budgeted, 0) AS DECIMAL(10,2)) as budgeted,
            CAST(COALESCE(b.actual, 0) AS DECIMAL(10,2)) as actual
        FROM months m
        LEFT JOIN budget b ON m.id = b.month_id AND b.year = %s
        ORDER BY m.month_number, b.category
        """, (year,))

        # Convert Decimal to float for consistency
        result = []
        for row in cursor.fetchall():
            row['budgeted'] = float(row['budgeted'])
            row['actual'] = float(row['actual'])
            result.append(row)

        return result

    except Error as e:
        print(f"Error fetching annual budget data: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_available_years():
    """Get list of years that have budget data."""
    connection = create_connection()
    if connection is None:
        return [2026]

    try:
        cursor = connection.cursor()
        cursor.execute("""
        SELECT DISTINCT year FROM budget
        UNION
        SELECT DISTINCT year FROM expenses
        ORDER BY year DESC
        """)

        years = [row[0] for row in cursor.fetchall()]
        if not years:
            years = [2026]
        return years

    except Error as e:
        print(f"Error fetching years: {e}")
        return [2026]
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_years_range(start_year=2020, end_year=2030):
    """Get a range of years for the year selector."""
    return list(range(start_year, end_year + 1))
