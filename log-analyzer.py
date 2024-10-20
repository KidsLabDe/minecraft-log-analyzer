import os
import re
import telegram
import argparse
from config import BOT_TOKEN, CHAT_ID, LOG_DIR

# ANSI escape sequences for colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def setup_telegram_bot(token, chat_id):
    try:
        bot = telegram.Bot(token=token)
        return bot
    except telegram.error.InvalidToken:
        print("Invalid Telegram bot token")
        return None

def parse_log_file(log_file, state_file):
    print(state_file)
    parsed_chat_messages = []
    last_line = ''
    if os.path.isfile(state_file):
        with open(state_file, 'r') as state:
            last_line = state.read().strip()

    with open(log_file, 'r') as file:
        lines = file.readlines()

    # Find the last occurrence of the last parsed line
    start_index = 0
    last_line_found = None
    last_line_number = None
    if last_line:
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == last_line:
                start_index = i + 1
                last_line_found = lines[i].strip()
                last_line_number = i + 1
                break



# Example usage
#-print(f"{Colors.OKGREEN}This is green text{Colors.ENDC}")
#print(f"{Colors.WARNING}This is a warning{Colors.ENDC}")
#print(f"{Colors.FAIL}This is an error{Colors.ENDC}")
    if last_line_found:
        print(f"{Colors.OKGREEN}Last line found: '{last_line_found}' at line number {last_line_number}")
    else:
        print(f"{Colors.WARNING}Last line not found")

    # Parse new lines
    for line in lines[start_index:]:
        chat_match = re.search(r'\[Server thread/INFO\]: <(.+)> (.+)', line)
        last_line = line
        if chat_match:
            username = chat_match.group(1)
            message = chat_match.group(2)
            parsed_chat_messages.append(f"{username} sagt: {message}")
            print(f"{Colors.OKCYAN}{username} sagt: {message}")

    # write the last line of the log file that was parsed to the state file
    with open(state_file, 'w') as file:
        file.write(last_line.strip())
        print(f"letzte Zeile:" + last_line.strip())



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
                state_file = os.path.join(root, file + '.state')
                print("Processing log file: " + log_file)
                parsed_chat_messages = parse_log_file(log_file, state_file)
                if args.telegram:
                    send_messages_to_telegram(bot, CHAT_ID, parsed_chat_messages)
                else:
                    for message in parsed_chat_messages:
                        print(message)

if __name__ == "__main__":
    main()