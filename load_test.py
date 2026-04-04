import concurrent.futures
import requests
import uuid
import argparse
import time

API_BASE = "http://127.0.0.1:5050"

def create_event(tickets):
    res = requests.post(
        f"{API_BASE}/admin/event", 
        json={"name": f"FlashSale_{uuid.uuid4()}", "total_tickets": tickets}
    )
    return res.json()["id"]

def reserve_ticket(event_id, user_id):
    for attempt in range(3):
        try:
            res = requests.post(f"{API_BASE}/reserve", json={
                "event_id": event_id,
                "user_email": f"user{user_id}_{uuid.uuid4().hex[:6]}@test.com"
            }, timeout=10)
            return res.status_code
        except (requests.ConnectionError, requests.Timeout):
            if attempt < 2:
                time.sleep(1)
    return 503  # treat connection failures as service unavailable

def run_load_test(tickets=100, users=150, workers=100):
    try:
        event_id = create_event(tickets)
    except Exception as e:
        print(f"Error: Ensure the API is running! ({e})")
        return

    print(f"Created Event {event_id} with {tickets} tickets.")
    print(f"Launching {users} concurrent users ({workers} threads)...")
    
    successes = 0
    failures = 0
    errors = 0
    start = time.perf_counter()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(reserve_ticket, event_id, i) for i in range(users)]
        for future in concurrent.futures.as_completed(futures):
            status = future.result()
            if status == 201:
                successes += 1
            elif status == 503:
                errors += 1
            else:
                failures += 1

    elapsed = time.perf_counter() - start
    rps = users / elapsed if elapsed > 0 else 0

    print("-" * 40)
    print(f"Completed in {elapsed:.2f}s ({rps:.0f} req/s)")
    print(f"Expected limit: {tickets} tickets")
    print(f"Total sold:     {successes}")
    print(f"Total blocked:  {failures}")
    if errors:
        print(f"Total errors:   {errors} (connection failures)")
    if successes > tickets:
        print("💥 FAIL: OVERSELLING DETECTED! Race condition exploited.")
    elif successes == tickets:
        print("✅ PASS: API maintained integrity under load.")
    else:
        print(f"⚠️  Sold {successes}/{tickets} (some may have timed out)")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flash Sale Load Tester")
    parser.add_argument("-t", "--tickets", type=int, default=100, help="Number of tickets")
    parser.add_argument("-u", "--users", type=int, default=150, help="Number of concurrent users")
    parser.add_argument("-w", "--workers", type=int, default=100, help="Thread pool size")
    args = parser.parse_args()
    run_load_test(args.tickets, args.users, args.workers)
