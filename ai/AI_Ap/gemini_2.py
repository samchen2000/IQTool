import google.generativeai as genai
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk

# --- 全域變數與模型設定 ---
model = None
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("請設定 GEMINI_API_KEY 環境變數。")
    genai.configure(api_key=api_key)
    #model = genai.GenerativeModel('gemini-1.5-flash')
    model = genai.GenerativeModel('gemini-2.5-flash')
except ValueError as e:
    # 如果 API Key 未設定，程式會在此處結束，並顯示錯誤訊息
    print(f"錯誤：{e}")
    model = None

# --- GUI 邏輯 ---
def send_query():
    """
    發送使用者輸入的問題給 Gemini 並顯示回答。
    """
    if not model:
        messagebox.showerror("錯誤", "無法載入 Gemini 模型。請檢查您的 API Key。")
        return

    user_query = input_text.get("1.0", tk.END).strip()
    if not user_query:
        messagebox.showwarning("警告", "請輸入您的問題！")
        return

    # 清空輸入框
    input_text.delete("1.0", tk.END)

    # 顯示等待訊息
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, "思考中...\n")
    output_text.config(state=tk.DISABLED)
    root.update_idletasks()  # 強制更新 GUI

    try:
        response = model.generate_content(user_query)
        if response.text:
            gemini_response = response.text
        else:
            gemini_response = "無法產生回答。可能內容不安全或無法理解。"
    except Exception as e:
        gemini_response = f"發生錯誤：{e}\n請檢查網路連線或 API Key。"

    # 在新的執行緒中更新 GUI
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, gemini_response)
    output_text.config(state=tk.DISABLED)

# --- GUI 介面建立 ---
# 建立主視窗
root = tk.Tk()
root.title("Gemini AI 查詢器")
root.geometry("600x500")
root.resizable(False, False)

# 設定風格
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Arial", 12), padding=10)
style.configure("TLabel", font=("Arial", 12))

# 建立介面框架
frame = ttk.Frame(root, padding="10")
frame.pack(fill=tk.BOTH, expand=True)

# 輸入區塊
input_label = ttk.Label(frame, text="請輸入您的問題：")
input_label.pack(anchor="w", pady=(0, 5))

input_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=50, height=8, font=("Arial", 11))
input_text.pack(fill=tk.BOTH, pady=(0, 10))

# 按鈕
send_button = ttk.Button(frame, text="發送", command=send_query)
send_button.pack(fill=tk.X, pady=(0, 10))

# 輸出區塊
output_label = ttk.Label(frame, text="Gemini 回答：")
output_label.pack(anchor="w", pady=(0, 5))

output_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=50, height=15, font=("Arial", 11), state=tk.DISABLED)
output_text.pack(fill=tk.BOTH, expand=True)

# 啟動主迴圈
root.mainloop()