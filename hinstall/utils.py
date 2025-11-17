from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse

PLATFORMS: tuple[str] = ('win32', 'linux', 'darwin')


def get_domain_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    # Extract the netloc (domain) part and remove the "www." prefix if present
    domain = parsed_url.netloc
    if domain.startswith("www."):
        domain = domain[4:]  # Remove the "www." prefix
    return domain



def check_site_reachable(url: str, max_retries: int = 3):
    """Check if site is reachable with retries"""
    for attempt in range(max_retries):
        try:
            # Ensure the URL includes the scheme (https://)
            if not url.startswith('http'):
                url = 'https://' + url

            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            urlopen(req, timeout=1)
            return True

        except (URLError, HTTPError) as e:
            ilog.debug(f"{url} is not reachable, retry {attempt} - {e}")
            if attempt < max_retries - 1:
                continue
    return False



if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from logger import ilog
    ilog.setLevel("DEBUG")

    urls = [
        "https://www.github.com",
        "https://github.com/JepEtau/external_rehost/releases/download/external",
    ]
    for url in urls:
        domain = get_domain_from_url(url)
        reachable = check_site_reachable(url=domain)
        if not reachable:
            ilog.error(f"{domain} is not reachable")
        else:
            ilog.info(f"{domain} is alive")
