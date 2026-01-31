import requests
import json
import urllib.parse

def check_jisho(word):
    url = f"https://jisho.org/api/v1/search/words?keyword={urllib.parse.quote(word)}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                first_match = data['data'][0]
                print(f"Word: {word}")
                print(f"JLPT: {first_match.get('jlpt')}")
                print(f"Is common: {first_match.get('is_common')}")
            else:
                print("No data found")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

check_jisho("私")
check_jisho("食べる")
