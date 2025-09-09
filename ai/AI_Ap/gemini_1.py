import google.generativeai as genai
import os

def get_gemini_api_key():
    """Retrieves the GEMINI_API_KEY from environment variables."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. "
                         "Please set it and try again.")
    return api_key

def main():
    """Main function to run the Gemini query program."""
    try:
        # Get and configure the API key
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)

        # Initialize the generative model
        model = genai.GenerativeModel('gemini-1.5-flash')

        print("歡迎使用 Gemini AI 查詢程式！")
        print("您可以輸入任何問題，輸入 '離開' 結束程式。")
        print("-" * 40)

        while True:
            # Get user input
            user_input = input("你的問題：")

            # Check for exit command
            if user_input.lower() == '離開':
                print("謝謝使用，再見！")
                break

            # Generate and print the response
            try:
                response = model.generate_content(user_input)
                # Check if the response contains text and print it
                if response.text:
                    print("\nGemini 回答：")
                    print(response.text)
                    print("-" * 40)
                else:
                    print("無法產生回答。可能內容不安全或無法理解。")
                    print("-" * 40)
            except Exception as e:
                print(f"發生錯誤：{e}")
                print("請檢查您的網路連線或 API Key 是否有效。")
                print("-" * 40)

    except ValueError as ve:
        print(f"錯誤：{ve}")
    except Exception as e:
        print(f"發生未預期的錯誤：{e}")

if __name__ == "__main__":
    main()