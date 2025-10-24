import os, asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from tracing import process_pdf_to_pdf, process_imagefile_to_pdf

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./work")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HELP = "Gửi PDF hoặc ảnh để bot vẽ lại đường kẻ thành file khuôn PDF ✂️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xin chào 👋\n" + HELP)

def parse_opts(text: str):
    opts = {"invert": True, "stroke": 2.0, "dpi": 400}
    if not text: return opts
    for t in text.split():
        if t.startswith("invert="): opts["invert"] = t.split("=")[1].lower() in ["true","1"]
        elif t.startswith("stroke="): opts["stroke"] = float(t.split("=")[1])
        elif t.startswith("dpi="): opts["dpi"] = int(t.split("=")[1])
    return opts

async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    cap = msg.caption or ""
    opts = parse_opts(cap)
    file = await msg.document.get_file()
    in_name = msg.document.file_name
    in_path = os.path.join(DOWNLOAD_DIR, in_name)
    out_path = os.path.join(DOWNLOAD_DIR, f"outlined_{in_name}")
    await msg.reply_text("Đang xử lý, vui lòng chờ...⏳")
    await file.download_to_drive(in_path)
    try:
        if in_name.endswith(".pdf"):
            process_pdf_to_pdf(in_path, out_path, opts["invert"], opts["stroke"], opts["dpi"])
        else:
            process_imagefile_to_pdf(in_path, out_path, opts["invert"], opts["stroke"])
        await msg.reply_document(document=open(out_path,"rb"), caption="✅ Đây là khuôn PDF của bạn.")
    except Exception as e:
        await msg.reply_text(f"Lỗi: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_doc))
    app.add_handler(MessageHandler(filters.PHOTO, handle_doc))
    print("Bot started ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
