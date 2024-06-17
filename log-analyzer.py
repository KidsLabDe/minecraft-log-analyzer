import os
import re
import telegram
import argparse



from config import BOT_TOKEN, CHAT_ID, LOG_DIR


# create the Telegram bot
if (BOT_TOKEN != '' and CHAT_ID != ''):
    bot = telegram.Bot(token=BOT_TOKEN)

# define a list to store the chat messages
chat_messages = []



# create a argument parser
parser = argparse.ArgumentParser(description='Parse the latest log files and send the results to a Telegram bot.')
parser.add_argument('--telegram', action='store_true', help='send results to Telegram bot')
parser.add_argument('--reset', action='store_true', help='reset all state files')
parser.add_argument('--logdir', help='set the log directory')


# parse the command-line arguments
args = parser.parse_args()

if args.logdir:
    LOG_DIR = args.logdir
    
# reset all state files if the --reset argument is specified
if args.reset:
    for root, dirs, files in os.walk(LOG_DIR):
        for file in files:
            if file.endswith('.state'):
                state_file = os.path.join(root, file)
                print("Removing state file: " + state_file)
                os.remove(state_file)


def parse_chat_messages(log_file, state_file):
    # read the last line of the log file that was parsed
    last_line = ''
    if os.path.isfile(state_file):
        with open(state_file, 'r') as file:
            last_line = file.read().strip()

    with open(log_file, 'r') as file:
        # skip lines that have already been parsed
        if last_line:
            for line in file:
                if line.strip() == last_line:
                    break
        # parse new lines
        for line in file:
            chat_match = re.search(r'\[Server thread/INFO\]: <(.+)> (.+)', line)
            if chat_match:
                username = chat_match.group(1)
                message = chat_match.group(2)
                chat_messages.append(f"{username} sagt: {message}")                    
            join_match = re.search(r'\[Server thread/INFO\]: (.+) joined the game', line)
            if join_match:
                username = join_match.group(1)
                chat_messages.append(f"{username} hat das Spiel betreten.")
    # create a table to display the results

    # send the chat messages to the Telegram bot if it has entries
    if args.telegram and len(chat_messages) > 0:
        message = 'Log-Datei:\n' + log_file + '\n\nLog-Einträge:\n' + '\n'.join(chat_messages)
        # message = 'Log-Einträge:\n' + '\n'.join(chat_messages)
        bot.send_message(chat_id=CHAT_ID, text=message)
    # output the chat messages to the console if it has entries
    elif not args.telegram and len(chat_messages) > 0:
        print('Log-Datei:\n' + log_file)
        print('Log-Einträge:')
        for message in chat_messages:
            print(message)
# write the last line of the log file that was parsed to the state file
    with open(state_file, 'w') as file:
        file.write(line.strip())
    # clear the chat messages and action counts for the next log file
    chat_messages.clear()

# loop through all log files in the logs directory and its subdirectories
for root, dirs, files in os.walk(LOG_DIR):
    for file in files:
        if file == 'console.out':
            log_file = os.path.join(root, file)
            state_file = os.path.join(LOG_DIR, file + '.state')
            print("Processing log file: " + log_file)
            parse_chat_messages(log_file, state_file)