import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading, subprocess, os, time, json, requests
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

SETTINGS_PATH = os.path.abspath("settings.json")
VERSION_FILE = os.path.abspath("version.txt")
LOG_FILE = os.path.abspath("../logs/trades.log")
WALLET_FILE = os.path.abspath("../bot/wallet.json")
BOT_PATH = os.path.abspath("../bot/main.py")

SYMBOLS = {
    "BTC_ZAR": "XBTZAR",
    "ETH_ZAR": "ETHZAR",
    "BTC_USDT": "BTCUSDT",
    "ETH_USDT": "ETHUSDT"
}
price_history = {k: [] for k in SYMBOLS}

def load_settings():
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except:
        return {"zoom": 100}

def save_settings(settings):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)

def get_version():
    try:
        with open(VERSION_FILE, "r") as f:
            return f.readline().strip()
    except:
        return "LunoSimBot"

class LunoSimGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.zoom_factor = self.settings.get("zoom", 100) / 100
        self.title("LunoSimBot GUI")
        self.geometry("900x600")
        self.bot_process = None

        self.create_menu()

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(expand=1, fill="both")

        self.status_bar = tk.Label(self, text=f"{get_version()} | Ready", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.build_control_tab()
        self.build_price_tab()
        self.build_log_tab()
        self.build_wallet_tab()
        self.build_chart_tab()

        self.update_prices()
        self.update_logs()

    def zoom_font(self, size):
        return int(size * self.zoom_factor)

    def create_menu(self):
        menubar = tk.Menu(self)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Zoom / Settings", command=self.open_settings)
        menubar.add_cascade(label="⚙️ Settings", menu=settings_menu)
        self.config(menu=menubar)

    def open_settings(self):
        popup = tk.Toplevel(self)
        popup.title("Settings")
        popup.geometry("300x150")
        tk.Label(popup, text="Zoom (%)").pack(pady=10)
        zoom_var = tk.StringVar(value=str(self.settings.get("zoom", 100)))
        entry = ttk.Entry(popup, textvariable=zoom_var)
        entry.pack()

        def save_zoom():
            try:
                new_zoom = int(zoom_var.get())
                self.settings["zoom"] = new_zoom
                save_settings(self.settings)
                messagebox.showinfo("Saved", "Restart app to apply new zoom.")
                popup.destroy()
            except:
                messagebox.showerror("Error", "Invalid zoom value.")

        ttk.Button(popup, text="Save", command=save_zoom).pack(pady=10)

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
            label = ttk.Label(tab, text=f"{k}: ...", font=("Arial", self.zoom_font(14)))
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            self.price_labels[k] = label

    def build_log_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="📜 Logs")
        self.log_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD, font=("Courier", self.zoom_font(10)))
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_config("green", foreground="green")

    def build_wallet_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="💰 Wallet")
        self.wallet_entries = {}
        try:
            with open(WALLET_FILE, "r") as f:
                wallet = json.load(f)
            for i, key in enumerate(wallet):
                ttk.Label(tab, text=key.upper(), font=("Arial", self.zoom_font(10))).grid(row=i, column=0, padx=5, pady=5, sticky="e")
                entry = ttk.Entry(tab, font=("Arial", self.zoom_font(10)))
                entry.insert(0, str(wallet[key]))
                entry.grid(row=i, column=1, padx=5, pady=5)
                self.wallet_entries[key] = entry
            ttk.Button(tab, text="💾 Save Wallet", command=self.save_wallet).grid(row=len(wallet), column=0, columnspan=2, pady=10)
        except Exception as e:
            ttk.Label(tab, text="Failed to load wallet", foreground="red").pack()

    def build_chart_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="📊 Live Chart")
        self.chart_fig, self.ax = plt.subplots()
        self.chart_canvas = FigureCanvasTkAgg(self.chart_fig, master=tab)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.update_chart()

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
            price_history[key].append(price)
            self.price_labels[key].config(
                text=f"{key}: R{price:,.2f}" if "ZAR" in pair else f"{key}: ${price:,.2f}"
            )
        self.status_bar.config(text=f"{get_version()} | Last updated: {datetime.now().strftime('%H:%M:%S')}")
        self.after(60000, self.update_prices)

    def update_logs(self):
        try:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert(tk.END, "".join(lines[-100:]), "green")
        except:
            self.log_text.insert(tk.END, "[No logs found]\n", "green")
        self.after(5000, self.update_logs)

    def update_chart(self):
        self.ax.clear()
        for key, data in price_history.items():
            if data:
                self.ax.plot(data[-50:], label=key)
        if any(price_history.values()):
            self.ax.legend()
        self.ax.set_title("Live Price Chart")
        self.chart_canvas.draw()
        self.after(15000, self.update_chart)

    def start_bot(self):
        if self.bot_process and self.bot_process.poll() is None:
            return
        self.bot_process = subprocess.Popen(["python", BOT_PATH], creationflags=subprocess.CREATE_NO_WINDOW)
        self.status_bar.config(text=f"{get_version()} | Bot Running")

    def stop_bot(self):
        if self.bot_process and self.bot_process.poll() is None:
            self.bot_process.terminate()
            self.bot_process = None
            self.status_bar.config(text=f"{get_version()} | Bot Stopped")

    def save_wallet(self):
        try:
            updated_wallet = {k: float(entry.get()) for k, entry in self.wallet_entries.items()}
            with open(WALLET_FILE, "w") as f:
                json.dump(updated_wallet, f, indent=2)
            messagebox.showinfo("Saved", "Wallet saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = LunoSimGUI()
    app.mainloop()
