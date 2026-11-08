from sqlalchemy import text

from app.database import SessionLocal


def get_machines():
    db = SessionLocal()

    try:
        query = text("""
            SELECT
                machine_code,
                machine_name,
                machine_type,
                capacity_per_hour,
                is_active
            FROM machines
            WHERE is_active = 1
            ORDER BY machine_code
        """)

        machines = db.execute(query).fetchall()

        print("\nAVAILABLE MANUFACTURING MACHINES")
        print("=" * 65)

        for machine in machines:
            print(f"\nMachine Code   : {machine.machine_code}")
            print(f"Machine Name   : {machine.machine_name}")
            print(f"Machine Type   : {machine.machine_type}")
            print(f"Capacity/hour : {machine.capacity_per_hour} units")
            print("-" * 45)

        print("\nTotal active machines:", len(machines))

    except Exception as error:
        print("Error reading machines:", error)

    finally:
        db.close()


if __name__ == "__main__":
    get_machines()

