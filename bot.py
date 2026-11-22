import os
import sys
import io
import re
import html
import time
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from ai_engine import ai_engine
import database

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)

CHANNEL_USERNAME = "@frozentools"
CHANNEL_URL = "https://t.me/frozentools"
OWNER_HANDLE = "@moh_maya_official"

def get_platform_label(mode: str) -> str:
    return "⚡ TelebotCreator (TPY - Python)" if mode == "tbc" else "🌐 Bots.Business (BJS - JavaScript)"

def get_welcome_text(user_id: int) -> str:
    current_mode = database.get_user_platform(user_id)
    mode_label = get_platform_label(current_mode)
    return (
        "<b>🤖 Multi-Platform Bot Architect & Code Fixer!</b>\n\n"
        f"🎯 <b>Active Platform Mode:</b> <code>{mode_label}</code>\n\n"
        "<b>✨ Mode Switch Commands:</b>\n"
        "• <b>/bb</b> — Switch to <b>Bots.Business (BJS - JavaScript)</b>\n"
        "• <b>/tbc</b> — Switch to <b>TelebotCreator (TPY - Python)</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🛠️ What you can do:</b>\n"
        "• 🚀 <b>Generate New Bots:</b> Complete command breakdown, wait-for-answer settings, and working code.\n"
        "• 🔧 <b>Fix Errors / Debug:</b> Paste any broken code with error — get 100% fixed code in a 1-click copybox!\n"
        "• 🔄 <b>Upgrade Bots:</b> Request feature additions anytime.\n\n"
        "Select an action below or send your prompt/code! 👇"
    )

def get_join_channel_markup():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Join Channel @frozentools", url=CHANNEL_URL))
    markup.row(InlineKeyboardButton("✅ Check Membership", callback_data="check_membership"))
    return markup

def get_start_markup(user_id: int):
    current_mode = database.get_user_platform(user_id)
    markup = InlineKeyboardMarkup()

    # Mode switch toggle
    if current_mode == "bb":
        markup.row(InlineKeyboardButton("⚡ Switch to TelebotCreator (/tbc)", callback_data="set_mode_tbc"))
    else:
        markup.row(InlineKeyboardButton("🌐 Switch to Bots.Business (/bb)", callback_data="set_mode_bb"))

    markup.row(
        InlineKeyboardButton("🎁 Generate Referral Bot", callback_data="prompt_sample_referral"),
        InlineKeyboardButton("🎮 Generate Giveaway Bot", callback_data="prompt_sample_giveaway")
    )
    markup.row(
        InlineKeyboardButton("🛠️ How to Fix Code", callback_data="prompt_debug_help"),
        InlineKeyboardButton("💎 My Plan & Limits", callback_data="view_plan")
    )
    markup.row(InlineKeyboardButton("🔄 Reset History", callback_data="reset_history"))
    return markup

def is_user_channel_member(user_id: int) -> bool:
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member', 'restricted']:
            return True
        return False
    except Exception as e:
        err_msg = str(e).lower()
        if "member list is inaccessible" in err_msg or "chat not found" in err_msg:
            print(f"[!] Channel check warning: {e}. Bot needs admin permissions in {CHANNEL_USERNAME}.")
            return True
        return False

def require_membership(chat_id: int, user_id: int) -> bool:
    if not is_user_channel_member(user_id):
        join_msg = (
            "<b>🔒 Channel Membership Required!</b>\n\n"
            "To use this bot, you must join our official channel:\n"
            f"👉 <b>{CHANNEL_USERNAME}</b>\n\n"
            "<i>If you leave the channel at any point, access will be blocked immediately.</i>\n\n"
            "Click the button below to join, then press <b>Check Membership</b>."
        )
        try:
            bot.send_message(chat_id, join_msg, reply_markup=get_join_channel_markup(), parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, join_msg, reply_markup=get_join_channel_markup())
        return False
    return True

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    database.get_or_create_user(user_id, username, first_name)

    if not require_membership(message.chat.id, user_id):
        return

    text = get_welcome_text(user_id)
    try:
        bot.reply_to(message, text, reply_markup=get_start_markup(user_id), parse_mode="HTML")
    except Exception:
        bot.reply_to(message, text, reply_markup=get_start_markup(user_id))

