"""
Configuration handler for Sync.so API key management.
Handles reading API key from config.ini or environment variables.

API KEY HANDLING EXPLANATION:
=============================

This module follows the same pattern as Fal API nodes for consistency.

WORKFLOW:
=========

1. CHECK ENVIRONMENT VARIABLE:
   - First, check if SYNC_API_KEY is set as environment variable
   - This allows users to set it without modifying config.ini
   - Useful for deployment environments

2. CHECK CONFIG.INI FILE:
   - If environment variable not found, read from config.ini
   - Config file is located at: <node_root>/config.ini
   - Format: [API] section with SYNC_API_KEY = <key>

3. VALIDATE API KEY:
   - Check if key is empty or placeholder
   - Warn user if using default placeholder
   - Provide helpful error messages

4. CACHE API KEY:
   - Singleton pattern ensures API key is loaded once
   - Cached for performance (avoid reading file repeatedly)

USAGE:
======
from .sync_config import SyncConfig

api_key = SyncConfig().get_key()
"""

import configparser
import os


class SyncConfig:
    """
    Singleton class to handle Sync.so configuration.
    
    Reads API key from config.ini file or SYNC_API_KEY environment variable.
    Follows the same pattern as Fal API nodes for consistency with Floyo platform.
    
    This is a singleton to ensure the API key is loaded once and cached.
    """

    _instance = None
    _key = None

    def __new__(cls):
        """
        Singleton pattern: Ensure only one instance exists.
        
        Returns:
            SyncConfig: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(SyncConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize configuration and API key.
        
        WORKFLOW:
        1. Locate config.ini file (in node root directory)
        2. Check environment variable first (SYNC_API_KEY)
        3. If not found, read from config.ini
        4. Validate API key (not empty, not placeholder)
        5. Cache the key for future use
        """
        # Config file is at root level (parent directory of nodes/)
        # Structure: <node_root>/config.ini
        # Try multiple methods to find the config file
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(os.path.dirname(current_file))
        config_path = os.path.join(current_dir, "config.ini")
        
        # Alternative: Try relative to current working directory
        if not os.path.exists(config_path):
            # Try finding config.ini in common locations
            possible_paths = [
                os.path.join(os.getcwd(), "config.ini"),
                os.path.join(os.path.dirname(current_file), "..", "config.ini"),
                os.path.join(current_dir, "config.ini"),
            ]
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    config_path = abs_path
                    print(f"→ Found config file at alternative location: {config_path}")
                    break

        config = configparser.ConfigParser()
        
        # Check if config file exists first
        if not os.path.exists(config_path):
            print(f"⚠ WARNING: Config file not found at: {config_path}")
            print(f"   Current working directory: {os.getcwd()}")
            print(f"   File path being checked: {config_path}")
            self._key = None
            return
        
        # Read config file
        config.read(config_path)
        print(f"→ Config file found: {config_path}")
        print(f"→ Config file sections: {config.sections()}")

        try:
            # ============================================================
            # STEP 1: CHECK ENVIRONMENT VARIABLE FIRST
            # ============================================================
            # Environment variables take precedence (useful for deployment)
            env_key = os.environ.get("SYNC_API_KEY")
            if env_key is not None and env_key.strip():
                print("✓ SYNC_API_KEY found in environment variables")
                self._key = env_key.strip()
                return
            
            # ============================================================
            # STEP 2: READ FROM CONFIG.INI FILE
            # ============================================================
            print("→ SYNC_API_KEY not found in environment variables")
            print(f"→ Reading from config file: {config_path}")
            
            # Check if API section exists
            if "API" not in config:
                raise Exception(f"'[API]' section not found in config.ini. Found sections: {config.sections()}")
            
            # Get API key and strip whitespace
            if "SYNC_API_KEY" not in config["API"]:
                raise Exception(f"SYNC_API_KEY key not found in [API] section. Available keys: {list(config['API'].keys())}")
            
            self._key = config["API"]["SYNC_API_KEY"].strip()
            
            if not self._key:
                raise Exception("SYNC_API_KEY is empty in config.ini. Please set your API key.")
            
            print(f"✓ SYNC_API_KEY found in config.ini (length: {len(self._key)} characters)")
            print(f"  Key starts with: {self._key[:10]}...")
            
            # Also set in environment for consistency
            os.environ["SYNC_API_KEY"] = self._key
            print("✓ SYNC_API_KEY set in environment variables")

            # ============================================================
            # STEP 3: VALIDATE API KEY
            # ============================================================
            # Check if Sync API key is the default placeholder or empty
            if self._key == "" or self._key == "<your_sync_api_key_here>":
                print("\n" + "=" * 60)
                print("⚠ WARNING: You are using the default Sync API key placeholder!")
                print("=" * 60)
                print("Please set your actual Sync API key in either:")
                print("1. The config.ini file under [API] section")
                print("   Location: " + config_path)
                print("   Format: SYNC_API_KEY = your_actual_api_key_here")
                print("2. Or as an environment variable named SYNC_API_KEY")
                print("   Command: export SYNC_API_KEY=your_actual_api_key_here")
                print("\nGet your API key from: https://sync.so/")
                print("=" * 60 + "\n")
                
        except KeyError as e:
            # API key not found in config file
            print("\n" + "=" * 60)
            print("❌ ERROR: SYNC_API_KEY not found in config file")
            print("=" * 60)
            print(f"KeyError details: {str(e)}")
            print(f"Config file location: {config_path}")
            print(f"Config file exists: {os.path.exists(config_path)}")
            if os.path.exists(config_path):
                print(f"Config sections found: {config.sections()}")
                if "API" in config:
                    print(f"API section keys: {list(config['API'].keys())}")
            print("\nPlease set your API key in one of the following ways:")
            print("\n1. Edit config.ini file:")
            print(f"   Location: {config_path}")
            print("   Add the following:")
            print("   [API]")
            print("   SYNC_API_KEY = your_actual_api_key_here")
            print("\n2. Or set as environment variable:")
            print("   export SYNC_API_KEY=your_actual_api_key_here")
            print("\nGet your API key from: https://sync.so/")
            print("=" * 60 + "\n")
            self._key = None
        except Exception as e:
            # Any other error reading config
            print("\n" + "=" * 60)
            print("❌ ERROR: Failed to read API key from config")
            print("=" * 60)
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Config file location: {config_path}")
            print(f"Config file exists: {os.path.exists(config_path)}")
            print("=" * 60 + "\n")
            self._key = None

    def get_key(self):
        """
        Get the Sync API key.
        
        Returns the cached API key that was loaded during initialization.
        
        Returns:
            str: The Sync.so API key
            
        Raises:
            Exception: If API key is not configured
            
        Example:
            api_key = SyncConfig().get_key()
            # Use API key
        """
        if not self._key:
            # Try to re-initialize in case config was added after first load
            try:
                self._initialize()
            except:
                pass
            
            if not self._key:
                current_file = os.path.abspath(__file__)
                current_dir = os.path.dirname(os.path.dirname(current_file))
                config_path = os.path.join(current_dir, "config.ini")
                raise Exception(
                    f"SYNC_API_KEY not found. Please set it in config.ini or as environment variable.\n"
                    f"Config file location: {config_path}\n"
                    f"Config file exists: {os.path.exists(config_path)}\n"
                    f"Expected format in config.ini:\n"
                    f"[API]\n"
                    f"SYNC_API_KEY = your_api_key_here"
                )
        return self._key
