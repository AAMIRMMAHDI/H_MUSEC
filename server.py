import asyncio
import websockets

clients = set()

async def handler(websocket):
    clients.add(websocket)
    try:
        async for data in websocket:
            for client in clients:
                if client != websocket:
                    await client.send(data)
    except:
        pass
    finally:
        clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 10000):
        print("✅ WebSocket server is running...")
        await asyncio.Future()

asyncio.run(main())
