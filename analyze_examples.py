import json
from collections import Counter

with open('data/example.json', 'r') as f:
    data = json.load(f)

contents = [item.get('content') for item in data if item.get('content')]
null_contents = [item for item in data if not item.get('content')]

counter = Counter(contents)
duplicates = {k: v for k, v in counter.items() if v > 1}

print(f"Total items in JSON: {len(data)}")
print(f"Null/Empty contents: {len(null_contents)}")
print(f"Unique non-empty contents: {len(set(contents))}")
print(f"Total duplicates count (sum of occurrences - unique): {sum(duplicates.values()) - len(duplicates)}")
print(f"Example of duplicates:")
for k, v in list(duplicates.items())[:3]:
    print(f"  '{k}': {v} times")
