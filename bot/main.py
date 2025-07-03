import time, json, csv, requests, threading, os
from datetime import datetime
import shutil
import pandas as pd

# === Paths & Backup ===
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_wallet():
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(BACKUP_DIR, f"wallet_backup_{ts}.json")
    shutil.copyfile("wallet.json", backup_path)
    print(f"💾 Wallet backup saved: {backup_path}")

def export_to_excel():
    try:
        df_trades = pd.read_csv("trades.csv")
        df_pnl = pd.read_csv("pnl.csv")
        wallet = load_wallet()

        with pd.ExcelWriter("bot_export.xlsx", engine="openpyxl", mode="w") as writer:
            df_trades.to_excel(writer, sheet_name="Trades", index=False)
            df_pnl.to_excel(writer, sheet_name="PnL", index=False)
            pd.DataFrame([wallet]).to_excel(writer, sheet_name="Wallet", index=False)
        print("📤 Excel export written to bot_export.xlsx")
    except Exception as e:
        print(f"⚠️ Excel export failed: {e}")

# === Load Config ===
with open("config.json") as f:
    config = json.load(f)

SYMBOLS = config["symbols"]
TRADE_THRESHOLD = config["threshold"]
START_WALLET = config["start_wallet"]

# === Wallet Management ===
def load_wallet():
    try:
        with open("wallet.json") as f:
            return json.load(f)
    except:
        save_wallet(START_WALLET)
        return START_WALLET.copy()

def save_wallet(w):
    with open("wallet.json", "w") as f:
        json.dump(w, f, indent=2)

# === Logger ===
def log_trade(msg, pair=None, action=None, amount=0, price=0):
    with open("../logs/trades.log", "a") as f:
        f.write(time.ctime() + " — " + msg + "\n")
    print("🟢 " + msg)
    with open("trades.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([time.ctime(), pair, action, f"{price:.2f}", f"{amount:.6f}", f"{amount*price:.2f}"])
    calculate_pnl()

# === Get Price ===
def get_price(pair):
    try:
        if "ZAR" in pair:
            url = f"https://api.luno.com/api/1/ticker?pair={pair}"
            data = requests.get(url, timeout=5).json()
            return float(data["last_trade"])
        else:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
            data = requests.get(url, timeout=5).json()
            return float(data["price"])
    except:
        return 0.0

# === PnL Calculation ===
def calculate_pnl():
    wallet = load_wallet()
    btc_zar = get_price("XBTZAR")
    eth_zar = get_price("ETHZAR")
    btc_usdt = get_price("BTCUSDT")
    eth_usdt = get_price("ETHUSDT")
    total_zar = wallet["zar"] + wallet["btc"] * btc_zar + wallet["eth"] * eth_zar
    total_usdt = wallet["usdt"] + wallet["btc"] * btc_usdt + wallet["eth"] * eth_usdt
    with open("pnl.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            time.ctime(),
            wallet["zar"], wallet["usdt"], wallet["btc"], wallet["eth"],
            btc_zar, eth_zar, total_zar, total_usdt,
            total_zar - config["start_wallet"]["zar"],
            total_usdt - config["start_wallet"]["usdt"]
        ])

# === Trading Logic ===
def simulate(symbol, pair):
    wallet = load_wallet()
    base = "zar" if "ZAR" in pair else "usdt"
    coin = symbol.split("_")[0].lower()
    last = get_price(pair)

    while True:
        now = get_price(pair)
        if now == 0.0:
            time.sleep(60)
            continue
        change = (now - last) / last * 100

        if change <= -TRADE_THRESHOLD and wallet[base] > 0:
            amt = wallet[base]
            wallet[coin] += amt / now
            wallet[base] = 0
            save_wallet(wallet)
            log_trade(f"[{symbol}] BUY {amt / now:.6f} at {now:.2f}", pair, "BUY", amt / now, now)

        elif change >= TRADE_THRESHOLD and wallet[coin] > 0:
            held = wallet[coin]
            wallet[base] += held * now
            wallet[coin] = 0
            save_wallet(wallet)
            log_trade(f"[{symbol}] SELL {held:.6f} at {now:.2f}", pair, "SELL", held, now)

        last = now
        time.sleep(60)

def main():
    if not os.path.exists("trades.csv"):
        with open("trades.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "Pair", "Action", "Price", "Amount", "Value"])
    if not os.path.exists("pnl.csv"):
        with open("pnl.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "ZAR", "USDT", "BTC", "ETH", "BTC_ZAR", "ETH_ZAR", "Total_ZAR", "Total_USDT", "ZAR_PnL", "USDT_PnL"])

    for sym, pair in SYMBOLS.items():
        t = threading.Thread(target=simulate, args=(sym, pair), daemon=True)
        t.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("🛑 Bot interrupted. Backing up wallet...")
        backup_wallet()
        export_to_excel()

if __name__ == "__main__":
    main()
