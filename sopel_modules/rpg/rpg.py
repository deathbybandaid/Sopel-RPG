# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

# pylama:ignore=W,E201,E202,E203,E221,E222,w292,E231

from sopel import module

from .errormessages import *

import spicemanip
import sys
import time
import uuid
import copy


def configure(config):
    pass


def setup(bot):

    # Create memory reference for game
    bot.memory['rpg'] = dict()

    # open channel settings for current bot channels
    bot.memory['rpg']['channel_settings'] = dict()
    for channel in bot.channels.keys():
        bot.memory['rpg']['channel_settings'][str(channel).lower()] = bot.db.get_channel_value(bot, channel, 'rpg_channel_settings') or dict()

        if 'game_enabled' in bot.memory['rpg']['channel_settings'][str(channel).lower()].keys():
            if bot.memory['rpg']['channel_settings'][str(channel).lower()]['game_enabled']:
                dd = 5

    bot.memory['rpg']['message_display'] = dict()
    bot.memory['rpg']['message_display']["used_ids"] = [0]


"""
Triggers for usage
"""


# Base command
@module.commands('rpg')
@module.thread(True)
def rpg_trigger_module_command(bot, trigger):
    rpg_execute_start(bot, trigger, 'module_command')


# bot.nick do this
@module.nickname_commands('rpg')
@module.thread(True)
def rpg_trigger_nickname_command(bot, trigger):
    rpg_execute_start(bot, trigger, 'nickname_command')


"""
Command Processing
"""


def rpg_execute_start(bot, trigger, command_type):

    startupdebug = ["Testing RPG"]

    startupdebug.append("command_type=" + command_type)

    # Create dynamic class
    rpg = class_create('rpg')
    rpg.default = 'rpg'

    # Log unique ID for text processing
    rpg.messagesid = unique_id_create(bot)
    messagelog_start(bot, rpg.messagesid)

    rpg = rpg_prerun(bot, trigger, command_type, rpg)

    messagelog_error(bot, rpg.messagesid, "test_error1")
    startupdebug.append("messageID=" + str(rpg.messagesid))
    messagelog(bot, rpg.messagesid, rpg.channel_replyto, startupdebug)

    rpg_run_dict = rpg_run_check(bot, rpg)
    if rpg_run_dict["rpg_run_error"]:
        messagelog_error(bot, rpg.messagesid, rpg_run_dict["rpg_run_error"])
    else:
        rpg_execute_process(bot, rpg)

    messagelog_error(bot, rpg.messagesid, "test_error1")

    messagelog_error(bot, rpg.messagesid, "test_error2")
    messagelog_error(bot, rpg.messagesid, "test_error2")

    messagelog_exit(bot, rpg, rpg.messagesid)


def rpg_execute_process(bot, rpg):
    messagelog(bot, rpg.messagesid, rpg.channel_replyto, "All is good to continue running.")


"""
Prerun
"""


def rpg_prerun(bot, trigger, command_type, rpg):

    rpg.start = time.time()

    rpg.command_type = command_type

    rpg.instigator = trigger.nick

    rpg.channel_triggered = trigger.args[0]
    rpg.channel_replyto = trigger.sender
    rpg.channel_priv = trigger.is_privmsg

    rpg.triggerargs = sopel_triggerargs(bot, trigger, command_type)

    return rpg


def rpg_run_check(bot, rpg):

    rpg_run_dict = {"rpg_run_error": None}

    if rpg.channel_priv:
        rpg_run_dict["rpg_run_error"] = "privmsg_no"

    return rpg_run_dict


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
                existing_messagedict["count"] += 1
                error_exists_prior = True
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


"""
On Screen Text
"""


def osd(bot, recipients, text_type, messages):

    if not isinstance(messages, list):
        messages = [messages]

    if not isinstance(recipients, list):
        recipients = [recipients]
    recipients = ','.join(str(x) for x in recipients)

    # Count all Transfer bytes
    available_bytes = 512
    available_bytes -= bytecount(recipients)
    available_bytes -= bytecount(bot.nick)
    available_bytes -= 25

    messages_refactor = ['']
    for message in messages:
        chunknum = 0
        chunks = message.split()
        for chunk in chunks:
            if not chunknum:
                if bytecount(messages_refactor[-1] + "   " + chunk) <= available_bytes:
                    messages_refactor[-1] = messages_refactor[-1] + "   " + chunk
                else:
                    messages_refactor.append(chunk)
            else:
                if bytecount(messages_refactor[-1] + " " + chunk) <= available_bytes:
                    messages_refactor[-1] = messages_refactor[-1] + " " + chunk
                else:
                    messages_refactor.append(chunk)
            chunknum += 1

    # display
    for combinedline in messages_refactor:
        if text_type == 'action':
            bot.action(combinedline, recipients)
            text_type = 'say'
        elif text_type == 'notice':
            bot.notice(combinedline, recipients)
        else:
            bot.say(combinedline, recipients)


"""
How to Display Nicks
"""


# Outputs Nicks with correct capitalization
def nick_actual(bot, nick, userlist=[]):
    nick_actual = nick
    if userlist != []:
        for u in userlist:
            if u.lower() == nick_actual.lower():
                nick_actual = u
                continue
        return nick_actual
    for u in bot.users:
        if u.lower() == nick_actual.lower():
            nick_actual = u
            continue
    return nick_actual


"""
RPG Dynamic Classes
"""


def class_create(classname):
    compiletext = """
        def __init__(self):
            self.default = str(self.__class__.__name__)
        def __repr__(self):
            return repr(self.default)
        def __str__(self):
            return str(self.default)
        def __iter__(self):
            return str(self.default)
        def __unicode__(self):
            return str(u+self.default)
        def lower(self):
            return str(self.default).lower()
        pass
        """
    exec(compile("class class_" + str(classname) + ": " + compiletext, "", "exec"))
    newclass = eval('class_'+classname+"()")
    return newclass


"""
Functions that wrap around Sopel
"""


def sopel_triggerargs(bot, trigger, command_type):
    triggerargs = []

    if len(trigger.args) > 1:
        triggerargs = spicemanip.main(trigger.args[1], 'create')
    triggerargs = spicemanip.main(triggerargs, 'create')

    if command_type in ['module_command']:
        triggerargs = spicemanip.main(triggerargs, '2+', 'list')
    elif command_type in ['nickname_command']:
        triggerargs = spicemanip.main(triggerargs, '3+', 'list')

    return triggerargs


"""
Other Python Functions
"""


def unique_id_create(bot):
    unique_id = 0
    while unique_id in bot.memory['rpg']['message_display']["used_ids"]:
        unique_id = uuid.uuid4()
    bot.memory['rpg']['message_display']["used_ids"].append(unique_id)
    return unique_id


def bytecount(s):
    return sys.getsizeof(s)
    return len(s.encode('utf-8'))
