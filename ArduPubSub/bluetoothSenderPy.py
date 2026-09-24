import asyncio
from bleak import BleakScanner

async def main():
    dispositivi = await BleakScanner.discover()
    for d in dispositivi:
        print(d)
asyncio.run(main())