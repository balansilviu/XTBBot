from api.xtb_api import Client
import sys

client = Client()

response = client.login("17209604", "+Vaslui69BAL1")

if response is None:
    print("Login OK")
    all_symbols = client.get_all_symbols()
    print(client.get_lastn_candle_history("EURUSD", 60, 1))
else:
    print("Invalid username or password", file=sys.stderr)

