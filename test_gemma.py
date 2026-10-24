#!/usr/bin/env python3
"""
Test script for Google Gemma 4 integration via Google GenAI SDK.
Tests connectivity to the Gemini API and verifies Gemma 4 model response.
"""
import os
import sys
import time
from dotenv import load_dotenv

# Load .env
load_dotenv()

def test_integration():
    print("=" * 60)
    print("🧪 Gemma 4 Integration Test Suite")
    print("=" * 60)

    # 1. Check GEMINI_API_KEY
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        print("❌ FAILED: GEMINI_API_KEY is not set.")
        print("👉 Instructions:")
        print("   1. Create a .env file: cp .env.example .env")
        print("   2. Add your API key: GEMINI_API_KEY=AIzaSy...")
        print("   3. Or export in terminal: export GEMINI_API_KEY='your_key'")
        return False

    masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
    print(f"✅ Found GEMINI_API_KEY: {masked_key}")

    # 2. Check SDK imports
    try:
        from google import genai
        from google.genai import types
        print("✅ google-genai SDK imported successfully.")
    except ImportError as e:
        print(f"❌ FAILED: Could not import google-genai: {e}")
        print("👉 Run: pip install google-genai")
        return False

    # 3. Model target
    model_id = os.getenv("GEMMA_MODEL_ID", "gemma-4-26b-a4b-it")
    print(f"🎯 Target Model ID: {model_id}")

    # 4. Initialize Client
    try:
        client = genai.Client(
            api_key=api_key.strip(),
            http_options=types.HttpOptions(timeout=30000),
        )
        print("✅ GenAI Client initialized.")
    except Exception as e:
        print(f"❌ FAILED: Client initialization error: {e}")
        return False

    # 5. Test generation
    prompt = "Respond with exactly 5 words confirming Gemma 4 is operational."
    print(f"\n📨 Sending prompt: '{prompt}'")
    start = time.perf_counter()

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
        )
        latency = (time.perf_counter() - start) * 1000
        print(f"⚡ Response received in {latency:.1f}ms:")
        print("-" * 40)
        print(response.text.strip())
        print("-" * 40)
        print("🎉 SUCCESS: Gemma 4 integration is working perfectly!")
        return True

    except Exception as e:
        print(f"❌ API Call Failed: {type(e).__name__}: {e}")
        print("\n🔍 Troubleshooting suggestions:")
        err_str = str(e)
        if "API_KEY_INVALID" in err_str or "400" in err_str:
            print("   - Your GEMINI_API_KEY appears invalid. Check at https://aistudio.google.com/apikey")
        elif "404" in err_str or "NOT_FOUND" in err_str:
            print(f"   - Model '{model_id}' was not found.")
            print("   - Listing available Gemma models for your API key...")
            try:
                for m in client.models.list():
                    if "gemma" in m.name.lower():
                        print(f"     * Found: {m.name}")
            except Exception as list_err:
                print(f"     (Could not list models: {list_err})")
        elif "429" in err_str:
            print("   - Rate limit or quota hit. Wait a minute and try again.")
        return False

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
