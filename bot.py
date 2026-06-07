import os
import json
import urllib.request

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_KEY = os.environ.get("GEMINI_KEY", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

SYSTEM = """You are Veera, a warm caring male best friend like a close brother. Talk about work, career, stress, goals, feelings, relationships, family, daily life. Reply in 2-3 sentences max like a real friend. Be casual, honest, supportive. Use bro/yaar naturally. Ask one follow-up question. Support English, Hindi, Kannada, Tamil, Telugu. Reply in same language user writes. No bullet points."""

conversations = {}

def ask_gemini(user_id, user_message):
    if user_id not in conversations:
        conversations[user_id] = []
    conversations[user_id].append({"role": "user", "parts": [{"text": user_message}]})
    if len(conversations[user_id]) > 10:
        conversations[user_id] = conversations[user_id][-10:]
    contents = [{"role": m["role"], "parts": m["parts"]} for m in conversations[user_id]]
    if contents:
        contents[0]["parts"][0]["text"] = SYSTEM + "\n\n" + contents[0]["parts"][0]["text"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = json.dumps({"contents": contents, "generationConfig": {"maxOutputTokens": 200, "temperature": 0.9}}).encode()
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
        reply = result["candidates"][0]["content"]["parts"][0]["text"]
        conversations[user_id].append({"role": "model", "parts": [{"text": reply}]})
        return reply
    except Exception as e:
        return f"Small issue bro, try again! {e}"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except:
        pass

def set_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    payload = json.dumps({"url": f"{WEBHOOK_URL}/webhook"}).encode()
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            print("Webhook:", r.read())
    except Exception as e:
        print("Webhook error:", e)

from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Veera is running!")
    def do_POST(self):
        if self.path == "/webhook":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                update = json.loads(body)
                msg = update.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "")
                if chat_id:
                    if text == "/start":
                        send_message(chat_id, "Hey bro! 🌟 I'm Veera, your personal best friend! Talk to me about anything — work, life, feelings, everything. What's on your mind today? 😊")
                    elif text:
                        reply = ask_gemini(str(chat_id), text)
                        send_message(chat_id, reply)
            except Exception as e:
                print("Error:", e)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting on port {port}")
    set_webhook()
    server = HTTPServer(("0.0.0.0", port), Handler)
    print("Veera is live!")
    server.serve_forever()
