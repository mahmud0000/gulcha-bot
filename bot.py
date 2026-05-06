import logging
import os
import json
from datetime import datetime, timedelta
from telegram import (
Update, ReplyKeyboardMarkup, KeyboardButton,
InlineKeyboardMarkup, InlineKeyboardButton,
ReplyKeyboardRemove
)
from telegram.ext import (
Application, CommandHandler, MessageHandler, CallbackQueryHandler,
ConversationHandler, filters, ContextTypes
)
# ==================== SOZLAMALAR ====================
TOKEN = os.getenv("8619295805:AAHAR0TuU-wzDmgZS2kqDlnaHUr1AYxfNoQ", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5594795335"))
CARD_NUMBER = os.getenv("CARD_NUMBER", "5614 6821 2328 4780")
DATA_FILE = "data.json"
# ==================== HOLATLAR ====================
(
REG_NAME, REG_PHONE, REG_LOCATION,
ORDER_MENU, ORDER_QUANTITY, ORDER_UPSELL,
ORDER_PAYMENT, ORDER_CONFIRM,
BROADCAST_TEXT, MENU_INPUT, CHANGE_LOCATION
) = range(11)
# ==================== MA'LUMOTLAR ====================
users = {}
menu = {}
orders = {}
order_counter = [0]
stats = {
"total_orders": 0,
"total_revenue": 0,
"daily": {},
"weekly": {}
}
UPSELL_ITEMS = [
{"name": " Cola", "price": 8000},
{"name": " Non", "price": 3000},
{"name": " Salat", "price": 12000},]
logging.basicConfig(
format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
level=logging.INFO
)
logger = logging.getLogger(__name__)
# ==================== SAQLASH ====================
def save_data():
try:
data = {
"users": {str(k): v for k, v in users.items()},
"menu": menu,
"orders": {str(k): v for k, v in orders.items()},
"order_counter": order_counter[0],
"stats": stats
}
with open(DATA_FILE, "w", encoding="utf-8") as f:
json.dump(data, f, ensure_ascii=False, indent=2)
except Exception as e:
logger.error(f"Saqlash xatosi: {e}")
def load_data():
global users, menu, orders, stats
try:
if os.path.exists(DATA_FILE):
with open(DATA_FILE, "r", encoding="utf-8") as f:
data = json.load(f)
users = {int(k): v for k, v in data.get("users", {}).items()}
menu = data.get("menu", {})
orders = {int(k): v for k, v in data.get("orders", {}).items()}
order_counter[0] = data.get("order_counter", 0)
stats = data.get("stats", {
"total_orders": 0, "total_revenue": 0,
"daily": {}, "weekly": {}
})
logger.info(f"Yuklandi: {len(users)} mijoz, {len(orders)} buyurtma")
except Exception as e:
logger.error(f"Yuklash xatosi: {e}")
# ==================== YORDAMCHI ====================def is_admin(user_id):
return user_id == ADMIN_ID
def get_today():
return datetime.now().strftime("%d.%m.%Y")
def get_week_key():
now = datetime.now()
week_start = now - timedelta(days=now.weekday())
return week_start.strftime("%d.%m.%Y")
def maps_link(lat, lon):
return f"https://maps.google.com/?q={lat},{lon}"
def main_keyboard(user_id):
if is_admin(user_id):
return ReplyKeyboardMarkup([
[" Menyu kiritish", " Buyurtmalar"],
[" Xabar yuborish", " Hisobot"],
[" Mijozlar bazasi"]
], resize_keyboard=True)
return ReplyKeyboardMarkup([
[" Buyurtma berish"],
[" Mening buyurtmalarim", " Profilim"],
[" Manzilni yangilash"]
], resize_keyboard=True)
def format_order_admin(order, user):
items_text = "\n".join([
f" • {i['name']} x{i['qty']} — {i['qty'] * i['price']:,} so'm"
for i in order["items"]
])
payment = " Naqd" if order["payment"] == "cash" else ""

status_map = {
"new": " Yangi",
"cooking": " Tayyorlanmoqda",
"delivering": " Yetkazilmoqda",
"delivered": " Yetkazildi",
"cancelled": " Bekor"
"Karta"
}
status = status_map.get(order.get("status", "new"), "")

lat = user.get("lat")
lon = user.get("lon")
location_text = f" [{user.get('address', 'Manzil')}]({maps_link(lat, lon)})" if lat and
return (
f" *Buyurtma #{order['id']}*\n\n"
f" {user.get('name', '?')}\n"
f" {user.get('phone', '?')}\n"
f"{location_text}\n\n"
f" *Tarkib:*\n{items_text}\n\n"
f" *Jami: {order['total']:,} so'm*\n"
f"{payment}\n"
f" Holat: {status}\n"
f" {order['time']}"
)
# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
if is_admin(user_id):
await update.message.reply_text(
" Salom, Admin!\n\nBoshqaruv paneliga xush kelibsiz. ",
reply_markup=main_keyboard(user_id)
)
return ConversationHandler.END
if user_id in users:
u = users[user_id]
if menu:
menu_text = "\n".join([
f" • {n} — {(v['price'] if isinstance(v, dict) else v):,} so'm"
for n, v in menu.items()
])
else:
menu_msg = f" *Bugungi menyu:*\n{menu_text}"
menu_msg = " Bugungi menyu hali tayyor emas."
await update.message.reply_text(
f" Qaytib keldingiz, *{u['name']}*!\n\n{menu_msg}",
reply_markup=main_keyboard(user_id),
parse_mode="Markdown"
)
return ConversationHandler.END
await update.message.reply_text(" *Gulcha Taom* botiga xush kelibsiz! \n\n"
"Toshkentdagi eng mazali tushliklar eshigingizgacha yetkaziladi!\n\n"
"Ro'yxatdan o'tish uchun *ism va familiyangizni* kiriting:",
parse_mode="Markdown",
reply_markup=ReplyKeyboardRemove()
)
return REG_NAME
# ==================== RO'YXATDAN O'TISH ====================
async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data["reg_name"] = update.message.text.strip()
keyboard = [[KeyboardButton(" Telefon raqamni yuborish", request_contact=True)]]
await update.message.reply_text(
" Telefon raqamingizni yuboring:",
reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=Tr
)
return REG_PHONE
async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.message.contact:
phone = update.message.contact.phone_number
if not phone.startswith("+"):
phone = "+" + phone
else:
phone = update.message.text.strip()
context.user_data["reg_phone"] = phone
keyboard = [[KeyboardButton(" Lokatsiyamni yuborish", request_location=True)]]
await update.message.reply_text(
" Ofis yoki yetkazib berish manzilini yuborish uchun quyidagi tugmani bosing:\n\n"
"*(Bu orqali kuryer to'g'ri manzilni topadi)*",
reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=Tr
parse_mode="Markdown"
)
return REG_LOCATION
async def reg_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
if update.message.location:
lat = update.message.location.latitude
lon = update.message.location.longitude
address = f" {lat:.4f}, {lon:.4f}"else:
lat, lon = None, None
address = update.message.text.strip()
users[user_id] = {
"name": context.user_data["reg_name"],
"phone": context.user_data["reg_phone"],
"address": address,
"lat": lat,
"lon": lon,
"joined": get_today(),
"orders": [],
"total_spent": 0,
"order_count": 0,
"favorite_items": {},
"vip": False
}
save_data()
maps_url = f"\n [Xaritada ko'rish]({maps_link(lat, lon)})" if lat and lon else ""
await update.message.reply_text(
f" *Ro'yxatdan muvaffaqiyatli o'tdingiz!*\n\n"
f" {users[user_id]['name']}\n"
f" {users[user_id]['phone']}\n"
f" {address}{maps_url}\n\n"
f"Endi buyurtma berishingiz mumkin! ",
parse_mode="Markdown",
reply_markup=main_keyboard(user_id)
)
return ConversationHandler.END
# ==================== MANZIL YANGILASH ====================
async def change_location_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
if user_id not in users:
await update.message.reply_text("Avval /start bosing.")
return ConversationHandler.END
keyboard = [[KeyboardButton(" Yangi lokatsiyamni yuborish", request_location=True)]]
await update.message.reply_text(
" Yangi manzilni yuboring:",
reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=Tr
)
return CHANGE_LOCATIONasync def change_location_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
if update.message.location:
lat = update.message.location.latitude
lon = update.message.location.longitude
address = f" {lat:.4f}, {lon:.4f}"
else:
lat, lon = None, None
address = update.message.text.strip()
users[user_id]["address"] = address
users[user_id]["lat"] = lat
users[user_id]["lon"] = lon
save_data()
maps_url = f" — [Xaritada]({maps_link(lat, lon)})" if lat and lon else ""
await update.message.reply_text(
f" Manzil yangilandi!\n {address}{maps_url}",
reply_markup=main_keyboard(user_id),
parse_mode="Markdown"
)
return ConversationHandler.END
# ==================== BUYURTMA ====================
async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
if user_id not in users:
await update.message.reply_text("Avval /start bosing va ro'yxatdan o'ting.")
return ConversationHandler.END
if not menu:
await update.message.reply_text(
    "Bugungi menyu hali tayyor emas."
)

return ConversationHandler.END
context.user_data["cart"] = {}
return await show_menu(update, context)
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
cart = context.user_data.get("cart", {})
buttons = []
for name, item in menu.items():price = item["price"] if isinstance(item, dict) else item
qty = cart.get(name, 0)
qty_text = f" ({qty}x)" if qty > 0 else ""
icon = " " if isinstance(item, dict) and item.get("photo_id") else ""
buttons.append([InlineKeyboardButton(
f"{icon}{name}{qty_text} — {price:,} so'm",
callback_data=f"item_{name}"
)])
if cart:
total = sum(
cart[n] * (menu[n]["price"] if isinstance(menu[n], dict) else menu[n])
for n in cart
)
buttons.append([InlineKeyboardButton(
f" Buyurtma berish — {total:,} so'm", callback_data="checkout"
)])
buttons.append([
    InlineKeyboardButton(
        " Savatchani tozalash",
        callback_data="clear_cart"
    )
])

cart_lines = ""
if cart:
lines = []
for n, q in cart.items():
p = menu[n]["price"] if isinstance(menu[n], dict) else menu[n]
lines.append(f" • {n} x{q} — {q * p:,} so'm")
cart_lines = "\n\n *Savatcha:*\n" + "\n".join(lines)
text = f" *Bugungi menyu:*{cart_lines}\n\nTaom tanlang:"
markup = InlineKeyboardMarkup(buttons)
if update.callback_query:
try:
await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mo
except Exception:
await update.callback_query.message.reply_text(text, reply_markup=markup, parse_m
else:
await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
return ORDER_MENU
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
if query.data == "checkout":
return await upsell_show(update, context)if query.data == "clear_cart":
context.user_data["cart"] = {}
return await show_menu(update, context)
if query.data == "back_menu":
return await show_menu(update, context)
name = query.data.replace("item_", "")
if name not in menu:
return ORDER_MENU
item = menu[name]
price = item["price"] if isinstance(item, dict) else item
photo_id = item.get("photo_id") if isinstance(item, dict) else None
current = context.user_data.get("cart", {}).get(name, 0)
buttons = [
[InlineKeyboardButton(str(i), callback_data=f"qty_{name}_{i}") for i in range(1, 6)],
[InlineKeyboardButton(" O'chirish", callback_data=f"qty_{name}_0")],
[InlineKeyboardButton(" Orqaga", callback_data="back_menu")]
]
text = f"*{name}*\n {price:,} so'm\nSavatchada: {current} ta\n\nNechtа?"
if photo_id:
try:
await query.message.reply_photo(
photo=photo_id, caption=text,
reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown"
)
await query.message.delete()
except Exception:
await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), p
else:
await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse
return ORDER_QUANTITY
async def quantity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
if query.data == "back_menu":
return await show_menu(update, context)
parts = query.data.replace("qty_", "").rsplit("_", 1)
name, qty = parts[0], int(parts[1])cart = context.user_data.get("cart", {})
if qty == 0:
cart.pop(name, None)
else:
cart[name] = qty
context.user_data["cart"] = cart
return await show_menu(update, context)
# ==================== UPSELL ====================
async def upsell_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data["upsell_index"] = 0
context.user_data["upsell_added"] = []
return await show_upsell_item(update, context)
async def show_upsell_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
idx = context.user_data.get("upsell_index", 0)
if idx >= len(UPSELL_ITEMS):
return await payment_choice(update, context)
item = UPSELL_ITEMS[idx]
buttons = [
[
    InlineKeyboardButton(
        f" Ha, qo'shaman ({item['price']:,} so'm)",
        callback_data="upsell_yes"
    )
]
[InlineKeyboardButton(" Yo'q, kerak emas", callback_data="upsell_no")]
]
text = f" *Qo'shimcha taklif:*\n\n{item['name']} — {item['price']:,} so'm\n\nQo'shasizm
query = update.callback_query
if query:
try:
await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), p
except Exception:
await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons),
else:
await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), par
return ORDER_UPSELL
async def upsell_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()idx = context.user_data.get("upsell_index", 0)
item = UPSELL_ITEMS[idx]
if query.data == "upsell_yes":
cart = context.user_data.get("cart", {})
cart[item["name"]] = cart.get(item["name"], 0) + 1
context.user_data["cart"] = cart
# menu ga ham qo'shamiz agar yo'q bo'lsa
if item["name"] not in menu:
menu[item["name"]] = {"price": item["price"], "photo_id": None}
context.user_data["upsell_index"] = idx + 1
return await show_upsell_item(update, context)
# ==================== TO'LOV ====================
async def payment_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
cart = context.user_data.get("cart", {})
total = sum(
cart[n] * (menu[n]["price"] if isinstance(menu[n], dict) else menu[n])
for n in cart if n in menu
)
items = [
{"name": n, "qty": q, "price": menu[n]["price"] if isinstance(menu[n], dict) else men
for n, q in cart.items() if n in menu
]
context.user_data["order_items"] = items
context.user_data["order_total"] = total
items_text = "\n".join([f" • {i['name']} x{i['qty']} — {i['qty'] * i['price']:,} so'm" f
buttons = [
[InlineKeyboardButton(" Naqd (yetkazganda)", callback_data="pay_cash")],
[InlineKeyboardButton(" Karta orqali", callback_data="pay_card")]
]
text = f" *Buyurtmangiz:*\n{items_text}\n\n *Jami: {total:,} so'm*\n\nTo'lov usulini
query = update.callback_query
if query:
try:
await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), p
except Exception:
await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons),
else:
await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parreturn ORDER_PAYMENT
async def payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
payment = "cash" if query.data == "pay_cash" else "card"
context.user_data["payment"] = payment
items = context.user_data["order_items"]
total = context.user_data["order_total"]
items_text = "\n".join([f" • {i['name']} x{i['qty']} — {i['qty'] * i['price']:,} so'm" f
pay_text = " Naqd (yetkazganda)" if payment == "cash" else f" Karta: *{CARD_NUMBER}*"
text = (
f" *Buyurtmangiz:*\n{items_text}\n\n"
f" *Jami: {total:,} so'm*\n"
f"To'lov: {pay_text}\n\n"
f"Tasdiqlaysizmi?"
)
buttons = [
[InlineKeyboardButton(" Tasdiqlash", callback_data="confirm_yes")],
[InlineKeyboardButton(" O'zgartirish", callback_data="confirm_no")]
]
await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mod
return ORDER_CONFIRM
async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
if query.data == "confirm_no":
context.user_data["cart"] = {
i["name"]: i["qty"] for i in context.user_data.get("order_items", [])
}
return await show_menu(update, context)
user_id = update.effective_user.id
user = users[user_id]
items = context.user_data["order_items"]
payment = context.user_data["payment"]
total = context.user_data["order_total"]
order_counter[0] += 1
order_id = order_counter[0]now = datetime.now().strftime("%d.%m.%Y %H:%M")
today = get_today()
week = get_week_key()
order = {
"id": order_id,
"user_id": user_id,
"items": items,
"payment": payment,
"total": total,
"time": now,
"status": "new",
"rated": False,
"rating": 0
}
orders[order_id] = order
# CRM yangilash
if "orders" not in users[user_id]:
users[user_id]["orders"] = []
users[user_id]["orders"].append(order_id)
users[user_id]["total_spent"] = users[user_id].get("total_spent", 0) + total
users[user_id]["order_count"] = users[user_id].get("order_count", 0) + 1
users[user_id]["last_order"] = now
# Sevimli taomlar
if "favorite_items" not in users[user_id]:
users[user_id]["favorite_items"] = {}
for item in items:
name = item["name"]
users[user_id]["favorite_items"][name] = users[user_id]["favorite_items"].get(name, 0
# VIP (5+ buyurtma yoki 500k+ xarid)
if users[user_id]["order_count"] >= 5 or users[user_id]["total_spent"] >= 500000:
users[user_id]["vip"] = True
# Statistika
stats["total_orders"] += 1
stats["total_revenue"] += total
stats["daily"][today] = stats["daily"].get(today, 0) + 1
stats["weekly"][week] = stats["weekly"].get(week, 0) + 1
save_data()
# Mijozga tasdiqlash
pay_info = " await query.edit_message_text(
Naqd — yetkazganda to'laysiz" if payment == "cash" else f" Karta: {CARD_f" *Buyurtmangiz qabul qilindi!*\n\n"
f" Buyurtma #{order_id}\n"
f" Jami: {total:,} so'm\n"
f"{pay_info}\n\n"
f" Tez orada yetkazib boramiz!",
parse_mode="Markdown"
)
# Adminga xabar
if ADMIN_ID:
try:
admin_buttons = InlineKeyboardMarkup([
[InlineKeyboardButton(" Tayyorlanmoqda", callback_data=f"st_{order_id}_cook
[InlineKeyboardButton(" Yetkazilmoqda", callback_data=f"st_{order_id}_deliv
[InlineKeyboardButton(" Yetkazildi", callback_data=f"st_{order_id}_delivere
[InlineKeyboardButton(" Bekor qilish", callback_data=f"st_{order_id}_cancel
])
msg = format_order_admin(order, user)
# Lokatsiya ham yuboramiz
if user.get("lat") and user.get("lon"):
await context.bot.send_location(
chat_id=ADMIN_ID,
latitude=user["lat"],
longitude=user["lon"]
)
await context.bot.send_message(
chat_id=ADMIN_ID,
text=msg,
reply_markup=admin_buttons,
parse_mode="Markdown"
)
except Exception as e:
logger.error(f"Admin xabari: {e}")
return ConversationHandler.END
# ==================== BUYURTMA HOLATI ====================
async def order_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
if not is_admin(update.effective_user.id):
returnparts = query.data.split("_")
order_id = int(parts[1])
new_status = parts[2]
if order_id not in orders:
return
orders[order_id]["status"] = new_status
save_data()
user = users.get(orders[order_id]["user_id"], {})
try:
await query.edit_message_text(
format_order_admin(orders[order_id], user),
parse_mode="Markdown"
)
except Exception:
pass
# Mijozga bildirishnoma
uid = orders[order_id]["user_id"]
msgs = {
"cooking": f" *Buyurtma #{order_id}* tayyorlanmoqda!",
"delivering": f" *Buyurtma #{order_id}* yo'lda! Tez orada yetkazib boramiz!",
"delivered": f" *Buyurtma #{order_id}* yetkazildi!\n\nIltimos, taomni baholang ",
"cancelled": f" *Buyurtma #{order_id}* bekor qilindi. Kechirasiz!"
}
if new_status in msgs:
try:
if new_status == "delivered":
rate_buttons = InlineKeyboardMarkup([[
InlineKeyboardButton("1 ", callback_data=f"rate_{order_id}_1"),
InlineKeyboardButton("2 ", callback_data=f"rate_{order_id}_2"),
InlineKeyboardButton("3 ", callback_data=f"rate_{order_id}_3"),
InlineKeyboardButton("4 ", callback_data=f"rate_{order_id}_4"),
InlineKeyboardButton("5 ", callback_data=f"rate_{order_id}_5"),
]])
await context.bot.send_message(uid, msgs[new_status], reply_markup=rate_butto
else:
await context.bot.send_message(uid, msgs[new_status], parse_mode="Markdown")
except Exception as e:
logger.error(f"Mijoz bildirishnoma: {e}")
# ==================== BAHOLASH ====================async def rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
parts = query.data.split("_")
order_id, rating = int(parts[1]), int(parts[2])
if order_id in orders and not orders[order_id].get("rated"):
orders[order_id]["rating"] = rating
orders[order_id]["rated"] = True
save_data()
stars = " " * rating
await query.edit_message_text(f"Rahmat! {stars}\nBahoingiz qabul qilindi! ")
if ADMIN_ID:
try:
user = users.get(orders[order_id]["user_id"], {})
await context.bot.send_message(
ADMIN_ID,
f" Buyurtma #{order_id} — {user.get('name','?')} — {stars} ({rating}/5)",
parse_mode="Markdown"
)
except Exception:
pass
# ==================== MENING BUYURTMALARIM ====================
async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
if user_id not in users:
await update.message.reply_text("Avval /start bosing.")
return
user_order_ids = users[user_id].get("orders", [])
if not user_order_ids:
await update.message.reply_text("Siz hali buyurtma bermagansiz.")
return
recent = user_order_ids[-5:][::-1]
status_map = {"new": " ", "cooking": " ", "delivering": " ", "delivered": " ", "canc
text = " *Oxirgi buyurtmalaringiz:*\n\n"
for oid in recent:
if oid in orders:o = orders[oid]
items_text = ", ".join([f"{i['name']} x{i['qty']}" for i in o["items"]])
st = status_map.get(o.get("status", "new"), " ")
rating = f" {' ' * o['rating']}" if o.get("rated") else ""
text += f"{st} *#{oid}* | {o['time']}\n{items_text}\n {o['total']:,} so'm{ratin
await update.message.reply_text(text, parse_mode="Markdown")
# ==================== PROFIL ====================
async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
if user_id not in users:
await update.message.reply_text("Avval /start bosing.")
return
u = users[user_id]
vip = " VIP mijoz" if u.get("vip") else "Oddiy mijoz"
fav = max(u.get("favorite_items", {}), key=u.get("favorite_items", {}).get) if u.get("fav
lat, lon = u.get("lat"), u.get("lon")
maps_url = f"\n [Xaritada ko'rish]({maps_link(lat, lon)})" if lat and lon else ""
await update.message.reply_text(
f" *Profilingiz:*\n\n"
f"Ism: {u['name']}\n"
f"Telefon: {u['phone']}\n"
f"Manzil: {u.get('address', '?')}{maps_url}\n"
f"Ro'yxat: {u.get('joined', '?')}\n\n"
f" *Statistika:*\n"
f"Buyurtmalar: {u.get('order_count', 0)} ta\n"
f"Jami xarid: {u.get('total_spent', 0):,} so'm\n"
f"Sevimli taom: {fav}\n"
f"Status: {vip}",
parse_mode="Markdown"
)
# ==================== ADMIN: MENYU ====================
async def admin_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update.effective_user.id):
return ConversationHandler.END
menu.clear()
context.user_data["menu_active"] = True
await update.message.reply_text(" *Bugungi menyuni kiriting*\n\n"
"Har bir taom:\n"
"• Matn: `Taom nomi - narx`\n"
"• Rasmli: rasm yuboring, caption da `Taom nomi - narx`\n\n"
"Tugagach /done yuboring.",
parse_mode="Markdown"
)
return MENU_INPUT
async def menu_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not context.user_data.get("menu_active"):
return ConversationHandler.END
text = update.message.text.strip()
if " - " not in text:
await update.message.reply_text(" return MENU_INPUT
Format: `Taom nomi - narx`", parse_mode="Markdown
parts = text.split(" - ", 1)
name = parts[0].strip()
try:
price = int(parts[1].strip().replace(",", "").replace(" ", ""))
except ValueError:
await update.message.reply_text(" Narx faqat raqam.")
return MENU_INPUT
menu[name] = {"price": price, "photo_id": None}
await update.message.reply_text(f" return MENU_INPUT
*{name}* — {price:,} so'm", parse_mode="Markdown")
async def menu_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not context.user_data.get("menu_active"):
return ConversationHandler.END
caption = update.message.caption or ""
if " - " not in caption:
await update.message.reply_text(" return MENU_INPUT
Caption: `Taom nomi - narx`", parse_mode="Markdow
parts = caption.split(" - ", 1)
name = parts[0].strip()
try:
price = int(parts[1].strip().replace(",", "").replace(" ", ""))
except ValueError:
await update.message.reply_text(" Narx faqat raqam.")return MENU_INPUT
photo_id = update.message.photo[-1].file_id
menu[name] = {"price": price, "photo_id": photo_id}
await update.message.reply_text(f" return MENU_INPUT
*{name}* — {price:,} so'm (rasmli)", parse_mode="
async def menu_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data["menu_active"] = False
if not menu:
await update.message.reply_text("Hech narsa kiritilmadi.")
return ConversationHandler.END
save_data()
lines = []
for n, v in menu.items():
p = v["price"] if isinstance(v, dict) else v
icon = " " if isinstance(v, dict) and v.get("photo_id") else " "
lines.append(f" {icon} {n} — {p:,} so'm")
await update.message.reply_text(
f" parse_mode="Markdown"
*Menyu saqlandi ({len(menu)} ta taom):*\n\n" + "\n".join(lines),
)
return ConversationHandler.END
# ==================== ADMIN: BUYURTMALAR ====================
async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update.effective_user.id):
return
today = get_today()
today_orders = [o for o in orders.values() if o["time"].startswith(today)]
if not today_orders:
return
await update.message.reply_text("Bugun hali buyurtma yo'q.")
total_rev = sum(o["total"] for o in today_orders)
status_map = {"new": " ", "cooking": " ", "delivering": " ", "delivered": " ", "canc
text = f" for o in today_orders:
u = users.get(o["user_id"], {})
*Bugungi buyurtmalar ({len(today_orders)} ta):*\n\n"items_short = ", ".join([f"{i['name']} x{i['qty']}" for i in o["items"]])
pay = "Naqd" if o["payment"] == "cash" else "Karta"
st = status_map.get(o.get("status", "new"), " ")
text += f"{st} *#{o['id']}* | {u.get('name','?')} | {items_short} | {o['total']:,} so
text += f"\n *Jami: {total_rev:,} so'm*"
await update.message.reply_text(text, parse_mode="Markdown")
# ==================== ADMIN: MIJOZLAR BAZASI ====================
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update.effective_user.id):
return
if not users:
await update.message.reply_text("Hali mijoz yo'q.")
return
total_users = len(users)
vip_users = sum(1 for u in users.values() if u.get("vip"))
active_today = len(set(
o["user_id"] for o in orders.values()
if o["time"].startswith(get_today())
))
text = (
f" *Mijozlar bazasi*\n\n"
f"Jami: {total_users} ta\n"
f" VIP: {vip_users} ta\n"
f"Bugun faol: {active_today} ta\n\n"
f"{'─' * 25}\n\n"
)
for uid, u in list(users.items()):
vip_icon = " " if u.get("vip") else ""
lat, lon = u.get("lat"), u.get("lon")
maps_url = f" [ ]({maps_link(lat, lon)})" if lat and lon else ""
last = u.get("last_order", u.get("joined", "?"))
text += (
f"{vip_icon}*{u['name']}*\n"
f" {u['phone']}{maps_url}\n"
f" {u.get('order_count', 0)} buyurtma | {u.get('total_spent', 0):,} so'm\n"
f" Oxirgi: {last}\n\n"
)
# Telegram 4096 belgi chegarasiif len(text) > 3500:
await update.message.reply_text(text, parse_mode="Markdown")
text = ""
if text:
await update.message.reply_text(text, parse_mode="Markdown")
# ==================== ADMIN: BROADCAST ====================
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update.effective_user.id):
return ConversationHandler.END
await update.message.reply_text(
f" parse_mode="Markdown"
Barcha *{len(users)}* ta mijozga xabar:\n(/cancel — bekor)",
)
return BROADCAST_TEXT
async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text
sent, failed = 0, 0
for uid in users:
try:
await context.bot.send_message(chat_id=uid, text=text)
sent += 1
except Exception:
failed += 1
await update.message.reply_text(
f" Xabar yuborildi!\n Yuborildi: {sent}\n Xato: {failed}"
)
return ConversationHandler.END
# ==================== ADMIN: HISOBOT ====================
async def admin_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update.effective_user.id):
return
today = get_today()
today_orders = [o for o in orders.values() if o["time"].startswith(today)]
today_rev = sum(o["total"] for o in today_orders)
week = get_week_key()
week_orders = stats["weekly"].get(week, 0)rated = [o for o in orders.values() if o.get("rated")]
avg_rating = sum(o["rating"] for o in rated) / len(rated) if rated else 0
best_day = max(stats["daily"], key=stats["daily"].get) if stats["daily"] else "-"
best_count = stats["daily"].get(best_day, 0)
avg_check = stats["total_revenue"] // stats["total_orders"] if stats["total_orders"] else
vip_count = sum(1 for u in users.values() if u.get("vip"))
# Top mahsulotlar
item_counts = {}
for o in orders.values():
for i in o["items"]:
item_counts[i["name"]] = item_counts.get(i["name"], 0) + i["qty"]
top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:3]
top_text = "\n".join([f" {i+1}. {n} — {c} ta" for i, (n, c) in enumerate(top_items)]) or
await update.message.reply_text(
f" *To'liq hisobot*\n\n"
f" *Bugun:*\n"
f" Buyurtmalar: {len(today_orders)} ta\n"
f" Tushum: {today_rev:,} so'm\n\n"
f" *Bu hafta:* {week_orders} ta buyurtma\n\n"
f" *Jami:*\n"
f" Buyurtmalar: {stats['total_orders']} ta\n"
f" Tushum: {stats['total_revenue']:,} so'm\n"
f" O'rtacha chek: {avg_check:,} so'm\n"
f" Mijozlar: {len(users)} ta\n"
f" VIP: {vip_count} ta\n"
f" O'rtacha baho: {avg_rating:.1f}/5\n"
f" Eng faol kun: {best_day} ({best_count} ta)\n\n"
f" *Top mahsulotlar:*\n{top_text}",
parse_mode="Markdown"
)
# ==================== CANCEL ====================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data.clear()
await update.message.reply_text(
" Bekor qilindi.",
reply_markup=main_keyboard(update.effective_user.id)
)
return ConversationHandler.END# ==================== MAIN ====================
def main():
load_data()
app = Application.builder().token(TOKEN).build()
# Ro'yxatdan o'tish
reg_conv = ConversationHandler(
entry_points=[CommandHandler("start", start)],
states={
REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
REG_PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), r
REG_LOCATION: [MessageHandler(filters.LOCATION | (filters.TEXT & ~filters.COMMAND
},
fallbacks=[CommandHandler("cancel", cancel)],
allow_reentry=True
)
# Buyurtma
order_conv = ConversationHandler(
entry_points=[MessageHandler(filters.Regex("^ Buyurtma berish$"), order_start)],
states={
ORDER_MENU: [CallbackQueryHandler(menu_callback, pattern="^(item_|checkout|clear_
ORDER_QUANTITY: [CallbackQueryHandler(quantity_callback, pattern="^(qty_|back_men
ORDER_UPSELL: [CallbackQueryHandler(upsell_callback, pattern="^upsell_")],
ORDER_PAYMENT: [CallbackQueryHandler(payment_callback, pattern="^pay_")],
ORDER_CONFIRM: [CallbackQueryHandler(confirm_callback, pattern="^confirm_")],
},
fallbacks=[CommandHandler("cancel", cancel)]
)
# Menyu
menu_conv = ConversationHandler(
entry_points=[
CommandHandler("menyu", admin_menu_start),
MessageHandler(filters.Regex("^ Menyu kiritish$"), admin_menu_start)
],
states={
MENU_INPUT: [
MessageHandler(filters.PHOTO, menu_photo_input),
MessageHandler(filters.TEXT & ~filters.COMMAND, menu_text_input),
CommandHandler("done", menu_done)
],
},
fallbacks=[CommandHandler("cancel", cancel)])
# Broadcast
broadcast_conv = ConversationHandler(
entry_points=[
CommandHandler("xabar", broadcast_start),
MessageHandler(filters.Regex("^ Xabar yuborish$"), broadcast_start)
],
states={
BROADCAST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_send)]
},
fallbacks=[CommandHandler("cancel", cancel)]
)
# Manzil yangilash
location_conv = ConversationHandler(
entry_points=[MessageHandler(filters.Regex("^ Manzilni yangilash$"), change_locatio
states={
CHANGE_LOCATION: [MessageHandler(filters.LOCATION | (filters.TEXT & ~filters.COMM
},
fallbacks=[CommandHandler("cancel", cancel)]
)
app.add_handler(reg_conv)
app.add_handler(order_conv)
app.add_handler(menu_conv)
app.add_handler(broadcast_conv)
app.add_handler(location_conv)
app.add_handler(CallbackQueryHandler(order_status_callback, pattern="^st_"))
app.add_handler(CallbackQueryHandler(rate_callback, pattern="^rate_"))
app.add_handler(CommandHandler("buyurtmalar", admin_orders))
app.add_handler(CommandHandler("hisobot", admin_report))
app.add_handler(CommandHandler("mijozlar", admin_users))
app.add_handler(MessageHandler(filters.Regex("^ Buyurtmalar$"), admin_orders))
app.add_handler(MessageHandler(filters.Regex("^ Hisobot$"), admin_report))
app.add_handler(MessageHandler(filters.Regex("^ Mijozlar bazasi$"), admin_users))
app.add_handler(MessageHandler(filters.Regex("^ Mening buyurtmalarim$"), my_orders))
app.add_handler(MessageHandler(filters.Regex("^ Profilim$"), my_profile))
print(" Gulcha Taom Bot ishga tushdi!")
app.run_polling(drop_pending_updates=True)
if __name__ == "__main__":main()
