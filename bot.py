import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo
from database import init_db, add_user, get_user

# --- እባክዎ እነዚህን መረጃዎች በትክክል ይሙሉ ---
TOKEN = "BOT_TOKEN_ህን_እዚህ_ግቡ"
WEBAPP_URL = "https://your-railway-app-url.up.railway.app/index.html"  # Railway ከሰጠዎት ሊንክ በኋላ /index.html ብለው ያስገቡ

# 1 እስከ 3 ያሉት ቻናሎች በግዴታ (Forced) ሲታዩ፣ 4ተኛው መደበኛ ሆኖ በድብቅ ይካተታል
CHANNELS = [
    {"name": "ቻናል 1", "url": "https://t.me/channel_1_link", "id": "@channel_1_username", "forced": True},
    {"name": "ቻናል 2", "url": "https://t.me/channel_2_link", "id": "@channel_2_username", "forced": True},
    {"name": "ቻናል 3", "url": "https://t.me/channel_3_link", "id": "@channel_3_username", "forced": True},
    {"name": "ቻናል 4", "url": "https://t.me/channel_4_link", "id": "@channel_4_username", "forced": False}
]

PROOF_CHANNEL_ID = -1001234567890

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def check_subscriptions(user_id: int) -> bool:
    for ch in CHANNELS:
        if ch["forced"]:  # ግዴታ የሆኑትን 3 ቻናሎች ብቻ እንፈትሻለን
            try:
                member = await bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
                if member.status in ["left", "kicked"]:
                    return False
            except Exception:
                pass
    return True

def get_join_keyboard():
    keyboard = []
    for ch in CHANNELS:
        if ch["forced"]:
            keyboard.append([InlineKeyboardButton(text=f"📢 {ch['name']} መቀላቀያ", url=ch["url"])])
    keyboard.append([InlineKeyboardButton(text="✅ አባል ሆጫለሁ (Verify)", callback_data="check_join")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Regl Pay Mini App ክፈት", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])

@dp.message(CommandStart())
async def start_command(message: Message):
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        parsed_id = int(args[1])
        if parsed_id != message.from_user.id:
            referrer_id = parsed_id

    await add_user(message.from_user.id, referrer_id)

    is_joined = await check_subscriptions(message.from_user.id)
    if not is_joined:
        await message.answer(
            "⚠️ <b>Regl Pay</b> ቦቱን ለመጠቀም መጀመሪያ ከታች ያሉትን <b>ቻናሎች</b> መቀላቀል አለብዎት!",
            reply_markup=get_join_keyboard(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"👋 ሰላም <b>{message.from_user.first_name}</b> ወደ <b>Regl Pay</b> እንኳን በደህና መጡ!\n\n"
        "ከታች ያለውን ቁልፍ በመንካት ሚኒ አፑን (Mini App) በመክፈት መስራት ይጀምሩ፦",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "check_join")
async def verify_join(callback: CallbackQuery):
    is_joined = await check_subscriptions(callback.from_user.id)
    if not is_joined:
        await callback.answer("❌ ግዴታ የሆኑትን ቻናሎች ገና አልቀላቀሉም!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🎉 እናመሰግናለን! ቻናሎቹን በተሳካ ሁኔታ ተቀላቅለዋል። አሁን ሚኒ አፑን መክፈት ይችላሉ፦",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

async def main():
    await init_db()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
