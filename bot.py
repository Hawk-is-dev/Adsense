import asyncio
import random
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl import functions
import socks
from keepalive import keep_alive

# --- CONFIGURATIONS ---
API_ID = int(os.getenv("API_ID", 12345678))
API_HASH = os.getenv("API_HASH", "your_api_hash_here")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "your_target_channel")

# Batch & Timing Settings (60-minute cycle distribution)
BATCH_SIZE = 5
BATCH_TIME_WINDOW = 3600.0


async def worker_task(session_string, proxy_str):
    client = None
    try:
        # FlameProxies format parsing (host:port:username_with_params)
        parts = proxy_str.strip().split(':')
        host = parts[0]
        port = int(parts[1])
        username = ':'.join(parts[2:])
        password = None

        proxy = (
            socks.SOCKS5,
            host,
            port,
            True,
            username,
            password
        )

        client = TelegramClient(
            StringSession(session_string.strip()),
            API_ID,
            API_HASH,
            proxy=proxy
        )

        await client.connect()

        if not await client.is_user_authorized():
            print("[-] Session unauthorized or expired!")
            await client.disconnect()
            return

        print(f"[+] Connected via Proxy ({host}) successfully.")

        # Human-like jitter before action
        await asyncio.sleep(random.uniform(5.0, 15.0))

        channel = await client.get_entity(CHANNEL_USERNAME)

        # 1. Normal Posts View & Seen Logic
        posts = await client.get_messages(channel, limit=3)
        if posts:
            post_ids = [post.id for post in posts]
            await client.read_messages(channel, post_ids)
            print(f"[✓] Viewed and marked {len(posts)} channel posts as SEEN.")

        await asyncio.sleep(random.uniform(2.0, 5.0))

        # 2. Sponsored Ads Impression Logic
        try:
            sponsored_ads = await client(functions.messages.GetSponsoredMessagesRequest(
                peer=channel
            ))

            if sponsored_ads and hasattr(sponsored_ads, 'messages') and sponsored_ads.messages:
                print(f"[+] Found {len(sponsored_ads.messages)} sponsored ad(s). Triggering impressions...")
                for ad in sponsored_ads.messages:
                    if hasattr(ad, 'random_id'):
                        await client(functions.messages.ViewSponsoredMessageRequest(
                            random_id=ad.random_id
                        ))
                        print("[✓] Ad impression registered.")
            else:
                print("[i] No active sponsored ads on this channel right now.")

        except Exception as ad_err:
            print(f"[!] Sponsored ad check note: {ad_err}")

        await asyncio.sleep(random.uniform(5.0, 10.0))
        await client.disconnect()
        print("[x] Disconnected safely.")

    except Exception as e:
        print(f"[!] Error in session: {e}")
        if client and client.is_connected():
            await client.disconnect()


async def automation_loop():
    while True:
        if not os.path.exists('accounts.txt'):
            print("[!] Error: 'accounts.txt' file not found!")
            await asyncio.sleep(60)
            continue

        with open('accounts.txt', 'r') as f:
            lines = [line.strip() for line in f if '|' in line and not line.startswith('#')]

        if not lines:
            print("[!] Error: 'accounts.txt' has no valid entries.")
            await asyncio.sleep(60)
            continue

        account_data = [line.split('|', 1) for line in lines]
        total_accounts = len(account_data)
        print(f"\n[*] Starting 60-minute rotation cycle for {total_accounts} accounts...")

        total_batches = (total_accounts + BATCH_SIZE - 1) // BATCH_SIZE
        time_slot_per_batch = BATCH_TIME_WINDOW / max(total_batches, 1)

        for i in range(0, total_accounts, BATCH_SIZE):
            batch = account_data[i:i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            print(f"\n--- Running Batch {batch_num}/{total_batches} ({len(batch)} accounts) ---")

            tasks = []
            for sess_str, pxy in batch:
                await asyncio.sleep(random.uniform(2.0, 10.0))
                tasks.append(worker_task(sess_str, pxy))

            await asyncio.gather(*tasks)

            if i + BATCH_SIZE < total_accounts:
                print(f"[~] Batch {batch_num} done. Waiting {time_slot_per_batch:.1f}s for next batch...")
                await asyncio.sleep(time_slot_per_batch)

        print("\n[+] 60-minute cycle completed. Sleeping briefly before next cycle...")
        await asyncio.sleep(random.uniform(30.0, 60.0))


if __name__ == '__main__':
    keep_alive()
    print("[*] Keep-Alive HTTP server started.")
    asyncio.run(automation_loop())
