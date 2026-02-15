import json
from urllib.request import urlopen, Request
import ssl

def check():
    repo = "actexxat/net2000"
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    print(f"Checking URL: {url}")
    
    try:
        context = ssl._create_unverified_context()
        req = Request(url)
        req.add_header('User-Agent', 'Internet2000-AutoUpdater')
        
        with urlopen(req, context=context, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            print("Success!")
            print(f"Latest tag: {data.get('tag_name')}")
            print(f"Asset count: {len(data.get('assets', []))}")
            for asset in data.get('assets', []):
                print(f" - Asset: {asset['name']}")
    except Exception as e:
        print(f"Error: {e}")
        
    # Check all releases if latest fails
    url_all = f"https://api.github.com/repos/{repo}/releases"
    print(f"\nChecking all releases: {url_all}")
    try:
        req = Request(url_all)
        req.add_header('User-Agent', 'Internet2000-AutoUpdater')
        with urlopen(req, context=context, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            print(f"Found {len(data)} releases.")
            for rel in data:
                print(f" - Tag: {rel['tag_name']} (Draft: {rel['draft']}, Prerelease: {rel['prerelease']})")
    except Exception as e:
        print(f"Error checking all: {e}")

if __name__ == '__main__':
    check()
