#!/usr/bin/env python
# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division
# sopel imports
import sopel.module
from sopel.module import commands, nickname_commands, rule, priority, example, OP, HALFOP, ADMIN, VOICE, event, rule
from sopel.formatting import bold
import sopel
from sopel import module, tools, formatting
# Additional
import collections
import random
from random import randint, randrange
import time
import datetime
import re
import sys
import os
from os.path import exists
from num2words import num2words
from difflib import SequenceMatcher
from more_itertools import sort_together
from operator import itemgetter
import requests
from fake_useragent import UserAgent
from lxml import html
from statistics import mean
import itertools
import inspect
import pickle
# Game Folder
from .Global_Vars import *
reload(sys)
sys.setdefaultencoding('utf-8')


"""
Triggers for usage
"""


# Base command
@sopel.module.commands('rpg')
@sopel.module.thread(True)
def rpg_trigger_main(bot, trigger):
    command_type = 'normalcom'
    triggerargsarray = spicemanip(bot, trigger.group(2), 'create')
    execute_start(bot, trigger, triggerargsarray, command_type)


"""
Command Processing
"""


def execute_start(bot, trigger, triggerargsarray, command_type):

    bot.say("loading a test of rpg")

    # RPG dynamic Class
    rpg = class_create('rpg')
    rpg.default = 'rpg'

    # Load Game Players and map
    open_gamedict(bot, rpg)

    # Command type
    rpg.command_type = command_type

    # Time when Module use started
    rpg.start = time.time()

    # instigator
    rpg.instigator = trigger.nick

    rpg.tier_current = rpg.gamedict['tier_current']

    # Channel Listing
    rpg = rpg_command_channels(bot, rpg, trigger)

    # Bacic User List
    rpg = rpg_command_users(bot, rpg)

    # Error Display System Create
    rpg_errors_start(bot, rpg)

    # Get Map
    # rpg_map_read(bot, rpg)

    # Run the Process
    execute_main(bot, rpg, trigger, triggerargsarray)

    # Error Display System Display
    rpg_errors_end(bot, rpg)

    # Save open game dictionary at the end of each usage
    save_gamedict(bot, rpg)

    # Save any open user values
    save_user_dicts(bot, rpg)


def execute_main(bot, rpg, trigger, triggerargsarray):

    # No Empty Commands
    if triggerargsarray == []:
        errors(bot, rpg, 'commands', 3, 1)
        return

    # Entire command string
    rpg.command_full_complete = spicemanip(bot, triggerargsarray, 0)

    # IF "&&" is in the full input, it is treated as multiple commands, and is split
    rpg.multi_com_list = spicemanip(bot, triggerargsarray, "split_&&")
    rpg.commands_ran = []

    # Cycle through command array
    for command_split_partial in rpg.multi_com_list:
        rpg.triggerargsarray = spicemanip(bot, command_split_partial, 'create')

        # Admin only
        rpg.adminswitch = 0
        if [x for x in rpg.triggerargsarray if x == "-a"]:
            rpg.triggerargsarray.remove("-a")
            if rpg.instigator in rpg.gamedict["tempvals"]['bot_admins']:
                rpg.adminswitch = 1
            else:
                errors(bot, rpg, 'commands', 4, 1)

        # Split commands to pass
        rpg.command_full = spicemanip(bot, rpg.triggerargsarray, 0)
        rpg.command_main = spicemanip(bot, rpg.triggerargsarray, 1)
        # Check Command can run
        rpg = command_process(bot, trigger, rpg)
        if rpg.command_run:
            command_run(bot, rpg)
        rpg.commands_ran.append(rpg.command_main.lower())


def command_process(bot, trigger, rpg):

    rpg.command_run = 0

    # block instigator if not a playable
    if rpg.instigator.lower() in [x.lower() for x in rpg.gamedict["tempvals"]['cantplayarray']]:
        errors(bot, rpg, 'commands', 17, 1)
        return rpg

    # allow players to set custom shortcuts to numbers
    if str(rpg.command_main).isdigit():
        number_command = get_user_dict(bot, rpg, rpg.instigator, 'hotkey_'+str(rpg.command_main)) or 0
        if not number_command:
            errors(bot, rpg, 'commands', 8, rpg.command_main)
            return rpg
        else:
            number_command_list = get_user_dict(bot, rpg, rpg.instigator, 'hotkey_complete') or []
            if rpg.command_main.lower() not in number_command_list:
                adjust_user_dict_array(bot, rpg, rpg.instigator, 'hotkey_complete', [rpg.command_main.lower()], 'add')
            commandremaining = spicemanip(bot, rpg.triggerargsarray, '2+') or ''
            number_command = str(number_command + " " + commandremaining)
            rpg.triggerargsarray = spicemanip(bot, number_command, 'create')
            rpg.command_full = spicemanip(bot, rpg.triggerargsarray, 0)
            rpg.command_main = spicemanip(bot, rpg.triggerargsarray, 1)

    # Spell Check
    if rpg.command_main.lower() not in rpg.gamedict['static']['commands'].keys() and rpg.command_main.lower() not in rpg.gamedict['static']['alt_commands'].keys() and rpg.command_main.lower() not in [x.lower() for x in rpg.gamedict["users"]['users_all']]:
        startcom = rpg.command_main
        sim_com, sim_num = [], []
        command_type_list = ["rpg.gamedict['static']['commands'].keys()", "rpg.gamedict['static']['alt_commands'].keys()", "rpg.gamedict['users']['users_all']"]
        for comtype in command_type_list:
            comtype_eval = eval(comtype)
            for com in comtype_eval:
                similarlevel = similar(rpg.command_main.lower(), com.lower())
                if similarlevel >= .75:
                    sim_com.append(com)
                    sim_num.append(similarlevel)
        if sim_com != [] and sim_num != []:
            sim_num, sim_com = array_arrangesort(bot, sim_num, sim_com)
            rpg.command_main = spicemanip(bot, sim_com, 'last')
        if rpg.command_main.lower() != startcom.lower():
            rpg.triggerargsarray.remove(startcom)
            rpg.triggerargsarray.insert(0, rpg.command_main)
            rpg.command_full = spicemanip(bot, rpg.triggerargsarray, 0)

    # Instigator versus Instigator
    if rpg.command_main.lower() == rpg.instigator.lower() and not rpg.adminswitch:
        errors(bot, rpg, 'commands', 13, 1)
        return rpg

    # Instigator versus Bot
    if rpg.command_main.lower() == bot.nick.lower() and not rpg.adminswitch:
        errors(bot, rpg, 'commands', 12, 1)
        return rpg

    # Instigator versus Other Bots
    if rpg.command_main.lower() in [x.lower() for x in rpg.gamedict["tempvals"]['bots_list']]:
        errors(bot, rpg, 'commands', 11, nick_actual(bot, rpg.command_main, rpg.gamedict['users']['users_all']))
        return rpg

    # Targets
    if rpg.command_main.lower() in [x.lower() for x in rpg.gamedict["users"]['users_all']] and rpg.command_main.lower() not in rpg.gamedict['static']['commands'].keys():
        rpg.command_main = 'combat'
        rpg.triggerargsarray.insert(0, rpg.command_main)
        rpg.command_full = spicemanip(bot, rpg.triggerargsarray, 0)

    # Alternate commands convert
    if rpg.command_main.lower() in rpg.gamedict['static']['alt_commands'].keys():
        startcom = rpg.command_main
        rpg.triggerargsarray.remove(rpg.command_main)
        rpg.command_main = eval("rpg.gamedict['static']['alt_commands']['" + rpg.command_main.lower() + "']['realcom']") or 'invalidcommand'
        if rpg.command_main.lower() == 'invalidcommand':
            errors(bot, rpg, 'commands', 9, startcom)
            return rpg
        rpg.triggerargsarray.insert(0, rpg.command_main)
        rpg.command_full = spicemanip(bot, rpg.triggerargsarray, 0)

    # multicom multiple of the same
    if rpg.command_main.lower() in rpg.commands_ran and not rpg.adminswitch:
        errors(bot, rpg, 'commands', 5, 1)
        return rpg

    # konami

    # Verify Command is valid
    if rpg.command_main.lower() not in rpg.gamedict['static']['commands'].keys():
        errors(bot, rpg, 'commands', 6, rpg.command_main)
        return rpg

    # Verify Game enabled in current channel
    if rpg.channel_current not in rpg.gamedict['channels']['game_enabled'] and rpg.channel_real and not rpg.gamedict['static']['commands'][rpg.command_main.lower()]['admin_only']:
        if rpg.gamedict['channels']['game_enabled'] == []:
            errors(bot, rpg, 'commands', 1, 1)
            if rpg.instigator not in rpg.gamedict["tempvals"]['bot_admins']:
                return rpg
        else:
            errors(bot, rpg, 'commands', 2, 1)
            if rpg.instigator not in rpg.gamedict["tempvals"]['bot_admins']:
                return rpg

    # Admin Block
    if rpg.gamedict['static']['commands'][rpg.command_main.lower()]['admin_only'] and not rpg.adminswitch:
        errors(bot, rpg, 'commands', 7, rpg.command_main)
        return rpg

    # Commands that Must be run in a channel
    if rpg.gamedict['static']['commands'][rpg.command_main.lower()]['inchannel_only'] and not rpg.adminswitch:
        errors(bot, rpg, 'commands', 10, rpg.command_main)
        return rpg

    # action commands
    if rpg.command_type == 'action' and rpg.gamedict['static']['commands'][rpg.command_main.lower()]['action_dissallow']:
        errors(bot, rpg, 'commands', 14, rpg.command_main)
        return rpg

    # Tier Check
    command_tier_required = int(eval("rpg.gamedict['static']['commands']['" + rpg.command_main.lower() + "']['tier_number']")) or 0
    if command_tier_required > int(rpg.tier_current):
        errors(bot, rpg, 'commands', 15, rpg.command_main)
        return rpg

    # Safe to run command
    rpg.command_run = 1

    return rpg


