# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

# pylama:ignore=W,E201,E202,E203,E221,E222,w292,E231

from sopel import module

from .messagelog import *

import spicemanip
import sys
import time
import uuid
import copy


def configure(config):
    pass


def setup(bot):

    try:
        import sopel_modules.osd
    except:
        raise ImportError('Sopel-RPG requires Sopel-OSD')

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
    rpg.inchannel = trigger.is_privmsg

    rpg.triggerargs = sopel_triggerargs(bot, trigger, command_type)

    return rpg


def rpg_run_check(bot, rpg):

    rpg_run_dict = {"rpg_run_error": None}

    if rpg.inchannel:
        rpg_run_dict["rpg_run_error"] = "privmsg_no"

    return rpg_run_dict


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
