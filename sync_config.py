"""
Configuration handler for Sync.so API key management.
Handles reading API key from config.ini or environment variables.
"""

import configparser
import os


class SyncConfig:
    """
    Singleton class to handle Sync.so configuration.
    Reads API key from config.ini file or SYNC_API_KEY environment variable.
    """

    _instance = None
    _key = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SyncConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize configuration and API key."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "config.ini")

        config = configparser.ConfigParser()
        config.read(config_path)

        try:
            # Check environment variable first
            if os.environ.get("SYNC_API_KEY") is not None:
                print("SYNC_API_KEY found in environment variables")
                self._key = os.environ["SYNC_API_KEY"]
            else:
                # Read from config.ini
                print("SYNC_API_KEY not found in environment variables")
                self._key = config["API"]["SYNC_API_KEY"]
                print("SYNC_API_KEY found in config.ini")
                os.environ["SYNC_API_KEY"] = self._key
                print("SYNC_API_KEY set in environment variables")

            # Check if Sync API key is the default placeholder
            if self._key == "" or self._key == "<your_sync_api_key_here>":
                print("WARNING: You are using the default Sync API key placeholder!")
                print("Please set your actual Sync API key in either:")
                print("1. The config.ini file under [API] section")
                print("2. Or as an environment variable named SYNC_API_KEY")
                print("Get your API key from: https://sync.so/")
        except KeyError:
            print("Error: SYNC_API_KEY not found in config.ini or environment variables")
            print("Please set your API key in config.ini or as SYNC_API_KEY environment variable")
            print("Get your API key from: https://sync.so/")

    def get_key(self):
        """
        Get the Sync API key.

        Returns:
            str: The Sync.so API key
        """
        return self._key