def command_run(bot, rpg):

    # Clear triggerargsarray of the main command
    rpg.triggerargsarray.remove(rpg.command_main)

    # Check Initial Stamina
    instigator.stamina = get_user_dict(bot, rpg, rpg.instigator, 'stamina') or 10
    rpg.staminarequired, rpg.staminacharge = 0, 0
    """ TODO track rpg.staminarequired  adding/subtracting in comparison to completion of any action, and error if not enough"""

    # Run the command's function
    command_function_run = str('rpg_command_main_' + rpg.command_main.lower() + '(bot, rpg)')
    eval(command_function_run)

    if rpg.staminacharge:
        bot.say("charge")

    # Deduct stamina from instigator
    # if rpg.staminarequired:
    #    adjust_user_dict(bot, rpg, rpg.instigator, 'stamina', -abs(rpg.staminarequired))

    # usage counter - instigator
    adjust_user_dict(bot, rpg, rpg.instigator, 'usage_' + rpg.command_main.lower(), 1)
    adjust_user_dict(bot, rpg, rpg.instigator, 'usage_total', 1)

    # usage counter - Total
    adjust_user_dict(bot, rpg, 'rpg_game_records', 'usage_' + rpg.command_main.lower(), 1)
    adjust_user_dict(bot, rpg, 'rpg_game_records', 'usage_total', 1)


"""
Exploration
"""


def rpg_command_main_travel(bot, rpg):

    subcommand_valid = ['north', 'south', 'east', 'west', 'town', 'current']
    subcommand = spicemanip(bot, [x for x in rpg.triggerargsarray if x in subcommand_valid], 1) or 'current'

    nickmap, nickcoord = rpg_map_nick_get(bot, rpg, rpg.instigator)
    nickcoord = eval(str(nickcoord))
    locationdict = rpg_get_latlong(bot, rpg, nickmap, str(nickcoord), 'returndict')

    if subcommand == 'current':
        bot.say(str(nickmap))
        bot.say(str(nickcoord))
        bot.say(str(locationdict))
        return

    latitude = nickcoord[0]
    longitude = nickcoord[1]
    newlatitude = latitude
    newlongitude = longitude

    if subcommand == 'north':
        newlatitude = int(latitude) + 1
    elif subcommand == 'south':
        newlatitude = int(latitude) - 1
    elif subcommand == 'east':
        newlongitude = int(longitude) + 1
    elif subcommand == 'west':
        newlongitude = int(longitude) - 1
    elif subcommand == 'town':
        towncoordinates = rpg_map_town(bot, rpg, nickmap)
        towncoordinates = eval(str(towncoordinates))
        newlatitude = towncoordinates[0]
        newlongitude = towncoordinates[1]

    mapsize = get_user_dict(bot, rpg, nickmap, 'mapsize')
    if int(newlatitude) > abs(mapsize):
        bot.say("cant go north anymore")
        return
    if int(newlatitude) < -abs(mapsize):
        bot.say("cant go south anymore")
        return
    if int(newlongitude) > abs(mapsize):
        bot.say("cant go east anymore")
        return
    if int(newlongitude) < -abs(mapsize):
        bot.say("cant go west anymore")
        return
    if str(latitude) == str(newlatitude) and str(longitude) == str(newlongitude):
        bot.say("stay current location")
        return

    newnickcoord = str("(" + str(newlatitude) + "," + str(newlongitude) + ")")

    rpg_map_move_nick(bot, rpg, rpg.instigator, nickmap, str(newnickcoord))
    bot.say("moved to " + str(newnickcoord))


"""
Combat
"""


def rpg_command_main_combat(bot, rpg):
    bot.say("combat not written yet")


