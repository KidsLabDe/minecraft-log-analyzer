import os
import re
import telegram
import argparse
from config import BOT_TOKEN, CHAT_ID, LOG_DIR

def setup_telegram_bot(token, chat_id):
    try:
        bot = telegram.Bot(token=token)
        return bot
    except telegram.error.InvalidToken:
        print("Invalid Telegram bot token")
        return None

def parse_log_file(log_file, state_file):
    parsed_chat_messages = []
    try:
        with open(log_file, 'r') as file:
            # Read the last line of the log file that was parsed
            last_line = ''
            if os.path.isfile(state_file):
                with open(state_file, 'r') as state:
                    last_line = state.read().strip()

            # Skip lines that have already been parsed
            for line in file:
                if line.strip() == last_line:
                    break

            # Parse new lines
            for line in file:
                chat_match = re.search(r'\[Server thread/INFO\]: <(.+)> (.+)', line)
                if chat_match:
                    username = chat_match.group(1)
                    message = chat_match.group(2)
                    parsed_chat_messages.append(f"{username} sagt: {message}")
                join_match = re.search(r'\[Server thread/INFO\]: (.+) joined the game', line)
                if join_match:
                    username = join_match.group(1)
                    parsed_chat_messages.append(f"{username} hat das Spiel betreten.")
    except Exception as e:
        print(f"Error parsing log file: {e}")
        return []

    return parsed_chat_messages

def send_messages_to_telegram(bot, chat_id, messages):
    try:
        for message in messages:
            bot.send_message(chat_id=chat_id, text=message)
    except telegram.error.NetworkError:
        print("Error sending message to Telegram bot")

def main():
    parser = argparse.ArgumentParser(description='Parse the latest log files and send the results to a Telegram bot.')
    parser.add_argument('--telegram', action='store_true', help='send results to Telegram bot')
    parser.add_argument('--reset', action='store_true', help='reset all state files')
    parser.add_argument('--logdir', help='set the log directory')
    args = parser.parse_args()

    if args.logdir:
        LOG_DIR = args.logdir

    if args.reset:
        for root, dirs, files in os.walk(LOG_DIR):
            for file in files:
                if file.endswith('.state'):
                    state_file = os.path.join(root, file)
                    print("Removing state file: " + state_file)
                    os.remove(state_file)

    bot = setup_telegram_bot(BOT_TOKEN, CHAT_ID)
    if bot is None:
        return

    for root, dirs, files in os.walk(LOG_DIR):
        for file in files:
            if file == 'console.out':
                log_file = os.path.join(root, file)
                state_file = os.path.join(LOG_DIR, file + '.state')
                print("Processing log file: " + log_file)
                parsed_chat_messages = parse_log_file(log_file, state_file)
                if args.telegram:
                    send_messages_to_telegram(bot, CHAT_ID, parsed_chat_messages)
                else:
                    for message in parsed_chat_messages:
                        print(message)

if __name__ == '__main__':
    main()