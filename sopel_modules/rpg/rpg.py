# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

from sopel import module

from .rpg_errors import *

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


"""
Triggers for usage
"""


# Base command
@module.commands('rpg')
def rpg_trigger_module_command(bot, trigger):
    rpg_execute_start(bot, trigger, str(current_function()).split("rpg_trigger_")[-1])


# bot.nick do this
@module.nickname_commands('rpg')
def rpg_trigger_nickname_command(bot, trigger):
    rpg_execute_start(bot, trigger, str(current_function()).split("rpg_trigger_")[-1])


"""
Command Processing
"""


def rpg_execute_start(bot, trigger, command_type):

    bot.say("Testing RPG    command_type=" + command_type)

    # Create dynamic class
    rpg = class_create('rpg')
    rpg.default = 'rpg'

    rpg.uniqueid = uuid.uuid4()
    bot.say("your unique ID is " + str(rpg.uniqueid))

    bot.say("prerun time")

    rpg = rpg_prerun(bot, trigger, command_type, rpg)

    rpg_run_dict = rpg_run_check(bot, rpg)
    if rpg_run_dict["rpg_run_error"]:
        bot.say(rpg_run_dict["rpg_run_error"])
    else:
        bot.say("All is good to continue running.")


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

    bot.say(str(rpg.triggerargs))

    return rpg


def rpg_run_check(bot, rpg):

    rpg_run_dict = {"rpg_run_error": None}

    if rpg.channel_priv:
        rpg_run_dict["rpg_run_error"] = "Cannot run in private message!"

    return rpg_run_dict


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
Sopel Triggerargs list handling
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