"""
Configuration Commands
"""


def rpg_command_main_administrator(bot, rpg):

    # Subcommand
    subcommand_valid = rpg.gamedict['static']['commands'][rpg.command_main.lower()]['subcommands_valid'].keys()
    subcommand_default = rpg.gamedict['static']['commands'][rpg.command_main.lower()]['subcommands_valid']['default']
    subcommand = spicemanip(bot, [x for x in rpg.triggerargsarray if x in subcommand_valid], 1) or subcommand_default
    if not subcommand:
        errors(bot, rpg, rpg.command_main, 1, 1)
        return

    if subcommand == 'channel':

        # Toggle Type
        activation_type = spicemanip(bot, [x for x in rpg.triggerargsarray if x in rpg.gamedict['static']['commands'][rpg.command_main.lower()]['subcommands_valid'][subcommand.lower()].keys()], 1)
        if not activation_type:
            errors(bot, rpg, 'administrator', 2, 1)
            return

        activation_type_db = str(activation_type + "_enabled")

        # Channel
        channeltarget = spicemanip(bot, [x for x in rpg.triggerargsarray if x in rpg.gamedict["tempvals"]['channels_list']], 1)
        if not channeltarget:
            if rpg.channel_current.startswith('#'):
                channeltarget = rpg.channel_current
            else:
                errors(bot, rpg, 'administrator', 3, 1)
                return

        # on/off
        activation_direction = spicemanip(bot, [x for x in rpg.triggerargsarray if x in onoff_list], 1)
        if not activation_direction:
            errors(bot, rpg, rpg.command_main, 4, 1)
            return

        # Evaluate change
        current_channel_facet = rpg.gamedict['channels'][activation_type_db]
        if activation_type == 'devmode':
            if activation_direction in activate_list:
                current_channel_facet_error = 5
            else:
                current_channel_facet_error = 6
        elif activation_type == 'game':
            if activation_direction in activate_list:
                current_channel_facet_error = 7
            else:
                current_channel_facet_error = 8

        # make the change
        if activation_direction in activate_list:
            if channeltarget.lower() in [x.lower() for x in current_channel_facet]:
                errors(bot, rpg, rpg.command_main, current_channel_facet_error, 1)
                return
            rpg.gamedict['channels'][activation_type_db].append(channeltarget)
            osd(bot, channeltarget, 'say', "RPG " + activation_type + " has been enabled in " + channeltarget + "!")
        elif activation_direction in deactivate_list:
            if channeltarget.lower() not in [x.lower() for x in current_channel_facet]:
                errors(bot, rpg, rpg.command_main, current_channel_facet_error, 1)
                return
            rpg.gamedict['channels'][activation_type_db].remove(channeltarget)
            osd(bot, channeltarget, 'say', "RPG " + activation_type + " has been disabled in " + channeltarget + "!")

        if activation_type == 'game':
            errors_reset(bot, rpg, 'commands', 1)

        return


def rpg_command_main_settings(bot, rpg):

    # Subcommand
    subcommand_valid = rpg.gamedict['static']['commands'][rpg.command_main.lower()]['subcommands_valid'].keys()
    subcommand_default = rpg.gamedict['static']['commands'][rpg.command_main.lower()]['subcommands_valid']['default']
    subcommand = spicemanip(bot, [x for x in rpg.triggerargsarray if x in subcommand_valid], 1) or subcommand_default
    if not subcommand:
        errors(bot, rpg, rpg.command_main, 1, 1)
        return

    # Who is the target
    target = spicemanip(bot, [x for x in rpg.triggerargsarray if x in rpg.gamedict["users"]['users_all']], 1) or rpg.instigator
    if target != rpg.instigator:
        if not rpg.adminswitch:
            errors(bot, rpg, rpg.command_main, 2, 1)
            return
        if target not in rpg.gamedict["users"]['users_all']:
            errors(bot, rpg, rpg.command_main, 3, target)
            return

    # Hotkey
    if subcommand == 'hotkey':
        rpg.triggerargsarray.remove(subcommand)

        numberused = spicemanip(bot, [x for x in rpg.triggerargsarray if str(x).isdigit()], 1) or 'nonumber'

        activation_type = spicemanip(bot, [x for x in rpg.triggerargsarray if x in rpg.gamedict['static']['commands'][rpg.command_main.lower()]['subcommands_valid'][subcommand.lower()].keys()], 1) or 'view'

        if hotkeysetting == 'list':
            hotkeyscurrent = get_user_dict(bot, rpg, target, 'hotkey_complete') or []
            if hotkeyscurrent == []:
                errors(bot, rpg, rpg.command_main, 5, 1)
                return
            hotkeyslist = []
            for key in hotkeyscurrent:
                keynumber = get_user_dict(bot, rpg, rpg.instigator, 'hotkey_'+str(key)) or 0
                if keynumber:
                    hotkeyslist.append(str(key) + "=" + str(keynumber))
            hotkeyslist = spicemanip(bot, hotkeyslist, 'list')
            osd(bot, rpg.channel_current, 'say', "Your hotkey list: " + hotkeyslist)
            return

        if numberused == 'nonumber':
            errors(bot, rpg, rpg.command_main, 4, 1)
            return
        number_command = get_user_dict(bot, rpg, rpg.instigator, 'hotkey_'+str(numberused)) or 0

        if hotkeysetting != 'update':
            if not number_command:
                errors(bot, rpg, rpg.command_main, 6, numberused)
                return

        if hotkeysetting == 'view':
            osd(bot, rpg.channel_current, 'say', "You currently have " + str(numberused) + " set to '" + number_command + "'")
            return

        if hotkeysetting == 'reset':
            reset_user_dict(bot, rpg, rpg.instigator, 'hotkey_'+str(numberused))
            adjust_user_dict_array(bot, rpg, target, 'hotkey_complete', [numberused], 'del')
            osd(bot, rpg.channel_current, 'say', "Your command for hotkey "+str(numberused)+" has been reset")
            return

        if hotkeysetting == 'update':
            if target in rpg.triggerargsarray:
                rpg.triggerargsarray.remove(target)
            rpg.triggerargsarray.remove(numberused)
            rpg.triggerargsarray.remove(hotkeysetting)

            newcommandhot = spicemanip(bot, rpg.triggerargsarray, 0) or 0
            if not newcommandhot:
                errors(bot, rpg, rpg.command_main, 7, 1)
                return

            actualcommand_main = spicemanip(bot, rpg.triggerargsarray, 1) or 0
            if actualcommand_main not in rpg.gamedict['static']['commands'].keys():  # TODO altcoms
                errors(bot, rpg, rpg.command_main, 8, str(actualcommand_main))
                return

            set_user_dict(bot, rpg, rpg.instigator, 'hotkey_'+str(numberused), newcommandhot)
            adjust_user_dict_array(bot, rpg, target, 'hotkey_complete', [numberused], 'add')
            osd(bot, rpg.channel_current, 'say', "Your "+str(numberused)+" command has been set to '" + newcommandhot+"'")
            return

        return


