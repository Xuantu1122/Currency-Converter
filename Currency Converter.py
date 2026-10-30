import requests
import json
import time

CACHE_FILE = "rates.json"
HISTORY_FILE = "history.txt"
MAX_AGE = 3600  # 1 hour in seconds
POPULAR = ["USD", "VND", "EUR", "JPY", "GBP", "KRW", "CNY", "THB", "AUD", "SGD"]


# ---------- Rates: fetch, cache, fallback ----------

def fetch_rates():
    r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
    data = r.json()
    with open(CACHE_FILE, "w") as f:
        json.dump({"time": time.time(), "rates": data["rates"]}, f)
    return data["rates"]


def load_cache():
    with open(CACHE_FILE, "r") as f:
        return json.load(f)


def get_rates():
    cache = None

    try:
        cache = load_cache()
        age = time.time() - cache["time"]
        if age < MAX_AGE:
            print("(using saved rates)")
            return cache["rates"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        cache = None

    try:
        print("(getting new rates)")
        return fetch_rates()
    except requests.exceptions.RequestException:
        if cache is not None:
            print("(no internet, using old saved rates)")
            return cache["rates"]
        raise


# ---------- Core logic ----------

def convert(amount, from_cur, to_cur, rates):
    in_usd = amount / rates[from_cur]
    return in_usd * rates[to_cur]


def save_history(line):
    with open(HISTORY_FILE, "a") as f:
        f.write(line + "\n")


# ---------- Input helpers ----------

def ask_amount():
    text = input("Amount: ").strip()
    try:
        return float(text)
    except ValueError:
        print("Please type a number, like 100 or 12.5")
        return None


def ask_currency(prompt, rates):
    code = input(prompt).strip().upper()
    if code not in rates:
        print("Unknown currency code. Try USD, VND, EUR, JPY...")
        return None
    return code


# ---------- Menu features ----------

def show_popular(rates):
    print("\nPopular currencies (1 USD =)")
    for code in POPULAR:
        if code in rates:
            print(f"  {code}: {rates[code]:,.2f}")


def single_convert(rates):
    amount = ask_amount()
    if amount is None:
        return
    src = ask_currency("From (e.g. USD): ", rates)
    if src is None:
        return
    dst = ask_currency("To (e.g. VND): ", rates)
    if dst is None:
        return

    result = convert(amount, src, dst, rates)
    line = f"{amount:,.2f} {src} = {result:,.2f} {dst}"
    print(line)
    save_history(line)


def multi_convert(rates):
    amount = ask_amount()
    if amount is None:
        return
    src = ask_currency("From (e.g. USD): ", rates)
    if src is None:
        return

    text = input("To (e.g. VND EUR JPY, or press Enter for popular): ")
    text = text.replace(",", " ").upper()
    targets = text.split()
    if not targets:
        targets = [c for c in POPULAR if c != src]

    for dst in targets:
        if dst not in rates:
            print(f"  {dst}: unknown code, skipped")
            continue
        result = convert(amount, src, dst, rates)
        line = f"{amount:,.2f} {src} = {result:,.2f} {dst}"
        print("  " + line)
        save_history(line)


def view_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        lines = []

    if not lines:
        print("No history yet.")
        return

    print("\nLast 10 conversions:")
    for line in lines[-10:]:
        print("  " + line)


# ---------- Main ----------

def main():
    try:
        rates = get_rates()
    except requests.exceptions.RequestException:
        print("No internet and no saved rates. Connect once and try again.")
        return

    print("=== Currency Converter ===")
    show_popular(rates)

    while True:
        print("\n1) Convert")
        print("2) Convert to several currencies")
        print("3) View history")
        print("4) Show popular rates")
        print("q) Quit")
        choice = input("Choose: ").strip().lower()

        if choice == "1":
            single_convert(rates)
        elif choice == "2":
            multi_convert(rates)
        elif choice == "3":
            view_history()
        elif choice == "4":
            show_popular(rates)
        elif choice == "q":
            break
        else:
            print("Please choose 1, 2, 3, 4 or q.")

    print("Bye!")


main()