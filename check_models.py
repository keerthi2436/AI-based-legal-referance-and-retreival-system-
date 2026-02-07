import os
import sys
from dotenv import load_dotenv
import openai

# Force load .env
load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
print(f"Testing Key: {api_key[:10]}...{api_key[-10:] if api_key else ''}")

if not api_key:
    print("No API Key found.")
    sys.exit(1)

client = openai.OpenAI(api_key=api_key)

models_to_test = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-4"]

print("\n--- Testing Model Access ---")
success_model = None

for model in models_to_test:
    print(f"Testing {model}...", end=" ")
    try:
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1
        )
        print("SUCCESS! ✅")
        success_model = model
        break
    except openai.AuthenticationError:
        print("FAILED (401 - Invalid Key) ❌")
        break # No point testing other models
    except openai.PermissionDeniedError:
        print("FAILED (403 - Permission Denied) 🚫")
    except openai.NotFoundError:
         print("FAILED (404 - Model Not Found/No Access) 🚫")
    except Exception as e:
        print(f"FAILED ({type(e).__name__}) ⚠️")

if success_model:
    print(f"\nRecommended Action: Update .env to use OPENAI_MODEL={success_model}")
else:
    print("\nCRITICAL: The API key is valid (authenticated) but cannot access ANY common models.")
    print("Please check your API key permissions at https://platform.openai.com/api-keys")
