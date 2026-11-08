from sqlalchemy import text

from app.database import SessionLocal


def get_machine_downtimes():
    db = SessionLocal()

    try:
        query = text("""
            SELECT
                m.machine_code,
                m.machine_name,
                md.reason,
                md.start_time,
                md.end_time,
                md.status
            FROM machine_downtimes md
            JOIN machines m
                ON md.machine_id = m.id
            ORDER BY md.start_time
        """)

        downtimes = db.execute(query).fetchall()

        print("\nMACHINE DOWNTIME RECORDS")
        print("=" * 65)

        for downtime in downtimes:
            print(f"\nMachine    : {downtime.machine_code}")
            print(f"Name       : {downtime.machine_name}")
            print(f"Reason     : {downtime.reason}")
            print(f"Start      : {downtime.start_time}")
            print(f"End        : {downtime.end_time}")
            print(f"Status     : {downtime.status}")
            print("-" * 45)

        print("\nTotal downtime records:", len(downtimes))

    except Exception as error:
        print("Error reading downtime records:", error)

    finally:
        db.close()


if __name__ == "__main__":
    get_machine_downtimes()