import time

from time import sleep
from typing import Optional

from telegram import Message, User
from telegram import MessageEntity, ParseMode
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, run_async

from ElitesOfRobot import dispatcher
from ElitesOfRobot import REDIS
from ElitesOfRobot.modules.users import get_user_id

from ElitesOfRobot.modules.helper_funcs.alternate import send_message
from ElitesOfRobot.modules.helper_funcs.readable_time import get_readable_time

from ElitesOfRobot.modules.disable import ( DisableAbleCommandHandler, 
                                            DisableAbleMessageHandler )
from ElitesOfRobot.modules.sql.redis import ( start_afk, end_afk, 
                                              is_user_afk, afk_reason )


AFK_GROUP = 7
AFK_REPLY_GROUP = 8

@run_async
def afk(update, context):
    args = update.effective_message.text.split(None, 1)
    user = update.effective_user
    if not user:  # ignore channels
        return

    if user.id == 777000:
        return
    start_afk_time = time.time()
    if len(args) >= 2:
        reason = args[1]
    else:
        reason = "none"
    start_afk(update.effective_user.id, reason)
    REDIS.set(f'afk_time_{update.effective_user.id}', start_afk_time)
    fname = update.effective_user.first_name
    try:
        sett_afkk = update.effective_message.reply_text(
            "User <b>{}</b> Is Now AFK!".format(fname), parse_mode="html")
        sleep(15)
        try:
            sett_afkk.delete()
        except BadRequest:
            pass
    except BadRequest:
        pass

@run_async
def no_longer_afk(update, context):
    user = update.effective_user
    message = update.effective_message
    if not user:  # ignore channels
        return

    if not is_user_afk(user.id):  #Check if user is afk or not
        return
    end_afk_time = get_readable_time((time.time() - float(REDIS.get(f'afk_time_{user.id}'))))
    REDIS.delete(f'afk_time_{user.id}')
    res = end_afk(user.id)
    if res:
        if message.new_chat_members:  #dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            rm_afkk = message.reply_text(
                "User <b>{}</b> Is No Longer AFK!\nYou Were AFK: <code>{}</code>".format(firstname, end_afk_time), parse_mode="html")
            sleep(30)
            try:
               rm_afkk.delete()
            except BadRequest:
               pass
        except Exception:
            return


@run_async
def reply_afk(update, context):
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION])

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            elif ent.type == MessageEntity.MENTION:
                user_id = get_user_id(message.text[ent.offset:ent.offset +
                                                   ent.length])
                if not user_id:
                    # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                    return

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

                try:
                    chat = context.bot.get_chat(user_id)
                except BadRequest:
                    print("Error: Could not fetch userid {} for AFK module".
                          format(user_id))
                    return
                fst_name = chat.first_name

            else:
                return

            check_afk(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, context, user_id, fst_name, userc_id)


def check_afk(update, context, user_id, fst_name, userc_id):
    if is_user_afk(user_id):
        reason = afk_reason(user_id)
        since_afk = get_readable_time((time.time() - float(REDIS.get(f'afk_time_{user_id}'))))
        if reason == "none":
            if int(userc_id) == int(user_id):
                return
            res = "User <b>{}</b> Is Currently AFK!\n\nLast Seen: <code>{}</code>".format(fst_name, since_afk)
            reply_afkk = update.effective_message.reply_text(res, parse_mode="html")
            sleep(60)
            try:
                reply_afkk.delete()
            except BadRequest:
               pass
        else:
            if int(userc_id) == int(user_id):
                return
            res = "User <b>{}</b> Is Currently AFK! \nSays It's Because Of:\n{}\n\nLast Seen: <code>{}</code>".format(fst_name, reason, since_afk)
            replly_afkk = update.effective_message.reply_text(res, parse_mode="html")
            sleep(60)
            try:
               replly_afkk.delete()
            except BadRequest:
               pass



def __gdpr__(user_id):
    end_afk(user_id)


__mod_name__ = "AFK"


AFK_HANDLER = DisableAbleCommandHandler("afk", afk)
AFK_REGEX_HANDLER = MessageHandler(Filters.regex("(?i)brb"), afk)
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.group, no_longer_afk)
AFK_REPLY_HANDLER = MessageHandler(Filters.all & Filters.group, reply_afk)

dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)

