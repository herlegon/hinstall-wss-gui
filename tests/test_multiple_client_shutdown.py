
import asyncio
import websockets
import json
import time

async def trigger_worker_and_disconnect():
    uri = "ws://127.0.0.1:49990"
    try:
        async with websockets.connect(uri) as websocket:
            print("[Client A] Connected")
            # Trigger install worker
            msg = {"cmd": "install", "payload": {"cfg": "{}"}}
            print(f"[Client A] Sending install command")
            await websocket.send(json.dumps(msg))

            # Wait a bit for worker to start
            await asyncio.sleep(2)
            print("[Client A] Disconnecting abruptly (simulating hinstall kill)")
            # Exiting block closes socket
    except Exception as e:
        print(f"[Client A] Error: {e}")

async def try_shutdown():
    uri = "ws://127.0.0.1:49990"
    print("[Client B] Connecting to send shutdown...")
    try:
        async with websockets.connect(uri) as websocket:
            print("[Client B] Connected")
            msg = {"cmd": "shutdown"}
            print(f"[Client B] Sending shutdown")
            await websocket.send(json.dumps(msg))

            try:
                await websocket.wait_closed()
                print("[Client B] Connection closed by server")
            except Exception as e:
                print(f"[Client B] Wait closed exception: {e}")
    except Exception as e:
        print(f"[Client B] Error: {e}")

async def main():
    # 1. Start server (assumed running or start it)
    # We assume 'python a:\hwss\wss.py' is running in background

    # 2. Trigger worker and disconnect
    await trigger_worker_and_disconnect()

    print("Waiting 2 seconds...")
    await asyncio.sleep(2)

    # 3. Try to shutdown
    await try_shutdown()

if __name__ == "__main__":
    asyncio.run(main())
