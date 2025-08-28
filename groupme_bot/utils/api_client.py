"""
Resilient GroupMe API client with retries, timeouts, and structured logging.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class GroupMeConfig:
    """Configuration for GroupMe API client."""
    api_key: str
    base_url: str = "https://api.groupme.com/v3"
    timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 0.3


class GroupMeAPIClient:
    """Resilient GroupMe API client with automatic retries and error handling."""
    
    def __init__(self, config: GroupMeConfig):
        self.config = config
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "DELETE"],
            backoff_factor=self.config.backoff_factor,
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """Make a resilient API request with logging."""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        # Add API key to params
        if params is None:
            params = {}
        params["token"] = self.config.api_key
        
        # Set default headers
        headers = kwargs.get("headers", {})
        headers.setdefault("Content-Type", "application/json")
        kwargs["headers"] = headers
        
        logger.info(
            "Making API request",
            extra={
                "method": method,
                "url": url,
                "endpoint": endpoint,
                "has_data": json_data is not None,
            }
        )
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.config.timeout,
                **kwargs
            )
            
            response.raise_for_status()
            
            logger.info(
                "API request successful",
                extra={
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                }
            )
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(
                "API request failed",
                extra={
                    "method": method,
                    "endpoint": endpoint,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            raise
    
    def get_groups(self) -> List[Dict[str, Any]]:
        """Get all groups for the authenticated user."""
        response = self._make_request("GET", "groups")
        data = response.json()
        return data.get("response", [])
    
    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific group."""
        try:
            response = self._make_request("GET", f"groups/{group_id}")
            data = response.json()
            return data.get("response")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Group {group_id} not found")
                return None
            raise
    
    def get_messages(
        self, 
        group_id: str, 
        limit: int = 100, 
        before_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from a group with pagination."""
        params = {"limit": limit}
        if before_id:
            params["before_id"] = before_id
        
        response = self._make_request("GET", f"groups/{group_id}/messages", params=params)
        data = response.json()
        return data.get("response", {}).get("messages", [])
    
    def send_message(self, group_id: str, text: str, source_guid: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to a group."""
        payload = {
            "message": {
                "text": text,
            }
        }
        
        if source_guid:
            payload["message"]["source_guid"] = source_guid
        
        response = self._make_request("POST", f"groups/{group_id}/messages", json_data=payload)
        return response.json()
    
    def delete_message(self, group_id: str, message_id: str) -> bool:
        """Delete a message from a group."""
        try:
            response = self._make_request(
                "DELETE", 
                f"conversations/{group_id}/messages/{message_id}",
                headers={"Accept": "application/json, text/plain, */*"}
            )
            return response.status_code == 204
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Message {message_id} not found or already deleted")
                return False
            raise


def create_api_client(api_key: Optional[str] = None) -> GroupMeAPIClient:
    """Create a GroupMe API client with configuration from environment."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if api_key is None:
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError("API_KEY environment variable is required")
    
    config = GroupMeConfig(api_key=api_key)
    return GroupMeAPIClient(config)
