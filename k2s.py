import sys
import time
import requests
import contextlib
from io import BytesIO
from random import choice
from concurrent.futures import as_completed

from PIL import Image
from tqdm import tqdm
from requests_futures.sessions import FuturesSession

from utils import get_working_proxies

DOMAINS = [
    "keep2share.cc",
    "k2s.cc",
]

def generate_from_key(url: str, key: str, proxy: str) -> str:

    if proxy:
        prox = {'https': f'http://{proxy}'}
    else:
        prox = None
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"}
    while True:
        try:
            r = requests.post(f"https://{choice(DOMAINS)}/api/v2/getUrl", json={
                "file_id": url,
                "free_download_key": key
            }, proxies=prox, headers=headers, timeout=10)
            data = r.json()
            if data.get('status') == 'success' and 'url' in data:
                return data['url']
            elif data.get('status') == 'error':
                print(f"Error in generate_from_key: {data.get('message')}")
                # If it's a permanent error, we might want to break or return None
                if data.get('message') == 'File not found':
                    return None
                time.sleep(1)
        except Exception as e:
            time.sleep(1)
            continue

def generate_download_urls(file_id: str, count: int = 1, skip: int = 0) -> list:

    if skip > 0:
        proxy_urls = get_working_proxies()[skip:]
    else:
        proxy_urls = get_working_proxies()
    working_link = False
    free_download_key = ""
    urls = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
    
    captcha = None
    max_retries = 15
    prox = None
    
    # Try multiple domains and proxies for captcha
    for attempt in range(max_retries):
        domain = choice(DOMAINS)
        prox = None
        p_info = "LOCAL"
        if proxy_urls:
            p = choice(proxy_urls)
            if p:
                prox = {'https': f'http://{p}'}
                p_info = p

        print(f"\033[KRequesting captcha from {domain} using {p_info}... (Attempt {attempt+1}/{max_retries})", end='\r')
        
        try:
            r = requests.post(f"https://{domain}/api/v2/requestCaptcha", headers=headers, proxies=prox, timeout=10)
            if r.status_code == 200:
                captcha = r.json()
                if captcha.get('status') == 'success':
                    break
        except Exception:
            continue
            
    if not captcha:
        print("\nFailed to get captcha after multiple attempts.")
        sys.exit(1)
    
    print(f"\nGot captcha challenge: {captcha['challenge']}")
    
    # Get captcha image with the same proxy used to request it
    try:
        r = requests.get(captcha["captcha_url"], headers=headers, proxies=prox, timeout=10)
        if r.status_code != 200 or 'image' not in r.headers.get('Content-Type', '').lower():
            print(f"\nError: Captcha image could not be loaded (Status: {r.status_code}). Try running again.")
            sys.exit(1)
            
        im = Image.open(BytesIO(r.content))
        im.show()
    except Exception as e:
        print(f"Failed to download or show captcha image: {e}")
        sys.exit(1)

    response = input(f"Enter captcha response: ")

    for url in proxy_urls:
        print(f"\033[KTrying {url}", end='\r')
        prox = {'https': f'http://{url}'}
        if not url:
            prox = None
        while not working_link:
            try:
                r = requests.post(f"https://{choice(DOMAINS)}/api/v2/getUrl", json={
                    "file_id": file_id,
                    "captcha_challenge": captcha["challenge"],
                    "captcha_response": response
                }, proxies=prox, headers=headers, timeout=10)
                free_r = r.json()
            except KeyboardInterrupt:
                sys.exit()
            except Exception:
                break

            if free_r['status'] == "error":
                if free_r["message"] == "Invalid captcha code":
                    r = requests.get(captcha["captcha_url"], headers=headers, proxies=prox, timeout=10)
                    im = Image.open(BytesIO(r.content))
                    im.show()
                    response = input(f"Enter captcha response: ")
                    continue
                elif free_r["message"] == "File not found":
                    sys.exit("File not found")

            if "time_wait" not in free_r:
                working_link = True
                break

            if free_r['time_wait'] > 30:
                break

            for i in range(free_r['time_wait'] - 1):
                print(f"\033[K[{url}] Waiting {free_r['time_wait'] - i} seconds...", end='\r')
                time.sleep(1)
            
            free_download_key = free_r['free_download_key']
            working_link = True

        if working_link:

            session = FuturesSession(max_workers=5)
            futures = []

            # Generate links
            while len(urls) < count:
                futures = []
                to_generate = count - len(urls)
                for _ in range(to_generate):
                    future = session.post(f"https://{choice(DOMAINS)}/api/v2/getUrl", json={
                        "file_id": file_id,
                        "free_download_key": free_download_key
                    }, proxies=prox)
                    futures.append(future)

                for future in tqdm(as_completed(futures), total=len(futures), leave=False):
                    try:
                        result = future.result()
                        urls.append(result.json()['url'])
                    except KeyboardInterrupt:
                        sys.exit()
                    except:
                        continue

    if not working_link:
        raise Exception("No working links found")

    return urls[:count]

def get_name(file_id: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"}
    r = requests.post(f"https://{choice(DOMAINS)}/api/v2/getFilesInfo", json={
        "ids": [file_id]
    }, headers=headers)
    try:
        data = r.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Error: getFilesInfo returned non-JSON from {r.url}")
        print(f"Status Code: {r.status_code}")
        sys.exit(1)
    
    if data.get('status') == 'error':
        print(f"Error getting file info: {data.get('message')}")
        sys.exit(1)

    return data['files'][0]['name']