@bot.message_handler(commands=['bb'])
def handle_set_bb(message):
    user_id = message.from_user.id
    database.set_user_platform(user_id, 'bb')
    ai_engine.reset_session(user_id)
    reply = (
        "🌐 <b>Platform Mode set to: Bots.Business (BJS)</b>\n\n"
        "• All future bot generations will be strictly in <b>Bots.Business (BJS - JavaScript)</b>.\n"
        "• All error fixes will use BJS APIs (`Api.sendMessage`, `need_reply`, `User.setProperty`).\n"
        "• AI will make ZERO platform confusion mistakes!\n\n"
        "<i>Send your prompt or broken code now!</i>"
    )
    bot.reply_to(message, reply, reply_markup=get_start_markup(user_id), parse_mode="HTML")

@bot.message_handler(commands=['tbc'])
def handle_set_tbc(message):
    user_id = message.from_user.id
    database.set_user_platform(user_id, 'tbc')
    ai_engine.reset_session(user_id)
    reply = (
        "⚡ <b>Platform Mode set to: TelebotCreator (TPY)</b>\n\n"
        "• All future bot generations will be strictly in <b>TelebotCreator (TPY - Python)</b>.\n"
        "• All error fixes will use TelebotCreator APIs (`bot.replyText()`, `Bot.handleNextCommand()`, `User.saveData()`).\n"
        "• AI will make ZERO platform confusion mistakes!\n\n"
        "<i>Send your prompt or broken code now!</i>"
    )
    bot.reply_to(message, reply, reply_markup=get_start_markup(user_id), parse_mode="HTML")

@bot.message_handler(commands=['plan', 'myplan'])
def handle_plan(message):
    user_id = message.from_user.id
    show_plan_details(message.chat.id, user_id)

def show_plan_details(chat_id: int, user_id: int):
    user = database.get_or_create_user(user_id)
    is_premium = bool(user["is_premium"])
    used = user["daily_generations"]
    limit = 15 if is_premium else 3
    remaining = max(0, limit - used)
    current_mode = get_platform_label(user.get("platform_mode", "bb"))

    plan_title = "💎 <b>PREMIUM PLAN</b>" if is_premium else "🆓 <b>FREE PLAN</b>"
    exp_info = ""
    if is_premium and user["premium_expires_at"]:
        exp_info = f"\n• <b>Valid Until:</b> <code>{user['premium_expires_at'][:10]}</code>"

    text = (
        f"📊 <b>Account Status & Usage:</b>\n\n"
        f"• <b>Current Tier:</b> {plan_title}\n"
        f"• <b>Active Platform:</b> <code>{current_mode}</code>\n"
        f"• <b>Daily Code Generations / Fixes:</b> <code>{used} / {limit}</code>\n"
        f"• <b>Remaining Today:</b> <code>{remaining}</code>"
        f"{exp_info}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "💎 <b>Premium Features:</b>\n"
        "• <b>15 Code Generations & Fixes</b> per day\n"
        "• Dedicated Bots.Business (BJS) & TelebotCreator (TPY) support\n"
        "• Priority AI response speed\n"
        "• <b>Price:</b> ₹29 for 7 Days\n\n"
        f"👉 <b>To purchase Premium:</b> Contact Owner: {OWNER_HANDLE}"
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("💬 Contact Owner to Buy", url=f"https://t.me/{OWNER_HANDLE.lstrip('@')}"))
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['reset'])
def handle_reset(message):
    ai_engine.reset_session(message.from_user.id)
    bot.reply_to(message, "🔄 <b>Conversation history reset!</b> You can now start fresh.", parse_mode="HTML")

@bot.message_handler(commands=['help'])
def handle_help(message):
    help_msg = (
        "<b>📖 How to Use:</b>\n\n"
        "1. <b>Select Platform Mode:</b>\n"
        "   • <b>/bb</b> — for Bots.Business (BJS - JavaScript)\n"
        "   • <b>/tbc</b> — for TelebotCreator (TPY - Python)\n\n"
        "2. <b>Generate New Bots:</b> Send your idea:\n"
        "   • <i>'Create a referral reward bot with withdraw and balance'</i>\n\n"
        "3. <b>Fix Errors / Debug Code:</b>\n"
        "   • Paste your code and error message:\n"
        "     <i>'Here is my code and error: [Code + Error] - please fix it'</i>\n\n"
        "4. <b>Check Limits:</b> Use /plan\n"
        "5. <b>Reset History:</b> Use /reset"
    )
    try:
        bot.reply_to(message, help_msg, parse_mode="HTML")
    except Exception:
        bot.reply_to(message, help_msg)

# ---------- ADMIN COMMANDS ----------

