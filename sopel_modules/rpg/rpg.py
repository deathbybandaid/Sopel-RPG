# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

from sopel import module

import spicemanip
import sys
import inspect


def configure(config):
    pass


def setup(bot):
    pass


"""
Triggers for usage
"""


# Base command
@module.commands('rpg')
def rpg_trigger_normal(bot, trigger):
    execute_start(bot, trigger, str(current_function()).split("rpg_trigger_")[-1])


# work with /me ACTION
@module.rule('^(?:challenges|(?:fi(?:ght|te)|duel)s(?:\s+with)?)\s+([a-zA-Z0-9\[\]\\`_\^\{\|\}-]{1,32}).*')
@module.intent('ACTION')
def rpg_trigger_action(bot, trigger):
    execute_start(bot, trigger, str(current_function()).split("rpg_trigger_")[-1])


# bot.nick do this
@module.nickname_commands('rpg')
def rpg_trigger_nick_command(bot, trigger):
    execute_start(bot, trigger, str(current_function()).split("rpg_trigger_")[-1])


"""
Command Processing
"""


def execute_start(bot, trigger, command_type):

    bot.say("Testing RPG    command_type=" + command_type)

    # triggerargsarray = spicemanip.main(trigger.group(2), 'create')

    bot.say(str(trigger.args))
    bot.say(str(trigger))


"""
Other Python Functions
"""


def current_function():
    return inspect.stack()[1][3]
