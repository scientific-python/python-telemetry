"""Python package analytics client"""
import requests
import uuid
import os
import platform

class AnalyticsClient:
    """
    Example usage:
    analytics = AnalyticsClient(
        proxy_url="https://your-project.up.railway.app"
    )

    analytics.track_event('package_imported', {
        'package_version': '1.0.0'
    })
    """
    def __init__(self, proxy_url):
        self.proxy_url = proxy_url
        self.client_id = str(uuid.uuid4())
        self.enabled = not self._is_disabled()
    
    def _is_disabled(self):
        if os.environ.get('DO_NOT_TRACK', '').lower() in ('1', 'true'):
            return True
        if os.environ.get('CI', '').lower() in ('1', 'true'):
            return True
        return False
    
    def track_event(self, event_name, params=None):
        if not self.enabled:
            return
        
        if params is None:
            params = {}
        
        params.update({
            'python_version': platform.python_version(),
            'os': platform.system(),
        })
        
        payload = {
            'client_id': self.client_id,
            'event_name': event_name,
            'params': params
        }
        
        try:
            requests.post(
                f"{self.proxy_url}/track",
                json=payload,
                timeout=2
            )
        except Exception:
            pass
