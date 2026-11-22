import os
import json
import config
from openai import OpenAI

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

BB_SYSTEM_PROMPT = """You are an EXPERT Bots.Business (BJS - Bot Java Script) Developer, Debugger, and Software Architect.

⚠️ STRICT PLATFORM RULE:
You are in BOTS.BUSINESS (BJS) MODE.
Generate ONLY 100% pure Bots.Business BJS (JavaScript) code.
DO NOT use Python, Telebot, TelebotCreator, Aiogram, Node.js, or any other framework.
All descriptions, breakdowns, explanations, and responses MUST BE IN CLEAR, PROFESSIONAL ENGLISH.

⚠️ NEVER REFUSE TO GENERATE CODE:
You must NEVER refuse a request or say "I can't produce" or ask the user to provide API endpoints/schemas.
If a user provides an API URL (e.g. Vercel, Render, or custom domain), you MUST assume/construct standard REST endpoints (e.g. `https://.../api?url=` or `?url=`), write complete HTTP requests (`HTTP.get`), handle JSON responses, errors, private accounts, and provide 100% production-ready, complete code!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### CASE 1: USER REQUESTS A NEW BOT OR FEATURE
Provide a comprehensive Bots.Business command breakdown using this EXACT format for each command:

### 📌 Command: `/command_name`
- **Platform**: Bots.Business (BJS - JavaScript)
- **Wait for Answer (need_reply)**: `ON (true)` OR `OFF (false)`
  - **Reason**: [Clear English explanation why need_reply is ON or OFF]
- **Answer Field (Default Message)**: [The text message to be placed in the Bots.Business Answer field]
- **Keyboard / Buttons**: [InlineKeyboardMarkup or ReplyKeyboardMarkup layout if applicable]
- **BJS Code**:
```javascript
// Production-ready Bots.Business JavaScript Code
// Standard APIs:
// - Api.sendMessage({ chat_id: chat.chatid, text: "...", parse_mode: "html" })
// - User.setProperty("prop_name", value, "string" | "integer") / User.getProperty("prop_name")
// - Bot.run({ command: "cmd_name", options: { ... } })
// - Bot.getProperty("prop_name") / Bot.setProperty("prop_name", value)
// - Libs.ResourcesLib.user.res("coins")
// - request.data (for callback query), message, user.telegramid, chat.chatid
```

At the end of bot generation, provide:
### 🚀 Suggested Upgrades:
List 3 to 5 powerful upgrades (e.g., Anti-cheat & self-referral detection, Channel Join Verification via `Api.getChatMember`, Admin Broadcast, Daily Streak).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### CASE 2: FIXING BJS CODE & ERRORS
If user provides code with an error:
1. 🔍 **Error Diagnosis**: Explain what caused the bug in 2-3 clear bullet points.
2. 🛠️ **The Solution**: Explain how it was resolved.
3. 📋 **Fixed BJS Code (1-Click Copybox)**:
```javascript
// Complete Fixed Bots.Business BJS Code
```
4. ⚙️ **Command Setting**: Specify if `Wait for Answer (need_reply)` is ON or OFF.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### MANDATORY FOOTER:
At the very end of every single response, you MUST include:
developer : @moh_maya_official
"""

