import logging
import os
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import bot as yambot

# =========================================
# ENV
# =========================================

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# =========================================
# LOGGING
# =========================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================================
# USER STATES
# =========================================

user_states = {}

# =========================================
# STORAGE
# =========================================

def get_track_data():

    data = yambot.load_file_to_json(
        yambot.RESULT_PATH
    )

    return data if data else []

def save_track_data(data):

    yambot.save_json_to_file(
        data,
        yambot.RESULT_PATH
    )

# =========================================
# START
# =========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = (
        "👋 Yambot\n\n"
        "/add - thêm keyword\n"
        "/list - xem danh sách\n"
        "/cancel - huỷ\n"
        "/help - trợ giúp"
    )

    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# =========================================
# CANCEL
# =========================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    if chat_id in user_states:
        del user_states[chat_id]

    await update.message.reply_text(
        "❌ Đã huỷ."
    )

# =========================================
# LIST
# =========================================

async def list_configs(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = get_track_data()

    if not data:

        await update.message.reply_text(
            "📭 Chưa có dữ liệu."
        )

        return

    msg = "📋 Danh sách:\n\n"

    for item in data:

        keyword = (
            item.get("keyword")
            or item.get("va")
            or "N/A"
        )

        site = item.get("site")

        msg += (
            f"🔹 ID: {item['id']} | Site: {site}\n"
            f"   Từ khoá: {keyword}\n"
            f"   👉 Bấm để xoá: /remove_{item['id']}\n\n"
        )

    await update.message.reply_text(msg)

# =========================================
# REMOVE COMMAND
# =========================================

async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        remove_id = int(text.split("_")[1])
    except (IndexError, ValueError):
        return

    track_data = get_track_data()
    new_data = [x for x in track_data if x.get("id") != remove_id]

    if len(new_data) < len(track_data):
        save_track_data(new_data)
        await update.message.reply_text(f"✅ Đã xoá cấu hình ID {remove_id}.")
    else:
        await update.message.reply_text(f"⚠️ Không tìm thấy ID {remove_id} hoặc đã xoá trước đó.")

# =========================================
# ADD START
# =========================================

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    user_states[chat_id] = {
        "step": "site"
    }

    await update.message.reply_text(
        "Nhập trang web bạn muốn theo dõi:\n"
        "- Gõ 'm' cho Mercari\n"
        "- Gõ 'y' cho Yahoo"
    )

# =========================================
# CALLBACK
# =========================================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data

    chat_id = query.message.chat.id

    print("CALLBACK:", data)

    # =====================================
    # REMOVE
    # =====================================

    if data.startswith("remove_"):

        remove_id = int(
            data.split("_")[1]
        )

        track_data = get_track_data()

        new_data = [
            x for x in track_data
            if x.get("id") != remove_id
        ]

        save_track_data(new_data)

        await query.edit_message_text(
            f"✅ Đã xoá ID {remove_id}"
        )

        return

    # =====================================
    # CHECK STATE
    # =====================================

    if chat_id not in user_states:

        await query.edit_message_text(
            "⚠️ Session hết hạn.\n"
            "Gõ /add lại."
        )

        return

    state = user_states[chat_id]



# =========================================
# TEXT HANDLER
# =========================================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    if chat_id not in user_states:
        return

    state = user_states[chat_id]
    text = update.message.text.strip()
    
    if text == '/done':
        if state["step"] in ["site", "keyword"]:
            await update.message.reply_text("❌ Không thể bỏ qua bước này.")
            return
        state["step"] = "save_now"
    elif text == '/skip':
        text = '0'

    print(f"TEXT ({state['step']}):", text)

    # =====================================
    # SITE
    # =====================================
    if state["step"] == "site":
        text_lower = text.lower()
        if text_lower == 'm':
            state["site"] = yambot.SITE_MERCARI
        elif text_lower == 'y':
            state["site"] = yambot.SITE_YAHOO_AUCTIONS
        else:
            await update.message.reply_text("❌ Không hợp lệ. Vui lòng gõ 'm' cho Mercari hoặc 'y' cho Yahoo.")
            return

        state["step"] = "keyword"
        await update.message.reply_text(
            f"✅ Đã chọn {state['site']}.\n\n"
            "Nhập từ khoá tìm kiếm (Keyword):"
        )
        return

    # =====================================
    # KEYWORD
    # =====================================
    elif state["step"] == "keyword":
        state["keyword"] = text
        if state["site"] == yambot.SITE_MERCARI:
            state["step"] = "level"
            await update.message.reply_text(
                "Chọn mức độ mở rộng (Nhập số 1, 2, hoặc 3):\n"
                "1. Track tất cả kết quả\n"
                "2. Tên phải chứa từ khoá (Khuyên dùng)\n"
                "3. Kết hợp từ khoá bổ sung\n"
                "(Bấm /skip để bỏ qua, hoặc /done để lưu luôn)"
            )
        else:
            state["step"] = "exclude"
            await update.message.reply_text(
                "Nhập từ khoá muốn LOẠI TRỪ.\n"
                "(Bấm /skip để bỏ qua, hoặc /done để lưu luôn)"
            )
        return

    # =====================================
    # LEVEL (Mercari only)
    # =====================================
    elif state["step"] == "level":
        if text != '0':
            if text not in ["1", "2", "3"]:
                await update.message.reply_text("❌ Không hợp lệ. Nhập 1, 2, hoặc 3.")
                return
            state["level"] = int(text)
        
        if state.get("level") == 3:
            state["step"] = "supplement"
            await update.message.reply_text(
                "Nhập từ khoá BỔ SUNG (Supplemental keyword).\n"
                "(Bấm /skip để bỏ qua, hoặc /done để lưu luôn)"
            )
        else:
            state["step"] = "category"
            await update.message.reply_text(
                "Nhập MÃ DANH MỤC (Category ID) bạn muốn tìm.\n"
                "Ví dụ: CD là 75. Có thể nhập nhiều mã (vd: 694,695).\n"
                "(Bấm /skip để bỏ qua, hoặc /done để lưu luôn)"
            )
        return

    # =====================================
    # SUPPLEMENT (Mercari only)
    # =====================================
    elif state["step"] == "supplement":
        if text != '0':
            state["supplement"] = text
        state["step"] = "category"
        await update.message.reply_text(
            "Nhập MÃ DANH MỤC (Category ID) bạn muốn tìm.\n"
            "Ví dụ: CD là 75. Có thể nhập nhiều mã (vd: 694,695).\n"
            "(Bấm /skip để bỏ qua, hoặc /done để lưu luôn)"
        )
        return

    # =====================================
    # EXCLUDE (Yahoo only)
    # =====================================
    elif state["step"] == "exclude":
        if text != '0':
            state["exclude_keyword"] = text
        state["step"] = "category"
        await update.message.reply_text(
            "Nhập MÃ DANH MỤC (Category ID) bạn muốn tìm.\n"
            "Ví dụ: Music là 22152, CD là 22192.\n"
            "(Bấm /skip để bỏ qua, hoặc /done để lưu luôn)"
        )
        return

    # =====================================
    # CATEGORY
    # =====================================
    elif state["step"] == "category":
        if text != '0':
            try:
                state["category_id"] = [int(x.strip()) for x in text.split(',')]
            except ValueError:
                await update.message.reply_text("❌ Mã danh mục không hợp lệ, vui lòng chỉ nhập số.\n(Bấm /skip để bỏ qua)")
                return
        
        state["step"] = "condition"
        if state["site"] == yambot.SITE_MERCARI:
            await update.message.reply_text(
                "Chọn TÌNH TRẠNG hàng:\n"
                "1. Mới tinh\n"
                "2. Gần như mới\n"
                "3. Không xước rõ\n"
                "4. Xước nhẹ\n"
                "5. Xước bẩn rõ\n"
                "6. Rất tệ\n"
                "(Nhập số 1-6, có thể nhập nhiều cách nhau dấu phẩy. Bấm /skip để bỏ qua, hoặc /done để lưu luôn)"
            )
        else:
            await update.message.reply_text(
                "Chọn TÌNH TRẠNG hàng:\n"
                "1. Mới tinh\n"
                "2. Cũ nói chung\n"
                "3. Gần như mới\n"
                "4. Không xước rõ\n"
                "5. Xước nhẹ\n"
                "6. Xước bẩn rõ\n"
                "7. Rất tệ\n"
                "(Nhập số 1-7, có thể nhập nhiều cách nhau dấu phẩy. Bấm /skip để bỏ qua, hoặc /done để lưu luôn)"
            )
        return

    # =====================================
    # CONDITION
    # =====================================
    elif state["step"] == "condition":
        if text != '0':
            try:
                state["item_condition_id"] = [int(x.strip()) for x in text.split(',')]
            except ValueError:
                await update.message.reply_text("❌ Tình trạng không hợp lệ.\n(Bấm /skip để bỏ qua)")
                return
        
        state["step"] = "price_max"
        await update.message.reply_text(
            "Nhập GIÁ TỐI ĐA (Max price) bạn chấp nhận mua.\n"
            "(Bấm /skip để bỏ qua, hoặc /done để lưu luôn)"
        )
        return

    # =====================================
    # PRICE MAX
    # =====================================
    elif state["step"] == "price_max":
        if text != '0':
            try:
                state["price_max"] = int(text)
            except ValueError:
                await update.message.reply_text("❌ Giá trị không hợp lệ. Vui lòng nhập SỐ.\n(Bấm /skip để bỏ qua)")
                return
        
        state["step"] = "price_min"
        await update.message.reply_text(
            "Nhập GIÁ TỐI THIỂU (Min price) để tránh hàng rác.\n"
            "(Bấm /skip để bỏ qua, hoặc /done để lưu luôn)"
        )
        return

    # =====================================
    # PRICE MIN & SAVE
    # =====================================
    elif state["step"] == "price_min":
        if text != '0':
            try:
                state["price_min"] = int(text)
            except ValueError:
                await update.message.reply_text("❌ Giá trị không hợp lệ. Vui lòng nhập SỐ.\n(Bấm /skip để bỏ qua)")
                return
        state["step"] = "save_now"
        
    # =====================================
    # SAVE
    # =====================================
    if state["step"] == "save_now":
        track_data = get_track_data()
        max_id = max([x.get("id", 0) for x in track_data], default=0)

        new_entry = {
            "id": max_id + 1,
            "site": state["site"],
            "last_result": {}
        }

        if state["site"] == yambot.SITE_MERCARI:
            new_entry["keyword"] = state.get("keyword")
            new_entry["level"] = state.get("level", 1)
            if "supplement" in state: new_entry["supplement"] = state["supplement"]
            if "exclude_keyword" in state: new_entry["exclude_keyword"] = state["exclude_keyword"]
            if "category_id" in state: new_entry["category_id"] = state["category_id"]
            if "item_condition_id" in state: new_entry["item_condition_id"] = state["item_condition_id"]
            if "price_max" in state: new_entry["price_max"] = state["price_max"]
            if "price_min" in state: new_entry["price_min"] = state["price_min"]
        else:
            new_entry["va"] = state.get("keyword")
            if "exclude_keyword" in state: new_entry["ve"] = state["exclude_keyword"]
            if "category_id" in state and len(state["category_id"]) > 0: 
                new_entry["auccat"] = state["category_id"][0]
            if "item_condition_id" in state: new_entry["istatus"] = state["item_condition_id"]
            if "price_max" in state: new_entry["max"] = state["price_max"]
            if "price_min" in state: new_entry["min"] = state["price_min"]

        track_data.append(new_entry)
        save_track_data(track_data)

        await update.message.reply_text(
            "✅ Đã thêm cấu hình thành công!\n"
            f"ID: {new_entry['id']}\n"
            f"Trang: {new_entry['site']}\n"
            f"Từ khoá: {new_entry.get('keyword', new_entry.get('va'))}"
        )
        print("SAVED:", new_entry)
        del user_states[chat_id]
        return

# =========================================
# ERROR
# =========================================

async def error_handler(update, context):

    logging.error(
        msg="Exception:",
        exc_info=context.error
    )

# =========================================
# MAIN
# =========================================

def main():

    if not TELEGRAM_TOKEN:

        print("❌ Missing TELEGRAM_TOKEN")

        return

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    # =============================
    # COMMANDS
    # =============================

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^/remove_\d+$"),
            remove_command
        )
    )

    app.add_handler(
        CommandHandler("add", add_start)
    )

    app.add_handler(
        CommandHandler("list", list_configs)
    )

    app.add_handler(
        CommandHandler("cancel", cancel)
    )

    # =============================
    # CALLBACK
    # =============================

    app.add_handler(
        CallbackQueryHandler(callback_handler)
    )

    # =============================
    # TEXT
    # =============================

    app.add_handler(
        MessageHandler(
            filters.TEXT,
            text_handler
        )
    )

    # =============================
    # ERROR
    # =============================

    app.add_error_handler(
        error_handler
    )

    print("✅ Telegram bot started")

    app.run_polling(
        drop_pending_updates=True
    )

# =========================================
# ENTRY
# =========================================

if __name__ == "__main__":
    main()