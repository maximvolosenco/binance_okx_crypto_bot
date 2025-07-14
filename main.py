import telebot
import time
import requests
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is running!')

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"Web server starting on port {port}")
    server.serve_forever()
  
def get_crypto_data():
    binance_data = requests.get("https://api.binance.com/api/v3/ticker/price").json()

    okx = requests.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT").json()

    okx_data = [dict(item, instId=item['instId'].replace('-', '')) for item in okx.get('data')]

    display_items = []
    for binance_item in binance_data:
        for okx_item in okx_data:
            if binance_item.get('symbol') == okx_item.get('instId'):
                value_diff, percentage_diff = percentage_difference(float(okx_item.get('last')), float(binance_item.get('price')))

                if percentage_diff > 0.2:
                    display_items.append(
                        {
                            "symbol": binance_item.get('symbol'),
                            "okx_price": okx_item.get('last'),
                            "binance_price": binance_item.get('price'),
                            "value_diff": value_diff,
                            "percentage_diff": percentage_diff,
                        }
                    )

    display_items.sort(key=lambda x: x['percentage_diff'], reverse=True)

    return display_items

def percentage_difference(value1, value2):
    if value1 == 0 and value2 == 0:
        return 0.0
    
    difference = abs(value1 - value2)
    average = (value1 + value2) / 2
    
    if average == 0:
        return float('inf')
    
    percentage_diff = (difference / average) * 100
    return int(difference * 10000) / 10000, int(percentage_diff * 100) / 100

def set_separator_line_column(length):
    return "-" * length

def set_separator_line(column_1_len, column_2_len, column_3_len, column_4_len):
    return f"{set_separator_line_column(column_1_len)}|{set_separator_line_column(column_2_len)}|{set_separator_line_column(column_3_len)}|{set_separator_line_column(column_4_len)}\n"

def set_table_header(column_1_len, column_2_len, column_3_len, column_4_len):
    header_lines = f"<pre>{adapt_column_len('Nr', column_1_len)}|{adapt_column_len('Diff', column_2_len)}|{adapt_column_len('OKX', column_3_len)}|{adapt_column_len('Binance', column_4_len)}\n"
    header_lines += set_separator_line(column_1_len, column_2_len, column_3_len, column_4_len)
    return header_lines

def adapt_column_len(table_text, column_len):
    table_text = str(table_text)
    if len(table_text) < column_len:
        spaces_to_add = column_len - len(table_text)
        table_text += " " * spaces_to_add

    return table_text[:column_len]
    # return table_text

def get_tables(column_1_len=4, column_2_len=13, column_3_len=12, column_4_len=12):
    display_items = get_crypto_data()
    tables = []
    table_text = set_table_header(column_1_len, column_2_len, column_3_len, column_4_len)

    higher_price_string = "🟢"
    lower_price_string = "🔴"

    for index, item in enumerate(display_items[:], 1):
        if item.get('okx_price') < item.get('binance_price'):
            okx_indicator = lower_price_string
            binance_indicator = higher_price_string
        else:
            okx_indicator = higher_price_string
            binance_indicator = lower_price_string
        
        okx_price = f"{okx_indicator}{item.get('okx_price')}"
        binance_price = f"{binance_indicator}{item.get('binance_price')}"
        percentage_diff = f"{item.get('percentage_diff')}%"

        table_text += f"{adapt_column_len('', column_1_len)}|{adapt_column_len(item.get('symbol'), column_2_len)}|{adapt_column_len('', column_3_len)}|\n"
        table_text += f"{adapt_column_len(index, column_1_len)}|{adapt_column_len(percentage_diff, column_2_len)}|{adapt_column_len(okx_price, column_3_len-1)}|{adapt_column_len(binance_price, column_4_len)}\n"
        table_text += f"{adapt_column_len('', column_1_len)}|{adapt_column_len(item.get('value_diff'), column_2_len)}|{adapt_column_len('', column_3_len)}|\n"
        table_text += set_separator_line(column_1_len, column_2_len, column_3_len, column_4_len)

        if len(table_text) > 3800:
            table_text += "</pre>"
            tables.append(table_text)
            table_text = set_table_header(column_1_len, column_2_len, column_3_len, column_4_len)

    table_text += "</pre>"

    tables.append(table_text)

    return tables

def run_bot(bot, chat_id):
    while True:
        tables = get_tables()
        try:
            for table_text in tables:
                bot.send_message(chat_id,  text=table_text,  parse_mode='HTML')
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(300)


if __name__ == "__main__":
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    CHAT_ID = os.environ.get('CHAT_ID')

    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    bot = telebot.TeleBot(BOT_TOKEN)

    while True:
        tables = get_tables()
        try:
            for table_text in tables:
                bot.send_message(CHAT_ID,  text=table_text,  parse_mode='HTML')
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(300)
    # run_bot(bot, CHAT_ID)