"""
Basic User Commands
"""


def rpg_command_main_author(bot, rpg):

    osd(bot, rpg.channel_current, 'say', "The author of RPG is deathbybandaid.")


def rpg_command_main_intent(bot, rpg):

    # Who is the target
    target = spicemanip(bot, [x for x in rpg.triggerargsarray if x in rpg.gamedict["users"]['users_all']], 1) or rpg.instigator

    osd(bot, rpg.channel_current, 'say', "The intent is to provide " + target + " with a sense of pride and accomplishment...")


def rpg_command_main_about(bot, rpg):

    osd(bot, rpg.channel_current, 'say', "The purpose behind RPG is for deathbybandaid to learn python, while providing a fun, evenly balanced gameplay.")


def rpg_command_main_version(bot, rpg):

    # Attempt to get revision date from Github
    if not rpg.gamedict["tempvals"]['versionnumber']:
        rpg.gamedict["tempvals"]['versionnumber'] = versionnumber(bot, rpg)

    osd(bot, rpg.channel_current, 'say', "The RPG framework was last modified on " + str(rpg.gamedict["tempvals"]['versionnumber']) + ".")


def rpg_command_main_docs(bot, rpg):  # TODO
    bot.say("wip")


def rpg_command_main_usage(bot, rpg):  # TODO

    # Get The Command Used
    subcommand = spicemanip(bot, [x for x in rpg.triggerargsarray if x in rpg.gamedict['static']['commands'].keys()], 1) or 'total'

    # Who is the target
    target = spicemanip(bot, [x for x in rpg.triggerargsarray if x in rpg.gamedict["users"]['users_all'] or x == 'channel'], 1) or rpg.instigator
    targetname = target
    if target == 'channel':
        target = 'rpg_game_records'
        targetname = "The channel"

    # Usage Counter
    totaluses = get_user_dict(bot, rpg, target, 'usage_' + subcommand) or 0
    if not totaluses:
        if subcommand == 'total':
            subcommand = ''
        osd(bot, rpg.channel_current, 'say', targetname + " has no record of using rpg " + subcommand + ". ")
        return

    # Display
    if subcommand == 'total':
        subcommand = 'a total of'
    else:
        subcommand = str(subcommand + ' a total of')
    osd(bot, rpg.channel_current, 'say', targetname + " has used rpg " + subcommand + " " + str(totaluses) + " times.")


"""
Bot Startup Monologue
"""


@sopel.module.interval(rpg_game_dict['tempvals']['monologuecheck'])  # TODO make this progress with the game
def rpg_bot_start_script(bot):

    # Create rp class
    rpg = class_create('rpg')

    # Load Game Players and map
    open_gamedict(bot, rpg)

    if rpg.gamedict['channels']['game_enabled'] == []:
        return

    # null trigger stuff
    trigger = class_create('trigger')
    trigger.sender = "SpiceRealm"

    startup_monologue = []
    startup_monologue.append("\x0309The Spice Realms are vast; full of wonder, loot, monsters, and peril!     Will you, Brave Adventurers, be triumphant over the challenges that await?\x03")

    if not rpg.gamedict["tempvals"]['versionnumber']:
        rpg.gamedict["tempvals"]['versionnumber'] = versionnumber(bot, rpg)

    for channel in rpg.gamedict['channels']['game_enabled']:
        if channel not in rpg.gamedict["tempvals"]['startupmonologue']:
            rpg.gamedict["tempvals"]['startupmonologue'].append(channel)
            osd(bot, channel, 'notice', startup_monologue)

            # spacing for extra lines
            amountofspace = len(str(channel))
            spacing = " " * amountofspace
            spacing = str(spacing + "           ")

            osd(bot, channel, 'say', str(spacing) + "\x0309Loading Game Version Revision " + str(rpg.gamedict["tempvals"]['versionnumber'] + "\x03"))

    # no need to continually check
    rpg_game_dict['tempvals']['monologuecheck'] = rpg_game_dict['tempvals']['monologuecheck'] + 99999999999999999

    # Channel Listing
    rpg = rpg_command_channels(bot, rpg, trigger)

    # Bacic User List
    rpg = rpg_command_users(bot, rpg)

    # TODO enforce loading time to ensure users are loaded corectly as admin/owner/etc
    # then add to the dialogue "Loading game, version *"


"""
Switches
"""


def find_switch_equal(bot, inputarray, switch):
    exitoutput = ''
    switchtofind = str("-"+str(switch)+'="')
    arraymarker = 0
    beguinemark, finishmark = 0, 0
    if [wordpart for wordpart in inputarray if wordpart.startswith(switchtofind)]:
        for partial in inputarray:
            arraymarker += 1
            if partial.startswith(switchtofind):
                beguinemark = arraymarker
            if partial.endswith('"'):
                if not finishmark and beguinemark != 0:
                    finishmark = arraymarker
                    continue
        if finishmark != 0:
            exitoutputrange = str(str(beguinemark) + "^" + str(finishmark))
            exitoutput = spicemanip(bot, inputarray, exitoutputrange)
            exitoutput = spicemanip(bot, exitoutput, 0)  # new
            # exitoutput = exitoutput.replace("-"+switch+'=', ' ')
            # exitoutput = exitoutput.replace('"', '')
            # exitoutput = exitoutput.strip()
    return exitoutput


"""
Small Functions
"""


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


"""
Debug
"""


def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno


"""
Errors
"""


def errors(bot, rpg, error_type, number, append):
    current_error_value = eval("rpg.errors." + error_type + str(number))
    current_error_value.append(append)


def errors_reset(bot, rpg, error_type, number):
    current_error_value = str("rpg.errors." + error_type + str(number) + " = []")
    exec(current_error_value)


def rpg_errors_start(bot, rpg):
    rpg.errors = class_create('errors')
    if rpg.gamedict["tempvals"]['errorscanlist'] == []:
        for error_type in rpg.gamedict['static']['errors'].keys():
            rpg.gamedict["tempvals"]['errorscanlist'].append(error_type)
    for error_type in rpg.gamedict["tempvals"]['errorscanlist']:
        for i in range(0, len(rpg.gamedict['static']['errors'][error_type.lower()])):
            current_error_number = i + 1
            current_error_value = str("rpg.errors." + error_type + str(current_error_number) + " = []")
            exec(current_error_value)


