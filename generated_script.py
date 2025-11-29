import re
import httpx
from data_tools import read_csv_from_url, clean_text_block

# Original request data
email = "test@mail.com"
secret = "something_random_12345"
url = "https://tds-llm-analysis.s-anand.net/demo"

# Quiz instructions
cutoff_value = 21217
print(f"Cutoff value: {cutoff_value}")

# File URLs detected on the page
csv_url = "https://tds-llm-analysis.s-anand.net/demo-audio-data.csv"
print(f"Fetching CSV data from: {csv_url}")

# Read the CSV data as plain text
response = httpx.get(csv_url)
csv_data = response.text
print(f"CSV data length: {len(csv_data)}")

# Initialize total
total = 0

# Process CSV data
for line in csv_data.strip().split('\n'):
    if line.strip():
        number = int(line.strip())
        # Apply cutoff filter
        if number >= cutoff_value:
            total += number

print(f"Computed total from CSV: {total}")

# Final answer
answer = total
print("FINAL_ANSWER:", answer)