TBC_SYSTEM_PROMPT = """You are an EXPERT TelebotCreator (TPY - Telebot Python) Developer, Debugger, and Software Architect.

⚠️ STRICT PLATFORM RULE:
You are in TELEBOTCREATOR (TPY) MODE.
Generate ONLY 100% pure TelebotCreator (TPY - Python) code.
DO NOT use JavaScript, Bots.Business BJS, or any external framework.
All descriptions, breakdowns, explanations, and responses MUST BE IN CLEAR, PROFESSIONAL ENGLISH.

⚠️ NEVER REFUSE TO GENERATE CODE:
You must NEVER refuse a request or say "I can't produce" or ask the user to provide API endpoints/schemas.
If a user provides an API URL (e.g. Vercel, Render, or custom domain), you MUST assume/construct standard REST endpoints (e.g. `https://.../api?url=` or `?url=`), write complete HTTP requests (`HTTP.get`), handle JSON responses, errors, private accounts, and provide 100% production-ready, complete code!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### CASE 1: USER REQUESTS A NEW BOT OR FEATURE
Provide a comprehensive TelebotCreator command breakdown using this EXACT format for each command:

### 📌 Command: `/command_name`
- **Platform**: TelebotCreator (TPY - Python)
- **Wait for Answer / Next Command**: `Bot.handleNextCommand("/next_cmd")` OR `None`
  - **Reason**: [Explain why next command handler is needed or None]
- **Buttons / Keyboard**: [ReplyKeyboardMarkup(True) or InlineKeyboardMarkup layout]
- **TPY Python Code**:
```python
# Pure TelebotCreator Python (TPY) Code
# Standard TelebotCreator APIs:
# - bot.replyText(u, text, parse_mode="HTML")
# - bot.sendMessage(text, parse_mode="HTML") or bot.sendMessage(chat_id=message.chat.id, text=...)
# - bot.replyPhoto(u, photo="url", caption="...", parse_mode="HTML")
# - bot.deleteMessage(chat_id=message.chat.id, message_id=message.message_id)
# - Bot.handleNextCommand("/next_command") (for multi-step input capture)
# - User.saveData("key", value) / User.getData("key")
# - Bot.setProperty("key", value) / Bot.getProperty("key")
# - balance = libs.Resources.userRes('balance')
# - check = MembershipCheck("@channel", u)
# - params (arguments like /cmd 123)
# - raise ReturnCommand() (to exit early)
```

At the end of bot generation, provide:
### 🚀 Suggested Upgrades:
List 3 to 5 powerful upgrades (e.g., Anti-cheat & self-referral detection, Channel Join Verification via MembershipCheck, Admin Broadcast, Daily Streak).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### CASE 2: FIXING TPY CODE & ERRORS
If user provides code with an error:
1. 🔍 **Error Diagnosis**: Explain what caused the bug in 2-3 clear bullet points.
2. 🛠️ **The Solution**: Explain how it was resolved.
3. 📋 **Fixed TPY Code (1-Click Copybox)**:
```python
# Complete Fixed TelebotCreator TPY Code
```
4. ⚙️ **Command Setting**: Specify if `Bot.handleNextCommand()` is required.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### MANDATORY FOOTER:
At the very end of every single response, you MUST include:
developer : @moh_maya_official
"""

