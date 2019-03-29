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
    command_type = str(current_function()).split("rpg_trigger_")[-1]
    bot.say(command_type)
    bot.say("testing update command")
    triggerargsarray = spicemanip.main(trigger.group(2), 'create')
    execute_start(bot, trigger, triggerargsarray, command_type)


"""
Command Processing
"""


def execute_start(bot, trigger, triggerargsarray, command_type):

    bot.say("loading a test of rpg")


"""
Other Python Functions
"""


def current_function():
    return inspect.stack()[1][3]
