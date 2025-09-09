import tkinter as tk
from tkinter import scrolledtext, messagebox
from openai import OpenAI
import os

# 初始化 OpenAI 客戶端（會從環境變數讀取 API key）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 建立主視窗
root = tk.Tk()
root.title("ChatGPT GUI")
root.geometry("600x500")

# 聊天紀錄框
chat_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, state="disabled", font=("Microsoft JhengHei", 12))
chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# 輸入框
entry = tk.Entry(root, font=("Microsoft JhengHei", 12))
entry.pack(padx=10, pady=5, fill=tk.X)

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
                {"role": "system", "content": "你是一個有幫助的助手"},
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

# 發送按鈕
send_btn = tk.Button(root, text="發送", command=send_message, font=("Microsoft JhengHei", 12))
send_btn.pack(pady=5)

# 按 Enter 也能發送
root.bind("<Return>", lambda event: send_message())

# 設定文字顏色樣式
chat_box.tag_config("user", foreground="blue")
chat_box.tag_config("bot", foreground="green")

# 啟動 GUI 事件迴圈
root.mainloop()
