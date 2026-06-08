from pyrogram import Client, filters
from pyrogram.types import Message

from bot.configs import config
from bot.database.repositories.requests import RequestRepository
from bot.database.repositories.users import UserRepository
from bot.filters import banned_filter
from bot.utils.decorators import log_errors, rate_limit


@Client.on_message(filters.command("request") & filters.private & ~banned_filter)
@rate_limit
@log_errors
async def request_handler(client: Client, message: Message) -> None:
    args = message.command[1:]
    if not args:
        await message.reply("Usage: `/request <movie title>`")
        return

    title = " ".join(args).strip()
    uid = message.from_user.id

    req_id = await RequestRepository.create(uid, title)
    await message.reply(
        f"✅ Your request for **{title}** has been saved.\n"
        "You'll be notified once it's added."
    )

    # Notify admins
    for admin_id in config.ADMINS:
        try:
            from bot.modules.keyboards import request_buttons
            await client.send_message(
                admin_id,
                f"📩 **New Movie Request**\n\n"
                f"Movie: **{title}**\n"
                f"From: [{message.from_user.first_name}](tg://user?id={uid}) (`{uid}`)\n"
                f"Request ID: `{req_id}`",
                reply_markup=request_buttons(req_id),
            )
        except Exception:
            pass


@Client.on_message(filters.command("myrequests") & filters.private & ~banned_filter)
@log_errors
async def my_requests_handler(client: Client, message: Message) -> None:
    reqs = await RequestRepository.get_user_requests(message.from_user.id)
    if not reqs:
        await message.reply("You have no pending requests.")
        return
    lines = ["📩 **Your Requests:**\n"]
    for r in reqs:
        lines.append(
            f"• **{r.get('title')}** — _{r.get('status', 'pending')}_"
        )
    await message.reply("\n".join(lines))
