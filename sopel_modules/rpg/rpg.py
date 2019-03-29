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


"""
Command Processing
"""


def execute_start(bot, trigger, command_type):

    bot.say("loading a test of rpg")

    # triggerargsarray = spicemanip.main(trigger.group(2), 'create')

    bot.say(str(trigger.args))
    bot.say(str(trigger))


"""
Other Python Functions
"""


def current_function():
    return inspect.stack()[1][3]
