#!/usr/bin/env python
# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

# pylama:ignore=W,E201,E202,E203,E221,E222,w292,E231

error_message_dict = {
                        "privmsg_no": "RPG must be run in channel.",
                        }


"""
RPG Message Handling
"""


def messagelog_start(bot, log_id):

    bot.memory['rpg']['message_display'][log_id] = []


def messagelog_error(bot, log_id, error_id, error_content=[]):

    newloglist = []
    newerrorcontent = []
    error_exists_prior = False

    for existing_messagedict in bot.memory['rpg']['message_display'][log_id]:
        if existing_messagedict["type"] == "error":
            if existing_messagedict["error_id"] == error_id:
                error_exists_prior = True
                existing_messagedict["count"] += 1
                if error_content != []:
                    existing_messagedict["error_content"].extend(error_content)
        newloglist.append(existing_messagedict)

    if not error_exists_prior:
        newmessagedict = {"type": "error", "error_id": error_id, "count": 1, "error_content": error_content}
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
            osd(bot, rpg.instigator, 'notice', messagedict['message'])
        else:
            osd(bot, messagedict["recipients"], 'say', messagedict['message'])

    del bot.memory['rpg']['message_display'][log_id]


def messagelog_fillin(bot, rpg, message):

    if "$current_chan" in message:
        if rpg.inchannel:
            message = str(message.replace("$current_chan", rpg.channel_current))
        else:
            message = str(message.replace("$current_chan", 'privmsg'))

    return message


"""
On Screen Text
"""


def osd(bot, recipients, text_type, messages):

    if not isinstance(messages, list):
        messages = [messages]

    text_type = text_type.upper()
    if text_type == 'SAY' or text_type not in ['NOTICE', 'ACTION']:
        text_type = 'PRIVMSG'

    if not isinstance(recipients, list):
        recipients = recipients.split(",")

    available_bytes = 512
    reserved_irc_bytes = 15
    available_bytes -= reserved_irc_bytes
    available_bytes -= len((bot.users.get(bot.nick).hostmask).encode('utf-8'))

    maxtargets = 2
    # if server.capabilities.maxtargets # TODO
    recipientgroups, groupbytes = [], []
    while len(recipients):
        recipients_part = ','.join(x for x in recipients[-2:])
        groupbytes.append(len((recipients_part).encode('utf-8')))
        recipientgroups.append(recipients_part)
        del recipients[-2:]

    max_recipients_bytes = max(groupbytes)
    available_bytes -= max_recipients_bytes

    messages_refactor = ['']
    for message in messages:
        chunknum = 0
        chunks = message.split()
        for chunk in chunks:
            if not chunknum:
                if messages_refactor[-1] == '':
                    if len(chunk.encode('utf-8')) <= available_bytes:
                        messages_refactor[-1] = chunk
                    else:
                        chunksplit = map(''.join, zip(*[iter(chunk)]*available_bytes))
                        messages_refactor.extend(chunksplit)
                elif len((messages_refactor[-1] + " " + chunk).encode('utf-8')) <= available_bytes:
                    messages_refactor[-1] = messages_refactor[-1] + "   " + chunk
                else:
                    if len(chunk.encode('utf-8')) <= available_bytes:
                        messages_refactor.append(chunk)
                    else:
                        chunksplit = map(''.join, zip(*[iter(chunk)]*available_bytes))
                        messages_refactor.extend(chunksplit)
            else:
                if len((messages_refactor[-1] + " " + chunk).encode('utf-8')) <= available_bytes:
                    messages_refactor[-1] = messages_refactor[-1] + " " + chunk
                else:
                    if len(chunk.encode('utf-8')) <= available_bytes:
                        messages_refactor.append(chunk)
                    else:
                        chunksplit = map(''.join, zip(*[iter(chunk)]*available_bytes))
                        messages_refactor.extend(chunksplit)
            chunknum += 1

    for recipientgroup in recipientgroups:

        for combinedline in messages_refactor:
            if text_type == 'ACTION':
                bot.write(('PRIVMSG', recipientgroup), '\001ACTION {}\001'.format(combinedline))
                text_type = 'PRIVMSG'
            elif text_type == 'NOTICE':
                bot.write(('NOTICE', recipientgroup), combinedline)
            else:
                bot.write(('PRIVMSG', recipientgroup), combinedline)
