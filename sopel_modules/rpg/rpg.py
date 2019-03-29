# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

# pylama:ignore=W,E201,E202,E203,E221,E222,w292,E231

from sopel import module

from .errormessages import *

import spicemanip
import sys
import inspect
import time
import uuid


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


"""
Triggers for usage
"""


# Base command
@module.commands('rpg')
@module.thread(True)
def rpg_trigger_module_command(bot, trigger):
    rpg_execute_start(bot, trigger, str(current_function()).split("rpg_trigger_")[-1])


# bot.nick do this
@module.nickname_commands('rpg')
@module.thread(True)
def rpg_trigger_nickname_command(bot, trigger):
    rpg_execute_start(bot, trigger, str(current_function()).split("rpg_trigger_")[-1])


"""
Command Processing
"""


def rpg_execute_start(bot, trigger, command_type):

    # Create dynamic class
    rpg = class_create('rpg')
    rpg.default = 'rpg'

    # Log unique ID for text processing
    rpg.messagesid = uuid.uuid4()
    messagelog_start(bot, rpg.messagesid)

    messagelog(bot, rpg.messagesid, trigger.sender, "Testing RPG    command_type=" + command_type + "    messageID=" + str(rpg.messagesid))

    rpg = rpg_prerun(bot, trigger, command_type, rpg)

    rpg_run_dict = rpg_run_check(bot, rpg)
    if rpg_run_dict["rpg_run_error"]:
        messagelog_error(bot, rpg.messagesid, rpg_run_dict["rpg_run_error"])
    else:
        messagelog(bot, rpg.messagesid, trigger.sender, "All is good to continue running.")

    messagelog_exit(bot, rpg, rpg.messagesid)


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
    for existing_messagedict in bot.memory['rpg']['message_display'][log_id]:
        if existing_messagedict["type"] == "error":
            if existing_messagedict["error_id"] == error_id:
                existing_messagedict["count"] += 1
                newloglist.append(existing_messagedict)
            else:
                newmessagedict = {"type": "error", "error_id": error_id, "count": 1, "recipient": "error"}
                newloglist.append(newmessagedict)
        else:
            newloglist.append(existing_messagedict)

    bot.memory['rpg']['message_display'][log_id] = newloglist


def messagelog(bot, log_id, recipient, message):

    messagedict = {"type": "normal", "message": message, "recipient": recipient}

    bot.memory['rpg']['message_display'][log_id].append(messagedict)


def messagelog_exit(bot, rpg, log_id):

    for messagedict in bot.memory['rpg']['message_display'][log_id]:
        if messagedict["type"] == "error":
            if messagedict["error_id"] not in error_message_dict.keys():
                message = "Error missing for ID '" + str(messagedict["error_id"]) + "'"
            else:
                message = error_message_dict[messagedict["error_id"]] + str(messagedict["count"])
            message += " (" + str(messagedict["count"]) + ")"
        else:
            message = messagedict["message"]

        if not isinstance(message, list):
            message = [message]
        for entry in message:
            if messagedict["recipient"] == 'error':
                bot.notice(entry, rpg.instigator)
            else:
                bot.say(entry, messagedict["recipient"])

    del bot.memory['rpg']['message_display'][log_id]


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


def current_function():
    return inspect.stack()[1][3]
