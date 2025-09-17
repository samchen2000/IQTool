import tkinter as tk
from tkinter import scrolledtext, messagebox
from openai import OpenAI
import os

# 初始化 OpenAI 客戶端（會從環境變數讀取 API key）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

root = tk.Tk()
root.title("ChatGPT GUI")
root.geometry("600x500")

# 上方輸入框區塊
input_frame = tk.Frame(root)
input_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

entry = tk.Entry(input_frame, font=("Microsoft JhengHei", 12))
entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

send_btn = tk.Button(input_frame, text="發送", command=lambda: send_message(), font=("Microsoft JhengHei", 12))
send_btn.pack(side=tk.LEFT, padx=5)

# 下方聊天紀錄框
chat_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, state="disabled", font=("Microsoft JhengHei", 12))
chat_box.pack(side=tk.BOTTOM, padx=10, pady=10, fill=tk.BOTH, expand=True)

# 發送訊息函式
def send_message():
    user_message = entry.get().strip()
    if not user_message:
        messagebox.showwarning("警告", "請輸入問題！")
        return
    
    # 在聊天框顯示用戶訊息
    chat_box.config(state="normal")
    chat_box.insert(tk.END, f"🧑 你: {user_message}\n", "user")
    chat_box.config(state="disabled")
    chat_box.yview(tk.END)

    entry.delete(0, tk.END)

    try:
        # 呼叫 ChatGPT API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一個熱心幫助的助手,可以建立表格,並提供表格說明,也會提供參考資料的網址去查詢"},
                {"role": "user", "content": user_message}
            ]
        )

        reply = response.choices[0].message.content

        # 在聊天框顯示 ChatGPT 回覆
        chat_box.config(state="normal")
        chat_box.insert(tk.END, f"🤖 ChatGPT: {reply}\n\n", "bot")
        chat_box.config(state="disabled")
        chat_box.yview(tk.END)

    except Exception as e:
        messagebox.showerror("錯誤", str(e))

root.bind("<Return>", lambda event: send_message())

# 設定文字顏色樣式
chat_box.tag_config("user", foreground="blue")
chat_box.tag_config("bot", foreground="green")

# 啟動 GUI 事件迴圈
root.mainloop()
