from sqlalchemy import text

from app.database import SessionLocal


def test_database_connection():
    db = SessionLocal()

    try:
        result = db.execute(text("SELECT DATABASE()")).scalar()
        print("Connected database:", result)

        tables = db.execute(text("SHOW TABLES")).fetchall()

        print("\nAvailable tables:")

        for table in tables:
            print("-", table[0])

        print("\nDatabase test completed successfully.")

    except Exception as error:
        print("Database test failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    test_database_connection()