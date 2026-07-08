import telebot
import requests
import sys
import os
import html as html_lib
from datetime import datetime

BOT_TOKEN = "8924492918:AAEiJafRy_Xi0Hz4XyCFOSZ-Or70AY_0jdI"  # <-- Put your BotFather token here
SEARXNG_URL = "https://global-scraping-production.up.railway.app"


def test_searxng_connection():
    """Test if SearXNG is working before starting the bot"""
    print("Testing SearXNG connection...")
    try:
        r = requests.get(
            f"{SEARXNG_URL}/search",
            params={"q": "test", "format": "json"},
            timeout=15
        )
        print(f"Status Code: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                result_count = len(data.get("results", []))
                print(f"SearXNG working! Got {result_count} results for test query.")
                return True
            except ValueError:
                print("SearXNG responded but NOT in JSON format.")
                print("   Fix: check that settings.yml has 'formats: [html, json]',")
                print("   then redeploy on Railway.")
                print(f"   Raw response (first 300 chars): {r.text[:300]}")
                return False
        else:
            print(f"SearXNG returned status {r.status_code}")
            print(f"   Response: {r.text[:300]}")
            return False

    except requests.exceptions.ConnectionError:
        print("Connection failed - SearXNG URL is wrong or server is down.")
        return False
    except requests.exceptions.Timeout:
        print("Request timed out - server slow or not responding.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def check_bot_token():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN.strip():
        print("BOT_TOKEN is not set! Put your real token at the top of this script.")
        print("   Get a token from BotFather: t.me/BotFather -> /newbot")
        return False
    return True


# ---------- Pre-flight checks ----------
print("=" * 50)
print("SHUVO AI Global Search Bot - Starting checks")
print("=" * 50)

if not check_bot_token():
    sys.exit(1)

searxng_ok = test_searxng_connection()
if not searxng_ok:
    print("\nWarning: SearXNG has an issue, but the bot will still start.")
    print("   Search command may not work until SearXNG is fixed.\n")

print("=" * 50)

# ---------- Bot setup ----------
bot = telebot.TeleBot(BOT_TOKEN)


def global_search_full(query):
    """
    Gets the FULL JSON response from SearXNG - all fields, all results,
    no truncation. Used to build the HTML file.
    """
    try:
        params = {
            "q": query,
            "format": "json",
            "language": "en",
        }
        response = requests.get(f"{SEARXNG_URL}/search", params=params, timeout=20)
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            return {"error": "SearXNG did not return JSON. Check settings.yml formats config."}

        return data

    except requests.exceptions.RequestException as e:
        return {"error": f"Search server error: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


def build_html_report(query, data):
    """
    Builds a full, styled HTML file with every result and every field
    SearXNG returned - not limited by Telegram's message size.
    """
    results = data.get("results", [])
    answers = data.get("answers", [])
    infoboxes = data.get("infoboxes", [])
    suggestions = data.get("suggestions", [])
    corrections = data.get("corrections", [])
    number_of_results = data.get("number_of_results", len(results))

    safe_query = html_lib.escape(query)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for i, r in enumerate(results, 1):
        title = html_lib.escape(r.get("title", "No title"))
        url = html_lib.escape(r.get("url", ""))
        content = html_lib.escape(r.get("content", "") or "No description")
        engine = html_lib.escape(r.get("engine", "unknown"))
        engines_list = r.get("engines", [])
        engines = html_lib.escape(", ".join(engines_list) if engines_list else engine)
        score = r.get("score", "N/A")
        published = html_lib.escape(str(r.get("publishedDate", "") or ""))
        category = html_lib.escape(r.get("category", "") or "")
        thumbnail = r.get("thumbnail") or r.get("img_src") or ""

        thumb_html = f'<img src="{html_lib.escape(thumbnail)}" class="thumb" loading="lazy">' if thumbnail else ""

        rows.append(f"""
        <div class="result-card">
            <div class="result-number">#{i}</div>
            {thumb_html}
            <div class="result-body">
                <a href="{url}" target="_blank" class="result-title">{title}</a>
                <div class="result-url">{url}</div>
                <div class="result-content">{content}</div>
                <div class="result-meta">
                    <span class="badge">🔧 {engines}</span>
                    {f'<span class="badge">📁 {category}</span>' if category else ''}
                    {f'<span class="badge">📅 {published}</span>' if published else ''}
                    <span class="badge">⭐ Score: {score}</span>
                </div>
            </div>
        </div>
        """)

    answers_html = ""
    if answers:
        answers_items = "".join(f"<li>{html_lib.escape(str(a))}</li>" for a in answers)
        answers_html = f'<div class="section"><h2>💡 Direct Answers</h2><ul>{answers_items}</ul></div>'

    suggestions_html = ""
    if suggestions:
        sug_items = "".join(f"<span class='badge'>{html_lib.escape(str(s))}</span>" for s in suggestions)
        suggestions_html = f'<div class="section"><h2>🔍 Related Searches</h2>{sug_items}</div>'

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Global Search: {safe_query}</title>
<style>
    * {{ box-sizing: border-box; }}
    body {{
        font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        background: #0f0f14;
        color: #e8e8e8;
        margin: 0;
        padding: 20px;
    }}
    .header {{
        background: linear-gradient(135deg, #6a11cb, #2575fc);
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
    }}
    .header h1 {{ margin: 0 0 8px 0; font-size: 22px; }}
    .header p {{ margin: 0; opacity: 0.85; font-size: 14px; }}
    .section {{
        background: #1a1a22;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }}
    .result-card {{
        display: flex;
        gap: 14px;
        background: #1a1a22;
        border: 1px solid #2a2a35;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
    }}
    .result-number {{
        color: #7d5fff;
        font-weight: bold;
        min-width: 34px;
    }}
    .thumb {{
        width: 80px;
        height: 80px;
        object-fit: cover;
        border-radius: 8px;
        flex-shrink: 0;
    }}
    .result-body {{ flex: 1; min-width: 0; }}
    .result-title {{
        color: #8ab4ff;
        font-size: 16px;
        font-weight: 600;
        text-decoration: none;
        word-break: break-word;
    }}
    .result-title:hover {{ text-decoration: underline; }}
    .result-url {{
        color: #6a9955;
        font-size: 12px;
        margin: 4px 0;
        word-break: break-all;
    }}
    .result-content {{
        color: #c0c0c0;
        font-size: 14px;
        line-height: 1.5;
        margin: 8px 0;
    }}
    .result-meta {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }}
    .badge {{
        background: #2a2a35;
        color: #a0a0b0;
        font-size: 11px;
        padding: 3px 9px;
        border-radius: 12px;
        display: inline-block;
        margin: 2px;
    }}
    .footer {{
        text-align: center;
        color: #555;
        font-size: 12px;
        margin-top: 30px;
    }}
</style>
</head>
<body>
    <div class="header">
        <h1>🔍 Global Search Report</h1>
        <p>Query: <strong>{safe_query}</strong> | Results: {number_of_results} | Generated: {generated_at}</p>
    </div>

    {answers_html}
    {suggestions_html}

    <div class="section">
        <h2>📄 All Results ({len(results)})</h2>
    </div>

    {"".join(rows) if rows else "<p>No results found.</p>"}

    <div class="footer">Generated by SHUVO AI Global Search &mdash; powered by self-hosted SearXNG</div>
</body>
</html>"""

    return html_doc


def format_results(query, results):
    if isinstance(results, dict) and "error" in results:
        return f"Search failed: {results['error']}"

    if not results:
        return f"No results found for '{query}'."

    text = f"*Global Search Results for:* `{query}`\n\n"
    for i, r in enumerate(results, 1):
        text += f"*{i}. {r['title']}*\n"
        text += f"{r['url']}\n"
        text += f"{r['content']}...\n\n"

    return text


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Welcome to SHUVO AI Global Search!\n\n"
        "Use: `/search <your query>`\n"
        "Example: `/search SHUVO5600`",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["search"])
def handle_search(message):
    query = message.text.replace("/search", "").strip()

    if not query:
        bot.reply_to(message, "Please provide a query. Example: `/search SHUVO5600`", parse_mode="Markdown")
        return

    waiting_msg = bot.reply_to(message, f"Searching for `{query}`...", parse_mode="Markdown")

    data = global_search_full(query)

    if isinstance(data, dict) and "error" in data:
        bot.edit_message_text(
            f"Search failed: {data['error']}",
            chat_id=message.chat.id,
            message_id=waiting_msg.message_id,
        )
        return

    result_count = len(data.get("results", []))

    if result_count == 0:
        bot.edit_message_text(
            f"No results found for '{query}'.",
            chat_id=message.chat.id,
            message_id=waiting_msg.message_id,
        )
        return

    # Build the full HTML report (no Telegram length limit here)
    html_content = build_html_report(query, data)

    # Save to a temp file
    safe_filename = "".join(c if c.isalnum() else "_" for c in query)[:40]
    filepath = f"/tmp/search_{safe_filename}.html"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Update the waiting message
    bot.edit_message_text(
        f"Found {result_count} results for `{query}`. Sending full report...",
        chat_id=message.chat.id,
        message_id=waiting_msg.message_id,
        parse_mode="Markdown"
    )

    # Send the HTML file as a document
    with open(filepath, "rb") as f:
        bot.send_document(
            message.chat.id,
            f,
            caption=f"Full global search report for: {query}\nOpen this file in a browser to view all {result_count} results.",
            visible_file_name=f"search_{safe_filename}.html"
        )

    # Clean up temp file
    try:
        os.remove(filepath)
    except OSError:
        pass


if __name__ == "__main__":
    print("Bot is running... (Ctrl+C to stop)")
    bot.infinity_polling()
