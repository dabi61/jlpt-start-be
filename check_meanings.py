import json
from collections import defaultdict

with open('data/example.json', 'r') as f:
    data = json.load(f)

d = defaultdict(list)
for item in data:
    content = item.get('content')
    if content:
        d[content].append(item.get('mean'))

diff_mean = 0
for content, meanings in d.items():
    if len(set(meanings)) > 1:
        diff_mean += 1

print(f"Total unique contents: {len(d)}")
print(f"Contents with multiple distinct meanings: {diff_mean}")
