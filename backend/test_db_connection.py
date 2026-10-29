from sqlalchemy import text
from app.database import engine

print("Testing Supabase connection...")

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("SUCCESS:", result.scalar())

except Exception as error:
    print("CONNECTION FAILED")
    print("Error type:", type(error).__name__)
    print("Error details:", str(error))

finally:
    engine.dispose()