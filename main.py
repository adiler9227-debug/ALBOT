import asyncio
import sys
import os

# Add the current directory to sys.path to ensure 'bot' module is found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.__main__ import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped!")
