# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

from sopel import module

import spicemanip


def configure(config):
    pass


def setup(bot):
    pass


"""
Triggers for usage
"""


# Base command
@sopel.module.commands('rpg')
@sopel.module.thread(True)
def rpg_trigger_main(bot, trigger):
    command_type = 'normalcom'
    triggerargsarray = spicemanip.main(trigger.group(2), 'create')
    execute_start(bot, trigger, triggerargsarray, command_type)


"""
Command Processing
"""


def execute_start(bot, trigger, triggerargsarray, command_type):

    bot.say("loading a test of rpg")
