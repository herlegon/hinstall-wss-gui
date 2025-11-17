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


