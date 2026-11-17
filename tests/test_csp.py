from csp_router import assign_moderator

MODERATORS = [
    {"id": "mod_1", "name": "Aarav Sharma", "role": "Junior", "languages": ["English", "Hindi"], "active_load": 1, "max_capacity": 5},
    {"id": "mod_2", "name": "Priya Kulkarni", "role": "Senior", "languages": ["English", "Hindi", "Marathi"], "active_load": 3, "max_capacity": 5},
    {"id": "mod_3", "name": "Rohan Deshmukh", "role": "Junior", "languages": ["Marathi"], "active_load": 5, "max_capacity": 5},
    {"id": "mod_4", "name": "Ananya Iyer", "role": "Senior", "languages": ["English"], "active_load": 0, "max_capacity": 5},
    {"id": "mod_5", "name": "Vikram Patil", "role": "Senior", "languages": ["Marathi", "Hindi"], "active_load": 4, "max_capacity": 5},
    {"id": "mod_6", "name": "Neha Verma", "role": "Junior", "languages": ["English", "Hindi"], "active_load": 2, "max_capacity": 5},
    {"id": "mod_7", "name": "Siddharth Joshi", "role": "Junior", "languages": ["Hindi", "Marathi"], "active_load": 1, "max_capacity": 5},
    {"id": "mod_8", "name": "Kavita Rao", "role": "Senior", "languages": ["English", "Hindi", "Marathi"], "active_load": 5, "max_capacity": 5}
]

# Run Test Cases
print("\n--- RUNNING CSP ROUTER TESTS ---\n")

print("--- TEST 1: Severe Marathi Tweet ---")
result_1 = assign_moderator("tweet_101", "Marathi", "Severe", MODERATORS)
print(f"Status: {result_1['status']}")
print(f"Assigned To: {result_1['moderator_name']}")
print(f"Reason: {result_1['decision_reason']}\n")

print("--- TEST 2: Mild Hindi Tweet ---")
result_2 = assign_moderator("tweet_102", "Hindi", "Mild", MODERATORS)
print(f"Status: {result_2['status']}")
print(f"Assigned To: {result_2['moderator_name']}")
print(f"Reason: {result_2['decision_reason']}\n")

print("--- TEST 3: Severe English Tweet ---")
result_3 = assign_moderator("tweet_103", "English", "Severe", MODERATORS)
print(f"Status: {result_3['status']}")
print(f"Assigned To: {result_3['moderator_name']}")
print(f"Reason: {result_3['decision_reason']}\n")

from csp_router import PriorityBufferQueue

print("--- TEST 4: Priority Buffer Queue Test ---")
queue = PriorityBufferQueue()

# Simulate incoming tweets when all moderators are busy
queue.push({"id": "tweet_104", "severity": "Mild", "language": "English"})
queue.push({"id": "tweet_105", "severity": "Severe", "language": "Marathi"})
queue.push({"id": "tweet_106", "severity": "Moderate", "language": "Hindi"})

print(f"Total tweets in queue: {queue.get_queue_length()}")

# Pop highest priority item (Should be Severe tweet_105)
next_tweet = queue.pop()
print(f"Highest priority tweet dequeued first: {next_tweet['id']} (Severity: {next_tweet['severity']})")