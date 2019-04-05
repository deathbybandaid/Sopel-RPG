#!/usr/bin/env python
# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import sopel_modules.osd

error_message_dict = {
                        "privmsg_no": "RPG must be run in channel.",
                        }


"""
RPG Message Handling
"""


def messagelog_start(bot, log_id):

    bot.memory['rpg']['message_display'][log_id] = []


def messagelog_error(bot, log_id, error_id):

    newloglist = []
    error_exists_prior = False

    for existing_messagedict in bot.memory['rpg']['message_display'][log_id]:
        if existing_messagedict["type"] == "error":
            if existing_messagedict["error_id"] == error_id:
                error_exists_prior = True
                existing_messagedict["count"] += 1
        newloglist.append(existing_messagedict)

    if not error_exists_prior:
        newmessagedict = {"type": "error", "error_id": error_id, "count": 1}
        newloglist.append(newmessagedict)

    bot.memory['rpg']['message_display'][log_id] = newloglist


def messagelog(bot, log_id, recipients, message):

    messagedict = {"type": "normal", "message": message, "recipients": recipients}

    bot.memory['rpg']['message_display'][log_id].append(messagedict)


def messagelog_exit(bot, rpg, log_id):

    current_messages = []
    current_errors = []

    for messagedict in bot.memory['rpg']['message_display'][log_id]:

        if messagedict["type"] == "error":
            if messagedict["error_id"] not in error_message_dict.keys():
                message = "Error missing for ID '" + str(messagedict["error_id"]) + "'"
            else:
                message = error_message_dict[messagedict["error_id"]]
            message += " (" + str(messagedict["count"]) + ")"
            message = messagelog_fillin(bot, rpg, message)
            current_errors.append(message)
        else:
            if current_errors != []:
                currenterrordict = {"type": "error", "message": current_errors}
                current_messages.append(currenterrordict)
                current_errors = []
            message = messagedict["message"]
            current_messages.append(messagedict)
    if current_errors != []:
        currenterrordict = {"type": "error", "message": current_errors}
        current_messages.append(currenterrordict)
        current_errors = []

    for messagedict in current_messages:
        if messagedict["type"] == 'error':
            bot.osd(messagedict['message'], rpg.instigator, 'notice')
        else:
            bot.osd(messagedict['message'], messagedict["recipients"], 'say')

    del bot.memory['rpg']['message_display'][log_id]


def messagelog_fillin(bot, rpg, message):

    if "$current_chan" in message:
        if rpg.inchannel:
            message = str(message.replace("$current_chan", rpg.channel_current))
        else:
            message = str(message.replace("$current_chan", 'privmsg'))

    return message
