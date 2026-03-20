import os
import sys
import pathlib
from concurrent.futures import as_completed

import requests
from requests_futures.sessions import FuturesSession
from tqdm import tqdm


import time
import contextlib

@contextlib.contextmanager
def lock_file(file_path):
    if os.name == 'nt':  # Windows
        import msvcrt
        with open(file_path, 'r+') if os.path.exists(file_path) else open(file_path, 'w+') as f:
            while True:
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    yield f
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    break
                except IOError:
                    time.sleep(0.1)
    else:  # Linux/Unix
        import fcntl
        with open(file_path, 'r+') if os.path.exists(file_path) else open(file_path, 'w+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                yield f
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

def get_working_proxies(refresh: bool = False):

    if pathlib.Path("proxies.txt").exists() and not refresh:
        with open("proxies.txt") as f:
            proxy_urls = [None] + f.read().splitlines()

        return proxy_urls

    proxies = []

    print("No proxies found, fetching proxies from api.proxyscrape.com...")
    r = requests.get("https://api.proxyscrape.com/?request=getproxies&proxytype=https&timeout=10000&country=all&ssl=all&anonymity=all")
    proxies += r.text.splitlines()
    r = requests.get("https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000&country=all&ssl=all&anonymity=all")
    proxies += r.text.splitlines()
    working_proxies = []
    print(f"Checking {len(proxies)} proxies...")

    session = FuturesSession(max_workers=100)
    futures = []
    
    for proxy in proxies:
        future = session.get('https://api.myip.com', proxies={'https': f'http://{proxy}'}, timeout=5)
        future.proxy = proxy
        futures.append(future)

    for future in tqdm(as_completed(futures), total=len(futures)):#, disable=True):
        try:
            future.result()
            working_proxies.append(future.proxy)
        except KeyboardInterrupt:
            sys.exit()
        except:
            continue

    with open("proxies.txt", "w") as f:
        f.write("\n".join(working_proxies))

    os.system("cls")

    return [None] + working_proxies
