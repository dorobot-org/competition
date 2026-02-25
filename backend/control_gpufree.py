#!/usr/bin/env python3
"""
GPUFree Instance Manager
A modular library for managing GPU instances on gpufree.cn

Features:
- List instances
- Start instance
- Stop instance

Status Codes:
- 3: Running (on)
- 5: Stopped (off)
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# API Configuration
BASE_URL = "https://www.gpufree.cn/api/v1"

# Status constants
STATUS_RUNNING = 3  # Instance is running (on)
STATUS_STOPPED = 5  # Instance is stopped (off)


class GPUFreeClient:
    """Client for GPUFree API operations"""

    def __init__(self, bearer_token: Optional[str] = None, base_url: str = BASE_URL):
        self.base_url = base_url

        # Get bearer token from parameter or environment variable
        if bearer_token is None:
            bearer_token = os.environ.get("GPUFREE_BEARER_TOKEN")
            if not bearer_token:
                raise RuntimeError(
                    "GPUFREE_BEARER_TOKEN environment variable is required. "
                    "Obtain your bearer token from https://www.gpufree.cn"
                )

        # Validate and clean bearer token
        clean_token = bearer_token.strip()
        if not clean_token:
            raise ValueError("Bearer token cannot be empty")

        self.headers = {
            "accept": "application/json, text/plain, */*",
            "authorization": f"Bearer {clean_token}",
            "content-type": "application/json"
        }

    def list_instances(self, page_no: int = 1, page_size: int = 50,
                       status: str = "", nick_name: str = "") -> Optional[Dict]:
        """
        List all GPU instances

        Args:
            page_no: Page number (default: 1)
            page_size: Number of items per page (default: 50)
            status: Filter by status (optional)
            nick_name: Filter by nickname (optional)

        Returns:
            dict: API response data or None if failed
        """
        url = f"{self.base_url}/jupyter/list_instance_pages"
        params = {
            "page_no": page_no,
            "page_size": page_size,
            "status": status,
            "nick_name": nick_name
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error listing instances: {e}")
            return None

    def get_instance_by_uuid(self, uuid: str) -> Optional[Dict]:
        """
        Get instance details by UUID

        Args:
            uuid: Instance UUID

        Returns:
            dict: Instance data or None if not found
        """
        result = self.list_instances(page_no=1, page_size=50)
        if result and result.get("code") == 200:
            instances = result.get("data", {}).get("dataList", [])
            for instance in instances:
                if instance.get("webide_instance_uuid") == uuid:
                    return instance
        return None

    def get_instance_by_id(self, instance_id: int) -> Optional[Dict]:
        """
        Get instance details by instance ID

        Args:
            instance_id: Instance ID

        Returns:
            dict: Instance data or None if not found
        """
        result = self.list_instances(page_no=1, page_size=50)
        if result and result.get("code") == 200:
            instances = result.get("data", {}).get("dataList", [])
            for instance in instances:
                if instance.get("webide_instance_id") == instance_id:
                    return instance
        return None

    def get_instance_status(self, instance_id: int) -> Tuple[Optional[int], Optional[str]]:
        """
        Get the status of an instance by ID

        Args:
            instance_id: Instance ID

        Returns:
            Tuple[Optional[int], Optional[str]]: (status_code, jupyter_url) or (None, None) if not found
            Status codes: 3 = running, 5 = stopped
        """
        instance = self.get_instance_by_id(instance_id)
        if instance:
            return instance.get("status"), instance.get("jupyter_url")
        return None, None

    def _send_instance_action(self, instance_id: int, instance_uuid: str,
                               action: str, start_mode: str = "gpu") -> Optional[Dict]:
        """
        Send action (start/stop) to instance

        Args:
            instance_id: Instance ID
            instance_uuid: Instance UUID
            action: Action to perform ("start" or "stop")
            start_mode: Start mode (default: "gpu")

        Returns:
            dict: API response or None if failed
        """
        url = f"{self.base_url}/inferring-api/webide/"
        payload = {
            "instance_id": instance_id,
            "instance_uuid": instance_uuid,
            "start_mode": start_mode,
            "action": action
        }

        try:
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error {action} instance: {e}")
            return None

    def start_instance(self, instance_id: int, instance_uuid: str,
                       start_mode: str = "gpu") -> Tuple[bool, Optional[str]]:
        """
        Start a GPU instance

        Args:
            instance_id: Instance ID
            instance_uuid: Instance UUID
            start_mode: Start mode (default: "gpu")

        Returns:
            Tuple[bool, Optional[str]]: (success, timestamp or error_message)
        """
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{start_time}] Starting instance {instance_uuid} (ID: {instance_id})...")

        # Check current status first
        instance = self.get_instance_by_uuid(instance_uuid)
        if instance:
            current_status = instance.get("status")
            if current_status == STATUS_RUNNING:
                print(f"Instance is already running (status={current_status}). Skipping start API call.")
                return True, start_time
            else:
                print(f"Current status: {current_status}")

        # Send start request
        result = self._send_instance_action(instance_id, instance_uuid, "start", start_mode)

        if result and result.get("code") == 200:
            print(f"Instance start request accepted")
            print(f"  Start Time: {start_time}")
            return True, start_time
        else:
            error_msg = f"Failed to start instance. Response: {result}"
            print(f"Error: {error_msg}")
            return False, error_msg

    def stop_instance(self, instance_id: int, instance_uuid: str) -> Tuple[bool, Optional[str]]:
        """
        Stop a GPU instance

        Args:
            instance_id: Instance ID
            instance_uuid: Instance UUID

        Returns:
            Tuple[bool, Optional[str]]: (success, timestamp or error_message)
        """
        stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{stop_time}] Stopping instance {instance_uuid} (ID: {instance_id})...")

        # Check current status first
        instance = self.get_instance_by_uuid(instance_uuid)
        if instance:
            current_status = instance.get("status")
            if current_status == STATUS_STOPPED:
                print(f"Instance is already stopped (status={current_status}). Skipping stop API call.")
                return True, stop_time
            else:
                print(f"Current status: {current_status}")

        # Send stop request
        result = self._send_instance_action(instance_id, instance_uuid, "stop")

        if result and result.get("code") == 200:
            print(f"Instance stopped successfully")
            print(f"  Stop Time: {stop_time}")
            return True, stop_time
        else:
            error_msg = f"Failed to stop instance. Response: {result}"
            print(f"Error: {error_msg}")
            return False, error_msg


def print_instance_info(instance: Dict) -> None:
    """Print formatted instance information"""
    status = instance.get('status')
    status_str = "RUNNING" if status == STATUS_RUNNING else "STOPPED" if status == STATUS_STOPPED else f"UNKNOWN({status})"

    print("-" * 60)
    print(f"Instance ID:   {instance.get('webide_instance_id')}")
    print(f"Instance UUID: {instance.get('webide_instance_uuid')}")
    print(f"Name:          {instance.get('webide_instance_name')}")
    print(f"Nickname:      {instance.get('nick_name', 'N/A')}")
    print(f"Product:       {instance.get('product_name')}")
    print(f"Data Center:   {instance.get('data_center_name')}")
    print(f"Image:         {instance.get('image_display_name')} ({instance.get('image_display_version')})")
    print(f"Status:        {status} ({status_str})")
    print(f"Charge Type:   {instance.get('charge_type')}")
    print(f"SSH Command:   {instance.get('ssh_command')}")
    print(f"SSH Password:  {instance.get('ssh_password')}")
    print(f"Jupyter URL:   {instance.get('jupyter_url')}")

    open_apis = instance.get('open_apis', [])
    if open_apis:
        print("Open APIs:")
        for api in open_apis:
            print(f"  - {api.get('name')}: {api.get('api_url')}")


def main():
    """Main function demonstrating start and stop operations"""

    # Instance configurations
    START_INSTANCE_ID = 8379
    START_INSTANCE_UUID = "562clu54-eh98hxdt"

    #STOP_INSTANCE_ID = 7792
    #STOP_INSTANCE_UUID = "pe8xqrcp-d79wvs3s"

    # Create client
    client = GPUFreeClient()

    print("=" * 60)
    print("GPUFree Instance Manager")
    print("=" * 60)

    # Step 1: List all instances
    print("\n[Step 1] Listing all instances...\n")
    result = client.list_instances(page_no=1, page_size=20)

    if result and result.get("code") == 200:
        data = result.get("data", {})
        instances = data.get("dataList", [])
        total = data.get("totalRecord", 0)

        print(f"Total instances: {total}\n")

        for instance in instances:
            print_instance_info(instance)
        print("-" * 60)
    else:
        print("Failed to fetch instances.")
        return 1


    # Step 2: Start instance
    print(f"\n[Step 2] Starting instance...\n")
    success, result_msg = client.start_instance(
        instance_id=START_INSTANCE_ID,
        instance_uuid=START_INSTANCE_UUID
    )

    if not success:
        print(f"Start failed: {result_msg}")
        return 1
'''
    # Step 3: Stop another instance
    print(f"\n[Step 3] Stopping instance...\n")
    success, result_msg = client.stop_instance(
        instance_id=STOP_INSTANCE_ID,
        instance_uuid=STOP_INSTANCE_UUID
    )

    if not success:
        print(f"Stop failed: {result_msg}")
        return 1

    print("\nAll operations completed successfully!")
    return 0

'''

# Example usage for external programs
"""
from control_gpufree import GPUFreeClient, STATUS_RUNNING, STATUS_STOPPED

# Create client
client = GPUFreeClient()

# List instances
result = client.list_instances()

# Start instance (skips API call if already running)
success, msg = client.start_instance(
    instance_id=7764,
    instance_uuid="gghcmwa6-emgm7485"
)

# Stop instance (skips API call if already stopped)
success, msg = client.stop_instance(
    instance_id=7792,
    instance_uuid="pe8xqrcp-d79wvs3s"
)
"""


if __name__ == "__main__":
    sys.exit(main())
