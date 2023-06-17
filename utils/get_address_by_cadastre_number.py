import requests
import re
import random
import string

def get_page_by_cadastral_number(cadastral_number: str) -> str:
    url = f"https://egrp365.org/list5.php?id={cadastral_number}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    print(url)
    response = requests.get(url, headers=headers, timeout=100)
    print(response.status_code)
    if response.status_code == 200:
        return response.text
    else:
        return None

def extract_address(page_content: str) -> str:
    pattern = r"<div class='rs_address'><a rel='nofollow' href='/reestr\?egrp=[^>]*?>(.*?)<\/a>"
    match = re.search(pattern, page_content)
    if match:
        address = match.group(1)
        return address
    else:
        return None

def get_random_string(length: int) -> str:
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length))

def get_address_by_cadastre_number(cadastre_number: str) -> str:
    page_content = get_page_by_cadastral_number(cadastre_number)
    if page_content:
        address = extract_address(page_content)
        if address:
            return address
    return 'Неверный кадастровый номер'