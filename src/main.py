import asyncio
import time


async def one():
    print("Start 1")
    await asyncio.sleep(1)
    print("Finish 1")

async def two():
    print("Start 2")
    # await asyncio.sleep(2)
    time.sleep(5)
    print("Finish 2")

async def three():
    print("Start 3")
    await asyncio.sleep(3)
    print("Finish 3")

async def main():
    await asyncio.gather(one(), three(), two())

if __name__ == '__main__':
    start = time.time()
    asyncio.run(main())
    print(time.time() - start)
