# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

from sopel import module


def configure(config):
    pass


def setup(bot):
    pass


@module.commands('rpg')
def execute_start(bot, trigger, triggerargsarray, command_type):

    bot.say("loading a test of rpg")
