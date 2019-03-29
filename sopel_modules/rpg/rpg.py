# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

# pylama:ignore=W,E201,E202,E203,E221,E222,w292,E231

from sopel import module

from .errormessages import *

import spicemanip
import sys
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
    rpg.messagesid = uuid.uuid4()
    messagelog_start(bot, rpg.messagesid)

    messagelog_error(bot, rpg.messagesid, "test_error1")
    startupdebug.append("messageID=" + str(rpg.messagesid))
    messagelog(bot, rpg.messagesid, trigger.sender, startupdebug)

    rpg = rpg_prerun(bot, trigger, command_type, rpg)

    rpg_run_dict = rpg_run_check(bot, rpg)
    if rpg_run_dict["rpg_run_error"]:
        messagelog_error(bot, rpg.messagesid, rpg_run_dict["rpg_run_error"])
    else:
        messagelog(bot, rpg.messagesid, trigger.sender, "All is good to continue running.")

    messagelog_error(bot, rpg.messagesid, "test_error1")

    messagelog_error(bot, rpg.messagesid, "test_error2")
    messagelog_error(bot, rpg.messagesid, "test_error2")

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

    for messagedict in bot.memory['rpg']['message_display'][log_id]:
        if messagedict["type"] == "error":
            if messagedict["error_id"] not in error_message_dict.keys():
                message = "Error missing for ID '" + str(messagedict["error_id"]) + "'"
            else:
                message = error_message_dict[messagedict["error_id"]]
            message += " (" + str(messagedict["count"]) + ")"
        else:
            message = messagedict["message"]

        if messagedict["type"] == 'error':
            osd(bot, rpg.instigator, 'notice', message)
        else:
            osd(bot, messagedict["recipients"], 'say', message)

    del bot.memory['rpg']['message_display'][log_id]


"""
On Screen Text
"""


def osd(bot, target_array, text_type_array, text_array):

    # if text_array is a string, make it an array
    textarraycomplete = []
    if not isinstance(text_array, list):
        textarraycomplete.append(text_array)
    else:
        for x in text_array:
            textarraycomplete.append(x)

    # if target_array is a string, make it an array
    texttargetarray = []
    if not isinstance(target_array, list):
        if not str(target_array).startswith("#"):
            target_array = nick_actual(bot, str(target_array))
        texttargetarray.append(target_array)
    else:
        for target in target_array:
            if not str(target).startswith("#"):
                target = nick_actual(bot, str(target))
            texttargetarray.append(target)

    # Handling for text_type
    texttypearray = []
    if not isinstance(text_type_array, list):
        for i in range(len(texttargetarray)):
            texttypearray.append(str(text_type_array))
    else:
        for x in text_type_array:
            texttypearray.append(str(x))
    text_array_common = max(((item, texttypearray.count(item)) for item in set(texttypearray)), key=lambda a: a[1])[0]

    # make sure len() equals
    if len(texttargetarray) > len(texttypearray):
        while len(texttargetarray) > len(texttypearray):
            texttypearray.append(text_array_common)
    elif len(texttargetarray) < len(texttypearray):
        while len(texttargetarray) < len(texttypearray):
            texttargetarray.append('osd_error_handle')

    # Rebuild the text array to ensure string lengths

    for target, text_type in zip(texttargetarray, texttypearray):

        if target == 'osd_error_handle':
            dont_say_it = 1
        else:

            # Text array
            temptextarray = []

            # Notice handling
            if text_type == 'notice':
                temptextarray.insert(0, target + ", ")
                # temptextarray.append(target + ", ")
            for part in textarraycomplete:
                temptextarray.append(part)

            # 'say' can equal 'priv'
            if text_type == 'say' and not str(target).startswith("#"):
                text_type = 'priv'

            # Make sure no individual string ins longer than it needs to be
            currentstring = ''
            texttargetarray = []
            for textstring in temptextarray:
                if len(textstring) > 420:
                    chunks = textstring.split()
                    for chunk in chunks:
                        if currentstring == '':
                            currentstring = chunk
                        else:
                            tempstring = str(currentstring + " " + chunk)
                            if len(tempstring) <= 420:
                                currentstring = tempstring
                            else:
                                texttargetarray.append(currentstring)
                                currentstring = chunk
                    if currentstring != '':
                        texttargetarray.append(currentstring)
                else:
                    texttargetarray.append(textstring)

            # Split text to display nicely
            combinedtextarray = []
            currentstring = ''
            for textstring in texttargetarray:
                if currentstring == '':
                    currentstring = textstring
                elif len(textstring) > 420:
                    if currentstring != '':
                        combinedtextarray.append(currentstring)
                        currentstring = ''
                    combinedtextarray.append(textstring)
                else:
                    tempstring = currentstring + "   " + textstring
                    if len(tempstring) <= 420:
                        currentstring = tempstring
                    else:
                        combinedtextarray.append(currentstring)
                        currentstring = textstring
            if currentstring != '':
                combinedtextarray.append(currentstring)

            # display
            textparts = len(combinedtextarray)
            textpartsleft = textparts
            for combinedline in combinedtextarray:
                if text_type == 'action' and textparts == textpartsleft:
                    bot.action(combinedline, target)
                elif str(target).startswith("#"):
                    bot.msg(target, combinedline)
                elif text_type == 'notice' or text_type == 'priv':
                    bot.notice(combinedline, target)
                elif text_type == 'say':
                    bot.say(combinedline)
                else:
                    bot.say(combinedline)
                textpartsleft = textpartsleft - 1


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


def current_function():
    return inspect.stack()[1][3]
