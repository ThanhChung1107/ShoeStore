import requests
from requests.adapters import HTTPAdapter, Retry
from django.conf import settings

class AddressResolver:
    def __init__(self, base_url=None, endpoint=None, token=None, timeout=8):
        self.base_url = (base_url or settings.EXTERNAL_API_BASE_URL or '').rstrip('/')
        self.endpoint = endpoint or settings.EXTERNAL_ADDRESS_ENDPOINT or ''
        self.timeout = timeout
        self.session = requests.Session()
        retries = Retry(total=2, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        headers = {}
        token = token or settings.EXTERNAL_API_TOKEN
        if token:
            headers['Authorization'] = f'Bearer {token}'
        self.session.headers.update(headers)

    def resolve(self, query: str) -> dict | None:
        """Resolve a free-text address query using external API.
        Expected to return a dict with standardized fields.
        Returns None if not configured or fails.
        """
        if not self.base_url or not self.endpoint:
            return None
        url = f"{self.base_url}{self.endpoint}"
        try:
            resp = self.session.get(url, params={'q': query}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            # Normalize typical shapes
            if isinstance(data, dict) and data.get('address'):
                return data['address']
            if isinstance(data, dict):
                return data
            return None
        except Exception:
            return None
