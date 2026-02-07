import os
from dotenv import load_dotenv
import openai
import sys

# Load environment variables
pre_env_key = os.getenv("OPENAI_API_KEY")
if pre_env_key:
    print(f"DEBUG: Found OPENAI_API_KEY in system environment before loading .env")
    print(f"DEBUG: System Env Key start: {pre_env_key[:5]}...")
else:
    print("DEBUG: No OPENAI_API_KEY in system environment before loading .env")

# Force reload from .env to test the file content specifically
load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
print(f"DEBUG: Final API Key used (from .env if present): {api_key[:10] if api_key else 'None'}...")

if not api_key:
    print("ERROR: API Key is None")
    sys.exit(1)

print(f"Key length: {len(api_key)}")
print(f"Key start: {api_key[:10]}...")
print(f"Key end: ...{api_key[-10:]}")

# Check for whitespace
if api_key.strip() != api_key:
    print("WARNING: API Key has leading/trailing whitespace!")

client = openai.OpenAI(api_key=api_key.strip())

try:
    print("Attempting to list models...")
    # Just a simple valid call
    client.models.list()
    print("SUCCESS: API Key is valid and can list models.")
except openai.AuthenticationError:
    print("ERROR: AuthenticationError - The API key is invalid.")
except openai.PermissionDeniedError:
    print("ERROR: PermissionDeniedError - The API key lacks permissions.")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

try:
    print("Attempting chat completion with gpt-4o-mini...")
    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5
    )
    print("SUCCESS: Chat completion worked.")
except openai.APIConnectionError as e:
    print(f"ERROR: CONNECTION ERROR: {e}")
except openai.AuthenticationError as e:
    print(f"ERROR: AUTHENTICATION ERROR (401): {e}")
    print(f"Full Body: {e.body}")
except openai.PermissionDeniedError as e:
    print(f"ERROR: PERMISSION DENIED (403): {e}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
