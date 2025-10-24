import os, asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from tracing import process_pdf_to_pdf, process_imagefile_to_pdf, count_pdf_pages

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./work")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

WAITING_FOR_PAGES = 1

HELP = """Gửi PDF hoặc ảnh để bot vẽ lại đường kẻ thành file khuôn PDF ✂️

🎯 Mặc định: Độ chính xác 100% (precision=0, dpi=600)

Tùy chỉnh (ghi vào caption):
• invert=true/false - đảo màu (mặc định: true)
• stroke=2.0 - độ dày nét (mặc định: 2.0)
• dpi=600 - độ phân giải (mặc định: 600)
• precision=0 - độ chính xác 100% (mặc định: 0)
• min_len=10 - độ dài nét tối thiểu (mặc định: 10)

📄 Với file PDF nhiều trang, bot sẽ hỏi bạn muốn xử lý trang nào!"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xin chào 👋\n" + HELP)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Đã hủy. Gửi file mới để bắt đầu lại!")
    return ConversationHandler.END

def parse_opts(text: str):
    opts = {"invert": True, "stroke": 2.0, "dpi": 600, "precision": 0, "min_len": 10}
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
        return ConversationHandler.END
    
    in_path = os.path.join(DOWNLOAD_DIR, in_name)
    out_path = os.path.join(DOWNLOAD_DIR, f"outlined_{in_name.rsplit('.', 1)[0]}.pdf")
    
    await file.download_to_drive(in_path)
    
    if is_pdf:
        try:
            num_pages = count_pdf_pages(in_path)
            context.user_data["in_path"] = in_path
            context.user_data["out_path"] = out_path
            context.user_data["opts"] = opts
            context.user_data["total_pages"] = num_pages
            
            await msg.reply_text(
                f"📄 File PDF có {num_pages} trang.\n\n"
                f"Bạn muốn xử lý trang nào?\n"
                f"• Ghi 'all' hoặc 'tất cả' để xử lý hết\n"
                f"• Ghi số trang (VD: 1 hoặc 1-3 hoặc 1,3,5)"
            )
            return WAITING_FOR_PAGES
        except Exception as e:
            await msg.reply_text(f"Lỗi khi đọc PDF: {e}")
            return ConversationHandler.END
    else:
        await msg.reply_text("Đang xử lý, vui lòng chờ...⏳")
        try:
            process_imagefile_to_pdf(in_path, out_path, opts["invert"], opts["stroke"], opts["precision"], opts["min_len"])
            await msg.reply_document(document=open(out_path,"rb"), caption="✅ Đây là khuôn PDF của bạn.")
        except Exception as e:
            await msg.reply_text(f"Lỗi: {e}")
        return ConversationHandler.END

async def handle_page_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    response = msg.text.strip().lower()
    
    in_path = context.user_data.get("in_path")
    out_path = context.user_data.get("out_path")
    opts = context.user_data.get("opts", {})
    total_pages = context.user_data.get("total_pages", 1)
    
    first_page = None
    last_page = None
    
    try:
        if response in ["all", "tất cả", "tat ca", "hết", "het"]:
            first_page = 1
            last_page = total_pages
            page_desc = f"tất cả {total_pages} trang"
        elif "-" in response:
            parts = response.split("-")
            first_page = int(parts[0].strip())
            last_page = int(parts[1].strip())
            page_desc = f"trang {first_page}-{last_page}"
        elif "," in response:
            await msg.reply_text("⚠️ Hiện tại chưa hỗ trợ chọn trang rời rạc. Vui lòng chọn khoảng trang (VD: 1-3) hoặc 'all'")
            return WAITING_FOR_PAGES
        else:
            page_num = int(response)
            first_page = page_num
            last_page = page_num
            page_desc = f"trang {page_num}"
        
        if first_page < 1 or last_page > total_pages or first_page > last_page:
            await msg.reply_text(f"❌ Số trang không hợp lệ. PDF có {total_pages} trang. Vui lòng thử lại:")
            return WAITING_FOR_PAGES
        
        await msg.reply_text(f"⏳ Đang xử lý {page_desc} với độ chính xác 100%...\nVui lòng chờ!")
        
        process_pdf_to_pdf(
            in_path, out_path, 
            opts["invert"], opts["stroke"], opts["dpi"], 
            opts["precision"], opts["min_len"],
            first_page=first_page, last_page=last_page
        )
        
        await msg.reply_document(document=open(out_path,"rb"), caption=f"✅ Đã hoàn thành {page_desc}!")
        
    except ValueError:
        await msg.reply_text("❌ Định dạng không đúng. Vui lòng ghi số trang (VD: 1 hoặc 1-3) hoặc 'all':")
        return WAITING_FOR_PAGES
    except Exception as e:
        await msg.reply_text(f"❌ Lỗi: {e}")
    
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Document.ALL | filters.PHOTO, handle_doc)
        ],
        states={
            WAITING_FOR_PAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_page_selection)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    
    print("Bot started ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
