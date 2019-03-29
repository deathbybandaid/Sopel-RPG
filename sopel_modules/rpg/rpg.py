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

    # Create dynamic class
    rpg = class_create('rpg')
    rpg.default = 'rpg'

    bot.say("prerun time")

    rpg = rpg_prerun(bot, trigger, command_type, rpg)


"""
RPG Dynamic Classes
"""


def rpg_prerun(bot, trigger, command_type, rpg):

    rpg.triggerargs = []

    if len(trigger.args) > 1:
        rpg.triggerargs = spicemanip.main(trigger.args[0], 'create')
    rpg.triggerargs = spicemanip.main(rpg.triggerargs, 'create')
    bot.say(str(rpg.triggerargs))

    return rpg


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
Other Python Functions
"""


def current_function():
    return inspect.stack()[1][3]