@bot.message_handler(commands=['addpremium'])
def handle_add_premium(message):
    sender_uname = (message.from_user.username or "").lower()
    if sender_uname != OWNER_HANDLE.lstrip('@').lower() and message.from_user.id not in [5311223486]:
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: <code>/addpremium &lt;user_id&gt; [days]</code>", parse_mode="HTML")
        return

    try:
        target_uid = int(parts[1])
        days = int(parts[2]) if len(parts) > 2 else 7
        exp = database.add_premium(target_uid, days)
        bot.reply_to(message, f"✅ Premium granted to user <code>{target_uid}</code> for {days} days!\nExpires: {exp}", parse_mode="HTML")
        try:
            bot.send_message(target_uid, f"🎉 <b>Congratulations!</b> Your account has been upgraded to <b>Premium</b> for {days} days!\nYou now get 15 code generations/fixes per day.", parse_mode="HTML")
        except Exception:
            pass
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['removepremium'])
def handle_remove_premium(message):
    sender_uname = (message.from_user.username or "").lower()
    if sender_uname != OWNER_HANDLE.lstrip('@').lower() and message.from_user.id not in [5311223486]:
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: <code>/removepremium &lt;user_id&gt;</code>", parse_mode="HTML")
        return

    try:
        target_uid = int(parts[1])
        database.remove_premium(target_uid)
        bot.reply_to(message, f"✅ Premium removed for user <code>{target_uid}</code>.", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['stats'])
def handle_stats(message):
    sender_uname = (message.from_user.username or "").lower()
    if sender_uname != OWNER_HANDLE.lstrip('@').lower() and message.from_user.id not in [5311223486]:
        return

    st = database.get_stats()
    bot.reply_to(message, f"📊 <b>Bot Stats:</b>\n• Total Users: {st['total_users']}\n• Premium Users: {st['premium_users']}", parse_mode="HTML")

# ---------- CALLBACKS & MESSAGES ----------

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if call.data == "check_membership":
        if is_user_channel_member(user_id):
            bot.send_message(chat_id, "✅ <b>Channel verified!</b> You can now use the bot.", parse_mode="HTML")
            bot.send_message(chat_id, get_welcome_text(user_id), reply_markup=get_start_markup(user_id), parse_mode="HTML")
        else:
            bot.send_message(chat_id, f"❌ You have not joined {CHANNEL_USERNAME} yet! Please join first.", reply_markup=get_join_channel_markup(), parse_mode="HTML")
        return

    if not require_membership(chat_id, user_id):
        return

    if call.data == "set_mode_bb":
        database.set_user_platform(user_id, 'bb')
        ai_engine.reset_session(user_id)
        bot.send_message(chat_id, "🌐 <b>Platform Mode set to: Bots.Business (BJS)</b>\n\nAll requests will now generate strict Bots.Business code.", reply_markup=get_start_markup(user_id), parse_mode="HTML")
        return

    if call.data == "set_mode_tbc":
        database.set_user_platform(user_id, 'tbc')
        ai_engine.reset_session(user_id)
        bot.send_message(chat_id, "⚡ <b>Platform Mode set to: TelebotCreator (TPY)</b>\n\nAll requests will now generate strict TelebotCreator Python code.", reply_markup=get_start_markup(user_id), parse_mode="HTML")
        return

    if call.data == "reset_history":
        ai_engine.reset_session(user_id)
        bot.send_message(chat_id, "🔄 <b>Conversation history reset!</b> Send your new bot prompt or code to fix.", parse_mode="HTML")
        return

    if call.data == "view_plan":
        show_plan_details(chat_id, user_id)
        return

    if call.data == "prompt_debug_help":
        mode = database.get_user_platform(user_id)
        mode_str = "Bots.Business BJS" if mode == "bb" else "TelebotCreator TPY"
        bot.send_message(
            chat_id,
            f"🛠️ <b>How to Fix {mode_str} Code Errors:</b>\n\n"
            "Simply paste your code and explain the error, for example:\n\n"
            "<i>\"Here is my code and error: [paste code] / Error: [paste error message] - please fix this error.\"</i>\n\n"
            "The bot will analyze the bug and return the fixed code in a 1-click copybox!",
            parse_mode="HTML"
        )
        return

    if call.data == "prompt_sample_referral":
        mode = database.get_user_platform(user_id)
        if mode == "tbc":
            p = "Create a complete Referral Reward Telegram Bot in TelebotCreator (TPY - Python) using bot.replyText(), Bot.handleNextCommand(), and libs.Resources balance tracking."
        else:
            p = "Create a complete Referral Reward Telegram Bot in Bots.Business (BJS) where users earn coins per referral, check /balance, get a referral link, and request withdrawal via /withdraw."
        process_prompt(chat_id, user_id, p)
        return

    if call.data == "prompt_sample_giveaway":
        mode = database.get_user_platform(user_id)
        if mode == "tbc":
            p = "Create a Giveaway Bot in TelebotCreator (TPY - Python) where admin can create giveaway with timers and users participate with a button."
        else:
            p = "Create a Giveaway Bot in Bots.Business (BJS) where an admin can host giveaways with timers, participants join with a button, and a random winner is picked."
        process_prompt(chat_id, user_id, p)
        return

