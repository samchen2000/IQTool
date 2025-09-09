import google.generativeai as genai
import os

def check_gemini_api_key():
    """
    Checks for the presence of the GEMINI_API_KEY environment variable.

    Returns:
        bool: True if the API key is found, False otherwise.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("API key found! Attempting to configure the API...")
        try:
            genai.configure(api_key=api_key)
            print("API successfully configured.")
            return True
        except ValueError as e:
            print(f"Error configuring API: {e}")
            print("The API key may be invalid or there's a problem with the configuration.")
            return False
    else:
        print("API key not found. Please set the GEMINI_API_KEY environment variable.")
        return False

if __name__ == "__main__":
    if check_gemini_api_key():
        print("\nYou're all set to use the Gemini API!")
    else:
        print("\nPlease set your API key and try again.")