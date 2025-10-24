import os, asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from tracing import process_pdf_to_pdf, process_imagefile_to_pdf

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./work")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HELP = """Gửi PDF hoặc ảnh để bot vẽ lại đường kẻ thành file khuôn PDF ✂️

Tùy chỉnh (ghi vào caption):
• invert=true/false - đảo màu (mặc định: true)
• stroke=2.0 - độ dày nét (mặc định: 2.0)
• dpi=400 - độ phân giải (mặc định: 400)
• precision=0.0005 - độ chính xác (nhỏ hơn = chi tiết hơn, mặc định: 0.0005, đặt 0 để giữ 100% chi tiết)
• min_len=20 - độ dài nét tối thiểu (mặc định: 20)

Ví dụ: precision=0 dpi=600"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xin chào 👋\n" + HELP)

def parse_opts(text: str):
    opts = {"invert": True, "stroke": 2.0, "dpi": 400, "precision": 0.0005, "min_len": 20}
    if not text: return opts
    for t in text.split():
        if t.startswith("invert="): opts["invert"] = t.split("=")[1].lower() in ["true","1"]
        elif t.startswith("stroke="): opts["stroke"] = float(t.split("=")[1])
        elif t.startswith("dpi="): opts["dpi"] = int(t.split("=")[1])
        elif t.startswith("precision="): opts["precision"] = float(t.split("=")[1])
        elif t.startswith("min_len="): opts["min_len"] = int(t.split("=")[1])
    return opts

async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    cap = msg.caption or ""
    opts = parse_opts(cap)
    
    is_pdf = False
    if msg.document:
        file = await msg.document.get_file()
        in_name = msg.document.file_name
        mime_type = msg.document.mime_type or ""
        is_pdf = mime_type == "application/pdf" or in_name.lower().endswith(".pdf")
    elif msg.photo:
        file = await msg.photo[-1].get_file()
        in_name = f"photo_{file.file_id}.jpg"
        is_pdf = False
    else:
        await msg.reply_text("Vui lòng gửi PDF hoặc ảnh.")
        return
    
    in_path = os.path.join(DOWNLOAD_DIR, in_name)
    out_path = os.path.join(DOWNLOAD_DIR, f"outlined_{in_name.rsplit('.', 1)[0]}.pdf")
    await msg.reply_text("Đang xử lý, vui lòng chờ...⏳")
    await file.download_to_drive(in_path)
    try:
        if is_pdf:
            process_pdf_to_pdf(in_path, out_path, opts["invert"], opts["stroke"], opts["dpi"], opts["precision"], opts["min_len"])
        else:
            process_imagefile_to_pdf(in_path, out_path, opts["invert"], opts["stroke"], opts["precision"], opts["min_len"])
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
