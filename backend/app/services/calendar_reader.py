from sqlalchemy import text

from app.database import SessionLocal


def get_machine_calendars():
    db = SessionLocal()

    try:
        query = text("""
            SELECT
                m.machine_code,
                m.machine_name,
                mc.shift_name,
                mc.start_time,
                mc.end_time,
                mc.is_working_day
            FROM machine_calendars mc
            JOIN machines m
                ON mc.machine_id = m.id
            ORDER BY m.machine_code
        """)

        calendars = db.execute(query).fetchall()

        print("\nMACHINE WORKING CALENDARS")
        print("=" * 65)

        for calendar in calendars:
            working_status = (
                "Working day" if calendar.is_working_day else "Non-working day"
            )

            print(f"\nMachine     : {calendar.machine_code}")
            print(f"Name        : {calendar.machine_name}")
            print(f"Shift       : {calendar.shift_name}")
            print(f"Start time  : {calendar.start_time}")
            print(f"End time    : {calendar.end_time}")
            print(f"Status      : {working_status}")
            print("-" * 45)

        print("\nTotal calendar records:", len(calendars))

    except Exception as error:
        print("Error reading machine calendars:", error)

    finally:
        db.close()


if __name__ == "__main__":
    get_machine_calendars()