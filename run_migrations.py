import alembic.config
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

def run_migrations():
    print("Running migrations...")
    try:
        alembicArgs = [
            '--raiseerr',
            'upgrade', 'head',
        ]
        alembic.config.main(argv=alembicArgs)
        print("Migrations applied successfully!")
    except Exception as e:
        print(f"Error running migrations: {e}")

if __name__ == "__main__":
    run_migrations()