@bot.message_handler(func=lambda message: True)
def handle_user_message(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_text = message.text.strip()

    database.get_or_create_user(user_id, message.from_user.username, message.from_user.first_name)

    if not require_membership(chat_id, user_id):
        return

    process_prompt(chat_id, user_id, user_text)

def md_to_telegram_html(text: str) -> str:
    code_blocks = []
    def save_code_block(match):
        lang = match.group(1) or ''
        code = match.group(2)
        code_blocks.append((lang, code))
        return f"___CODE_BLOCK_{len(code_blocks)-1}___"

    text = re.sub(r'```([a-zA-Z0-9_\-+]*)\n?(.*?)```', save_code_block, text, flags=re.DOTALL)

    inline_codes = []
    def save_inline_code(match):
        code = match.group(1)
        inline_codes.append(code)
        return f"___INLINE_CODE_{len(inline_codes)-1}___"

    text = re.sub(r'`([^`]+)`', save_inline_code, text)

    text = html.escape(text)

    # Headers
    text = re.sub(r'^(?:#{1,6})\s+(.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Bullets
    text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)

    # Restore inline code
    for i, code in enumerate(inline_codes):
        text = text.replace(f"___INLINE_CODE_{i}___", f"<code>{html.escape(code)}</code>")

    # Restore code blocks
    for i, (lang, code) in enumerate(code_blocks):
        lang_attr = f' class="language-{html.escape(lang)}"' if lang else ''
        text = text.replace(f"___CODE_BLOCK_{i}___", f"<pre><code{lang_attr}>{html.escape(code.strip())}</code></pre>")

    return text

def send_long_message(chat_id, text, user_id, platform_mode):
    credit_footer = f"\n\ndeveloper : {OWNER_HANDLE}"
    if OWNER_HANDLE not in text:
        text = text.rstrip() + credit_footer

    platform_label = "TelebotCreator (TPY)" if platform_mode == "tbc" else "Bots.Business (BJS)"
    file_caption = (
        f"📄 Complete {platform_label} Code Generated!\n\n"
        "Code kaafi extensive tha, isliye poori file (.md format) attach kar di gayi hai jisme saari commands, code aur details hain.\n\n"
        f"developer : {OWNER_HANDLE}"
    )

    html_text = md_to_telegram_html(text)

    if len(html_text) <= 3900:
        try:
            bot.send_message(chat_id, html_text, parse_mode="HTML", disable_web_page_preview=True)
            return
        except Exception as e:
            print(f"[!] HTML send failed: {e}, falling back to plain text", flush=True)
            bot.send_message(chat_id, text)
            return

    if len(html_text) <= 8500:
        raw_parts = re.split(r'(?=<b>(?:📌\s*)?Command:)', html_text, flags=re.IGNORECASE)
        if len(raw_parts) <= 1:
            raw_parts = html_text.split("\n\n---\n\n")

        parts = []
        curr = ""
        for p in raw_parts:
            if len(curr) + len(p) + 2 > 3800:
                if curr:
                    parts.append(curr)
                curr = p
            else:
                curr = curr + "\n\n" + p if curr else p
        if curr:
            parts.append(curr)

        all_sent = True
        for part in parts:
            try:
                bot.send_message(chat_id, part, parse_mode="HTML", disable_web_page_preview=True)
            except Exception as e:
                print(f"[!] Part HTML send failed: {e}", flush=True)
                try:
                    bot.send_message(chat_id, part)
                except Exception:
                    all_sent = False

        if all_sent:
            return

    filename = "telebotcreator_tpy_code.md" if platform_mode == "tbc" else "bots_business_code.md"
    file_bytes = io.BytesIO(text.encode('utf-8'))
    file_bytes.name = filename
    try:
        bot.send_document(chat_id, file_bytes, caption=file_caption)
    except Exception as e:
        print(f"[!] Document send error: {e}", flush=True)
        bot.send_document(chat_id, file_bytes)

def process_prompt(chat_id, user_id, prompt):
    print(f"[*] [User {user_id}] Received prompt: {prompt}", flush=True)
    can_generate, used, limit, is_premium = database.check_daily_limit(user_id)
    if not can_generate:
        limit_msg = (
            "⚠️ <b>Daily Generation Limit Reached!</b>\n\n"
            f"You have used all <b>{limit}</b> code generations for today.\n\n"
            "💎 <b>Upgrade to Premium:</b>\n"
            "• <b>15 Code Generations & Fixes</b> per day\n"
            "• Both Bots.Business (BJS) & TelebotCreator (TPY) support\n"
            "• Priority AI response speed\n"
            "• <b>Price:</b> ₹29 for 7 Days\n\n"
            f"👉 <b>To purchase Premium, contact Owner:</b> {OWNER_HANDLE}"
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("💬 Buy Premium (₹29 / 7 Days)", url=f"https://t.me/{OWNER_HANDLE.lstrip('@')}"))
        bot.send_message(chat_id, limit_msg, reply_markup=markup, parse_mode="HTML")
        return

    platform_mode = database.get_user_platform(user_id)
    is_debug_request = any(w in prompt.lower() for w in ['error', 'fix', 'bug', 'debug', 'solve', 'issue', 'not working'])

    if is_debug_request:
        mode_label = "TelebotCreator TPY" if platform_mode == "tbc" else "Bots.Business BJS"
        status_header = f"🛠️ <b>Analyzing & Fixing {mode_label} Code...</b>"
    elif platform_mode == "tbc":
        status_header = "⚡ <b>Designing TelebotCreator (TPY) Code...</b>"
    else:
        status_header = "🌐 <b>Designing Bots.Business (BJS) Code...</b>"

    status_msg = None
    try:
        status_msg = bot.send_message(
            chat_id,
            f"{status_header}\n<i>Processing syntax, commands, and logic. Please wait 10-15 seconds...</i>",
            parse_mode="HTML"
        )
    except Exception:
        pass

    try:
        bot.send_chat_action(chat_id, 'typing')
        response = ai_engine.generate_response(user_id, prompt, platform_mode=platform_mode)

        database.increment_daily_count(user_id)

        if status_msg:
            try:
                bot.delete_message(chat_id, status_msg.message_id)
            except Exception:
                pass

        send_long_message(chat_id, response, user_id, platform_mode)

        user_info = database.get_or_create_user(user_id)
        rem = max(0, limit - user_info["daily_generations"])
        quota_text = f"💡 <i>Remaining daily generations: {rem}/{limit} | Mode: {get_platform_label(platform_mode)}</i>"
        try:
            bot.send_message(chat_id, quota_text, parse_mode="HTML")
        except Exception:
            pass

    except Exception as e:
        print(f"[!] Error in process_prompt: {e}", flush=True)
        bot.send_message(chat_id, f"⚠️ Error: {str(e)}")

# ---------- BACKGROUND EXPIRY NOTIFICATION THREAD ----------

def expiry_checker_loop():
    while True:
        try:
            expiring_users = database.get_expiring_premium_users()
            for u in expiring_users:
                uid = u["user_id"]
                exp_date = u["premium_expires_at"][:10]
                warning_text = (
                    "⚠️ <b>Premium Expiration Notice!</b>\n\n"
                    f"Your Premium subscription will expire on <b>{exp_date}</b> (within 2 days).\n\n"
                    f"To renew your plan for another 7 days (₹29), please contact owner: {OWNER_HANDLE}"
                )
                try:
                    bot.send_message(uid, warning_text, parse_mode="HTML")
                    database.mark_expiry_warned(uid)
                except Exception as e:
                    print(f"[!] Could not send expiry warning to {uid}: {e}")
        except Exception as e:
            print(f"[!] Expiry checker loop error: {e}")
        time.sleep(3600)

t = threading.Thread(target=expiry_checker_loop, daemon=True)
t.start()

if __name__ == '__main__':
    print("[*] Multi-Platform BJS & TPY Bot Architect is running...")
    print(f"[*] Token: {config.TELEGRAM_BOT_TOKEN[:10]}...")
    bot.infinity_polling(skip_pending=True)