def rpg_errors_end(bot, rpg):
    rpg.error_display = []
    rpg.tier_current = rpg.gamedict['tier_current']
    if rpg.gamedict["tempvals"]['errorscanlist'] == []:
        for error_type in rpg.gamedict['static']['errors'].keys():
            rpg.gamedict["tempvals"]['errorscanlist'].append(error_type)
    for error_type in rpg.gamedict["tempvals"]['errorscanlist']:
        for i in range(0, len(rpg.gamedict['static']['errors'][error_type.lower()])):
            current_error_number = i + 1
            currenterrorvalue = eval("rpg.errors." + error_type.lower() + str(current_error_number)) or []
            if currenterrorvalue != []:
                errormessage = spicemanip(bot, rpg.gamedict['static']['errors'][error_type.lower()], current_error_number)
                if error_type in rpg.gamedict['static']['commands'].keys():
                    errormessage = str("[" + str(error_type.title()) + "] " + errormessage)
                totalnumber = len(currenterrorvalue)
                errormessage = str("(" + str(totalnumber) + ") " + errormessage)
                if "$list" in errormessage:
                    errorlist = spicemanip(bot, currenterrorvalue, 'list')
                    errormessage = str(errormessage.replace("$list", errorlist))
                if "$tiers_nums_peppers" in errormessage:
                    numberarray, pepperarray, combinedarray = [], [], []
                    for command in currenterrorvalue:
                        peppereval = rpg.gamedict['static']['commands'][rpg.command.lower()][tier_pepper]
                        pepperarray.append(peppereval)
                        numbereval = int(rpg.gamedict['static']['commands'][rpg.command.lower()]['tier_number'])
                        numberarray.append(numbereval)
                    for num, pepp in zip(numberarray, pepperarray):
                        combinedarray.append(str(num) + " " + pepp)
                    errorlist = spicemanip(bot, combinedarray, 'list')
                    errormessage = str(errormessage.replace("$tiers_nums_peppers", errorlist))
                if "$valid_coms" in errormessage:
                    validcomslist = spicemanip(bot, rpg.gamedict['static']['commands'].keys(), 'list')
                    errormessage = str(errormessage.replace("$valid_coms", validcomslist))
                if "$game_chans" in errormessage:
                    gamechanlist = spicemanip(bot, rpg.gamedict['channels']['game_enabled'], 'list')
                    errormessage = str(errormessage.replace("$game_chans", gamechanlist))
                if "$valid_channels" in errormessage:
                    validchanlist = spicemanip(bot, rpg.gamedict["tempvals"]['channels_list'], 'list')
                    errormessage = str(errormessage.replace("$valid_channels", validchanlist))
                if "$valid_onoff" in errormessage:
                    validtogglelist = spicemanip(bot, onoff_list, 'list')
                    errormessage = str(errormessage.replace("$valid_onoff", validtogglelist))
                if "$valid_subcoms" in errormessage:
                    subcommand_valid = rpg.gamedict['static']['commands'][error_type.lower()]['subcommands_valid'].keys()
                    subcommand_valid = spicemanip(bot, subcommand_valid, 'list')
                    errormessage = str(errormessage.replace("$valid_subcoms", subcommand_valid))
                if "$valid_game_change" in errormessage:
                    subcommand_arg_valid = spicemanip(bot, rpg.gamedict['static']['commands'][rpg.command_main.lower()]['subcommands_valid']['channel'].keys(), 'list')
                    errormessage = str(errormessage.replace("$valid_game_change", subcommand_arg_valid))
                if "$dev_chans" in errormessage:
                    devchans = spicemanip(bot, rpg.gamedict['channels']['devmode_enabled'], 'list')
                    errormessage = str(errormessage.replace("$dev_chans", devchans))
                if "$game_chans" in errormessage:
                    gamechans = spicemanip(bot, rpg.gamedict['channels']['game_enabled'], 'list')
                    errormessage = str(errormessage.replace("$game_chans", gamechans))
                if "$current_chan" in errormessage:
                    if rpg.channel_real:
                        errormessage = str(errormessage.replace("$current_chan", rpg.channel_current))
                    else:
                        errormessage = str(errormessage.replace("$current_chan", 'privmsg'))
                if errormessage not in rpg.error_display:
                    rpg.error_display.append("\x0304,01" + errormessage + "\x03")
    if rpg.error_display != []:
        osd(bot, rpg.instigator, 'notice', rpg.error_display)


"""
Channels
"""


def rpg_command_channels(bot, rpg, trigger):

    # current Channels
    rpg.channel_current = trigger.sender

    # determine the type of channel
    if not rpg.channel_current.startswith("#"):
        rpg.channel_priv = 1
        rpg.channel_real = 0
    else:
        rpg.channel_priv = 0
        rpg.channel_real = 1

    # All channels the bot is in
    if rpg.gamedict["tempvals"]['channels_list'] == []:
        for channel in bot.channels:
            rpg.gamedict["tempvals"]['channels_list'].append(channel)

    # Development mode
    rpg.dev_bypass = 0  # TODO not needed
    if rpg.channel_current.lower() in [x.lower() for x in rpg.gamedict['channels']['devmode_enabled']]:
        rpg.dev_bypass = 1
    return rpg


"""
Users
"""


@event('JOIN')
@rule('.*')
@sopel.module.thread(True)
def rpg_player_return(bot, trigger):

    instigator = trigger.nick

    # RPG dynamic Class
    rpg = class_create('rpg')
    rpg.default = 'rpg'

    # Load Game Players and map
    open_gamedict(bot, rpg)

    # Channel Listing
    rpg = rpg_command_channels(bot, rpg, trigger)

    # Bacic User List
    rpg = rpg_command_users(bot, rpg)

    if instigator not in rpg.gamedict["tempvals"]['current_users']:
        if instigator not in rpg.gamedict['static']['commands'].keys() and instigator not in rpg.gamedict['static']['alt_commands'].keys() and instigator not in rpg.gamedict['tempvals']['bots_list']:
            rpg.gamedict["tempvals"]['current_users'].append(instigator)

    if instigator not in rpg.gamedict["users"]['users_all']:
        rpg.gamedict["users"]['users_all'].append(instigator)

    if instigator in rpg.gamedict["tempvals"]['offline_users']:
        rpg.gamedict["tempvals"]['offline_users'].remove(instigator)


@event('QUIT', 'PART')
@rule('.*')
@sopel.module.thread(True)
def rpg_player_leave(bot, trigger):

    instigator = trigger.nick

    # RPG dynamic Class
    rpg = class_create('rpg')
    rpg.default = 'rpg'

    # Load Game Players and map
    open_gamedict(bot, rpg)

    # Channel Listing
    rpg = rpg_command_channels(bot, rpg, trigger)

    # Bacic User List
    rpg = rpg_command_users(bot, rpg)

    if instigator in rpg.gamedict["tempvals"]['current_users']:
        rpg.gamedict["tempvals"]['current_users'].remove(instigator)

    if instigator not in rpg.gamedict["tempvals"]['offline_users']:
        rpg.gamedict["tempvals"]['offline_users'].append(instigator)


