# K2S Downloader

A multi-threaded downloader for k2s.cc and keep2share.cc with proxy support and automatic captcha handling.

## Features
- **Multi-threaded downloading**: Splits files into chunks for faster downloads.
- **Tail-End Speedup**: Automatically re-assigns the last few remaining chunks to multiple idle threads to eliminate slow-proxy bottlenecks at the end of the download.
- **Proxy Rotation**: Automatically fetches and uses proxies from `api.proxyscrape.com` if `proxies.txt` is missing.
- **Robust Captcha Handling**: Rotates through domains and proxies to fetch captcha challenges. Includes validation to prevent crashes from invalid captcha image responses.
- **Corruption Check**: Uses `ffmpeg` to verify downloaded video files.
- **Resume Support**: Checks for existing `.part` files in the `tmp/` directory.
- **Concurrent Instance Support**: Uses per-file URL caches in `tmp/`, allowing multiple instances to run safely in parallel.

## Environment
- Python 3.10+ (Tested on Linux and Windows)
- `ffmpeg` must be in your system's PATH for corruption checking.

## Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd k2s-downloader
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Basic usage:
```bash
python main.py "https://k2s.cc/file/..." --filename "video.mp4"
```

Advanced options:
```bash
python main.py "https://keep2share.cc/file/..." \
    --filename "video.mp4" \
    --threads 20 \
    --split-size 50mb
```

### Parameters:
- `url`: The k2s.cc or keep2share.cc file URL.
- `--filename`: (Optional) Name to save the file as. If omitted, it will try to fetch the name from the API.
- `--threads`: (Default: 20) Number of concurrent connections to use.
- `--split-size`: (Default: 20mb) Size of each chunk. Minimum 20MB recommended.

## Development Branch
The **`dev`** branch contains the latest features, including the Tail-End Speedup and improved Captcha stability fixes. It is recommended to use the `dev` branch for the most up-to-date and resilient version of the downloader.

## Proxies
The script uses `proxies.txt` if available. If not, it will automatically fetch a list of working proxies. You can manually add your own proxies to `proxies.txt` (one per line, format: `ip:port`).

## Notes
- **Concurrent Downloads**: You can run multiple instances of the script for different files. Make sure to use unique `--filename` values for each.
- **API Errors**: If you encounter a `522` or `JSONDecodeError`, the script will automatically retry using different proxies and domains (`k2s.cc` vs `keep2share.cc`).
- **Captcha**: Captcha response is required for free users. The script will display the captcha image and prompt for input.
