import concurrent.futures
import requests
import uuid

API_BASE = "http://127.0.0.1:5001"

def create_event():
    res = requests.post(
        f"{API_BASE}/admin/event", 
        json={"name": f"FlashSale_{uuid.uuid4()}", "total_tickets": 100}
    )
    return res.json()["id"]

def reserve_ticket(event_id, user_id):
    res = requests.post(f"{API_BASE}/reserve", json={
        "event_id": event_id,
        "user_email": f"user{user_id}@test.com"
    })
    return res.status_code

def run_load_test():
    try:
        event_id = create_event()
    except Exception as e:
        print("Error: Ensure the API is running on port 5001!")
        return

    print(f"Created Event {event_id} with 100 tickets.")
    print("Initiating 150 concurrent users battling for 100 tickets...")
    
    successes = 0
    failures = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(reserve_ticket, event_id, i) for i in range(150)]
        for future in concurrent.futures.as_completed(futures):
            status = future.result()
            if status == 201:
                successes += 1
            else:
                failures += 1

    print("-" * 30)
    print(f"Expected limit: 100 tickets")
    print(f"Total magically sold: {successes}")
    print(f"Total safely blocked: {failures}")
    if successes > 100:
        print("💥 FAIL: OVERSELLING DETECTED! Race condition exploited.")
    elif successes == 100:
        print("✅ PASS: API maintained integrity under load.")
    else:
        print(f"API sold {successes} which is less than 100.")
        
if __name__ == "__main__":
    run_load_test()