def rpg_command_users(bot, rpg):

    # Userlists that typically don't change when bot is running
    if rpg.gamedict["tempvals"]['bots_list'] == []:
        rpg.gamedict["tempvals"]['bots_list'] = bot_config_names(bot)

    if rpg.gamedict["tempvals"]['bot_owner'] == []:
        for user in bot.config.core.owner:
            if user not in rpg.gamedict["tempvals"]['bot_owner']:
                rpg.gamedict["tempvals"]['bot_owner'].append(user)

    if rpg.gamedict["tempvals"]['bot_admins'] == []:
        for user in bot.config.core.admins:
            if user not in rpg.gamedict["tempvals"]['bot_admins']:
                rpg.gamedict["tempvals"]['bot_admins'].append(user)

    # users that cannot be part of the game
    if rpg.gamedict["tempvals"]['cantplayarray'] == []:
        cantplayarrays = ["rpg.gamedict['static']['commands'].keys()", "rpg.gamedict['static']['alt_commands'].keys()", "rpg.gamedict['tempvals']['bots_list']", "rpg.gamedict['static']['maps'].keys()"]
        for nicklist in cantplayarrays:
            currentnicklist = eval(nicklist)
            for x in currentnicklist:
                if x not in rpg.gamedict["tempvals"]['cantplayarray']:
                    rpg.gamedict["tempvals"]['cantplayarray'].append(x)

    for channelcheck in rpg.gamedict["tempvals"]['channels_list']:
        for user in bot.privileges[channelcheck].keys():
            if user not in rpg.gamedict["tempvals"]['cantplayarray']:

                # Start with Channel permissions
                if bot.privileges[channelcheck][user] == OP:
                    if user not in rpg.gamedict["tempvals"]['chanops']:
                        rpg.gamedict["tempvals"]['chanops'].append(user)

                elif bot.privileges[channelcheck][user] == HALFOP:
                    if user not in rpg.gamedict["tempvals"]['chanhalfops']:
                        rpg.gamedict["tempvals"]['chanhalfops'].append(user)

                elif bot.privileges[channelcheck][user] == VOICE:
                    if user not in rpg.gamedict["tempvals"]['chanvoices']:
                        rpg.gamedict["tempvals"]['chanvoices'].append(user)

                # user lists
                if user not in rpg.gamedict["tempvals"]['current_users']:
                    rpg.gamedict["tempvals"]['current_users'].append(user)

    for user in rpg.gamedict["tempvals"]['current_users']:
        if user not in rpg.gamedict["tempvals"]['cantplayarray']:
            if user not in rpg.gamedict["users"]['users_all']:
                rpg.gamedict["users"]['users_all'].append(user)

    for user in rpg.gamedict["users"]['users_all']:
        if user not in rpg.gamedict["tempvals"]['cantplayarray']:
            if user not in rpg.gamedict["tempvals"]['current_users']:
                if user not in rpg.gamedict["tempvals"]['offline_users']:
                    rpg.gamedict["tempvals"]['offline_users'].append(user)

    return rpg


