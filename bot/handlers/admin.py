import asyncio

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.configs import config
from bot.database.repositories.movies import MovieRepository
from bot.database.repositories.requests import RequestRepository
from bot.database.repositories.users import UserRepository
from bot.filters import admin_filter
from bot.modules import admin_panel
from bot.utils.decorators import log_errors
from bot.utils.logger import log


@Client.on_message(filters.command("admin") & admin_filter)
@log_errors
async def admin_menu(app: Client, message: Message) -> None:
    await message.reply("🛠 **Admin Panel**", reply_markup=admin_panel())


@Client.on_message(filters.command("stats") & admin_filter)
@log_errors
async def stats_handler(app: Client, message: Message) -> None:
    total_users = await UserRepository.count()
    total_movies = await MovieRepository.count_all()
    pending_reqs = await RequestRepository.count_pending()
    await message.reply(
        f"📊 **Bot Statistics**\n\n"
        f"👥 Users: `{total_users}`\n"
        f"🎬 Indexed Movies: `{total_movies}`\n"
        f"📩 Pending Requests: `{pending_reqs}`"
    )


@Client.on_message(filters.command("broadcast") & admin_filter)
@log_errors
async def broadcast_handler(app: Client, message: Message) -> None:
    if not message.reply_to_message:
        await message.reply("Reply to a message to broadcast it.")
        return

    user_ids = await UserRepository.get_all_ids()
    success = failed = 0
    status = await message.reply(f"Broadcasting to {len(user_ids)} users…")
    for uid in user_ids:
        try:
            await message.reply_to_message.copy(uid)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await status.edit_text(
        f"📢 Broadcast complete\n✅ Sent: {success} | ❌ Failed: {failed}"
    )


@Client.on_message(filters.command("ban") & admin_filter)
@log_errors
async def ban_handler(app: Client, message: Message) -> None:
    parts = message.command
    if len(parts) < 2:
        await message.reply("Usage: `/ban <user_id> [reason]`")
        return
    uid = int(parts[1])
    reason = " ".join(parts[2:]) if len(parts) > 2 else "No reason"
    await UserRepository.ban(uid, reason)
    await message.reply(f"Banned user `{uid}`.")


@Client.on_message(filters.command("unban") & admin_filter)
@log_errors
async def unban_handler(app: Client, message: Message) -> None:
    parts = message.command
    if len(parts) < 2:
        await message.reply("Usage: `/unban <user_id>`")
        return
    uid = int(parts[1])
    ok = await UserRepository.unban(uid)
    await message.reply(f"Unbanned user `{uid}`." if ok else f"User `{uid}` was not banned.")


@Client.on_message(filters.command("addadmin") & admin_filter)
@log_errors
async def addadmin_handler(app: Client, message: Message) -> None:
    parts = message.command
    if len(parts) < 2:
        await message.reply("Usage: `/addadmin <user_id>`")
        return
    uid = int(parts[1])
    await UserRepository.add_admin(uid)
    await message.reply(f"User `{uid}` is now an admin.")


@Client.on_message(filters.command("removeadmin") & admin_filter)
@log_errors
async def removeadmin_handler(app: Client, message: Message) -> None:
    parts = message.command
    if len(parts) < 2:
        await message.reply("Usage: `/removeadmin <user_id>`")
        return
    uid = int(parts[1])
    ok = await UserRepository.remove_admin(uid)
    await message.reply(f"Removed admin `{uid}`." if ok else f"User `{uid}` was not an admin.")


@Client.on_message(filters.command("requests") & admin_filter)
@log_errors
async def requests_handler(app: Client, message: Message) -> None:
    pending = await RequestRepository.get_pending(10)
    if not pending:
        await message.reply("No pending requests.")
        return
    from bot.modules.keyboards import request_buttons
    for r in pending:
        rid = str(r["_id"])
        await message.reply(
            f"📩 **Request:** {r.get('title', '?')}\n"
            f"👤 User: `{r.get('user_id')}`\n"
            f"📅 Date: {str(r.get('requested_at', ''))[:10]}",
            reply_markup=request_buttons(rid),
        )


@Client.on_message(filters.command("reindex") & admin_filter)
@log_errors
async def reindex_handler(app: Client, message: Message) -> None:
    await message.reply(
        "Reindexing is done by forwarding videos to the storage channel(s). "
        "All new uploads are automatically indexed."
    )


@Client.on_message(filters.command("logs") & admin_filter)
@log_errors
async def logs_handler(app: Client, message: Message) -> None:
    import os
    from pathlib import Path

    log_path = Path(__file__).parent.parent / "logs" / "bot.log"
    if not log_path.exists():
        await message.reply("No log file found.")
        return
    size = os.path.getsize(log_path)
    if size > 4096:
        await app.send_document(message.chat.id, str(log_path), caption="Bot logs")
    else:
        with open(log_path) as f:
            await message.reply(f"```\n{f.read()[-3800:]}\n```")


# ── Callback dispatcher for admin panel ───────────────────────────────────────

async def admin_callback(app: Client, query: CallbackQuery) -> None:
    data = query.data or ""

    if data == "admin_stats":
        total_users = await UserRepository.count()
        total_movies = await MovieRepository.count_all()
        pending_reqs = await RequestRepository.count_pending()
        await query.message.edit_text(
            f"📊 **Stats**\n\n"
            f"👥 Users: `{total_users}`\n"
            f"🎬 Movies: `{total_movies}`\n"
            f"📩 Pending Requests: `{pending_reqs}`",
            reply_markup=admin_panel(),
        )
        await query.answer()

    elif data == "admin_requests":
        pending = await RequestRepository.get_pending(5)
        if not pending:
            await query.answer("No pending requests.", show_alert=True)
            return
        await query.answer()
        from bot.modules.keyboards import request_buttons
        for r in pending:
            rid = str(r["_id"])
            await app.send_message(
                query.message.chat.id,
                f"📩 **{r.get('title')}** — `{r.get('user_id')}`",
                reply_markup=request_buttons(rid),
            )

    elif data == "admin_users":
        count = await UserRepository.count()
        await query.answer(f"Total users: {count}", show_alert=True)

    elif data.startswith("fulfill|"):
        rid = data.split("|", 1)[1]
        ok = await RequestRepository.fulfill(rid, query.from_user.id)
        if ok:
            req = await RequestRepository.get_by_id(rid)
            if req:
                try:
                    await app.send_message(
                        req["user_id"],
                        f"✅ Your request for **{req.get('title')}** has been fulfilled! "
                        "Search for it now.",
                    )
                except Exception:
                    pass
            await query.answer("Request fulfilled.", show_alert=True)
        else:
            await query.answer("Failed.", show_alert=True)

    elif data.startswith("reject|"):
        rid = data.split("|", 1)[1]
        from bot.database.client import get_db
        from bson import ObjectId

        await get_db()["requests"].update_one(
            {"_id": ObjectId(rid)}, {"$set": {"status": "rejected"}}
        )
        await query.answer("Request rejected.", show_alert=True)

    elif data == "admin_broadcast":
        await query.message.reply("Reply to any message with /broadcast to send it to all users.")
        await query.answer()

    elif data == "admin_reindex":
        await query.answer("Upload videos to storage channels to index them.", show_alert=True)
