# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx"
# ]
# ///

import httpx
import csv
import io

url = "https://tds-llm-analysis.s-anand.net/demo-audio-data.csv"
text = httpx.get(url).text

print("First 500 chars:")
print(text[:500])
print("\n" + "="*50)

# Try to parse as CSV
f = io.StringIO(text)
reader = csv.DictReader(f)
rows = list(reader)

print(f"Number of rows: {len(rows)}")
print(f"First row keys: {list(rows[0].keys())}")
print(f"First 3 rows: {rows[:3]}")

# Try summing
total = 0
for row in rows:
    first_key = list(row.keys())[0]
    val = row[first_key]
    print(f"Row value: {val}, type: {type(val)}")
    total += int(val)
    if total > 100000:  # Just check first few
        break

print(f"\nSum of first few: {total}")