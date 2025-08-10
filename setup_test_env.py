#!/usr/bin/env python3
"""
Setup test environment for live archival memory testing.

Creates a test configuration with multiple Gemini keys and validates the setup.
"""

import os
from pathlib import Path

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, environment variables should be set manually
    pass

from cogency.providers.gemini import Gemini


def setup_test_environment():
    """Setup and validate test environment for live archival memory testing."""
    
    print("🔧 Setting up Live Archival Memory Test Environment")
    print("=" * 55)
    
    # Check for API keys
    api_keys_env = os.getenv("GEMINI_API_KEY", "")
    if not api_keys_env:
        print("❌ GEMINI_API_KEY environment variable not set")
        print("\n💡 To set up Gemini API keys:")
        print("   export GEMINI_API_KEY='key1,key2,key3,key4,key5,key6,key7,key8'")
        return False
    
    print("✅ GEMINI_API_KEY found - auto-detection will handle the rest")
    
    # Quick validation
    print("\n🧪 Testing Cogency Agent setup...")
    try:
        from cogency import Agent
        from cogency.config import MemoryConfig
        
        # Test basic agent creation
        agent = Agent("test", provider="gemini")
        print("✅ Agent with Gemini provider created successfully")
        
        print("\n🎯 Environment Ready!")
        print("   Run: poetry run python test_archival_live.py")
        return True
            
    except Exception as e:
        print(f"❌ Agent setup failed: {e}")
        return False


def show_requirements():
    """Show requirements for testing."""
    print("\n📋 Requirements for Live Testing:")
    print("   1. Multiple Gemini API keys (for rate limit handling)")
    print("   2. google-genai package installed")
    print("   3. Cogency archival memory implementation")
    print("   4. Temporary directory access for memory storage")


if __name__ == "__main__":
    success = setup_test_environment()
    if not success:
        show_requirements()
        exit(1)
    print("\n🚀 Ready to run comprehensive archival memory tests!")