# Bot Nicks
def bot_config_names(bot):
    config_listing = []
    networkname = str(bot.config.core.user.split("/", 1)[1] + "/")
    validconfigsdir = str("/home/spicebot/.sopel/" + bot.nick + "/System-Files/Configs/" + networkname)
    for filename in os.listdir(validconfigsdir):
        filenameminuscfg = str(filename).replace(".cfg", "")
        config_listing.append(filenameminuscfg)
    return config_listing


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
                if len(textstring) > osd_limit:
                    chunks = textstring.split()
                    for chunk in chunks:
                        if currentstring == '':
                            currentstring = chunk
                        else:
                            tempstring = str(currentstring + " " + chunk)
                            if len(tempstring) <= osd_limit:
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
                elif len(textstring) > osd_limit:
                    if currentstring != '':
                        combinedtextarray.append(currentstring)
                        currentstring = ''
                    combinedtextarray.append(textstring)
                else:
                    tempstring = currentstring + "   " + textstring
                    if len(tempstring) <= osd_limit:
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
RPG Version
"""


def versionnumber(bot, rpg):
    if bot.nick.endswith("dev"):
        githubpage = "https://github.com/SpiceBot/SpiceBot/commits/dev/modulesold/spiceRPG/Game/__init__.py"
    else:
        githubpage = "https://github.com/SpiceBot/SpiceBot/commits/master/modulesold/spiceRPG/Game/__init__.py"
    rpg_version_plainnow = rpg.gamedict["tempvals"]['versionnumber']
    page = requests.get(githubpage, headers=None)
    if page.status_code == 200:
        tree = html.fromstring(page.content)
        rpg_version_plainnow = str(tree.xpath('//*[@id="js-repo-pjax-container"]/div[2]/div[1]/div[2]/div[1]/text()'))
        for r in (("\\n", ""), ("['", ""), ("']", ""), ("'", ""), ('"', ""), (',', ""), ('Commits on', "")):
            rpg_version_plainnow = rpg_version_plainnow.replace(*r)
        rpg_version_plainnow = rpg_version_plainnow.strip()
    return rpg_version_plainnow


"""
Counter
"""


def countX(lst, x):
    count = 0
    for ele in lst:
        if (ele == x):
            count = count + 1
    return count


"""
Array/List/String Manipulation
"""


# Hub
def spicemanip(bot, inputs, outputtask, output_type='default'):

    # TODO 'this*that' or '1*that' replace either all strings matching, or an index value
    # TODO reverse sort z.sort(reverse = True)
    # list.extend adds lists to eachother

    mainoutputtask, suboutputtask = None, None

    # Input needs to be a list, but don't split a word into letters
    if not inputs:
        inputs = []
    if not isinstance(inputs, list):
        inputs = list(inputs.split(" "))
        inputs = [x for x in inputs if x and x not in ['', ' ']]
        inputs = [inputspart.strip() for inputspart in inputs]

    # Create return
    if outputtask == 'create':
        return inputs

    # Make temparray to preserve original order
    temparray = []
    for inputpart in inputs:
        temparray.append(inputpart)
    inputs = temparray

    # Convert outputtask to standard
    if outputtask in [0, 'complete']:
        outputtask = 'string'
    elif outputtask == 'index':
        mainoutputtask = inputs[1]
        suboutputtask = inputs[2]
        inputs = inputs[0]
    elif str(outputtask).isdigit():
        mainoutputtask, outputtask = int(outputtask), 'number'
    elif "^" in str(outputtask):
        mainoutputtask = str(outputtask).split("^", 1)[0]
        suboutputtask = str(outputtask).split("^", 1)[1]
        outputtask = 'rangebetween'
        if int(suboutputtask) < int(mainoutputtask):
            mainoutputtask, suboutputtask = suboutputtask, mainoutputtask
    elif str(outputtask).startswith("split_"):
        mainoutputtask = str(outputtask).replace("split_", "")
        outputtask = 'split'
    elif str(outputtask).endswith(tuple(["!", "+", "-", "<", ">"])):
        mainoutputtask = str(outputtask)
        if str(outputtask).endswith("!"):
            outputtask = 'exclude'
        if str(outputtask).endswith("+"):
            outputtask = 'incrange_plus'
        if str(outputtask).endswith("-"):
            outputtask = 'incrange_minus'
        if str(outputtask).endswith(">"):
            outputtask = 'excrange_plus'
        if str(outputtask).endswith("<"):
            outputtask = 'excrange_minus'
        for r in (("!", ""), ("+", ""), ("-", ""), ("<", ""), (">", "")):
            mainoutputtask = mainoutputtask.replace(*r)

    if outputtask == 'string':
        returnvalue = inputs
    else:
        try:
            returnvalue = eval('spicemanip_' + outputtask + '(bot, inputs, outputtask, mainoutputtask, suboutputtask)')
        except NameError:
            returnvalue = ''

    # default return if not specified
    if output_type == 'default':
        if outputtask in [
                            'string', 'number', 'rangebetween', 'exclude', 'random',
                            'incrange_plus', 'incrange_minus', 'excrange_plus', 'excrange_minus'
                            ]:
            output_type = 'string'
        elif outputtask in ['count']:
            output_type = 'dict'

    # verify output is correct
    if output_type == 'string':
        if isinstance(returnvalue, list):
            returnvalue = ' '.join(returnvalue)
    elif output_type in ['list', 'array']:
        if not isinstance(returnvalue, list):
            returnvalue = list(returnvalue.split(" "))
            returnvalue = [x for x in returnvalue if x and x not in ['', ' ']]
            returnvalue = [inputspart.strip() for inputspart in returnvalue]
    return returnvalue


# compare 2 lists, based on the location of an index item, passthrough needs to be [indexitem, arraytoindex, arraytocompare]
def spicemanip_index(bot, indexitem, outputtask, arraytoindex, arraytocompare):
    item = ''
    for x, y in zip(arraytoindex, arraytocompare):
        if x == indexitem:
            item = y
    return item


# split list by string
def spicemanip_split(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    split_array = []
    restring = ' '.join(inputs)
    if mainoutputtask not in inputs:
        split_array = [restring]
    else:
        split_array = restring.split(mainoutputtask)
    split_array = [x for x in split_array if x and x not in ['', ' ']]
    split_array = [inputspart.strip() for inputspart in split_array]
    if split_array == []:
        split_array = [[]]
    return split_array


# dedupe list
def spicemanip_dedupe(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    newlist = []
    for inputspart in inputs:
        if inputspart not in newlist:
            newlist.append(inputspart)
    return newlist


# Sort list
def spicemanip_sort(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    return sorted(inputs)


# count items in list, return dictionary
def spicemanip_count(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    returndict = dict()
    if inputs == []:
        return returndict
    uniqueinputitems, uniquecount = [], []
    for inputspart in inputs:
        if inputspart not in uniqueinputitems:
            uniqueinputitems.append(inputspart)
    for uniqueinputspart in uniqueinputitems:
        count = 0
        for ele in inputs:
            if (ele == uniqueinputspart):
                count += 1
        uniquecount.append(count)
    for inputsitem, unumber in zip(uniqueinputitems, uniquecount):
        returndict[inputsitem] = unumber
    return returndict


# random item from list
def spicemanip_random(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    randomselectlist = []
    for temppart in inputs:
        randomselectlist.append(temppart)
    while len(randomselectlist) > 1:
        random.shuffle(randomselectlist)
        randomselect = randomselectlist[random.randint(0, len(randomselectlist) - 1)]
        randomselectlist.remove(randomselect)
    randomselect = randomselectlist[0]
    return randomselect


# remove random item from list
def spicemanip_exrandom(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return []
    randremove = spicemanip_random(bot, inputs, outputtask, mainoutputtask, suboutputtask)
    inputs.remove(randremove)
    return inputs


# Convert list into lowercase
def spicemanip_lower(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return [inputspart.lower() for inputspart in inputs]


# Convert list to uppercase
def spicemanip_upper(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return [inputspart.upper() for inputspart in inputs]


# Convert list to uppercase
def spicemanip_title(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return [inputspart.title() for inputspart in inputs]


# Reverse List Order
def spicemanip_reverse(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return []
    return inputs[::-1]


# comma seperated list
def spicemanip_list(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return ', '.join(str(x) for x in inputs)


# comma seperated list with and
def spicemanip_andlist(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    if len(inputs) < 2:
        return ' '.join(inputs)
    lastentry = str("and " + str(inputs[len(inputs) - 1]))
    del inputs[-1]
    inputs.append(lastentry)
    if len(inputs) == 2:
        return ' '.join(inputs)
    return ', '.join(str(x) for x in inputs)


# comma seperated list with or
def spicemanip_orlist(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    if len(inputs) < 2:
        return ' '.join(inputs)
    lastentry = str("or " + str(inputs[len(inputs) - 1]))
    del inputs[-1]
    inputs.append(lastentry)
    if len(inputs) == 2:
        return ' '.join(inputs)
    return ', '.join(str(x) for x in inputs)


# exclude number
def spicemanip_exclude(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    del inputs[int(mainoutputtask) - 1]
    return ' '.join(inputs)


# Convert list to string
def spicemanip_string(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return ' '.join(inputs)


# Get number item from list
def spicemanip_number(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    elif len(inputs) == 1:
        return inputs[0]
    elif int(mainoutputtask) > len(inputs) or int(mainoutputtask) < 0:
        return ''
    else:
        return inputs[int(mainoutputtask) - 1]


# Get Last item from list
def spicemanip_last(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return inputs[len(inputs) - 1]


# range between items in list
def spicemanip_rangebetween(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    if not str(mainoutputtask).isdigit() or not str(suboutputtask).isdigit():
        return ''
    mainoutputtask, suboutputtask = int(mainoutputtask), int(suboutputtask)
    if suboutputtask == mainoutputtask:
        return spicemanip_number(bot, inputs, outputtask, mainoutputtask, suboutputtask)
    if suboutputtask < mainoutputtask:
        return []
    if mainoutputtask < 0:
        mainoutputtask = 1
    if suboutputtask > len(inputs):
        suboutputtask = len(inputs)
    newlist = []
    for i in range(mainoutputtask, suboutputtask + 1):
        newlist.append(str(spicemanip_number(bot, inputs, outputtask, i, suboutputtask)))
    if newlist == []:
        return ''
    return ' '.join(newlist)


# Forward Range includes index number
def spicemanip_incrange_plus(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return spicemanip_rangebetween(bot, inputs, outputtask, int(mainoutputtask), len(inputs))


# Reverse Range includes index number
def spicemanip_incrange_minus(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return spicemanip_rangebetween(bot, inputs, outputtask, 1, int(mainoutputtask))


# Forward Range excludes index number
def spicemanip_excrange_plus(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return spicemanip_rangebetween(bot, inputs, outputtask, int(mainoutputtask) + 1, len(inputs))


# Reverse Range excludes index number
def spicemanip_excrange_minus(bot, inputs, outputtask, mainoutputtask, suboutputtask):
    if inputs == []:
        return ''
    return spicemanip_rangebetween(bot, inputs, outputtask, 1, int(mainoutputtask) - 1)


def array_arrangesort(bot, sortbyarray, arrayb):
    sortbyarray, arrayb = (list(x) for x in zip(*sorted(zip(sortbyarray, arrayb), key=itemgetter(0))))
    return sortbyarray, arrayb


"""
Database
"""


# Get a value
def get_database_value(bot, nick, databasekey):
    databasecolumn = str('rpg_' + databasekey)
    database_value = bot.db.get_nick_value(nick, databasecolumn) or 0
    return database_value


# set a value
def set_database_value(bot, nick, databasekey, value):
    databasecolumn = str('rpg_' + databasekey)
    bot.db.set_nick_value(nick, databasecolumn, value)


# set a value to None
def reset_database_value(bot, nick, databasekey):
    databasecolumn = str('rpg_' + databasekey)
    bot.db.set_nick_value(nick, databasecolumn, None)


# add or subtract from current value
def adjust_database_value(bot, nick, databasekey, value):
    oldvalue = get_database_value(bot, nick, databasekey) or 0
    databasecolumn = str('rpg_' + databasekey)
    bot.db.set_nick_value(nick, databasecolumn, float(oldvalue) + float(value))


# array stored in database length
def get_database_array_total(bot, nick, databasekey):
    array = get_database_value(bot, nick, databasekey) or []
    entriestotal = len(array)
    return entriestotal


# array stored in database, add or remove elements
def adjust_database_array(bot, nick, entries, databasekey, adjustmentdirection):
    if not isinstance(entries, list):
        entries = [entries]
    adjustarray = get_database_value(bot, nick, databasekey) or []
    adjustarraynew = []
    for x in adjustarray:
        adjustarraynew.append(x)
    reset_database_value(bot, nick, databasekey)
    adjustarray = []
    if adjustmentdirection == 'add':
        for y in entries:
            if y not in adjustarraynew:
                adjustarraynew.append(y)
    elif adjustmentdirection == 'del':
        for y in entries:
            if y in adjustarraynew:
                adjustarraynew.remove(y)
    for x in adjustarraynew:
        if x not in adjustarray:
            adjustarray.append(x)
    if adjustarray == []:
        reset_database_value(bot, nick, databasekey)
    else:
        set_database_value(bot, nick, databasekey, adjustarray)


"""
User Dictionaries
"""


# Database Users
def get_user_dict(bot, rpg, nick, dictkey):

    # check that db list is there
    if not hasattr(rpg, 'userdb'):
        rpg.userdb = class_create('userdblist')
    if not hasattr(rpg.userdb, 'list'):
        rpg.userdb.list = []

    returnvalue = 0

    # check if nick has been pulled from db already
    if nick not in rpg.userdb.list:
        rpg.userdb.list.append(nick)
        nickdict = get_database_value(bot, nick, rpg.default) or dict()
        createuserdict = str("rpg.userdb." + nick + " = nickdict")
        exec(createuserdict)
    else:
        if not hasattr(rpg.userdb, nick):
            nickdict = dict()
        else:
            nickdict = eval('rpg.userdb.' + nick)

    if dictkey in nickdict.keys():
        returnvalue = nickdict[dictkey]
    else:
        nickdict[dictkey] = 0
        returnvalue = 0

    return returnvalue


# set a value
def set_user_dict(bot, rpg, nick, dictkey, value):
    currentvalue = get_user_dict(bot, rpg, nick, dictkey)
    nickdict = eval('rpg.userdb.' + nick)
    nickdict[dictkey] = value


# reset a value
def reset_user_dict(bot, rpg, nick, dictkey):
    currentvalue = get_user_dict(bot, rpg, nick, dictkey)
    nickdict = eval('rpg.userdb.' + nick)
    if dictkey in nickdict:
        del nickdict[dictkey]


# add or subtract from current value
def adjust_user_dict(bot, rpg, nick, dictkey, value):
    oldvalue = get_user_dict(bot, rpg, nick, dictkey)
    if not str(oldvalue).isdigit():
        oldvalue = 0
    nickdict = eval('rpg.userdb.' + nick)
    nickdict[dictkey] = oldvalue + value


# Save all database users in list
def save_user_dicts(bot, rpg):

    # check that db list is there
    if not hasattr(rpg, 'userdb'):
        rpg.userdb = class_create('userdblist')
    if not hasattr(rpg.userdb, 'list'):
        rpg.userdb.list = []

    for nick in rpg.userdb.list:
        if not hasattr(rpg.userdb, nick):
            nickdict = dict()
        else:
            nickdict = eval('rpg.userdb.' + nick)
        set_database_value(bot, nick, rpg.default, nickdict)


# add or subtract from current value
def adjust_user_dict_array(bot, rpg, nick, dictkey, entries, adjustmentdirection):
    if not isinstance(entries, list):
        entries = [entries]
    oldvalue = get_user_dict(bot, rpg, nick, dictkey)
    nickdict = eval('rpg.userdb.' + nick)
    if not isinstance(oldvalue, list):
        oldvalue = []
    for x in entries:
        if adjustmentdirection == 'add':
            if x not in oldvalue:
                oldvalue.append(x)
        elif adjustmentdirection == 'del':
            if x in oldvalue:
                oldvalue.remove(x)
    nickdict[dictkey] = oldvalue


"""
Game Dictionary
"""


def open_gamedict(bot, rpg):

    # open global dict as part of rpg class
    global rpg_game_dict
    rpg.gamedict = rpg_game_dict

    # don't pull from database if already open
    if not rpg.gamedict["tempvals"]["game_loaded"]:
        opendict = rpg_game_dict.copy()
        dbgamedict = get_database_value(bot, 'rpg_game_records', 'rpg_game_dict') or dict()
        opendict = merge_gamedict(opendict, dbgamedict)
        rpg.gamedict.update(opendict)
        rpg.gamedict["tempvals"]['game_loaded'] = True


def save_gamedict(bot, rpg):

    # copy dict to not overwrite
    savedict = rpg.gamedict.copy()

    # Values to not save to database
    savedict_del = ['tempvals', 'static']
    for dontsave in savedict_del:
        if dontsave in savedict.keys():
            del savedict[dontsave]

    # save to database
    set_database_value(bot, 'rpg_game_records', 'rpg_game_dict', savedict)


def merge_gamedict(a, b, path=None):
    "merges b into a"
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_gamedict(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a


"""
Dynamic Classes
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
