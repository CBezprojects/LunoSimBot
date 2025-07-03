import tkinter as tk
from tkinter import ttk, scrolledtext
import threading, subprocess, os, time
import requests

SYMBOLS = {
    "BTC_ZAR": "XBTZAR",
    "ETH_ZAR": "ETHZAR",
    "BTC_USDT": "BTCUSDT",
    "ETH_USDT": "ETHUSDT"
}
LOG_FILE = os.path.abspath("../logs/trades.log")
BOT_PATH = os.path.abspath("../bot/main.py")

class LunoSimGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LunoSimBot GUI")
        self.geometry("700x500")
        self.bot_process = None

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(expand=1, fill="both")

        self.build_control_tab()
        self.build_price_tab()
        self.build_log_tab()
        self.update_prices()

    def build_control_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="⚙️ Control")
        ttk.Button(tab, text="▶️ Start Bot", command=self.start_bot).pack(pady=10)
        ttk.Button(tab, text="⏹ Stop Bot", command=self.stop_bot).pack()

    def build_price_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="📈 Prices")
        self.price_labels = {}

        for i, (k, pair) in enumerate(SYMBOLS.items()):
            label = ttk.Label(tab, text=f"{k}: ...", font=("Arial", 14))
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            self.price_labels[k] = label

    def build_log_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="📜 Logs")
        self.log_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True)
        self.update_logs()

    def update_prices(self):
        def get_price(pair):
            try:
                if "ZAR" in pair:
                    r = requests.get(f"https://api.luno.com/api/1/ticker?pair={pair}", timeout=3)
                    return float(r.json()["last_trade"])
                else:
                    r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={pair}", timeout=3)
                    return float(r.json()["price"])
            except:
                return 0.0

        for key, pair in SYMBOLS.items():
            price = get_price(pair)
            currency = "R" if "ZAR" in pair else "$"
            self.price_labels[key].config(text=f"{key}: {currency}{price:,.2f}")

        self.after(60000, self.update_prices)

    def update_logs(self):
        try:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert(tk.END, "".join(lines[-100:]))
        except:
            self.log_text.insert(tk.END, "[No logs found]\n")

        self.after(5000, self.update_logs)

    def start_bot(self):
        if self.bot_process and self.bot_process.poll() is None:
            return
        self.bot_process = subprocess.Popen(["python", BOT_PATH], creationflags=subprocess.CREATE_NO_WINDOW)

    def stop_bot(self):
        if self.bot_process and self.bot_process.poll() is None:
            self.bot_process.terminate()
            self.bot_process = None

if __name__ == "__main__":
    app = LunoSimGUI()
    app.mainloop()