class BotArchitectAI:
    def __init__(self):
        self.user_sessions = {}
        self.exa_client = None
        self.openrouter_client = None
        self.gemini_client = None

        if config.EXA_API_KEY:
            try:
                self.exa_client = OpenAI(
                    base_url=config.EXA_BASE_URL,
                    api_key=config.EXA_API_KEY
                )
                print(f"[*] Exa AI Client initialized with base_url: {config.EXA_BASE_URL}")
            except Exception as e:
                print(f"[!] Error initializing Exa: {e}")

        if config.OPENROUTER_API_KEY:
            try:
                self.openrouter_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=config.OPENROUTER_API_KEY,
                    default_headers={
                        "HTTP-Referer": "https://github.com/alonepro098/bjs-architect-telegram-bot",
                        "X-Title": "BJS & TPY Bot Architect"
                    }
                )
                print(f"[*] OpenRouter Client initialized with model: {config.OPENROUTER_MODEL}")
            except Exception as e:
                print(f"[!] Error initializing OpenRouter: {e}")

        if HAS_GENAI and config.GEMINI_API_KEY:
            try:
                self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
                print("[*] Gemini Client initialized.")
            except Exception as e:
                print(f"[!] Error initializing Gemini: {e}")

    def reset_session(self, user_id: int):
        self.user_sessions[user_id] = []

    def get_system_prompt(self, platform_mode: str) -> str:
        if platform_mode == 'tbc':
            return TBC_SYSTEM_PROMPT
        return BB_SYSTEM_PROMPT

    def generate_response(self, user_id: int, user_prompt: str, platform_mode: str = 'bb') -> str:
        provider = config.AI_PROVIDER.lower()
        system_prompt = self.get_system_prompt(platform_mode)

        if provider == "exa" or (config.EXA_API_KEY and self.exa_client and provider != "gemini" and provider != "openrouter"):
            try:
                return self._generate_exa(user_id, user_prompt, system_prompt)
            except Exception as e:
                print(f"[!] Exa error: {e}")
                if self.gemini_client:
                    try:
                        return self._generate_gemini(user_id, user_prompt, system_prompt)
                    except Exception as ge:
                        print(f"[!] Gemini fallback error: {ge}")
                if self.openrouter_client:
                    try:
                        return self._generate_openrouter(user_id, user_prompt, system_prompt)
                    except Exception as oe:
                        print(f"[!] OpenRouter fallback error: {oe}")
                return f"⚠️ **Exa AI Error:**\n`{str(e)}`"

        if provider == "openrouter" or (config.OPENROUTER_API_KEY and self.openrouter_client):
            try:
                return self._generate_openrouter(user_id, user_prompt, system_prompt)
            except Exception as e:
                print(f"[!] OpenRouter error: {e}")
                if self.exa_client:
                    try:
                        return self._generate_exa(user_id, user_prompt, system_prompt)
                    except Exception as ee:
                        print(f"[!] Exa fallback error: {ee}")
                if self.gemini_client:
                    try:
                        return self._generate_gemini(user_id, user_prompt, system_prompt)
                    except Exception as ge:
                        print(f"[!] Gemini fallback error: {ge}")
                return f"⚠️ **OpenRouter API Error:**\n`{str(e)}`"

        if self.gemini_client:
            try:
                return self._generate_gemini(user_id, user_prompt, system_prompt)
            except Exception as e:
                print(f"[!] Gemini error: {e}")
                if self.exa_client:
                    try:
                        return self._generate_exa(user_id, user_prompt, system_prompt)
                    except Exception as ee:
                        print(f"[!] Exa fallback error: {ee}")
                if self.openrouter_client:
                    try:
                        return self._generate_openrouter(user_id, user_prompt, system_prompt)
                    except Exception as oe:
                        print(f"[!] OpenRouter fallback error: {oe}")
                return f"⚠️ **Gemini API Error:**\n`{str(e)}`"

        if self.exa_client:
            try:
                return self._generate_exa(user_id, user_prompt, system_prompt)
            except Exception as e:
                return f"⚠️ **Exa AI Error:**\n`{str(e)}`"

        return "⚠️ **No AI API Key Configured!**\nPlease set `EXA_API_KEY`, `OPENROUTER_API_KEY`, or `GEMINI_API_KEY` in environment variables."

    def _generate_exa(self, user_id: int, user_prompt: str, system_prompt: str) -> str:
        print(f"[*] Calling Exa AI (model: exa) for user {user_id}...", flush=True)
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = [{"role": "system", "content": system_prompt}]
        else:
            self.user_sessions[user_id][0] = {"role": "system", "content": system_prompt}

        sess = self.user_sessions[user_id]
        sess.append({"role": "user", "content": user_prompt})

        messages_to_send = [sess[0]] + sess[-10:] if len(sess) > 11 else sess

        response = self.exa_client.chat.completions.create(
            model="exa",
            messages=messages_to_send
        )

        reply = response.choices[0].message.content or "Received empty response from Exa AI."

        refusal_triggers = ["can't produce", "cannot produce", "don't include the actual", "search results don't include", "paste the real"]
        if any(trig in reply.lower() for trig in refusal_triggers):
            print(f"[*] Exa returned a search refusal. Falling back to Gemini...", flush=True)
            if self.gemini_client:
                return self._generate_gemini(user_id, user_prompt, system_prompt)

        sess.append({"role": "assistant", "content": reply})

        if len(sess) > 15:
            self.user_sessions[user_id] = [sess[0]] + sess[-10:]

        return reply

    def _generate_openrouter(self, user_id: int, user_prompt: str, system_prompt: str) -> str:
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = [{"role": "system", "content": system_prompt}]
        else:
            # Always ensure current active platform prompt is used
            self.user_sessions[user_id][0] = {"role": "system", "content": system_prompt}

        sess = self.user_sessions[user_id]
        sess.append({"role": "user", "content": user_prompt})

        messages_to_send = [sess[0]] + sess[-10:] if len(sess) > 11 else sess

        response = self.openrouter_client.chat.completions.create(
            model=config.OPENROUTER_MODEL or "deepseek/deepseek-chat",
            messages=messages_to_send,
            temperature=0.3,
            max_tokens=5000
        )

        reply = response.choices[0].message.content or "Received empty response from OpenRouter."
        sess.append({"role": "assistant", "content": reply})

        if len(sess) > 15:
            self.user_sessions[user_id] = [sess[0]] + sess[-10:]

        return reply

    def _generate_gemini(self, user_id: int, user_prompt: str, system_prompt: str) -> str:
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []

        history = self.user_sessions[user_id]

        contents = []
        for msg in history[-6:]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["text"])]
            ))
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_prompt)]
        ))

        config_obj = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=6000
        )

        response = self.gemini_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=contents,
            config=config_obj
        )

        reply = response.text or "Received empty response from AI. Please try again."
        history.append({"role": "user", "text": user_prompt})
        history.append({"role": "model", "text": reply})
        if len(history) > 10:
            self.user_sessions[user_id] = history[-8:]

        return reply

ai_engine = BotArchitectAI()
