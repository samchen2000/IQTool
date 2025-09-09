import os
from openai import OpenAI

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 沒有讀到 OPENAI_API_KEY，請確認已經設在 Windows 環境變數。")
        return

    print(f"✅ 已讀到 API Key，開頭是: {api_key[:10]}...")

    try:
        client = OpenAI(api_key=api_key)

        # 測試呼叫 API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "你好，幫我回覆一句話：API key 測試成功"}
            ]
        )

        print("🤖 ChatGPT 回覆：", response.choices[0].message.content)

    except Exception as e:
        print("❌ 呼叫 API 失敗:", str(e))

if __name__ == "__main__":
    main()