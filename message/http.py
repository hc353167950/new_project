from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def make_session(retries: int = 3, backoff: float = 0.3, status_forcelist=(500, 502, 504)) -> Session:
    """
    Create a requests.Session with a built-in retry strategy.
    """
    session = Session()
    retry = Retry(total=retries, backoff_factor=backoff, status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session