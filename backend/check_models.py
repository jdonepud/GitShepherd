"""Script to check available Gemini models."""
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: GEMINI_API_KEY not found in .env file")
    exit(1)

genai.configure(api_key=API_KEY)

print("Checking available models...")
try:
    models = genai.list_models()
    print("\nAvailable models:")
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name} (display_name: {model.display_name})")
            print(f"    Supported methods: {model.supported_generation_methods}")
    
    # Try to find a working model
    print("\nTrying to initialize models...")
    working_models = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            model_name = model.name.split('/')[-1]
            try:
                test_model = genai.GenerativeModel(model_name)
                # Try a simple test
                response = test_model.generate_content("Hi")
                working_models.append(model_name)
                print(f"✓ {model_name} - WORKS")
            except Exception as e:
                print(f"✗ {model_name} - FAILED: {str(e)[:100]}")
    
    if working_models:
        print(f"\n✓ Working models: {', '.join(working_models)}")
        print(f"\nRecommended: Use '{working_models[0]}'")
    else:
        print("\n✗ No working models found!")
        
except Exception as e:
    print(f"Error listing models: {e}")
