import sqlite3
import os


DATABASE_PATH = os.path.join(
    os.path.dirname(__file__),
    "smartplot.db"
)


def create_database():
    """
    Create all SmartPlot database tables.
    """

    os.makedirs(
        os.path.dirname(DATABASE_PATH),
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_PATH)

    # ---------------- USERS TABLE ----------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # ---------------- PLOTS TABLE ----------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS plots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            area REAL NOT NULL,
            price REAL NOT NULL,
            road_width REAL NOT NULL,
            property_type TEXT NOT NULL,
            facing TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'available',

            FOREIGN KEY (owner_id)
                REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":

    create_database()

    print("SmartPlot database is ready.")