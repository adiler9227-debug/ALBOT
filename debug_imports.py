import sys
import os
import asyncio

sys.path.append(os.getcwd())

print("Attempting to import bot.handlers.menu...")
try:
    from bot.handlers import menu
    print("SUCCESS: bot.handlers.menu imported")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("Attempting to import bot.handlers.subscription...")
try:
    from bot.handlers import subscription
    print("SUCCESS: bot.handlers.subscription imported")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("Attempting to import bot.keyboards.inline...")
try:
    from bot.keyboards import inline
    print("SUCCESS: bot.keyboards.inline imported")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
