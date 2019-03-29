#!/usr/bin/env python
# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

# sopel imports
import sopel.module
from sopel.module import commands, nickname_commands, rule, priority, example, OP, ADMIN, VOICE, event, rule
import sopel
from sopel import module, tools

# Additional
import random
from random import randint
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
reload(sys)
sys.setdefaultencoding('utf-8')

import spicemanip


# Global Vars
moduledir = os.path.dirname(__file__)
sys.path.append(moduledir)
from Duels_Vars import *


"""
Main Command Usage
"""


# work with /me ACTION (does not work with manual weapon)
@module.rule('^(?:challenges|(?:fi(?:ght|te)|duel)s(?:\s+with)?)\s+([a-zA-Z0-9\[\]\\`_\^\{\|\}-]{1,32}).*')
@module.intent('ACTION')
@sopel.module.thread(True)
def duel_action(bot, trigger):
    command_type = 'actionduel'
    triggerargsarray = spicemanip.main(trigger.group(1), 'create')
    execute_main(bot, trigger, triggerargsarray, command_type)


# bot.nick do this
@nickname_commands('duel', 'challenge', 'duels', 'challenges')
@sopel.module.thread(True)
def duel_nickcom(bot, trigger):
    command_type = 'botnick'
    osd(bot, trigger.sender, 'say', "Don't tell me what to do!")
    # TODO maybe add the non-combat functions here?


# Base command
@sopel.module.commands('duel', 'challenge', 'duels', 'challenges')
@sopel.module.thread(True)
def mainfunction(bot, trigger):
    command_type = 'normalcom'
    triggerargsarray = spicemanip.main(trigger.group(2), 'create')
    execute_main(bot, trigger, triggerargsarray, command_type)


# respond to alternate start for command
@module.rule('^(?:duel)\s+?.*')
@module.rule('^(?:!duel)\s+?.*')
@module.rule('^(?:,duel)\s+?.*')
@module.rule('^(?:duels)\s+?.*')
@module.rule('^(?:!duels)\s+?.*')
@module.rule('^(?:,duels)\s+?.*')
@module.rule('^(?:challenge)\s+?.*')
@module.rule('^(?:!challenge)\s+?.*')
@module.rule('^(?:,challenge)\s+?.*')
@module.rule('^(?:challenges)\s+?.*')
@module.rule('^(?:!challenges)\s+?.*')
@module.rule('^(?:,challenges)\s+?.*')
@sopel.module.thread(True)
def mainfunctionnobeguine(bot, trigger):
    command_type = 'normalcom'
    triggerargsarray = spicemanip.main(trigger.group(0), 'create')
    triggerargsarray = spicemanip.main(triggerargsarray, '2+')
    triggerargsarray = spicemanip.main(triggerargsarray, 'create')
    execute_main(bot, trigger, triggerargsarray, command_type)


# rule for "use"
@module.rule('^(?:use)\s+?.*')
def mainfunctionuse(bot, trigger):
    command_type = 'normalcom'
    triggerargsarray = spicemanip.main(trigger.group(0), 'create')
    triggerargsarray = spicemanip.main(triggerargsarray, '2+')
    triggerargsarray = spicemanip.main(triggerargsarray, 'create')
    lootitem = spicemanip.main(triggerargsarray, 1)
    if lootitem in duels_loot_items:
        restoftheline = spicemanip.main(triggerargsarray, "2+")
        triggerargsarray = str("loot use " + lootitem + " " + restoftheline)
        triggerargsarray = spicemanip.main(triggerargsarray, 'create')
        execute_main(bot, trigger, triggerargsarray, command_type)


"""

starting map is 100x100

everytime a map is completely explored a new map begins, bigger than the last

different types of areas

location of town is randomized

those caught fighting in town are put in jail

class race benefits for each major location


"""

"""
monster mutates,,, enraged itsy bitsy
"""

"""
#
# Seperate Targets from Commands #
#
"""


# Check the Instigator, Build basic variables, and divide Multi-commands, Chance of deathblow at end
def execute_main(bot, trigger, triggerargsarray, command_type):

    # duels dynamic Class
    duels = class_create('main')

    # All Channels
    duels = duels_channel_lists(bot, trigger, duels)

    # Instigator variable to describe the nickname that initiated the command
    duels.instigator = trigger.nick

    # Type of command
    duels.command_type = command_type

    # First Command
    command_full = spicemanip.main(triggerargsarray, 0)
    if not command_full:
        if duels.command_type != 'actionduel':
            osd(bot, duels.instigator, 'notice', "You must specify either a target, or a subcommand. Online Docs: " + GITWIKIURL)
        else:
            osd(bot, duels.instigator, 'notice', "You must specify a target. Online Docs: " + GITWIKIURL)
        return
    if duels.command_type == 'actionduel':
        if "&&" in command_full:
            osd(bot, duels.instigator, 'notice', "you cannot run multiple commands via action.")
            return
    command_main = spicemanip.main(triggerargsarray, 1)

    # Time when Module use started
    duels.now = time.time()

    # Valid Commands and stats
    duels.commands_valid = duels_valid_commands(bot)
    duels.commands_alt = duels_valid_commands_alternative(bot)
    duels.stats_valid = duels_valid_stats(bot)

    # Verify Game enabled in current channel
    if duels.duels_enabled_channels == []:
        if not trigger.admin:
            osd(bot, duels.instigator, 'notice', "Duels has not been enabled in any bot channels. Talk to a bot admin.")
            return
    if duels.channel_current not in duels.duels_enabled_channels and duels.inchannel:
        if not trigger.admin:
            osd(bot, duels.instigator, 'notice', "Duels has not been enabled in " + duels.channel_current + ". Talk to a bot admin.")
            return

    # Build User list
    duels.admin = 0
    duels = duels_user_lists(bot, duels)

    # Check that their character has all valid basic setup components
    opening_monologue = []
    for char_basic in duels_character_basics:
        char_basic_check = get_database_value(bot, duels.instigator, char_basic)
        char_basic_valid = eval('duels_character_valid_'+char_basic)
        if not char_basic_check or char_basic_check not in char_basic_valid:
            opening_monologue.append(char_basic)
    if opening_monologue != []:
        duels_opening_monologue(bot, duels, duels.instigator, opening_monologue, 1, duels_character_basics_empty)

    # Tiers
    duels.currenttier = get_database_value(bot, 'duelrecorduser', 'tier') or 0
    duels.tierscaling = duels_tier_current_to_ratio(bot)

    # Validate Instigator
    duels_check_nick_condition(bot, duels.instigator, duels)
    instigatorbio = duel_target_playerbio(bot, duels, duels.instigator)
    duels.optcheck = 1
    duels_check_instigator_pass = duels_check_instigator(bot, trigger, command_main, duels, instigatorbio)
    if not duels_check_instigator_pass:
        return

    # IF "&&" is in the full input, it is treated as multiple commands, and is split
    commands_array = spicemanip.main(triggerargsarray, "split_&&")

    for command_split_partial in commands_array:
        triggerargsarray_part = spicemanip.main(command_split_partial, 'create')

        # Admin only
        duels.admin = 0
        if [x for x in triggerargsarray_part if x == "-a"]:
            duels.admin = 1
            triggerargsarray_part.remove("-a")
            # Block non-admin usage of the admin switch
            if not trigger.admin:
                osd(bot, duels.channel_current, 'say', "The Admin Switch is meant for Bot Admin use only.")
                continue

        # Split commands to pass
        command_full_part = spicemanip.main(triggerargsarray_part, 0)
        command_main_part = spicemanip.main(triggerargsarray_part, 1)

        # allow players to set custom shortcuts to numbers
        if command_main_part.isdigit():
            number_command = get_database_value(bot, duels.instigator, 'hotkey_'+str(command_main_part)) or 0
            if not number_command:
                osd(bot, duels.instigator, 'notice', "You don't have a command hotlinked to "+str(command_main_part)+".")
                continue
            else:
                number_command_list = get_database_value(bot, duels.instigator, 'hotkey_complete') or []
                if command_main_part not in number_command_list:
                    adjust_database_array(bot, duels.instigator, [command_main_part], 'hotkey_complete', 'add')
                commandremaining = spicemanip.main(triggerargsarray_part, '2+') or ''
                number_command = str(number_command + " " + commandremaining)
                triggerargsarray_part = spicemanip.main(number_command, 'create')
                command_full_part = spicemanip.main(triggerargsarray_part, 0)
                command_main_part = spicemanip.main(triggerargsarray_part, 1)

        # Run command process
        command_main_process(bot, trigger, triggerargsarray_part, command_full_part, command_main_part, duels, instigatorbio)

    # Deathblow
    deathblowpeoplearray = get_database_value(bot, 'duelrecorduser', 'deathblowmessagepeoplearray') or []
    if deathblowpeoplearray != []:
        for inflicter in deathblowpeoplearray:
            inflicterdeathblowpeoplearray = get_database_value(bot, inflicter, 'deathblowtargetsnew') or []
            if inflicterdeathblowpeoplearray != []:
                deathblowlist = spicemanip.main(inflicterdeathblowpeoplearray, "list")
                deathblowmsg = str(inflicter + " has a chance of striking a deathblow on " + deathblowlist + "! FINISH THEM!!!!")
                osd(bot, duels.channel_current, 'say', deathblowmsg)
                reset_database_value(bot, inflicter, 'deathblowtargetsnew')
            for inflictee in inflicterdeathblowpeoplearray:
                deathblownow = time.time()
                set_database_value(bot, inflictee, 'deathblowtargettime', deathblownow)
        reset_database_value(bot, 'duelrecorduser', 'deathblowmessagepeoplearray')

    # bot does not need stats or backpack items
    duels_refresh_bot(bot, duels)

    # Instigator last used
    set_database_value(bot, duels.instigator, 'lastcommand', duels.now)

    # Usage Counter
    adjust_database_value(bot, duels.instigator, 'usage_total', 1)
    adjust_database_value(bot, 'duelrecorduser', 'usage_total', 1)

    # reset the game
    currenttier = get_database_value(bot, 'duelrecorduser', 'tier') or 0
    if currenttier >= 15:
        osd(bot, duels.duels_enabled_channels, 'say', "Somebody has Triggered the Endgame! Stats will be reset.")
        duels_endgame(bot, duels)  # TODO


# Seperate Targets from Commands. Handle Misspellings of commands, and translate alternate commands
def command_main_process(bot, trigger, triggerargsarray, command_full, command_main, duels, instigatorbio):

    # Cheap error handling for people that like to find issues
    if command_main == 'invalidcommand':
        osd(bot, duels.instigator, 'notice', "AltCom finder broke.")
        return

    # channel_current Block
    if command_main.lower() in duels_commands_inchannel and not duels.inchannel and not duels.admin:
        osd(bot, duels.instigator, 'notice', "Duel " + command_main + " must be in channel.")
        return

    # Instigator versus Bot
    if command_main.lower() == bot.nick.lower() and not duels.admin:
        osd(bot, duels.channel_current, 'say', "I refuse to fight a biological entity! If I did, you'd be sure to lose!")
        return

    # Instigator versus Instigator
    if command_main.lower() == duels.instigator.lower() and not duels.admin:
        osd(bot, duels.channel_current, 'say', "If you are feeling self-destructive, there are places you can call. Alternatively, you can run the harakiri command.")
        return

    # Admin Command Blocker
    if command_main.lower() in duels_commands_admin and not duels.admin:
        osd(bot, duels.instigator, 'notice', "This admin function is only available to bot admins.")
        return

    # Cheat
    if command_main.lower() == 'upupdowndownleftrightleftrightba':
        duels_command_function_konami(bot, duels)
        return

    # Subcommand Versus Target
    if command_main.lower() in duels.commands_valid:
        # If command was issued as an action
        if duels.command_type != 'actionduel' or command_main.lower() in duels_action_subcommands:
            subcommands(bot, trigger, triggerargsarray, command_full, command_main, duels, instigatorbio)
        else:
            osd(bot, duels.instigator, 'notice', "Action duels should not be able to run commands. Targets Only")
        return

    # Alternative Commands
    if command_main.lower() in duels.commands_alt:
        command_main = duels_valid_commands_alternative_find_match(bot, command_main)
        command_main_process(bot, trigger, triggerargsarray, command_full, command_main, duels, instigatorbio)
        return

    # Spell Check for non-nicks
    if command_main not in duels.users_all_allchan:
        duels_command_spelling_check_main(bot, trigger, triggerargsarray, command_full, command_main, duels, instigatorbio)
        return

    """ Anything Else is a Target For Dueling """

    # Rebuild user input
    command_full = spicemanip.main(command_full, 0)
    command_full = str("combat " + command_full)
    command_main = spicemanip.main(command_full, 1)
    triggerargsarray = spicemanip.main(command_full, 'create')

    # Cycle back through with the subcommand "combat" as it will run various usage counters and such
    command_main_process(bot, trigger, triggerargsarray, command_full, command_main, duels, instigatorbio)


# process commands, and run
def subcommands(bot, trigger, triggerargsarray, command_full, command_main, duels, instigatorbio):

    command_restructure = spicemanip.main(triggerargsarray, '2+')
    duels.command_restructure = spicemanip.main(command_restructure, 'create')
    docscheck = spicemanip.main(duels.command_restructure, 1)
    if docscheck == 'docs' or docscheck in duels_commands_alternate_docs:
        endmessage = duels_docs_commands(bot, command_main)
        osd(bot, duels.channel_current, 'say', endmessage)
        return

    # Is the Tier Unlocked?
    duels.tiercommandeval = duels_tier_command_to_number(bot, command_main)
    duels.tierpepperrequired = duels_tier_number_to_pepper(bot, duels.tiercommandeval)
    if duels.tiercommandeval > 0 and command_main.lower() not in duels_commands_self:
        tierpass = 0
        duels.tiermath = int(duels.tiercommandeval) - int(duels.currenttier)
        if duels.tiermath > 0:
            if duels.channel_current in duels.duels_dev_channels or duels.admin:
                tierpass = 1
            elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
                tierpass = 1
        else:
            tierpass = 1
        if not tierpass:
            osd(bot, duels.channel_current, 'say', "Duel " + command_main.lower() + " will be unlocked when somebody reaches " + str(duels.tierpepperrequired) + ". " + str(duels.tiermath) + " tier(s) remaining!")
            return

    # Rebuild again
    duels = duels_user_lists(bot, duels)

    # Stamina Check
    staminapass, stamina, duels.command_stamina_cost = duels_stamina_check(bot, duels.instigator, command_main.lower(), duels)
    if not staminapass and command_main.lower() != 'location':
        osd(bot, duels.instigator, 'notice', "You do not have enough stamina to perform duel " + command_main.lower())
        return

    # Location Based Commands
    valid_location_commands = duels_location_valid_commands(bot, duels, duels.instigator)
    if command_main.lower() not in valid_location_commands:
        command_location = duels_location_search(bot, duels, command_main.lower())
        staminarequiredtomove = spicemanip.main(['location', duels_commands_stamina_required, duels_commands_stamina_cost], 'index')
        combinedstamina = int(duels.command_stamina_cost) + int(staminarequiredtomove)
        if int(combinedstamina) > int(stamina) and not duels.admin and duels.channel_current not in duels.duels_dev_channels:
            osd(bot, duels.instigator, 'notice', "You do not have enough stamina to move from the "+instigatorbio.location+" area to the "+command_location+" area AND perform this action.")
            return
        osd(bot, duels.instigator, 'notice', "You have been moved from the " + instigatorbio.location + " area to the " + command_location + " area at an extra cost of "+str(staminarequiredtomove)+" stamina.")
        duels_stamina_charge(bot, duels.instigator, 'location')
        duels_location_move(bot, duels, duels.instigator, command_location)
        instigatorbio.location = duels_get_location(bot, duels, duels.instigator)
        # Rebuild again
        duels = duels_user_lists(bot, duels)

    # users_current_arena Check for certain commands
    if command_main.lower() in duels_commands_canduel_generate:
        if duels.instigator not in duels.users_canduel_allchan:
            canduel, validtargetmsg = duels_criteria(bot, duels.instigator, duels, 1)
            return

    # Check bot is not a player for certain commands
    if command_main.lower() in duels_commands_canduel_remove_bot:
        if bot.nick in duels.users_canduel_allchan:
            duels.users_canduel_allchan.remove(bot.nick)

    # Events Check
    if command_main.lower() in duels_commands_events:
        executedueling, executeduelingmsg = duels_events_check(bot, command_main, duels)
        if not executedueling:
            osd(bot, duels.instigator, 'notice', executeduelingmsg)
            return
        for player in duels.users_canduel_allchan:
            if player != duels.instigator:
                duels_check_nick_condition(bot, player, duels)

    # If the above passes all above checks
    duels_command_function_run = str('duels_command_function_' + command_main.lower() + '(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio)')
    eval(duels_command_function_run)
    # Don't allow event repetition
    if command_main.lower() in duels_commands_events:
        set_database_value(bot, 'duelrecorduser', str('lastfullroom' + command_main.lower()), duels.now)
        set_database_value(bot, 'duelrecorduser', str('lastfullroom' + command_main.lower() + 'instigator'), duels.instigator)

    # Special Event
    if not duels.inchannel and command_main.lower() in duels_commands_special_events:
        speceventtext = ''
        speceventtotal = get_database_value(bot, 'duelrecorduser', 'specevent') or 0
        if speceventtotal >= 49:
            set_database_value(bot, 'duelrecorduser', 'specevent', 1)
            osd(bot, duels.channel_current, 'say', duels.instigator + " triggered the special event! Winnings are "+str(spicemanip.main(['specialevent', duels_ingame_coin_usage, duels_ingame_coin], 'index'))+" Coins!")
            adjust_database_value(bot, duels.instigator, 'coin', spicemanip.main(['specialevent', duels_ingame_coin_usage, duels_ingame_coin], 'index'))
        else:
            adjust_database_value(bot, 'duelrecorduser', 'specevent', 1)

    # Stamina charge
    if duels.command_stamina_cost:
        duels_stamina_charge(bot, duels.instigator, command_main.lower())

    # usage counter
    adjust_database_value(bot, duels.instigator, 'usage_total', 1)
    adjust_database_value(bot, duels.instigator, 'usage_'+command_main.lower(), 1)
    adjust_database_value(bot, 'duelrecorduser', 'usage_total', 1)
    adjust_database_value(bot, 'duelrecorduser', 'usage_'+command_main.lower(), 1)


"""
#
# Combat Commands and Events #
#
"""


""" Combat Shared Function """


def duel_combat(bot, maindueler, targetarray, triggerargsarray, typeofduel, duels):

    # Same person can't instigate twice in a row
    set_database_value(bot, 'duelrecorduser', 'lastinstigator', maindueler)

    # Starting Tier
    currenttierstart = get_database_value(bot, 'duelrecorduser', 'tier') or 0
    tierunlockweaponslocker = duels_tier_command_to_number(bot, 'weaponslocker_complete')

    # Manual Weapon Usage
    manualweapon = ''
    if typeofduel == 'target':
        if currenttierstart >= tierunlockweaponslocker:
            manualweapon = find_switch_equal(bot, triggerargsarray, "w")

    # Targetarray Start
    targetarraytotal = len(targetarray)
    for target in targetarray:

        # Events does not touch lastfought
        if typeofduel in duels_commands_events:
            targetlastfoughtstart = get_database_value(bot, target, 'lastfought')

        # Current Competitors
        competitors = [maindueler, target]

        # Cleanup from Previous runs
        combattextarraycomplete = []

        # Player Bios
        playerbio_maindueler, playerbio_target = duel_combat_playerbios(bot, maindueler, target, typeofduel, duels)

        # Announce Combat
        if typeofduel in duels_commands_events:
            osd(bot, [maindueler, target], 'priv', "  ")
        if typeofduel in duels_commands_events:
            osd(bot, [maindueler, target], 'priv', playerbio_maindueler.announce + " \x02VERSUS\x02 " + playerbio_target.announce)
        else:
            osd(bot, duels.channel_current, 'say', playerbio_maindueler.announce + " \x02VERSUS\x02 " + playerbio_target.announce)
        if playerbio_maindueler.actual == playerbio_target.actual:
            osd(bot, duels.channel_current, 'say', "Why are you hitting yourself?")

        # Chance of maindueler finding loot
        randominventoryfind = 0
        if playerbio_target.actual != bot.nick and playerbio_maindueler.actual != playerbio_target.actual and playerbio_maindueler.actual != 'duelsmonster':
            if playerbio_maindueler.luck * 10 > 100:
                randomfindchance = randint(90, 100)
            else:
                randomfindchance = randint(playerbio_maindueler.luck * 10, 100)
            if randomfindchance >= 90:
                randominventoryfind = 1
            if randominventoryfind:
                if randomfindchance >= 100:
                    howluckyarethey = ' very luckily'
                    loot = spicemanip.main(duels_loot_winnable_plus, 'random')
                elif randomfindchance <= 95:
                    howluckyarethey = ''
                    loot = spicemanip.main(duels_loot_winnable_lower, 'random')
                else:
                    howluckyarethey = ' luckily'
                    loot = spicemanip.main(duels_loot_winnable_norm, 'random')
                aoran = 'a'
                if loot.lower().startswith(('a', 'e', 'i', 'o', 'u')):
                    aoran = 'an'
                combattextarraycomplete.append(playerbio_maindueler.nametext + howluckyarethey + " found " + str(aoran) + " " + str(loot) + "!")
                adjust_database_value(bot, 'duelsmerchant', str("vendor_track_value_"+loot), -1)

        # Winner Selection
        winner = duels_combat_selectwinner(bot, competitors, duels, playerbio_maindueler, playerbio_target)
        loser = spicemanip.main([x for x in competitors if x != winner], 1) or winner

        # rebase the player bios
        if winner == playerbio_maindueler.actual:
            playerbio_winner = playerbio_maindueler
            playerbio_loser = playerbio_target
        else:
            playerbio_winner = playerbio_target
            playerbio_loser = playerbio_maindueler

        # Body Part Hit
        bodypart, bodypartname = duels_bodypart_select(bot, loser)

        # Weapon
        if playerbio_winner.actual == playerbio_maindueler.actual and manualweapon:
            if manualweapon == 'all':
                weapon = duels_weaponslocker_channel(bot)
            elif manualweapon == 'target':
                weapon = duels_weaponslocker_nick_selection(bot, playerbio_target.actual)
                weapon = str(playerbio_target.nametext + "'s " + weapon)
            else:
                weapon = manualweapon
        elif playerbio_winner.actual == bot.nick or playerbio_winner.actual == 'duelsmonster':
            weapon = ''
        else:
            weapon = duels_weaponslocker_nick_selection(bot, playerbio_winner.actual)
        # Format Weapon Name
        weapon = duels_weapons_formatter(bot, weapon)
        if weapon != '':
            weapon = str(" " + weapon)

        # Display main attack
        if playerbio_winner.actual != playerbio_loser.actual:
            striketype = spicemanip.main(duel_hit_types, 'random')
            combattextarraycomplete.append(playerbio_winner.nametext + " attempts to " + striketype + " " + playerbio_loser.nametextb + " " + weapon)
        else:
            striketype = spicemanip.main(duel_hit_types_s, 'random')
            combattextarraycomplete.append(playerbio_winner.nametext + " " + striketype + " " + playerbio_loser.nametextb + " " + weapon)

        # Damage
        if typeofduel == 'colosseum':
            damage = get_database_value(bot, 'duelrecorduser', 'colosseum_damage')
        else:
            damage = duels_combat_damage(bot, duels, playerbio_winner, playerbio_loser)

        # Deflect, Paladins more often
        if damage > 0 and playerbio_winner.actual != playerbio_loser.actual and not playerbio_loser.curse:
            if playerbio_winner.perception * 10 > 100:
                deflectodds = 100
            else:
                deflectodds = randint(playerbio_winner.perception * 10, 100)
            if deflectodds >= 95:
                combattextarraycomplete.append(playerbio_loser.nametext + " deflects the attack")
                # rebase the player bios
                winner, loser = loser, winner
                if winner == playerbio_maindueler.actual:
                    playerbio_winner = playerbio_maindueler
                    playerbio_loser = playerbio_target
                else:
                    playerbio_winner = playerbio_target
                    playerbio_loser = playerbio_maindueler
                # new weapon
                if playerbio_winner.actual == bot.nick or playerbio_winner.actual == 'duelsmonster':
                    weapon = ''
                else:
                    weapon = duels_weaponslocker_nick_selection(bot, playerbio_winner.actual)
                weapon = duels_weapons_formatter(bot, weapon)
                if weapon != '':
                    weapon = str(" " + weapon)
                combattextarraycomplete.append(playerbio_winner.nametext + " attempts to " + striketype + " " + playerbio_loser.nametext + " " + weapon)
                # Damage
                if typeofduel != 'colosseum':
                    damage = duels_combat_damage(bot, duels, playerbio_winner, playerbio_loser)

        # Druid animal shape
        if playerbio_loser.Class == 'druid' and playerbio_winner.actual != playerbio_loser.actual and not playerbio_loser.curse:
            if playerbio_loser.agility * 10 > 100:
                transformodds = 100
            else:
                transformodds = randint(playerbio_loser.agility * 10, 100)
            if transformodds >= 80:
                currentanimals = duels_druid_current_array(bot, playerbio_loser.actual)
                currentanimal = spicemanip.main(currentanimals, 'random')
                aoran = 'a'
                if currentanimal.lower().startswith(('a', 'e', 'i', 'o', 'u')):
                    aoran = 'an'
                combattextarraycomplete.append(playerbio_loser.nametext + " transforms and attacks " + playerbio_winner.nametext + " like " + str(aoran) + " " + str(currentanimal))
                winner, loser = loser, winner
                # rebase the player bios
                if winner == playerbio_maindueler.actual:
                    playerbio_winner = playerbio_maindueler
                    playerbio_loser = playerbio_target
                else:
                    playerbio_winner = playerbio_target
                    playerbio_loser = playerbio_maindueler

        # Berserker Rage
        if playerbio_winner.race == 'barbarian' and playerbio_winner.actual != playerbio_loser.actual:
            anticharisma = 10 - playerbio_winner.charisma
            if anticharisma <= 0:
                rageodds = 100
            else:
                rageodds = randint(anticharisma * 10, 100)
            if rageodds >= 80:
                extradamage = playerbio_winner.strength * 10
                extradamage = extradamage * duels.tierscaling
                combattextarraycomplete.append(playerbio_winner.nametext + " goes into Berserker Rage for an extra " + str(extradamage) + " damage.")
                damage = damage + extradamage

        # Vampires gain health from wins
        if playerbio_winner.race == 'vampire' and playerbio_winner.actual != playerbio_loser.actual:
            combattextarraycomplete.append(playerbio_winner.nametext + " siphons the energy of the attack into self health")
            damageinflictarray = duels_effect_inflict(bot, duels,  playerbio_loser, playerbio_winner, bodypart, 'healing', -abs(damage), typeofduel)
            for k in damageinflictarray:
                combattextarraycomplete.append(k)

        if damage > 0:
            damageinflictarray = duels_effect_inflict(bot, duels, playerbio_winner, playerbio_loser, bodypart, 'damage', damage, typeofduel)
            for k in damageinflictarray:
                combattextarraycomplete.append(k)

        # Chance that maindueler loses found loot
        lootwinner = playerbio_winner.actual
        if randominventoryfind:
            if playerbio_winner.actual == playerbio_target.actual:
                combattextarraycomplete.append(playerbio_winner.nametext + " gains the " + str(loot))
            adjust_database_value(bot, lootwinner, loot, 1)
            lootloser = spicemanip.main([x for x in competitors if x != lootwinner], 1) or lootwinner
            if typeofduel in duels_commands_events:
                adjust_database_value(bot, lootwinner, 'combat_track_loot_won', 1)
                adjust_database_value(bot, lootloser, 'combat_track_loot_lost', 1)

        # Update eXPerience for winner
        if playerbio_winner.actual != playerbio_loser.actual:
            XPearnedwinner = playerbio_winner.intelligence
            if playerbio_winner.Class == 'ranger':
                XPearnedwinner = XPearnedwinner * 2
            XPearnedwinner = XPearnedwinner * duels.tierscaling
            adjust_database_value(bot, playerbio_winner.actual, 'xp', XPearnedwinner)
            XPearnedloser = playerbio_loser.intelligence
            if playerbio_loser.Class == 'ranger':
                XPearnedloser = XPearnedloser * 2
            XPearnedloser = XPearnedloser * duels.tierscaling
            adjust_database_value(bot, playerbio_loser.actual, 'xp', XPearnedloser)
            if typeofduel in duels_commands_events:
                adjust_database_value(bot, playerbio_winner.actual, 'combat_track_xp_earned', XPearnedwinner)
            if typeofduel in duels_commands_events:
                adjust_database_value(bot, playerbio_loser.actual, 'combat_track_xp_earned', XPearnedloser)

        # hungergames winner value
        if typeofduel == "hungergames":
            set_database_value(bot, 'duelrecorduser', 'hungergame_winner', playerbio_winner.actual)
            set_database_value(bot, 'duelrecorduser', 'hungergame_loser', loser)

        # colosseum winner value
        if typeofduel == "colosseum":
            set_database_value(bot, 'duelrecorduser', 'colosseum_winner', playerbio_winner.actual)
            set_database_value(bot, 'duelrecorduser', 'colosseum_loser', loser)

        # Update Wins and Losses
        if playerbio_winner.actual != playerbio_loser.actual:
            if playerbio_winner.actual != bot.nick:
                adjust_database_value(bot, winner, 'wins', 1)
                adjust_database_value(bot, loser, 'losses', 1)
            if typeofduel in duels_commands_events:
                adjust_database_value(bot, playerbio_winner.actual, 'combat_track_wins', 1)
                adjust_database_value(bot, playerbio_loser.actual, 'combat_track_losses', 1)

        # Update streaks
        if playerbio_winner.actual != playerbio_loser.actual:
            if playerbio_winner.actual != bot.nick:
                duels_set_current_streaks(bot, playerbio_winner.actual, 'win')
                duels_set_current_streaks(bot, playerbio_loser.actual, 'loss')

        # Streaks Text
        if playerbio_winner.actual != playerbio_loser.actual:
            streaktext = duels_get_streaktext(bot, playerbio_winner, playerbio_loser) or ''
            if streaktext != []:
                for x in streaktext:
                    combattextarraycomplete.append(x)

        # new pepper level?
        if playerbio_winner.actual != playerbio_loser.actual and playerbio_winner.actual != 'duelsmonster' and playerbio_winner.actual != bot.nick:
            pepper_now_winner = duels_tier_nick_to_pepper(bot, playerbio_winner.actual)
            if pepper_now_winner != playerbio_winner.pepperstart:
                combattextarraycomplete.append(playerbio_winner.nametext + " graduates to " + pepper_now_winner + "! ")
        if playerbio_loser.actual != playerbio_winner.actual and loser != 'duelsmonster':
            pepper_now_loser = duels_tier_nick_to_pepper(bot, playerbio_loser.actual)
            if pepper_now_loser != playerbio_loser.pepperstart:
                combattextarraycomplete.append(playerbio_loser.nametext + " graduates to " + pepper_now_loser + "! ")

        # Tier update
        currenttierend = get_database_value(bot, 'duelrecorduser', 'tier') or 1
        if int(currenttierend) > int(currenttierstart):
            combattextarraycomplete.append("New Tier Unlocked!")
            tiercheck = eval("duels_commands_tier_unlocks_"+str(currenttierend))
            if tiercheck != []:
                newtierlist = spicemanip.main(tiercheck, "list")
                combattextarraycomplete.append("Feature(s) now available: " + newtierlist)
                if typeofduel in duels_commands_events:
                    osd(bot, duels.duels_enabled_channels, 'say', "New Tier Unlocked!     Feature(s) now available: " + newtierlist)

        # Magic Attributes text
        magicattributestext = duels_magic_attributes_text(bot, playerbio_winner, playerbio_loser)
        for x in magicattributestext:
            combattextarraycomplete.append(x)

        # Random Bonus
        if typeofduel == 'random':
            if playerbio_winner.actual != bot.nick and playerbio_winner.actual != playerbio_loser.actual:
                adjust_database_value(bot, playerbio_winner.actual, 'coin', spicemanip.main(['random', duels_ingame_coin_usage, duels_ingame_coin], 'index'))
                combattextarraycomplete.append(playerbio_winner.nametext + " won the random attack payout of " + str(spicemanip.main(['random', duels_ingame_coin_usage, duels_ingame_coin], 'index')) + " coin!")

        # Update last fought
        if playerbio_maindueler.actual != playerbio_target.actual and typeofduel in duels_commands_events:
            if playerbio_maindueler.actual == 'duelsmonster':
                set_database_value(bot, playerbio_target.actual, 'lastfought', playerbio_maindueler.nametext)
            else:
                set_database_value(bot, playerbio_target.actual, 'lastfought', playerbio_maindueler.actual)
            if playerbio_target.actual == 'duelsmonster':
                set_database_value(bot, playerbio_maindueler.actual, 'lastfought', playerbio_target.nametext)
            else:
                set_database_value(bot, playerbio_maindueler.actual, 'lastfought', playerbio_target.actual)

        # End Of event
        if typeofduel in duels_commands_events:
            set_database_value(bot, playerbio_target.actual, 'lastfought', targetlastfoughtstart)

        # Final Announce
        if typeofduel in duels_commands_events:
            osd(bot, [playerbio_winner.actual, playerbio_loser.actual], 'priv', combattextarraycomplete)
        else:
            osd(bot, duels.channel_current, 'say', combattextarraycomplete)

        # Prior Log
        lastlog = []
        lastlog.append(playerbio_maindueler.announce + " VERSUS " + playerbio_target.announce)
        for x in combattextarraycomplete:
            lastlog.append(x)
        set_database_value(bot, playerbio_maindueler.actual, 'combatlastplayeractualtext', lastlog)
        set_database_value(bot, playerbio_target.actual, 'combatlastplayeractualtext', lastlog)


""" Combat """


def duels_command_function_combat(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    subcommand = spicemanip.main([x for x in duels.command_restructure if x == 'last'], 1) or 'combat'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
    if not validtarget and not duels.admin:
        osd(bot, duels.instigator, 'notice', validtargetmsg)
        duels.command_stamina_cost = 0
        return

    if subcommand == 'last':
        combatlastplayeractual = get_database_value(bot, target, 'combatlastplayeractualtext') or str("I don't have a record of the last combat for "+target+".")
        osd(bot, duels.channel_current, 'say', combatlastplayeractual)
        duels.command_stamina_cost = 0
        return

    # Check that the target doesn't have a timeout preventing them from playing
    executedueling, executeduelingmsg = duels_criteria(bot, target, duels, 1)
    if not executedueling:
        duels.command_stamina_cost = 0
        return

    # Run the duel
    duel_combat(bot, duels.instigator, [target], duels.command_restructure, 'target', duels)


def duels_docs_combat(bot):
    dispmsgarray = []
    dispmsgarray.append("This the main function of gameplay.")
    dispmsgarray.append("Usage: Target another player.")
    dispmsgarray.append("Additional Switches: " + 'You may use -w="weapon name" to manually use a weapon.')
    dispmsgarray.append("Subcommand 'list': See the last combat that a player was in. You may manually select a target.")
    return dispmsgarray


""" Classic Duels by DGW, simple coinflip winning """


def duels_command_function_classic(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    if target != duels.instigator and target != bot.nick:
        if target == 'monster':
            osd(bot, duels.instigator, 'notice', "The monster can't play the classic duels game.")
            duels.command_stamina_cost = 0
            return
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget and not duels.admin:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
    target = nick_actual(bot, target)

    subcommand = spicemanip.main([x for x in duels.command_restructure if x == 'stats' or x == 'leaderboard'], 1) or 'combat'

    if subcommand == 'stats':
        duelclassic_stats(bot, trigger, target)
        return

    if subcommand == 'leaderboard':
        winrateplayers, winratescores = [], []
        bestwinsplayers, bestwinscores = [], []
        worstlossesplayers, worstlossesscores = [], []
        for player in duels.users_current_allchan_opted:
            wins, losses = duelclassic_get_duels(bot, player)
            total = wins + losses
            if total:
                win_rate = wins / total * 100
                winrateplayers.append(player)
                winratescores.append(win_rate)
            best_wins = duelclassic_get_best_win_streak(bot, player)
            if best_wins:
                bestwinsplayers.append(player)
                bestwinscores.append(best_wins)
            worst_losses = duelclassic_get_worst_loss_streak(bot, player)
            if worst_losses:
                worstlossesplayers.append(player)
                worstlossesscores.append(worst_losses)
        winratescores, winrateplayers = array_arrangesort(bot, winratescores, winrateplayers)
        bestwinscores, bestwinsplayers = array_arrangesort(bot, bestwinscores, bestwinsplayers)
        worstlossesscores, worstlossesplayers = array_arrangesort(bot, worstlossesscores, worstlossesplayers)
        classicleaderboardmessage = []
        if winrateplayers != []:
            winrateleadername = spicemanip.main(winrateplayers, 'last')
            winrateleadernumber = spicemanip.main(winratescores, 'last')
            winrateleadernumber = format(winrateleadernumber, '.3f')
            classicleaderboardmessage.append("Best win rate is " + winrateleadername + " with " + str(winrateleadernumber))
        if bestwinsplayers != []:
            bestwinleadername = spicemanip.main(bestwinsplayers, 'last')
            bestwinleadernumber = spicemanip.main(bestwinscores, 'last')
            classicleaderboardmessage.append("Worst losing streak is " + bestwinleadername + " with " + str(bestwinleadernumber))
        if worstlossesplayers != []:
            worstlossessleadername = spicemanip.main(worstlossesplayers, 'last')
            worstlossesleadernumber = spicemanip.main(worstlossesscores, 'last')
            classicleaderboardmessage.append("Best win streak is " + worstlossessleadername + " with " + str(worstlossesleadernumber))
        osd(bot, duels.channel_current, 'say', classicleaderboardmessage)
        duels.command_stamina_cost = 0
        return

    if subcommand == 'combat':
        duels_classic_timeout = 600
        if duels.channel_current in duels.duels_dev_channels or duels.admin:
            duels_classic_timeout = 0
        duelclassic_combat(bot, duels.channel_current, duels.instigator, target, duels_classic_timeout, trigger, is_admin=trigger.admin)
        return


def duels_docs_classic(bot):
    dispmsgarray = []
    dispmsgarray.append("This shows the gameplay that this game is based on. Note: this does not have an effect your actual stats.")
    dispmsgarray.append("Usage: Target another player.")

    dispmsgarray.append("Subcommand 'stats': displays stats.")
    dispmsgarray.append("Subcommand 'leaderboard': displays stats leaders.")
    return dispmsgarray


""" Assault """


def duels_command_function_assault(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # no instigator in array
    if duels.instigator in duels.users_canduel_allchan:
        duels.users_canduel_allchan.remove(duels.instigator)

    # Run a normal duel if only one opponent
    if len(duels.users_canduel_allchan) <= 1:
        if len(duels.users_canduel_allchan) == 1:
            osd(bot, duels.channel_current, 'say', duels.instigator + " Initiated a full channel " + command_main + " event, but only had one opponent.")
            duel_combat(bot, duels.instigator, duels.users_canduel_allchan, duels.command_restructure, 'target', duels)
            duels.command_stamina_cost = spicemanip.main(['combat', duels_commands_stamina_required, duels_commands_stamina_cost], 'index')
        else:
            osd(bot, duels.channel_current, 'say', duels.instigator + " Initiated a full channel " + command_main + " event, but had no targets.")
            duels.command_stamina_cost = 0
        return

    # Announce to channel the contestants
    displaymessage = spicemanip.main(duels.users_canduel_allchan, "list")
    osd(bot, duels.channel_current, 'say', duels.instigator + " Initiated a full channel " + command_main + " event. Good luck to " + displaymessage)

    # Temp stats
    lastfoughtstart = get_database_value(bot, duels.instigator, 'lastfought')
    for astat in combat_track_results:
        reset_database_value(bot, duels.instigator, "combat_track_" + astat)
    for player in duels.users_canduel_allchan:
        for astat in combat_track_results:
            reset_database_value(bot, player, "combat_track_" + astat)

    # Instigator versus the array
    for target in duels.users_canduel_allchan:
        currentdeathblowcheck = get_database_value(bot, target, 'deathblow')
        if not currentdeathblowcheck:
            currentdeathblowcheckb = get_database_value(bot, duels.instigator, 'deathblow')
            if not currentdeathblowcheckb:
                duel_combat(bot, duels.instigator, [target], duels.command_restructure, 'assault', duels)

    # Display results
    maindueler = duels.instigator
    osd(bot, maindueler, 'notice', "It looks like the Full Channel Assault has completed.")
    assaultstatsarray = []
    assaultstatsarray.append(maindueler + "'s Full Channel Assault results:")
    for astat in combat_track_results:
        astateval = get_database_value(bot, duels.instigator, "combat_track_" + astat) or 0
        if astateval:
            astatname = astat.replace("_", " ")
            astatname = astatname.title()
            astatstr = str(str(astatname) + " = " + str(astateval))
            assaultstatsarray.append(astatstr)
            reset_database_value(bot, duels.instigator, "combat_track_" + astat)
    osd(bot, duels.channel_current, 'say', assaultstatsarray)

    # Cleanup
    for player in duels.users_canduel_allchan:
        for astat in combat_track_results:
            reset_database_value(bot, player, "combat_track_" + astat)
    set_database_value(bot, duels.instigator, 'lastfought', lastfoughtstart)


def duels_docs_assault(bot):
    dispmsgarray = []
    dispmsgarray.append("This a combat event that allows you to attack every other duels player.")
    return dispmsgarray


""" Mayhem """


def duels_command_function_mayhem(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Run a normal duel if only one opponent
    if len(duels.users_canduel_allchan) <= 2:
        if duels.instigator in duels.users_canduel_allchan:
            duels.users_canduel_allchan.remove(duels.instigator)
        if len(duels.users_canduel_allchan) == 1:
            osd(bot, duels.channel_current, 'say', duels.instigator + " Initiated a full channel " + command_main + " event, but only had one opponent.")
            duel_combat(bot, duels.instigator, duels.users_canduel_allchan, duels.command_restructure, 'target', duels)
            duels.command_stamina_cost = spicemanip.main(['combat', duels_commands_stamina_required, duels_commands_stamina_cost], 'index')
        else:
            osd(bot, duels.channel_current, 'say', duels.instigator + " Initiated a full channel " + command_main + " event, but had no targets.")
            duels.command_stamina_cost = 0
        return

    # Announce to channel the contestants
    displaymessage = spicemanip.main(duels.users_canduel_allchan, "list")
    osd(bot, duels.channel_current, 'say', duels.instigator + " Initiated a full channel " + command_main + " event. Good luck to " + displaymessage)

    # Temp stats
    for user in duels.users_canduel_allchan:
        for astat in combat_track_results:
            reset_database_value(bot, duels.instigator, "combat_track_" + astat)

    # Build second users_current_arena
    mainduelerarray = []
    for userplayer in duels.users_canduel_allchan:
        mainduelerarray.append(userplayer)
    random.shuffle(mainduelerarray)

    # Every Player combination
    playercombinations = []
    for playercombo in itertools.product(mainduelerarray, duels.users_canduel_allchan):
        playercombinations.append(playercombo)
    random.shuffle(playercombinations)
    for usercombo in playercombinations:
        currentcombo = []
        for combouser in usercombo:
            currentcombo.append(combouser)
        playera = spicemanip.main(currentcombo, 1)
        playerb = spicemanip.main(currentcombo, "last")
        if playera != playerb:
            playerafought = get_database_value(bot, playera, 'mayhemorganizer') or []
            playerbfought = get_database_value(bot, playerb, 'mayhemorganizer') or []
            if playera not in playerbfought and playerb not in playerafought:
                currentdeathblowcheck = get_database_value(bot, playerb, 'deathblow')
                if not currentdeathblowcheck:
                    currentdeathblowcheckb = get_database_value(bot, playera, 'deathblow')
                    if not currentdeathblowcheckb:
                        duel_combat(bot, playera, [playerb], duels.command_restructure, 'assault', duels)
                adjust_database_array(bot, playera, playerb, 'mayhemorganizer', 'add')
                adjust_database_array(bot, playerb, playera, 'mayhemorganizer', 'add')

    # Results
    assaultstatsarray = []
    for user in duels.users_canduel_allchan:
        reset_database_value(bot, user, 'mayhemorganizer')
    for astat in combat_track_results:
        playerarray, statvaluearray = [], []
        for user in duels.users_canduel_allchan:
            astateval = get_database_value(bot, user, "combat_track_" + astat) or 0
            if astateval > 0:
                statvaluearray.append(astateval)
                playerarray.append(user)
            reset_database_value(bot, user, "combat_track_" + astat)
        if playerarray != [] and statvaluearray != []:
            statvaluearray, playerarray = array_arrangesort(bot, statvaluearray, playerarray)
            statleadername = spicemanip.main(playerarray, 'last')
            statleadernumber = spicemanip.main(statvaluearray, 'last')
            astatname = astat.replace("_", " ")
            astatname = astatname.title()
            assaultstatsarray.append("Most " + astatname + ": "+str(statleadername) + " at " + str(statleadernumber))
    if len(assaultstatsarray) > 1:
        osd(bot, duels.channel_current, 'say', assaultstatsarray)


def duels_docs_mayhem(bot):
    dispmsgarray = []
    dispmsgarray.append("This a combat event that finds every combination of combat possible.")
    return dispmsgarray


""" Hunger Games """


def duels_command_function_hungergames(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Need players
    totaltributes = len(duels.users_canduel_allchan)
    totaltributesstart = totaltributes
    if totaltributes == 1:
        osd(bot, duels.instigator, 'notice', "There is only one tribute.  Try again later.")
        duels.command_stamina_cost = 0
        return

    # Basic vars
    currenttierstart = get_database_value(bot, 'duelrecorduser', 'tier') or 0
    dispmsgarray = []

    # Announce to channel the contestants
    displaymessage = spicemanip.main(duels.users_canduel_allchan, "list")
    osd(bot, duels.channel_current, 'say', duels.instigator + " Initiated a full channel " + command_main + " event. Good luck to " + displaymessage)

    # Rebuild array
    hungerarray = []
    for player in duels.users_canduel_allchan:
        hungerarray.append(player)

    # generic
    totaltributes = len(hungerarray)
    firsttodie = ''

    # Individual duels to find victor
    while totaltributes > 1:
        totaltributes = totaltributes - 1
        maindueler = spicemanip.main(hungerarray, 1)
        current_target = spicemanip.main(hungerarray, 2)

        currentdeathblowcheck = get_database_value(bot, current_target, 'deathblow')
        if not currentdeathblowcheck:
            currentdeathblowcheckb = get_database_value(bot, maindueler, 'deathblow')
            if not currentdeathblowcheckb:
                duel_combat(bot, maindueler, [current_target], triggerargsarray, 'hungergames', duels)
                hungergameloser = get_database_value(bot, 'duelrecorduser', 'hungergame_loser')
                hungergamewinner = get_database_value(bot, 'duelrecorduser', 'hungergame_winner')
                if firsttodie == '':
                    firsttodie = hungergameloser
                hungerarray.remove(hungergameloser)
            else:
                if firsttodie == '':
                    firsttodie = maindueler
                hungerarray.remove(maindueler)
        else:
            if firsttodie == '':
                firsttodie = current_target
            hungerarray.remove(current_target)
        random.shuffle(hungerarray)

    # Reset
    reset_database_value(bot, 'duelrecorduser', 'hungergame_loser')
    reset_database_value(bot, 'duelrecorduser', 'hungergame_winner')

    # Display
    hungerwinner = spicemanip.main(hungerarray, 1)
    dispmsgarray.append(hungerwinner + " is the victor!")
    dispmsgarray.append(firsttodie + " was the first to fall.")
    osd(bot, duels.channel_current, 'say', dispmsgarray)


def duels_docs_hungergames(bot):
    dispmsgarray = []
    dispmsgarray.append("This pits all duels players against eachother with one victorious.")
    return dispmsgarray


""" Colosseum """


def duels_command_function_colosseum(bot, triggerargsarray, command_main,  trigger, command_full, duels, instigatorbio):

    # Run a normal duel if only one opponent
    if len(duels.users_canduel_allchan) <= 2:
        if duels.instigator in duels.users_canduel_allchan:
            duels.users_canduel_allchan.remove(duels.instigator)
        if len(duels.users_canduel_allchan) == 1:
            osd(bot, duels.channel_current, 'say', duels.instigator + " Initiated a full channel " + command_main + " event, but only had one opponent.")
            duel_combat(bot, duels.instigator, duels.users_canduel_allchan, duels.command_restructure, 'target', duels)
            duels.command_stamina_cost = spicemanip.main(['combat', duels_commands_stamina_required, duels_commands_stamina_cost], 'index')
        else:
            osd(bot, duels.channel_current, 'say', duels.instigator + " Initiated a full channel " + command_main + " event, but had no targets.")
            duels.command_stamina_cost = 0
        return

    # Vars
    currenttierstart = get_database_value(bot, 'duelrecorduser', 'tier') or 0
    dispmsgarray = []
    displaymessage = spicemanip.main(duels.users_canduel_allchan, "list")

    # Announce
    osd(bot, duels.channel_current, 'say', duels.instigator + " Initiated a full channel " + command_main + " event. Good luck to " + displaymessage)
    totalplayers = len(duels.users_canduel_allchan)
    riskcoins = int(totalplayers) * 30
    set_database_value(bot, 'duelrecorduser', 'colosseum_damage', int(riskcoins))

    # Individual duels to find victor
    while int(totalplayers) > 1:
        totalplayers = totalplayers - 1
        maindueler = spicemanip.main(duels.users_canduel_allchan, 1)
        current_target = spicemanip.main(duels.users_canduel_allchan, 2)
        currentdeathblowcheck = get_database_value(bot, current_target, 'deathblow')
        if not currentdeathblowcheck:
            currentdeathblowcheckb = get_database_value(bot, maindueler, 'deathblow')
            if not currentdeathblowcheckb:
                duel_combat(bot, maindueler, [current_target], triggerargsarray, 'colosseum', duels)
                colosseumloser = get_database_value(bot, 'duelrecorduser', 'colosseum_loser')
                colosseumwinner = get_database_value(bot, 'duelrecorduser', 'colosseum_winner')
                duels.users_canduel_allchan.remove(colosseumloser)
            else:
                duels.users_canduel_allchan.remove(maindueler)
        else:
            duels.users_canduel_allchan.remove(current_target)
        random.shuffle(duels.users_canduel_allchan)

    # Reset
    reset_database_value(bot, 'duelrecorduser', 'colosseum_loser')
    reset_database_value(bot, 'duelrecorduser', 'colosseum_winner')
    reset_database_value(bot, 'duelrecorduser', 'colosseum_damage')

    # Announce winner and pay out
    colosseumwinner = spicemanip.main(duels.users_canduel_allchan, 1)
    adjust_database_value(bot, colosseumwinner, 'coin', riskcoins)
    osd(bot, duels.channel_current, 'say', "The Winner is: " + colosseumwinner + "! Total winnings: " + str(riskcoins) + " coin! Losers took " + str(riskcoins) + " damage.")


def duels_docs_colosseum(bot):
    dispmsgarray = []
    dispmsgarray.append("This pits all users against eachother with a prize that is based on the amount of players present.")
    return dispmsgarray


""" Monster """


def duels_command_function_monster(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    playernew = get_database_value(bot, 'duelsmonster', 'newplayer')
    if not playernew:
        set_database_value(bot, 'duelsmonster', 'newplayer', 1)

    # command
    monstercommand = spicemanip.main([x for x in duels.command_restructure if x == 'hunt'], 1) or 'attack'

    if monstercommand == 'hunt':
        # Pick Monsters name
        duelsmonstername = get_database_value(bot, 'duelsmonster', 'last_monster') or None
        duelsmonstervarient = get_database_value(bot, 'duelsmonster', 'last_monster_varent') or None
        if not duelsmonstername:
            # Generate Monster's stats based on room average
            duels_monster_stats_generate(bot, duels, 1)

            # Monster's name
            duelsmonstervarient = spicemanip.main(duelsmonstervarientarray, 'random')
            set_database_value(bot, 'duelsmonster', 'last_monster_varent', duelsmonstervarient)
            duelsmonstername = spicemanip.main(monstersarray, 'random')
            set_database_value(bot, 'duelsmonster', 'last_monster', duelsmonstername)

        # Run a normal duel if only one opponent
        if len(duels.users_canduel_allchan) <= 1:
            duel_combat(bot, duels.instigator, ['duelsmonster'], triggerargsarray, 'combat', duels)
            duels.command_stamina_cost = spicemanip.main(['combat', duels_commands_stamina_required, duels_commands_stamina_cost], 'index')
            return

        # Announce to channel the contestants
        displaymessage = spicemanip.main(duels.users_canduel_allchan, "list")
        osd(bot, duels.channel_current, 'say', duels.instigator + " Initiated a full channel " + command_main + " hunt event. Good luck to " + displaymessage)

        lastfoughtstart = get_database_value(bot, duels.instigator, 'lastfought')
        for astat in combat_track_results:
            reset_database_value(bot, 'duelsmonster', "combat_track_" + astat)
        for player in duels.users_canduel_allchan:
            for astat in combat_track_results:
                reset_database_value(bot, player, "combat_track_" + astat)

        # Instigator versus the array
        for target in duels.users_canduel_allchan:
            currentdeathblowcheck = get_database_value(bot, target, 'deathblow')
            if not currentdeathblowcheck:
                currentdeathblowcheckb = get_database_value(bot, 'duelsmonster', 'deathblow')
                if not currentdeathblowcheckb:
                    duel_combat(bot, 'duelsmonster', [target], duels.command_restructure, 'assault', duels)

        # Display results
        maindueler = duels.instigator
        assaultstatsarray = []
        monsterannounce = str(duelsmonstervarient+" "+duelsmonstername)
        assaultstatsarray.append(monsterannounce + "'s Full Channel Assault results:")
        for astat in combat_track_results:
            astateval = get_database_value(bot, 'duelsmonster', "combat_track_" + astat) or 0
            if astateval:
                astatname = astat.replace("_", " ")
                astatname = astatname.title()
                astatstr = str(str(astatname) + " = " + str(astateval))
                assaultstatsarray.append(astatstr)
                reset_database_value(bot, 'duelsmonster', "combat_track_" + astat)
        osd(bot, duels.channel_current, 'say', assaultstatsarray)

        # Cleanup
        for player in duels.users_canduel_allchan:
            for astat in combat_track_results:
                reset_database_value(bot, player, "combat_track_" + astat)
        set_database_value(bot, 'duelsmonster', 'lastfought', lastfoughtstart)

    if monstercommand == 'attack':
        # Pick Monsters name
        currentmonster = get_database_value(bot, 'duelsmonster', 'last_monster') or None
        if not currentmonster:
            # Generate Monster's stats based on room average
            duels_monster_stats_generate(bot, duels, 1)

            # Monster's name
            duelsmonstervarient = spicemanip.main(duelsmonstervarientarray, 'random')
            set_database_value(bot, 'duelsmonster', 'last_monster_varent', duelsmonstervarient)
            duelsmonstername = spicemanip.main(monstersarray, 'random')
            set_database_value(bot, 'duelsmonster', 'last_monster', duelsmonstername)

        # Combat
        duels_check_nick_condition(bot, 'duelsmonster', duels)
        duel_combat(bot, duels.instigator, ['duelsmonster'], triggerargsarray, 'combat', duels)

        # Monster does not keep stats if dead
        currentmonster = get_database_value(bot, 'duelsmonster', 'last_monster') or None
        if not currentmonster:
            duels_monster_stats_reset(bot, duels)


def duels_docs_monster(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to do combat against a random low-level monster.")
    dispmsgarray.append("Additional Switches: " + 'You may use -w="weapon name" to manually use a weapon.')
    dispmsgarray.append("Subcommand 'loot': See the loot that the current monster has.")
    dispmsgarray.append("Subcommand 'health': See the health of the current monster.")
    return dispmsgarray


""" Random Target """


def duels_command_function_random(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Bot can fight in random
    if bot.nick not in duels.users_canduel_allchan:
        duels.users_canduel_allchan.append(bot.nick)

    # monster
    duels.users_canduel_allchan.append('duelsmonster')

    target = spicemanip.main(duels.users_canduel_allchan, 'random')
    if target == 'duelsmonster':
        duels_command_function_monster(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio)
        return
    else:
        targetname = target
        duels_check_nick_condition(bot, target, duels)
    osd(bot, duels.channel_current, 'say', duels.instigator + " summoned the Flying Fickle Finger of Fate, and it chose " + targetname + " to fight.")
    duel_combat(bot, duels.instigator, [target], triggerargsarray, 'random', duels)


def duels_docs_random(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to combat a random player. This has an added bonus if you win. There is a chance that the bot or monster may be selected. The bot always wins.")
    dispmsgarray.append("Additional Switches: " + 'You may use -w="weapon name" to manually use a weapon.')
    return dispmsgarray


"""
Other Damage Commands
"""


""" Russian Roulette """


def duels_command_function_roulette(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    roulettesubcom = spicemanip.main([x for x in duels.command_restructure if x == 'last' or str(x).isdigit()], 1) or 'normal'

    if roulettesubcom == 'last':
        roulettelastplayeractual = get_database_value(bot, 'duelrecorduser', 'roulettelastplayeractualtext') or str("I don't have a record of the last roulette.")
        osd(bot, duels.channel_current, 'say', roulettelastplayeractual)
        duels.command_stamina_cost = 0
        return

    # subcommands
    manualpick = 0
    if str(roulettesubcom).isdigit():
        if int(roulettesubcom) >= 1 and int(roulettesubcom) <= 6:
            manualpick = 1
        else:
            osd(bot, duels.channel_current, 'say', "Invalid Chamber Number!")
            duels.command_stamina_cost = 0
            return

    # instigator must wait until the next round
    roulettelastshot = get_database_value(bot, 'duelrecorduser', 'roulettelastplayershot') or bot.nick
    if roulettelastshot == duels.instigator:
        if duels.channel_current in duels.duels_dev_channels or duels.admin:
            allowpass = 1
        elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
            allowpass = 1
        else:
            osd(bot, duels.instigator, 'notice', "You must wait for the current round to complete, until you may play again.")
            duels.command_stamina_cost = 0
            return

    # Instigator must wait a day after death
    getlastdeath = duels_time_since(bot, duels.instigator, 'roulettedeath') or spicemanip.main(['rouelette_death', duels_timeouts, duels_timeouts_duration], 'index')
    if getlastdeath < spicemanip.main(['rouelette_death', duels_timeouts, duels_timeouts_duration], 'index'):
        if duels.channel_current in duels.duels_dev_channels or duels.admin:
            allowpass = 1
        elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
            allowpass = 1
        else:
            osd(bot, duels.instigator, 'notice', "You must wait 24 hours between roulette deaths.")
            duels.command_stamina_cost = 0
            return

    # Small timeout
    getlastusage = duels_time_since(bot, 'duelrecorduser', str('lastfullroom' + command_main)) or spicemanip.main(['roulette', duels_timeouts, duels_timeouts_duration], 'index')
    if getlastusage < spicemanip.main(['roulette', duels_timeouts, duels_timeouts_duration], 'index'):
        if duels.channel_current in duels.duels_dev_channels or duels.admin:
            allowpass = 1
        elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
            allowpass = 1
        else:
            osd(bot, duels.instigator, 'notice', "Roulette has a small timeout.")
            duels.command_stamina_cost = 0
            return
    set_database_value(bot, 'duelrecorduser', str('lastfullroom' + command_main), duels.now)

    # Check who last pulled the trigger, or if it's a new chamber
    roulettelastplayer = get_database_value(bot, 'duelrecorduser', 'roulettelastplayer') or bot.nick
    roulettecount = get_database_value(bot, 'duelrecorduser', 'roulettecount') or 1

    # Get the selected chamber from the database,, or set one
    roulettechamber = get_database_value(bot, 'duelrecorduser', 'roulettechamber')
    if not roulettechamber:
        roulettechamber = randint(1, 6)
        set_database_value(bot, 'duelrecorduser', 'roulettechamber', roulettechamber)

    # Display Text
    instigatorcurse = get_database_value(bot, duels.instigator, 'curse') or 0
    if manualpick == 1:
        osd(bot, duels.channel_current, 'say', duels.instigator + " is blindfolded while the chamber is set to " + str(roulettesubcom) + ".")
    elif instigatorcurse:
        osd(bot, duels.channel_current, 'say', duels.instigator + " spins the cylinder to the bullet's chamber and pulls the trigger.")
    elif roulettelastplayer == duels.instigator and int(roulettecount) > 1:
        osd(bot, duels.channel_current, 'say', duels.instigator + " spins the revolver and pulls the trigger.")
    elif int(roulettecount) == 1:
        osd(bot, duels.channel_current, 'say', duels.instigator + " reloads the revolver, spins the cylinder and pulls the trigger.")
    else:
        osd(bot, duels.channel_current, 'say', duels.instigator + " spins the cylinder and pulls the trigger.")

    # Default 6 possible chambers for bullet.
    # curses
    if instigatorcurse:
        adjust_database_value(bot, duels.instigator, 'curse', -1)
        reset_database_value(bot, 'duelrecorduser', 'roulettespinarray')
        currentspin = roulettechamber
    # manual number
    elif manualpick == 1:
        currentspin = int(roulettesubcom)
    # If instigator uses multiple times in a row, decrease odds of success
    elif roulettelastplayer == duels.instigator:
        roulettespinarray = get_database_value(bot, 'duelrecorduser', 'roulettespinarray')
        if not roulettespinarray:
            roulettespinarray = [1, 2, 3, 4, 5, 6]
        if len(roulettespinarray) > 1:
            roulettetemp = []
            for x in roulettespinarray:
                if int(x) != int(roulettechamber):
                    roulettetemp.append(x)
            rouletteremove = spicemanip.main(roulettetemp, "random")
            roulettetempb = []
            roulettetempb.append(roulettechamber)
            for j in roulettetemp:
                if int(j) != int(rouletteremove):
                    roulettetempb.append(j)
            set_database_value(bot, 'duelrecorduser', 'roulettespinarray', roulettetempb)
            currentspin = spicemanip.main(roulettetempb, "random")
        else:
            currentspin = roulettechamber  # if only one chambers left
            reset_database_value(bot, 'duelrecorduser', 'roulettespinarray')
    else:
        roulettespinarray = [1, 2, 3, 4, 5, 6]
        reset_database_value(bot, 'duelrecorduser', 'roulettespinarray')
        currentspin = spicemanip.main(roulettespinarray, "random")

    # current spin is safe
    if int(currentspin) != int(roulettechamber):
        osd(bot, duels.channel_current, 'say', "*click*")
        if manualpick == 1:
            roulettelastplayeractualtext = str(duels.instigator + " manually picked a chamber without the bullet. The Bullet was moved.")
            osd(bot, duels.channel_current, 'say', duels.instigator + " picked a chamber without the bullet. Bullet will be moved.")
            roulettechambernew = randint(1, 6)
            set_database_value(bot, 'duelrecorduser', 'roulettechamber', roulettechambernew)
        else:
            roulettelastplayeractualtext = str(duels.instigator + " pulled the trigger and was safe.")
        roulettecount = roulettecount + 1
        roulettepayout = spicemanip.main(['roulette', duels_ingame_coin_usage, duels_ingame_coin], 'index') * roulettecount
        currentpayout = get_database_value(bot, duels.instigator, 'roulettepayout')
        adjust_database_value(bot, duels.instigator, 'roulettepayout', roulettepayout)
        set_database_value(bot, 'duelrecorduser', 'roulettecount', roulettecount)
        set_database_value(bot, 'duelrecorduser', 'roulettelastplayer', duels.instigator)
        adjust_database_array(bot, 'duelrecorduser', [duels.instigator], 'roulettewinners', 'add')

    # instigator shoots themself in the head
    else:
        currenttierstart = get_database_value(bot, 'duelrecorduser', 'tier') or 0
        dispmsgarray = []

        if roulettecount == 1:
            if instigatorcurse:
                dispmsgarray.append("First in the chamber. Looks like " + duels.instigator + " was cursed!")
            else:
                dispmsgarray.append("First in the chamber. What bad luck.")

        # Dish out the pain
        damage = randint(50, 120)
        bodypart = 'head'
        revolver = spicemanip.main(roulette_revolver_list, 'random')
        damage = duels.tierscaling * damage
        dispmsgarray.append(duels.instigator + " shoots themself in the head with the " + revolver + ", dealing " + str(damage) + " damage. ")
        roulettelastplayeractualtext = str(duels.instigator + " shot themself in the head with the " + revolver + ", dealing " + str(damage) + " damage. ")

        # dish out the pain
        if damage > 0:
            damageinflictarray = duels_effect_inflict(bot, duels,  instigatorbio, instigatorbio, 'head',  'damage', damage, 'roulette')
            for k in damageinflictarray:
                dispmsgarray.append(k)

        # Payouts
        biggestpayout, biggestpayoutwinner = 0, ''
        playerarray, statvaluearray = [], []
        roulettewinners = get_database_value(bot, 'duelrecorduser', 'roulettewinners') or []
        uniquewinnersarray = []
        for x in roulettewinners:
            if x not in uniquewinnersarray and x != duels.instigator:
                uniquewinnersarray.append(x)

        for x in uniquewinnersarray:

            # coin
            roulettepayoutx = get_database_value(bot, x, 'roulettepayout')
            if roulettepayoutx > 0:
                playerarray.append(x)
                statvaluearray.append(roulettepayoutx)
            adjust_database_value(bot, x, 'coin', roulettepayoutx)
            if roulettepayoutx > 0:
                osd(bot, x, 'notice', "Your roulette payouts = " + str(roulettepayoutx) + " coins!")
            reset_database_value(bot, x, 'roulettepayout')

        # unique winner list
        if uniquewinnersarray != []:
            displaymessage = spicemanip.main(uniquewinnersarray, "list")
            if len(uniquewinnersarray) > 1:
                dispmsgarray.append("Winners: " + displaymessage + ".")
            else:
                dispmsgarray.append("Winner: " + displaymessage + ".")

        if playerarray != [] and statvaluearray != []:
            statvaluearray, playerarray = array_arrangesort(bot, statvaluearray, playerarray)
            statleadername = spicemanip.main(playerarray, 'last')
            statleadernumber = spicemanip.main(statvaluearray, 'last')
            dispmsgarray.append("Biggest Payout: " + statleadername + " with " + str(statleadernumber) + " coins.")

        roulettecount = get_database_value(bot, 'duelrecorduser', 'roulettecount') or 1
        if roulettecount > 1:
            dispmsgarray.append("The chamber spun " + str(roulettecount) + " times. ")
        osd(bot, duels.channel_current, 'say', dispmsgarray)

        # instigator must wait until the next round
        reset_database_value(bot, 'duelrecorduser', 'roulettelastplayershot')
        set_database_value(bot, 'duelrecorduser', 'roulettelastplayershot', duels.instigator)

        # Reset for next run
        reset_database_value(bot, 'duelrecorduser', 'roulettelastplayer')
        reset_database_value(bot, 'duelrecorduser', 'roulettechamber')
        reset_database_value(bot, 'duelrecorduser', 'roulettewinners')
        reset_database_value(bot, 'duelrecorduser', 'roulettecount')
        reset_database_value(bot, duels.instigator, 'roulettepayout')
    set_database_value(bot, 'duelrecorduser', 'roulettelastplayeractualtext', roulettelastplayeractualtext)


def duels_docs_roulette(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to risk a shot in the head for the chance at big coin winnings.")
    dispmsgarray.append("Subcommand 'last': Displays the last player to bite the bullet.")
    dispmsgarray.append("Subcommand 'any digit': Selects the chamber to shoot.")
    return dispmsgarray


""" Trebuchet """


def duels_command_function_trebuchet(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Can't hit self
    if duels.instigator in duels.users_canduel_allchan:
        duels.users_canduel_allchan.remove(duels.instigator)

    # make sure there is at least one target
    if duels.users_canduel_allchan == []:
        osd(bot, duels.instigator, 'notice', "It looks like the full channel " + command_main + " event target finder has failed.")
        duels.command_stamina_cost = 0
        return

    # what is launched
    projectile = spicemanip.main(trebuchet_projectiles_list, 'random')

    # Who might get hit
    target = spicemanip.main(duels.users_canduel_allchan, 'random')

    # Check target
    duels_check_nick_condition(bot, target, duels)
    targetbio = duel_target_playerbio(bot, duels, target)

    # Bodypart
    bodypart, bodypartname = duels_bodypart_select(bot, target)

    # Damage
    damage = randint(1, 120)
    damage = duels.tierscaling * damage

    # Display
    dispmsgarray = []
    dispmsgarray.append(duels.instigator + " places a " + projectile + " onto the spinning trebuchet and slings the projectile at the general direction of " + target + " with the velocity to deal a blow of " + str(damage) + " damage.")
    if damage > 0:
        damageinflictarray = duels_effect_inflict(bot, duels,  instigatorbio, targetbio, 'random', 'damage', damage, 'trebuchet')
        for k in damageinflictarray:
            dispmsgarray.append(k)
    osd(bot, duels.channel_current, 'say', dispmsgarray)


def duels_docs_trebuchet(bot):
    dispmsgarray = []
    dispmsgarray.append("This is a spinning target hitter.")
    return dispmsgarray


""" Deathblow """


def duels_command_function_deathblow(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    deathblowtargetarray = get_database_value(bot, duels.instigator, 'deathblowtargetarray') or []
    if deathblowtargetarray == []:
        osd(bot, duels.instigator, 'notice', "You don't have a deathblow target available.")
        duels.command_stamina_cost = 0
        return

    firstdeathblowtarget = spicemanip.main(deathblowtargetarray, 1)
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan or x == 'all'], 1) or firstdeathblowtarget
    if target not in deathblowtargetarray and target != 'all':
        osd(bot, duels.instigator, 'notice', target + " is not available for you to finish.")
        duels.command_stamina_cost = 0
        return

    if target != 'all':
        target = nick_actual(bot, target)
        deathblowcurrentarray = [target]
    else:
        deathblowcurrentarray = deathblowtargetarray

    for deathblowavail in deathblowcurrentarray:
        deathblowtargettime = duels_time_since(bot, deathblowavail, 'deathblowtargettime') or 0
        if deathblowtargettime <= 120:
            targetbio = duel_target_playerbio(bot, duels, target)
            osd(bot, duels.channel_current, 'say', duels.instigator + " strikes a deathblow upon " + deathblowavail + ".")
            deathblowkilltext = duels_death_handling(bot, duels, instigatorbio, targetbio)
            osd(bot, duels.channel_current, 'say', deathblowkilltext)
        else:
            osd(bot, duels.channel_current, 'say', duels.instigator + " had the opportunity to perform a deathblow, but was too late.")
        adjust_database_array(bot, duels.instigator, [deathblowavail], 'deathblowtargetarray', 'del')
        reset_database_value(bot, deathblowavail, 'deathblow')
        reset_database_value(bot, deathblowavail, 'deathblowtargettime')
        reset_database_value(bot, deathblowavail, 'deathblowkiller')


def duels_docs_template(bot):
    dispmsgarray = []
    dispmsgarray.append("This checks to see if a recent combat provided you with the chance to finish a player.")
    dispmsgarray.append("Usage: Either run the base command, or specify a target.")
    return dispmsgarray


""" Grenade """


def duels_command_function_grenade(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Can't be privmsg
    if not duels.inchannel:
        osd(bot, duels.instigator, 'notice', "Grenades must be used in channel.")
        duels.command_stamina_cost = 0
        return

    # verify user has a grenade to use
    instigatorgrenade = get_database_value(bot, duels.instigator, 'grenade') or 0
    if instigatorgrenade <= 0:
        osd(bot, duels.instigator, 'notice', "You don't have a grenade to use!")
        duels.command_stamina_cost = 0
        return

    # The quantity the player is applyint to this transaction
    quantity = spicemanip.main([x for x in duels.command_restructure if str(x).isdigit()], 1) or 1
    if quantity > 1:
        osd(bot, duels.instigator, 'notice', "You can only throw one grenade at a time.")
        duels.command_stamina_cost = 0
        return

    # instigator and bot don't get hit
    if duels.instigator in duels.users_canduel_allchan:
        duels.users_canduel_allchan.remove(duels.instigator)
    if bot.nick in duels.users_canduel_allchan:
        duels.users_canduel_allchan.remove(bot.nick)

    # verify there is at least one target
    if duels.users_canduel_allchan == []:
        osd(bot, duels.instigator, 'notice', "It looks like using a grenade right now won't hurt anybody.")
        duels.command_stamina_cost = 0
        return
    else:
        for player in duels.users_canduel_allchan:
            if player != duels.instigator:
                duels_check_nick_condition(bot, player, duels)

    # select targets that get hit, and don't
    dispmsgarray = []
    adjust_database_value(bot, duels.instigator, 'grenade', -1)
    fulltarget, secondarytarget, thirdtarget = '', '', ''
    firsttarget = 0
    damagetotal = 200
    for player in duels.users_canduel_allchan:
        if not firsttarget:
            damage = duels_grenade_damage_full
            dispmsgarray.append(player + " takes the brunt of the grenade")
            firsttarget = 1
        elif damagetotal > 0:
            damage = duels_grenade_damage_half
            dispmsgarray.append(player + " is close by and attempts to jump away")
        else:
            damage = 0
        damagetotal = damagetotal - damage
        if damage > 0:
            targetbio = duel_target_playerbio(bot, duels, player)
            damage = duels.tierscaling * damage
            damageinflictarray = duels_effect_inflict(bot, duels, instigatorbio, targetbio, 'random', 'damage',  damage, 'grenade')
            for j in damageinflictarray:
                dispmsgarray.append(j)
            duels.users_canduel_allchan.remove(player)
    if duels.users_canduel_allchan != []:
        remainingarray = spicemanip.main(duels.users_canduel_allchan, "list")
        dispmsgarray.append(remainingarray + " completely jump out of the way")
    osd(bot, duels.channel_current, 'say', dispmsgarray)

    # Track usage for vendor
    adjust_database_value(bot, 'duelsmerchant', str("vendor_track_value_grenade"), int(quantity))


def duels_docs_grenade(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to throw a grenade into the room. Damage is randomly based on who is able to jump out of the way.")
    return dispmsgarray


""" Magic """


def duels_command_function_magic(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Instigator
    instigatormagic = duels_special_get(bot, duels.instigator, 'magic')
    instigatorclass = get_database_value(bot, duels.instigator, 'class')
    instigatormana = get_database_value(bot, duels.instigator, 'mana')
    if not instigatormana:
        osd(bot, duels.instigator, 'notice', "You don't have any mana.")
        duels.command_stamina_cost = 0
        return

    magicusage = spicemanip.main([x for x in duels.command_restructure if x in duels_magic_types], 1)
    if not magicusage:
        magicoptions = spicemanip.main(duels_magic_types, 'list')
        osd(bot, duels.channel_current, 'say', "Magic uses include: " + magicoptions + ".")
        duels.command_stamina_cost = 0
        return

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    if target != duels.instigator:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    if targetbio.actual == bot.nick:
        osd(bot, duels.instigator, 'notice', "I am immune to magic " + magicusage + ".")
        duels.command_stamina_cost = 0
        return

    if magicusage == 'curse' and targetbio.curse:  # TODO
        osd(bot, duels.instigator, 'notice', "It looks like " + targetbio.nametext + " is already cursed.")
        duels.command_stamina_cost = 0
        return

    if magicusage == 'shield' and targetbio.shield:  # TODO
        osd(bot, duels.instigator, 'notice', "It looks like " + targetbio.nametext + " is already magic shielded.")
        duels.command_stamina_cost = 0
        return

    # The quantity the player is applyint to this transaction
    quantity = spicemanip.main([x for x in duels.command_restructure if str(x).isdigit()], 1) or 1

    # How much mana is required
    manarequired = spicemanip.main([magicusage, duels_magic_types, duels_magic_required], 'index')
    manarequired = int(manarequired) * int(quantity)

    if int(manarequired) > int(instigatormana):
        manamath = int(int(manarequired) - int(instigatormana))
        osd(bot, duels.instigator, 'notice', "You need " + str(manamath) + " more mana to use magic " + magicusage + ".")
        duels.command_stamina_cost = 0
        return

    # Charge mana cost
    adjust_database_value(bot, duels.instigator, 'mana', -abs(manarequired))

    # Display
    displaymsg = []
    if duels.instigator == targetbio.actual:
        displaymsg.append(duels.instigator + " uses magic " + magicusage + ".")
    else:
        displaymsg.append(duels.instigator + " uses magic " + magicusage + " on " + targetbio.nametext + ".")

    # instigatormagic
    damagedealtmax = spicemanip.main([magicusage, duels_magic_types, duels_magic_damage], 'index')
    damagedealtmax = damagedealtmax * duels.tierscaling
    if instigatormagic * 10 > 100:
        damage = abs(damagedealtmax)
    else:
        damage = randint(instigatormagic * 10, abs(damagedealtmax))
    damagedealt = int(damage) * int(quantity)

    durationofeffect = spicemanip.main([magicusage, duels_magic_types, duels_magic_duration], 'index')

    if magicusage == 'curse':
        actualcurseduration = int(quantity) * int(durationofeffect)
        set_database_value(bot, targetbio.actual, 'curse', actualcurseduration)
        displaymsg.append("This forces " + targetbio.nametext + " to lose the next " + str(actualcurseduration) + " duels")

    if magicusage == 'shield':
        actualshielddurationmax = int(quantity) * int(durationofeffect)
        actualshielddurationmax = actualshielddurationmax * duels.tierscaling
        actualshieldduration = randint(instigatormagic * 10 * duels.tierscaling, abs(actualshielddurationmax))
        adjust_database_value(bot, targetbio.actual, 'shield', actualshieldduration)
        displaymsg.append("This allows " + targetbio.nametext + " to take no damage for the duration of " + str(actualshieldduration) + " damage")
        damagedealt = -abs(damagedealt)

    if magicusage == 'health':
        damagedealt = -abs(damagedealt)

    damageinflictarray = duels_effect_inflict(bot, duels,  instigatorbio, targetbio, 'all',  'damage',  damagedealt, 'magic')
    for k in damageinflictarray:
        displaymsg.append(k)

    osd(bot, duels.channel_current, 'say', displaymsg)
    if not duels.inchannel and targetbio.actual != duels.instigator:
        osd(bot, duels.instigator, 'notice', displaymsg)
    instigatormana = get_database_value(bot, duels.instigator, 'mana')
    if instigatormana <= 0:
        reset_database_value(bot, duels.instigator, 'mana')


def duels_docs_magic(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to use mana to do various magic functions.")
    return dispmsgarray


"""
Character Commands
"""


""" Character """


def duels_command_function_character(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    valid_character_subcoms = ['setup']
    charcommand = spicemanip.main([x for x in duels.command_restructure if x in valid_character_subcoms or x in duels_character_basics], 1) or 'sheet'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
    if target != duels.instigator:
        if not validtarget and not duels.admin:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    for char_basic in duels_character_basics:
        currentrandomarray = eval('duels_character_valid_'+char_basic)
        currentrandom = spicemanip.main(currentrandomarray, 'random')
        exec("random" + char_basic + " = " + "'"+currentrandom+"'")

    if charcommand == 'sheet':

        # Is the Tier Unlocked?
        duels.tiercommandeval = duels_tier_command_to_number(bot, command_main)
        duels.tierpepperrequired = duels_tier_number_to_pepper(bot, duels.tiercommandeval)
        if duels.tiercommandeval > 0 and targetbio.actual != duels.instigator and targetbio.actual != 'duelsmonster':
            tierpass = 0
            duels.tiermath = int(duels.tiercommandeval) - int(duels.currenttier)
            if duels.tiermath > 0:
                if duels.channel_current in duels.duels_dev_channels or duels.admin:
                    tierpass = 1
                elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
                    tierpass = 1
            else:
                tierpass = 1
            if not tierpass:
                osd(bot, duels.instigator, 'notice', "Stats for other players cannot be viewed until somebody reaches " + str(duels.tierpepperrequired.title()) + ". "+str(duels.tiermath) + " tier(s) remaining!")
                duels.command_stamina_cost = 0
                return
        duels_command_function_special(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio)

    if charcommand == 'setup':

        setuptype = spicemanip.main([x for x in duels.command_restructure if x == 'quick' or x == 'valid' or x == 'random'], 1) or 'normal'

        if setuptype == 'valid':
            dispmsgarray = []
            dispmsgarray.append("Valid Character settings include:")
            for x in duels_character_basics:
                validarray = eval("duels_character_valid_" + x)
                validarraylist = spicemanip.main(validarray, "list")
                dispmsgarray.append(x.title() + " = " + validarraylist)
            osd(bot, duels.channel_current, 'say', dispmsgarray)
            osd(bot, duels.instigator, 'notice', "Example setup command is        .duel character setup " + randomgender + " " + randomrace + " " + randomclass + "     OR simply run .duel character setup quick")
            duels.command_stamina_cost = 0
            return

        # Block people from creating characters for other players, unless admin
        if targetbio.actual != duels.instigator and not duels.admin:
            osd(bot, duels.instigator, 'notice', "you may only run the setup command for yourself.")
            duels.command_stamina_cost = 0
            return

        # only allow character creation once unless in dev mode
        playerreset = 0
        if duels.channel_current not in duels.duels_dev_channels:
            confirm = spicemanip.main([x for x in duels.command_restructure if x == 'confirm'], 1) or 0
            if not confirm:
                osd(bot, duels.channel_current, 'say', "Your character sheet cannot be changed without resetting ALL stats. You may run this command with the word 'confirm' if you want a new character sheet.")
                duels.command_stamina_cost = 0
                return
            playerreset = 1

        # Verify switches and set values
        if setuptype != 'quick' and setuptype != 'random':
            for char_basic in duels_character_basics:
                validarray = eval("duels_character_valid_" + char_basic)
                char_basic_check = spicemanip.main([x for x in duels.command_restructure if x in validarray], 1) or 0
                if not char_basic_check:
                    playercurrent = get_database_value(bot, targetbio.actual, char_basic) or 'none'
                    if playercurrent not in validarray:
                        exec("random" + char_basic + " = " + "''")
                    else:
                        exec("random" + char_basic + " = " + "'"+playercurrent+"'")
                elif char_basic_check in validarray:
                    exec("random" + char_basic + " = " + "'"+char_basic_check+"'")
                else:
                    exec("random" + char_basic + " = " + "'"+currentrandom+"'")

        if playerreset:  # TODO
            for vstat in duels.stats_valid:
                reset_database_value(bot, targetbio.actual, vstat)

        char_basics_array = []
        for char_basic in duels_character_basics:
            randomset = eval("random"+char_basic)
            char_basics_array.append(randomset)

        duels_opening_monologue(bot, duels, targetbio.actual, duels_character_basics, 1, char_basics_array)

        return

    # Class, Race, Gender
    if charcommand in duels_character_basics:

        valid_list = spicemanip.main(eval("duels_character_valid_"+charcommand), "list")
        subcommand = spicemanip.main([x for x in duels.command_restructure if x == 'set' or x == 'change'], 1) or 'view'
        if charcommand == 'class':
            targetbio_current = eval(str("targetbio."+charcommand.title()))
        else:
            targetbio_current = eval(str("targetbio."+charcommand))
        if subcommand == 'view':
            if target == duels.instigator:
                osd(bot, duels.channel_current, 'say', targetbio.nametext+", your "+charcommand+" is currently set to " + targetbio_current + ".")
            else:
                osd(bot, duels.channel_current, 'say', targetbio.nametextpos+" "+charcommand+" is currently set to " + targetbio_current + ".")
            duels.command_stamina_cost = 0
            return
            if target != duels.instigator:
                if not duels.admin:
                    osd(bot, duels.instigator, 'notice', "you cannot change somebody elses "+charcommand)
                    duels.command_stamina_cost = 0
                    return
        newset = spicemanip.main([x for x in duels.command_restructure if x in eval("duels_character_valid_"+charcommand)], 1) or 0
        if not newset:
            osd(bot, duels.instigator, 'notice', "Which "+charcommand+" would you like to use? Options are: " + valid_list + ".")
            duels.command_stamina_cost = 0
            return

        if targetbio_current != 'unknown' and not duels.admin and charcommand != 'class' and duels.channel_current not in duels.duels_dev_channels:
            osd(bot, duels.instigator, 'notice', "only bot admins can change a players "+charcommand+" after character creation.")
            duels.command_stamina_cost = 0
            return

        if newset == targetbio_current:
            osd(bot, duels.instigator, 'notice', "Your "+charcommand+" is already set to " + newset + ".")
            duels.command_stamina_cost = 0
            return

        if charcommand == 'class' and duels.channel_current not in duels.duels_dev_channels:
            instigatorfreebie = get_database_value(bot, duels.instigator, 'class_freebie') or 0
            if targetbio.actual == duels.instigator:
                instigatorcoin = get_database_value(bot, duels.instigator, 'coin') or 0
                if instigatorcoin < spicemanip.main(['class', duels_ingame_coin_usage, duels_ingame_coin], 'index') and instigatorfreebie:
                    osd(bot, duels.instigator, 'notice', "Changing class costs " + str(spicemanip.main(['class', duels_ingame_coin_usage, duels_ingame_coin], 'index')) + " coin. You need more funding.")
                    duels.command_stamina_cost = 0
                    return

            if targetbio.actual == duels.instigator and duels.channel_current not in duels.duels_dev_channels:
                classtime = duels_time_since(bot, duels.instigator, 'class_timeout')
                if classtime < spicemanip.main(['class', duels_timeouts, duels_timeouts_duration], 'index'):
                    if duels.channel_current in duels.duels_dev_channels or duels.admin:
                        allowpass = 1
                    elif not duels.inchannel and len(duels_dev_channels) > 0:
                        allowpass = 1
                    else:
                        instigatorclasstime = duels_time_since(bot, duels.instigator, 'class_timeout')
                        osd(bot, duels.instigator, 'notice', "You may not change your class more than once per " + str(duels_hours_minutes_seconds((spicemanip.main(['class', duels_timeouts, duels_timeouts_duration], 'index') - 1))) + ". Please wait "+str(duels_hours_minutes_seconds((spicemanip.main(['class', duels_timeouts, duels_timeouts_duration], 'index') - instigatorclasstime)))+" to change.")
                        duels.command_stamina_cost = 0
                        return

        set_database_value(bot, targetbio.actual, charcommand, newset)
        if targetbio.actual != duels.instigator:
            osd(bot, duels.instigator, 'notice', targetbio.nametextpos + " "+charcommand+" is now set to " + newset + ".")
            osd(bot, targetbio.actual, 'notice', "Your "+charcommand+" is now set to " + newset + ".")
        else:
            osd(bot, targetbio.actual, 'notice', "Your "+charcommand+" is now set to " + newset + ".")
            if charcommand == 'class' and duels.channel_current not in duels.duels_dev_channels:
                set_database_value(bot, targetbio.actual, 'class_timeout', duels.now)
                if instigatorfreebie:
                    adjust_database_value(bot, duels.instigator, 'coin', -abs(spicemanip.main(['class', duels_ingame_coin_usage, duels_ingame_coin], 'index')))
                else:
                    set_database_value(bot, duels.instigator, 'class_freebie', 1)
        return


def duels_docs_character(bot):
    dispmsgarray = []
    dispmsgarray.append("This shows your character sheet.")
    return dispmsgarray


""" SPECIAL+M """


def duels_command_function_special(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Get The Command Used
    validstatcommands = ['combine']
    statcommand = spicemanip.main([x for x in duels.command_restructure if x in validstatcommands], 1) or 'view'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
    if target != duels.instigator:
        if not validtarget and not duels.admin:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    # Is the Tier Unlocked?
    duels.tiercommandeval = duels_tier_command_to_number(bot, command_main)
    duels.tierpepperrequired = duels_tier_number_to_pepper(bot, duels.tiercommandeval)
    if duels.tiercommandeval > 0 and targetbio.actual != duels.instigator and targetbio.actual != 'duelsmonster':
        tierpass = 0
        duels.tiermath = int(duels.tiercommandeval) - int(duels.currenttier)
        if duels.tiermath > 0:
            if duels.channel_current in duels.duels_dev_channels or duels.admin:
                tierpass = 1
            elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
                tierpass = 1
        else:
            tierpass = 1
        if not tierpass:
            osd(bot, duels.instigator, 'notice', "Stats for other players cannot be viewed until somebody reaches " + str(duels.tierpepperrequired.title()) + ". "+str(duels.tiermath) + " tier(s) remaining!")
            duels.command_stamina_cost = 0
            return

    if statcommand == 'combine':

        racecommand = spicemanip.main([x for x in duels.command_restructure if x in duels_character_valid_race], 1)
        if not racecommand:
            osd(bot, duels.instigator, 'notice', "you are missing race in the command.")
            return

        classcommand = spicemanip.main([x for x in duels.command_restructure if x in duels_character_valid_class], 1)
        if not classcommand:
            osd(bot, duels.instigator, 'notice', "you are missing class in the command.")
            return

        classstats = eval("duels_character_special_class_"+classcommand)
        racestats = eval("duels_character_special_race_"+racecommand)
        combinedarray = []
        combinedarray.append("The combination of " + racecommand + " and " + classcommand + " :")
        for statname, classstat, racestat in zip(duels_special_full, classstats, racestats):
            mathed = classstat + racestat
            currentvalue = str(statname.title()+"="+str(mathed))
            combinedarray.append(currentvalue)
        osd(bot, duels.channel_current, 'say', combinedarray)
    if statcommand == 'view':
        customview = 0
        target_stats_view = ['charsheet']
        for x in stats_character:
            target_stats_view.append(x)
        duels_stats_view(bot, duels, target_stats_view, targetbio, customview, 'character sheet')


def duels_docs_armor(bot):
    dispmsgarray = []
    dispmsgarray.append("This displays the current durability of any armor that you may possess.")
    return dispmsgarray


""" Stats View and admin control """


def duels_command_function_stats(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Get The Command Used
    validstatcommands = ['add', 'del', 'default', 'admin']
    statcommand = spicemanip.main([x for x in duels.command_restructure if x in validstatcommands], 1) or 'view'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan or x == 'everyone'], 1) or duels.instigator
    validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
    if target != duels.instigator:
        if not validtarget and not duels.admin:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    # Is the Tier Unlocked?
    duels.tiercommandeval = duels_tier_command_to_number(bot, command_main)
    duels.tierpepperrequired = duels_tier_number_to_pepper(bot, duels.tiercommandeval)
    if duels.tiercommandeval > 0 and targetbio.actual != duels.instigator and targetbio.actual != 'duelsmonster':
        tierpass = 0
        duels.tiermath = int(duels.tiercommandeval) - int(duels.currenttier)
        if duels.tiermath > 0:
            if duels.channel_current in duels.duels_dev_channels or duels.admin:
                tierpass = 1
            elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
                tierpass = 1
        else:
            tierpass = 1
        if not tierpass:
            osd(bot, duels.instigator, 'notice', "Stats for other players cannot be viewed until somebody reaches " + str(duels.tierpepperrequired.title()) + ". "+str(duels.tiermath) + " tier(s) remaining!")
            duels.command_stamina_cost = 0
            return

    if statcommand == 'add' or statcommand == 'del' or statcommand == 'default':

        if statcommand == 'default':
            reset_database_value(bot, targetbio.actual, 'stats_view')
            osd(bot, duels.instigator, 'notice', "Stats settings have been updated.")
            duels.command_stamina_cost = 0
            return
        if targetbio.actual in duels.command_restructure:
            duels.command_restructure.remove(targetbio.actual)
        duels.command_restructure.remove(statcommand)
        invalidstats = []
        for stat in duels.command_restructure:
            if stat not in duels.stats_valid and stat != 'health' and stat not in stats_character and stat != 'pepper' and stat != 'winlossratio' and stat != 'location':
                invalidstats.append(stat)
        if invalidstats != []:
            invalidstatslist = spicemanip.main(invalidstats, 'list')
            osd(bot, duels.instigator, 'notice', "the following stats are not valid: " + str(invalidstatslist))
            duels.command_stamina_cost = 0
            return
        adjust_database_array(bot, targetbio.actual, duels.command_restructure, 'stats_view', statcommand)
        osd(bot, duels.instigator, 'notice', "Stats settings have been updated.")
        duels.command_stamina_cost = 0
        return

    if statcommand == 'view':
        customview = 0
        target_stats_view = stats_view
        if targetbio.actual == duels.instigator:
            target_stats_view = get_database_value(bot, targetbio.actual, 'stats_view') or stats_view
            if target_stats_view != stats_view:
                customview = 1
        duels_stats_view(bot, duels, target_stats_view, targetbio, customview, command_main.lower())

    if statcommand == 'admin':

        if not duels.admin:
            osd(bot, duels.instigator, 'notice', "Stats cannot be adjusted for other players. (with the exception of bot admins.)")
            duels.command_stamina_cost = 0
            return

        statset = spicemanip.main([x for x in duels.command_restructure if x in duels.stats_valid], 1)
        if not statset:
            osd(bot, duels.instigator, 'notice', "Stat Missing.")
            duels.command_stamina_cost = 0
            return

        subcommand = spicemanip.main([x for x in duels.command_restructure if x == 'set' or x == 'reset'], 1)
        if not subcommand:
            osd(bot, duels.instigator, 'notice', "Set or Reset. ")
            duels.command_stamina_cost = 0
            return

        duels.command_restructure.remove(statcommand)
        if targetbio.actual in duels.command_restructure:
            duels.command_restructure.remove(targetbio.actual)
        duels.command_restructure.remove(statset)
        duels.command_restructure.remove(subcommand)
        newvalue = spicemanip.main(duels.command_restructure, 0) or 'None'
        if subcommand == 'set' and newvalue == 'None':
            osd(bot, duels.instigator, 'notice', "When using set, you must specify a value.")
            duels.command_stamina_cost = 0
            return
        if subcommand == 'reset':
            newvalue = 'None'
        if targetbio.actual == 'everyone':
            targets = []
            for u in duels.users_all_allchan:
                targets.append(u)
        else:
            targets = [targetbio.actual]
        for player in targets:
            try:
                if newvalue.isdigit():
                    newvalue = int(newvalue)
            except AttributeError:
                newvalue = newvalue
            if statset == 'all':
                for x in duels.stats_valid:
                    set_database_value(bot, player, x, newvalue)
            else:
                set_database_value(bot, player, statset, newvalue)
        osd(bot, duels.instigator, 'notice', "Possibly done Adjusting "+str(statset)+" stat(s) for "+str(targetbio.actual)+" to " + str(newvalue))


def duels_docs_stats(bot):
    dispmsgarray = []
    dispmsgarray.append("This provides a brief sysnopsis of your current condition.")
    return dispmsgarray


""" Health """


def duels_command_function_health(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Get The Command Used
    validstatcommands = []
    statcommand = spicemanip.main([x for x in duels.command_restructure if x in validstatcommands], 1) or 'view'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
    if target != duels.instigator:
        if not validtarget and not duels.admin:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    # Is the Tier Unlocked?
    duels.tiercommandeval = duels_tier_command_to_number(bot, command_main)
    duels.tierpepperrequired = duels_tier_number_to_pepper(bot, duels.tiercommandeval)
    if duels.tiercommandeval > 0 and targetbio.actual != duels.instigator and targetbio.actual != 'duelsmonster':
        tierpass = 0
        duels.tiermath = int(duels.tiercommandeval) - int(duels.currenttier)
        if duels.tiermath > 0:
            if duels.channel_current in duels.duels_dev_channels or duels.admin:
                tierpass = 1
            elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
                tierpass = 1
        else:
            tierpass = 1
        if not tierpass:
            osd(bot, duels.instigator, 'notice', "Stats for other players cannot be viewed until somebody reaches " + str(duels.tierpepperrequired.title()) + ". "+str(duels.tiermath) + " tier(s) remaining!")
            duels.command_stamina_cost = 0
            return

    if statcommand == 'view':
        customview = 0
        target_stats_view = ['health']
        for x in duels_bodyparts:
            target_stats_view.append(x)
        duels_stats_view(bot, duels, target_stats_view, targetbio, customview, command_main.lower())


def duels_docs_health(bot):
    dispmsgarray = []
    dispmsgarray.append("This displays a detailed look at each bodyparts current status.")
    return dispmsgarray


""" Streaks """


def duels_command_function_streaks(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Get The Command Used
    validstatcommands = []
    statcommand = spicemanip.main([x for x in duels.command_restructure if x in validstatcommands], 1) or 'view'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
    if target != duels.instigator:
        if not validtarget and not duels.admin:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    # Is the Tier Unlocked?
    duels.tiercommandeval = duels_tier_command_to_number(bot, command_main)
    duels.tierpepperrequired = duels_tier_number_to_pepper(bot, duels.tiercommandeval)
    if duels.tiercommandeval > 0 and targetbio.actual != duels.instigator and targetbio.actual != 'duelsmonster':
        tierpass = 0
        duels.tiermath = int(duels.tiercommandeval) - int(duels.currenttier)
        if duels.tiermath > 0:
            if duels.channel_current in duels.duels_dev_channels or duels.admin:
                tierpass = 1
            elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
                tierpass = 1
        else:
            tierpass = 1
        if not tierpass:
            osd(bot, duels.instigator, 'notice', "Stats for other players cannot be viewed until somebody reaches " + str(duels.tierpepperrequired.title()) + ". "+str(duels.tiermath) + " tier(s) remaining!")
            duels.command_stamina_cost = 0
            return

    if statcommand == 'view':
        customview = 0
        target_stats_view = ['streak_type_current', 'streak_win_best', 'streak_loss_best']
        duels_stats_view(bot, duels, target_stats_view, targetbio, customview, command_main.lower())


def duels_docs_streaks(bot):
    dispmsgarray = []
    dispmsgarray.append("This shows your current winning/losing streak. A streak is more than 2 in a row.")
    return dispmsgarray


""" Loot """


def duels_command_function_loot(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Get The Command Used
    validstatcommands = ['use']
    statcommand = spicemanip.main([x for x in duels.command_restructure if x in validstatcommands], 1) or 'view'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
    if target != duels.instigator:
        if not validtarget and not duels.admin:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    # Is the Tier Unlocked?
    duels.tiercommandeval = duels_tier_command_to_number(bot, command_main)
    duels.tierpepperrequired = duels_tier_number_to_pepper(bot, duels.tiercommandeval)
    if duels.tiercommandeval > 0 and targetbio.actual != duels.instigator and targetbio.actual != 'duelsmonster':
        tierpass = 0
        duels.tiermath = int(duels.tiercommandeval) - int(duels.currenttier)
        if duels.tiermath > 0:
            if duels.channel_current in duels.duels_dev_channels or duels.admin:
                tierpass = 1
            elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
                tierpass = 1
        else:
            tierpass = 1
        if not tierpass:
            osd(bot, duels.instigator, 'notice', "Stats for other players cannot be viewed until somebody reaches " + str(duels.tierpepperrequired.title()) + ". "+str(duels.tiermath) + " tier(s) remaining!")
            duels.command_stamina_cost = 0
            return

    if statcommand == 'view':
        customview = 0
        target_stats_view = duels_loot_view
        duels_stats_view(bot, duels, target_stats_view, targetbio, customview, command_main.lower())

    if statcommand == 'use':

        # plural loot
        plural_loot = []
        for item in duels_loot_items:
            itemname = str(item+"s")
            plural_loot.append(itemname)

        # Main transaction item
        lootitem = spicemanip.main([x for x in duels.command_restructure if x in duels_loot_items or x in plural_loot], 1)
        if not lootitem:
            osd(bot, duels.instigator, 'notice', "What do you want to " + str(statcommand) + "?")
            duels.command_stamina_cost = 0
            return

        # The quantity the player is applyint to this transaction
        gethowmanylootitem = get_database_value(bot, duels.instigator, lootitem) or 0
        quantity = spicemanip.main([x for x in duels.command_restructure if x == 'all' or str(x).isdigit()], 1) or 1
        if quantity == 'all':
            quantity = gethowmanylootitem

        if lootitem in plural_loot:
            for loots in duels_loot_items:
                similarlevel = similar(lootitem.lower(), loots)
                if similarlevel >= .90:
                    lootitem = loots
            if quantity == 1:
                quantity = 2

        # How many of that item
        if not gethowmanylootitem:
            osd(bot, duels.instigator, 'notice', "You do not have any " + lootitem + "!")
            duels.command_stamina_cost = 0
            return

        # Block for if the quantity above is greater than the players inventory
        if int(quantity) > int(gethowmanylootitem):
            osd(bot, duels.instigator, 'notice', "You do not have enough " + lootitem + " to use this command! You only have " + str(gethowmanylootitem) + ".")
            duels.command_stamina_cost = 0
            return

        # Stimpacks are only usable via the health command
        if lootitem == 'stimpack':
            mainlootusemessage = []

            potionworth = spicemanip.main(['stimpack', duels_loot_items, duels_loot_worth], 'index')
            potionmaths = int(quantity) * potionworth

            # Select a body part
            bodypartselect = spicemanip.main([x for x in duels.command_restructure if x in duels_bodyparts], 1) or 'list'
            if bodypartselect not in duels_bodyparts:
                bodypartlist = spicemanip.main(duels_bodyparts, 'list')
                osd(bot, duels.instigator, 'notice', "Select a valid body part to apply the stimpack to. Valid options: " + bodypartlist)
                duels.command_stamina_cost = 0
                return

            # Health Maximum and status
            maxbodyparthealth = spicemanip.main([bodypartselect, duels_bodyparts, duels_bodyparts_health], 'index')
            maxbodyparthealth = maxbodyparthealth * duels.tierscaling
            currentbodyparthealth = get_database_value(bot, targetbio.actual, bodypartselect)

            # If already at max health. don't use
            if currentbodyparthealth >= maxbodyparthealth:
                osd(bot, duels.instigator, 'notice', "It appears your " + bodypartselect + " is at max health.")
                duels.command_stamina_cost = 0
                return

            quantity = int(quantity)

            adjust_database_value(bot, targetbio.actual, 'stimpack', -abs(quantity))

            potionworth = spicemanip.main(['stimpack', duels_loot_items, duels_loot_worth], 'index')
            potionmaths = int(quantity) * potionworth

            if int(quantity) == 1:
                mainlootusemessage.append(targetbio.nametext + " uses a stimpack to heal " + bodypartselect + " Results:")
            else:
                mainlootusemessage.append(targetbio.nametext + " uses "+str(quantity)+" stimpacks to heal " + bodypartselect + " Results:")

            damageinflictarray = duels_effect_inflict(bot, duels,  targetbio, targetbio, bodypartselect,  'damage', -abs(potionmaths), 'loot')
            for k in damageinflictarray:
                mainlootusemessage.append(k)
            osd(bot, duels.channel_current, 'say', mainlootusemessage)

            return

        # Redirect to the grenade command
        elif lootitem == 'grenade':
            duels_command_function_grenade(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio)
            return

        # Timepotions are no good in quantities over 1
        if lootitem == 'timepotion' or lootitem in duels_loot_stat_modifiers:
            quantity = 1

        # Sometimes if this isn't set, the game throws errors about strings or unicode
        quantity = int(quantity)

        # charge the cost
        adjust_database_value(bot, duels.instigator, lootitem, -abs(quantity))

        # Empty settings
        mainlootusemessage, uselootarray, extramsg = [], [], []

        # Display based on target and quantity
        if targetbio.actual == duels.instigator:
            if int(quantity) == 1:
                mainlootusemessage.append(duels.instigator + ' uses a ' + lootitem)
            else:
                mainlootusemessage.append(duels.instigator + ' uses ' + str(quantity) + " " + lootitem + 's')
        else:
            if int(quantity) == 1:
                mainlootusemessage.append(duels.instigator + ' uses a ' + lootitem + ' on ' + targetbio.nametext)
            else:
                mainlootusemessage.append(duels.instigator + " used " + str(quantity) + " " + lootitem + "s on " + targetbio.nametext)

        lootusing = class_create('loot_use')
        for x in loot_use_effects:
            currentvalue = str("lootusing."+x+"=0")
            exec(currentvalue)

        # If not mysterypotion, apply the potion quickly
        uniquelootitems, uniquecount = [], []
        if lootitem != 'mysterypotion':
            uniquelootitems, uniquecount = [lootitem], [quantity]
        else:

            # Build a list of potions, randomly
            while int(quantity) > 0:
                quantity = int(quantity) - 1
                loot = spicemanip.main(duels_loot_potion_types, 'random')
                if loot == 'mysterypotion':
                    loot = spicemanip.main(duels_loot_null, 'random')
                uselootarray.append(loot)

            # Build baseline of how we will display what potions were used
            actualpotionmathedarray = []
            for lootuse in uselootarray:
                if lootuse not in uniquelootitems:
                    uniquelootitems.append(lootuse)
            for uniqueloot in uniquelootitems:
                currentnumber = countX(uselootarray, uniqueloot)
                uniquecount.append(currentnumber)
            for uloot, unumber in zip(uniquelootitems, uniquecount):
                if unumber > 1:
                    actualpotionmathedarray.append(str(str(unumber) + " "+uloot + "s"))
                else:
                    actualpotionmathedarray.append(uloot)

            postionsusedarray = spicemanip.main(actualpotionmathedarray, "list")
            mainlootusemessage.append("Potion(s) used: " + postionsusedarray)

        for uloot, unumber in zip(uniquelootitems, uniquecount):
            lootusing, mainlootusemessage = duels_use_loot_item(bot, duels, instigatorbio, targetbio, uloot, unumber, mainlootusemessage, lootusing)
        for x in loot_use_effects:
            currenteval = eval("lootusing."+x)
            if currenteval != 0:
                effectinflictarray = duels_effect_inflict(bot, duels,  instigatorbio, targetbio, 'all',  x, currenteval, 'loot')
                for k in effectinflictarray:
                    mainlootusemessage.append(k)

        # Display to player/target in privmsg if command issued in privmsg, otherwise in channel
        osd(bot, duels.channel_current, 'say', mainlootusemessage)
        if targetbio.actual != duels.instigator and not duels.inchannel:
            osd(bot, targetbio.actual, 'notice', mainlootusemessage)


def duels_docs_loot(bot):
    dispmsgarray = []
    dispmsgarray.append("This shows the items you currently possess and can use. You may also buy, sell, these items with the ingame store.")
    return dispmsgarray


""" Armor """


def duels_command_function_armor(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Get The Command Used
    validstatcommands = []
    statcommand = spicemanip.main([x for x in duels.command_restructure if x in validstatcommands], 1) or 'view'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
    if target != duels.instigator:
        if not validtarget and not duels.admin:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    # Is the Tier Unlocked?
    duels.tiercommandeval = duels_tier_command_to_number(bot, command_main)
    duels.tierpepperrequired = duels_tier_number_to_pepper(bot, duels.tiercommandeval)
    if duels.tiercommandeval > 0 and targetbio.actual != duels.instigator and targetbio.actual != 'duelsmonster':
        tierpass = 0
        duels.tiermath = int(duels.tiercommandeval) - int(duels.currenttier)
        if duels.tiermath > 0:
            if duels.channel_current in duels.duels_dev_channels or duels.admin:
                tierpass = 1
            elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
                tierpass = 1
        else:
            tierpass = 1
        if not tierpass:
            osd(bot, duels.instigator, 'notice', "Stats for other players cannot be viewed until somebody reaches " + str(duels.tierpepperrequired.title()) + ". "+str(duels.tiermath) + " tier(s) remaining!")
            duels.command_stamina_cost = 0
            return

    if statcommand == 'view':
        customview = 0
        target_stats_view = stats_armor
        duels_stats_view(bot, duels, target_stats_view, targetbio, customview, command_main.lower())


def duels_docs_armor(bot):
    dispmsgarray = []
    dispmsgarray.append("This displays the current durability of any armor that you may possess.")
    return dispmsgarray


""" Opt in and out of the game """


def duels_command_function_opt(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # is the opt in or out
    directionchange = spicemanip.main([x for x in triggerargsarray if x in duels_commands_alternate_opt], 1)
    if not directionchange:
        osd(bot, duels.channel_current, 'say', "Do you want to play duels or not?")
        duels.command_stamina_cost = 0
        return
    if directionchange in opt_enable_array:
        directionchange = 'on'
    else:
        directionchange = 'off'

    # Who is opting in/out
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan or x == 'everyone'], 1) or duels.instigator
    if target != duels.instigator and target != duels.channel_current:
        duels.optcheck = 0
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
    if target != 'everyone':
        targetbio = duel_target_playerbio(bot, duels, target)
    elif target == duels.instigator:
        targetbio = instigatorbio
    else:
        targetbio = duel_target_playerbio(bot, duels, target)

    # check target, admins can change other players opt
    if target != duels.instigator:
        if target == 'all' or target == 'everyone':
            if not duels.admin:
                if directionchange == 'on':
                    osd(bot, duels.duels_enabled_channels, 'say', duels.instigator + " thinks everybody should play duels!")
                else:
                    osd(bot, duels.duels_enabled_channels, 'say', duels.instigator + " thinks everybody should stop playing duels!")
            else:
                if directionchange == 'on':
                    osd(bot, duels.duels_enabled_channels, 'say', duels.instigator + " enabled duels for everyone!")
                    adjust_database_array(bot, 'duelrecorduser', duels.users_all_allchan, 'users_opted_allchan', 'add')
                else:
                    osd(bot, duels.duels_enabled_channels, 'say', duels.instigator + " disabled duels for everyone!")
                    reset_database_value(bot, 'duelrecorduser', 'users_opted_allchan')
            duels.command_stamina_cost = 0
            return
        if directionchange == 'on':
            if targetbio.actual.lower() in [x.lower() for x in duels.users_opted]:
                if targetbio.actual != duels.instigator:
                    osd(bot, duels.instigator, 'notice', "It looks like " + targetbio.nametext + " already has duels on.")
                else:
                    osd(bot, duels.instigator, 'notice', "It looks like you already have duels on.")
                duels.command_stamina_cost = 0
                return
        if directionchange == 'off':
            if targetbio.actual.lower() not in [x.lower() for x in duels.users_opted]:
                if targetbio.actual != duels.instigator:
                    osd(bot, duels.instigator, 'notice', "It looks like " + targetbio.nametext + " already has duels off.")
                else:
                    osd(bot, duels.instigator, 'notice', "It looks like you already have duels off.")
                duels.command_stamina_cost = 0
                return

        # Reason provided
        reasonmessage = spicemanip.main(triggerargsarray, '3+')
        if not reasonmessage:
            if not duels.admin:
                osd(bot, duels.instigator, 'notice', "if you would like " + targetbio.nametext + " to turn duels "+directionchange+", you can run this command along with a message, that they will get privately.")
            else:
                osd(bot, duels.instigator, 'notice', "you must include a message to send to " + targetbio.nametext + " as to why you are changing their opt-in status to "+directionchange+".")
            duels.command_stamina_cost = 0
            return
        else:
            if duels.admin:
                osd(bot, targetbio.actual, 'notice', duels.instigator + " turned duels " + directionchange + " for you for the following reason: " + str(reasonmessage) + ".")
            else:
                osd(bot, targetbio.actual, 'notice', duels.instigator + " thinks you should duels " + directionchange + " for the following reason: " + str(reasonmessage) + ".")
                duels.command_stamina_cost = 0
                return

    # User can't toggle status all the time
    targetopttime = duels_time_since(bot, target, 'timeout_opttimetime')
    if targetopttime < spicemanip.main(['opttime', duels_timeouts, duels_timeouts_duration], 'index'):
        if duels.channel_current in duels.duels_dev_channels or duels.admin:
            allowpass = 1
        elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
            allowpass = 1
        elif duels.admin and targetbio.actual != duels.instigator:
            allowpass = 1
        else:
            osd(bot, duels.instigator, 'notice', "It looks like you can't enable/disable duels for " + str(duels_hours_minutes_seconds((spicemanip.main(['opttime', duels_timeouts, duels_timeouts_duration], 'index') - targetopttime))) + ".")
            duels.command_stamina_cost = 0
            return

    # check if player already has duels on/off
    if directionchange == 'on':
        if targetbio.actual.lower() in [x.lower() for x in duels.users_opted] and targetbio.actual == duels.instigator:
            if targetbio.actual == duels.instigator:
                osd(bot, duels.instigator, 'notice', "It looks like you already have duels on.")
            else:
                osd(bot, duels.instigator, 'notice', "It looks like " + targetbio.nametext + " already has duels on.")
            duels.command_stamina_cost = 0
            return
    else:
        if targetbio.actual.lower() not in [x.lower() for x in duels.users_opted] and targetbio.actual == duels.instigator:
            if targetbio.actual == duels.instigator:
                osd(bot, duels.instigator, 'notice', "It looks like you already have duels off.")
            else:
                osd(bot, duels.instigator, 'notice', "It looks like " + targetbio.nametext + " already has duels off.")
            duels.command_stamina_cost = 0
            return

    # make the adjustment
    if directionchange == 'on':
        adjust_database_array(bot, 'duelrecorduser', [targetbio.actual], 'users_opted_allchan', 'add')
        set_database_value(bot, targetbio.actual, 'timeout_opttimetime', duels.now)
    else:
        adjust_database_array(bot, 'duelrecorduser', [targetbio.actual], 'users_opted_allchan', 'del')
    if targetbio.actual == duels.instigator:
        osd(bot, duels.instigator, 'notice', "Duels should now be " + directionchange + " for you.")
    elif targetbio.actual != duels.instigator and duels.admin:
        osd(bot, duels.instigator, 'notice', "Duels should now be " + directionchange + " for " + targetbio.nametext + ".")

    # Anounce to channels
    dispmsgarray = []
    targetlocation = duels_get_location(bot, duels, targetbio.actual)
    if targetlocation == 'arena':
        if targetbio.actual != duels.instigator:
            if directionchange == 'on':
                dispmsgarray.append(targetbio.nametext + " has entered the arena!")
            else:
                dispmsgarray.append(targetbio.nametext + " has left the arena! ")
        else:
            if directionchange == 'on':
                dispmsgarray.append(targetbio.nametext + " has entered the arena!")
            else:
                cowardterm = spicemanip.main(cowardarray, 'random')
                dispmsgarray.append(targetbio.nametext + " has left the arena! " + cowardterm)
        osd(bot, duels.duels_enabled_channels, 'say', dispmsgarray)


def duels_docs_opt(bot):
    dispmsgarray = []
    dispmsgarray.append("This opts you in/out.")
    dispmsgarray.append("Your opt status will announce to the channel. You can also use this command to have the bot primsg a nick to tell somebody join the fun.")
    return dispmsgarray


""" Location """


def duels_command_function_location(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    newlocation = spicemanip.main([x for x in duels.command_restructure if x in duels_commands_locations], 1) or 'view'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
    if not validtarget and not duels.admin:
        osd(bot, duels.instigator, 'notice', validtargetmsg)
        duels.command_stamina_cost = 0
        return
    if target != duels.instigator:
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio
    if targetbio.actual != duels.instigator and not duels.admin and newlocation != 'view':
        osd(bot, duels.instigator, 'notice', "You cannot make other players move location.")
        duels.command_stamina_cost = 0
        return

    targetlocation = duels_get_location(bot, duels, targetbio.actual)

    if newlocation == 'view':
        valid_locations = spicemanip.main(duels_commands_locations, "list")
        if targetbio.actual == duels.instigator:
            osd(bot, duels.instigator, 'notice',  "You are currently located at the " + targetlocation + " area. You may run   .duel location $location    to move your player. Valid locations are: " + valid_locations)
        else:
            osd(bot, duels.channel_current, 'say',  targetbio.nametext + " is currently located at the " + targetlocation + " area.")
        duels.command_stamina_cost = 0
        return

    if newlocation == targetlocation:
        if targetbio.actual == duels.instigator:
            osd(bot, duels.instigator, 'notice', "Your location is already "+targetlocation+".")
        else:
            osd(bot, duels.instigator, 'notice', targetbio.nametextpos+" location is already "+targetlocation+".")
        duels.command_stamina_cost = 0
        return

    # Stamina Check
    staminapass, stamina, duels.command_stamina_cost = duels_stamina_check(bot, duels.instigator, command_main.lower(), duels)
    if not staminapass and command_main.lower() != 'location':
        osd(bot, duels.instigator, 'notice', "You do not have enough stamina to perform duel " + command_main.lower())
        return

    duels_location_move(bot, duels, targetbio.actual, newlocation)
    if duels.instigator == targetbio.actual:
        osd(bot, duels.instigator, 'notice', "You have moved from the " + targetlocation + " area to the " + newlocation + " area.")
    else:
        osd(bot, targetbio.actual, 'notice', "You have moved from the " + targetlocation + " area to the " + newlocation + " area.")
    dispmsgarray = []
    if newlocation == 'arena':
        dispmsgarray.append(targetbio.nametext + " has entered the arena!")
    else:
        if targetlocation == 'arena' and newlocation != 'arena':
            cowardterm = spicemanip.main(cowardarray, 'random')
            dispmsgarray.append(targetbio.nametext + " has left the arena! " + cowardterm)
    if dispmsgarray != []:
        osd(bot, duels.duels_enabled_channels, 'say', dispmsgarray)


def duels_docs_location(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to travel between game locations.")
    return dispmsgarray


""" Suicide/harakiri """


def duels_command_function_harakiri(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    if target != duels.instigator:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
    if target != duels.instigator:
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    confirm = spicemanip.main([x for x in duels.command_restructure if x == 'confirm'], 1) or 0
    if not confirm:
        osd(bot, duels.channel_current, 'say', "You must run this command with 'confirm' to kill yourself. No rewards are given in to cowards.")
        duels.command_stamina_cost = 0
        return

    if targetbio.actual != duels.instigator:
        if not duels.admin:
            osd(bot, duels.channel_current, 'say', "You can't suicide other people. It's called Murder.")
            duels.command_stamina_cost = 0
            return

    suicidetextarray = duels_death_handling(bot, duels, targetbio, targetbio)
    osd(bot, duels.channel_current, 'say', suicidetextarray)


def duels_docs_template(bot):
    dispmsgarray = []
    dispmsgarray.append("This is a suicide command. You will lose all your items and respawn.")
    dispmsgarray.append("Usage: You must Confirm this command.")
    return dispmsgarray


""" Title """


def duels_command_function_title(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    if target != duels.instigator:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
    if target != duels.instigator:
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    if targetbio.actual != duels.instigator:
        if not duels.admin:
            osd(bot, duels.channel_current, 'say', "You can't change other people's titles.")
            duels.command_stamina_cost = 0
            return

    if targetbio.actual in duels.command_restructure:
        duels.command_restructure.remove(targetbio.actual)
    titletoset = spicemanip.main(duels.command_restructure, 0)
    if not titletoset:
        if targetbio.actual != duels.instigator:
            osd(bot, duels.instigator, 'notice', "What do you want "+targetbio.nametextpos+" your title to be?")
        else:
            osd(bot, duels.instigator, 'notice', "What do you want your title to be?")
        duels.command_stamina_cost = 0
        return

    if titletoset == 'remove':
        reset_database_value(bot, targetbio.actual, 'title')
        if targetbio.actual != duels.instigator:
            osd(bot, duels.instigator, 'notice', targetbio.nametextpos+" title has been removed.")
        else:
            osd(bot, duels.instigator, 'notice', "Your title has been removed.")
        duels.command_stamina_cost = 0
        return

    if targetbio.actual != duels.instigator:
        instigatorcoin = get_database_value(bot, duels.instigator, 'coin') or 0
        if instigatorcoin < spicemanip.main(['title', duels_ingame_coin_usage, duels_ingame_coin], 'index'):
            osd(bot, duels.instigator, 'notice', "Changing your title costs " + str(spicemanip.main(['title', duels_ingame_coin_usage, duels_ingame_coin], 'index')) + " coin. You need more funding.")
            duels.command_stamina_cost = 0
            return
        if len(titletoset) > 10:
            osd(bot, duels.instigator, 'notice', "Purchased titles can be no longer than 10 characters.")
            duels.command_stamina_cost = 0
            return
        adjust_database_value(bot, duels.instigator, 'coin', -abs(spicemanip.main(['title', duels_ingame_coin_usage, duels_ingame_coin], 'index')))

    set_database_value(bot, targetbio.actual, 'title', titletoset)
    if targetbio.actual != duels.instigator:
        osd(bot, duels.instigator, 'notice', targetbio.nametextpos+" title is now " + titletoset + ".")
    else:
        osd(bot, duels.instigator, 'notice', "Your title is now " + titletoset + ".")


def duels_docs_title(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to set a vanity title in front of your nick during combat.")
    return dispmsgarray


""" Weaponslocker """


def duels_command_function_weaponslocker(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    validdirectionarray = ['total', 'inv', 'add', 'del', 'reset']
    adjustmentdirection = spicemanip.main([x for x in duels.command_restructure if x in validdirectionarray], 1)
    if not adjustmentdirection:
        osd(bot, duels.instigator, 'notice', "Use .duel weaponslocker add/del to adjust Locker Inventory.")
        duels.command_stamina_cost = 0
        return
    duels.command_restructure.remove(adjustmentdirection)

    # Who is the target
    if adjustmentdirection == 'add' or adjustmentdirection == 'del':
        target = duels.instigator
    else:
        target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    if target != duels.instigator:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
    if target in duels.command_restructure:
        duels.command_restructure.remove(target)
    if target != duels.instigator:
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    weaponslist = get_database_value(bot, targetbio.actual, 'weaponslocker_complete') or []

    if adjustmentdirection == 'total':
        osd(bot, duels.channel_current, 'say', targetbio.nametext + ' has ' + str(len(weaponslist)) + " weapons in their locker. They Can be viewed in privmsg by running .duel weaponslocker inv .")
        duels.command_stamina_cost = 0
        return

    if adjustmentdirection == 'inv':
        if weaponslist == []:
            osd(bot, duels.instigator, 'notice', "There doesnt appear to be anything in the weapons locker! Use .duel weaponslocker add/del to adjust Locker Inventory.")
            duels.command_stamina_cost = 0
            return
        osd(bot, duels.instigator, 'say', spicemanip.main(weaponslist, 'list'))
        duels.command_stamina_cost = 0
        return

    if targetbio.actual != duels.instigator and not duels.admin:
        osd(bot, duels.instigator, 'notice', "You may not adjust somebody elses locker.")
        duels.command_stamina_cost = 0
        return

    if adjustmentdirection == 'reset':
        reset_database_value(bot, targetbio.actual, 'weaponslocker_complete')
        osd(bot, duels.instigator, 'notice', "Locker Reset.")
        duels.command_stamina_cost = 0
        return

    weaponchange = spicemanip.main(duels.command_restructure, 0)
    if not weaponchange:
        osd(bot, duels.instigator, 'notice', "What weapon would you like to add/remove?")
        duels.command_stamina_cost = 0
        return

    if adjustmentdirection == 'add' and weaponchange in weaponslist:
        osd(bot, duels.instigator, 'notice', weaponchange + " is already in weapons locker.")
        duels.command_stamina_cost = 0
        return

    if adjustmentdirection == 'del' and weaponchange not in weaponslist:
        osd(bot, duels.instigator, 'notice', weaponchange + " is already not in weapons locker.")
        duels.command_stamina_cost = 0
        return

    if adjustmentdirection == 'add' and len(weaponchange) > weapon_name_length:
        osd(bot, duels.instigator, 'notice', "That weapon exceeds the character limit of "+str(weapon_name_length)+".")
        duels.command_stamina_cost = 0
        return

    if adjustmentdirection == 'add':
        for word in duels.command_restructure:
            if word.lower() in [x.lower() for x in duels.users_all_allchan] or word.lower() in [str(x.lower()+"s") for x in duels.users_all_allchan] or word.lower() in [str(x.lower()+"'s") for x in duels.users_all_allchan]:
                osd(bot, duels.instigator, 'notice', "Weapons may not include user nicks.")
                duels.command_stamina_cost = 0
                return

    if adjustmentdirection == 'add':
        weaponlockerstatus = 'now'
    else:
        weaponlockerstatus = 'no longer'

    adjust_database_array(bot, targetbio.actual, [weaponchange], 'weaponslocker_complete', adjustmentdirection)
    osd(bot, duels.instigator, 'notice', weaponchange + " is " + weaponlockerstatus + " in your weapons locker.")


def duels_docs_weaponslocker(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to add, remove, and view items in your weapons locker. These weapon names are included in combat, and provide a boost for having.")
    return dispmsgarray


"""
Town Vendor Commands
"""


""" Forge """


def duels_command_function_forge(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):
    armors = spicemanip.main(stats_armor, 'list')

    subcommand = spicemanip.main([x for x in duels.command_restructure if x in duels_forge_transaction_types], 1) or 'view'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    if target != duels.instigator:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        if subcommand != 'view' and not duels.admin:
            osd(bot, duels.instigator, 'notice', "you cannot adjust armor for other players.")
            duels.command_stamina_cost = 0
            return
    if target != duels.instigator:
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    if subcommand != 'view':
        typearmor = spicemanip.main([x for x in duels.command_restructure if x in stats_armor or x == 'all'], 1)
        if not typearmor:
            osd(bot, duels.channel_current, 'say', "What type of armor do you wish to " + subcommand + "? Options are: " + armors + ".")
            duels.command_stamina_cost = 0
            return

    if subcommand == 'view':  # TODO add max like in health
        merchantarray = []  # TODO track loot usage by players and create supply vs demand
        for armor in stats_armor:
            merchantarray.append(armor + "="+str(armor_cost))
        merchantstock = spicemanip.main(merchantarray, 'list')
        osd(bot, duels.channel_current, 'say',  "Forge Supply (item=coin-cost): " + merchantstock)
        duels.command_stamina_cost = 0
        return

    if subcommand == 'buy':
        if typearmor != 'all':
            getarmor = get_database_value(bot, targetbio.actual, typearmor) or 0
            if getarmor and getarmor > 0:
                osd(bot, duels.channel_current, 'say', "It looks like you already have a " + typearmor + ".")
                duels.command_stamina_cost = 0
                return
            armorcommandarray = [typearmor]
            costinvolved = armor_cost
        else:
            armorcommandarray = []
            for armor in stats_armor:
                getarmor = get_database_value(bot, target, armor) or 0
                if not getarmor or getarmor <= 0:
                    armorcommandarray.append(armor)
            costinvolved = armor_cost * len(armorcommandarray)
        if armorcommandarray == []:
            osd(bot, duels.channel_current, 'say', "Looks like you don't have any armor to " + subcommand + ".")
            duels.command_stamina_cost = 0
            return
        if targetbio.actual != duels.instigator:
            if targetbio.Class == 'blacksmith':
                costinvolved = costinvolved * armor_cost_blacksmith_cut
                costinvolved = int(costinvolved)
                if targetbio.coin < costinvolved:
                    osd(bot, duels.channel_current, 'say', "Insufficient Funds.")
                    duels.command_stamina_cost = 0
                    return
                adjust_database_value(bot, targetbio.actual, 'coin', -abs(costinvolved))
        osd(bot, duels.channel_current, 'say', targetbio.nametext + " bought " + typearmor + " for " + str(costinvolved) + " coins.")
        for armorscom in armorcommandarray:
            set_database_value(bot, targetbio.actual, armorscom, armor_durability)
        duels.command_stamina_cost = 0
        return

    elif subcommand == 'sell':
        if typearmor != 'all':
            getarmor = get_database_value(bot, targetbio.actual, typearmor) or 0
            if not getarmor:
                osd(bot, duels.channel_current, 'say', "You don't have a " + typearmor + " to sell.")
                duels.command_stamina_cost = 0
                return
            if getarmor < 0:
                osd(bot, duels.channel_current, 'say', "Your armor is too damaged to sell.")
                reset_database_value(bot, targetbio.actual, typearmor)
                duels.command_stamina_cost = 0
                return
            armorcommandarray = [typearmor]
            durabilityremaining = getarmor / armor_durability
        else:
            armorcommandarray = []
            durabilityremaininga = 0
            for armor in stats_armor:
                getarmor = get_database_value(bot, targetbio.actual, armor) or 0
                if getarmor and getarmor > 0:
                    armorcommandarray.append(armor)
                    durabilityremaininga = getarmor + durabilityremaininga
            durabilityremainingmax = len(armorcommandarray) * armor_durability
            durabilityremaining = durabilityremaininga / durabilityremainingmax
        if armorcommandarray == []:
            osd(bot, duels.channel_current, 'say', "Looks like you don't have any armor to " + subcommand + ".")
            duels.command_stamina_cost = 0
            return
        sellingamount = durabilityremaining * armor_cost
        if targetbio.Class == 'blacksmith':
            sellingamount = sellingamount * armor_sell_blacksmith_cut
        sellingamount = int(sellingamount)
        osd(bot, duels.channel_current, 'say', "Selling " + typearmor + " armor earned you " + str(sellingamount) + " coins.")
        if targetbio.actual != duels.instigator:
            adjust_database_value(bot, targetbio.actual, 'coin', sellingamount)
        for armorscom in armorcommandarray:
            reset_database_value(bot, targetbio.actual, armorscom)
        duels.command_stamina_cost = 0
        return

    elif subcommand == 'repair':
        if typearmor != 'all':
            getarmor = get_database_value(bot, targetbio.actual, typearmor) or 0
            if not getarmor:
                osd(bot, duels.channel_current, 'say', "You don't have a " + typearmor + " to repair.")
                duels.command_stamina_cost = 0
                return
            durabilitycompare = armor_durability
            if targetbio.Class == 'blacksmith':
                durabilitycompare = armor_durability_blacksmith
            if getarmor >= durabilitycompare:
                osd(bot, duels.channel_current, 'say', "It looks like your armor does not need repair.")
                duels.command_stamina_cost = 0
                return
            durabilitytorepair = durabilitycompare - getarmor
        else:
            armorcommandarray = []  # TODO repair all is broken
            durabilityremaininga = 0
            for armor in stats_armor:
                getarmor = get_database_value(bot, targetbio.actual, armor) or 0
                if getarmor and getarmor > 0:
                    durabilitycompare = armor_durability
                    if targetbio.Class == 'blacksmith':
                        durabilitycompare = armor_durability_blacksmith
                    if getarmor < durabilitycompare:
                        armorcommandarray.append(armor)
                        durabilityremaininga = getarmor + durabilityremaininga
            durabilitycompare = len(armorcommandarray) * armor_durability
            if targetbio.Class == 'blacksmith':
                durabilitycompare = len(armorcommandarray) * armor_durability_blacksmith
            durabilitytorepair = durabilitycompare - durabilityremaininga
        if armorcommandarray == []:
            osd(bot, duels.channel_current, 'say', "Looks like you don't have any armor to " + subcommand + ".")
            duels.command_stamina_cost = 0
            return
        if targetbio.actual != duels.instigator:
            costinvolved = durabilitytorepair / durabilitycompare
            costinvolved = costinvolved * armor_cost
            costinvolved = costinvolved * armor_repair_cost
            if targetbio.Class == 'blacksmith':
                costinvolved = costinvolved * armor_cost_blacksmith_cut
                costinvolved = int(costinvolved)
            if targetbio.coin < costinvolved:
                osd(bot, duels.channel_current, 'say', "Insufficient Funds.")
                duels.command_stamina_cost = 0
                return
            adjust_database_value(bot, targetbio.actual, 'coin', -abs(costinvolved))
            osd(bot, duels.channel_current, 'say', "Repairing " + typearmor + " armor for " + str(costinvolved)+" coins.")
        else:
            osd(bot, duels.channel_current, 'say', "Repairing " + typearmor + " armor.")
        for armorscom in armorcommandarray:
            set_database_value(bot, targetbio.actual, armorscom, armor_durability)
        duels.command_stamina_cost = 0
        return


def duels_docs_forge(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to purchase armor.")
    return dispmsgarray


""" Merchant """


def duels_command_function_merchant(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Get The Command Used
    lootcommand = spicemanip.main([x for x in duels.command_restructure if x in duels_merchant_transaction_types], 1) or 'view'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    if target != duels.instigator:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        if not duels.admin:
            osd(bot, duels.instigator, 'notice', "you cannot adjust loot for other players.")  # TODO admin
            duels.command_stamina_cost = 0
            return
    if target != duels.instigator:
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    merchinv = duels_merchant_inventory(bot)

    # View target/own inventory
    if lootcommand == 'view':

        merchantarray = []  # TODO track loot usage by players and create supply vs demand
        merchantarray.append("Merchant's Supply: ")
        for lootitem in duels_loot_items:
            current_loot_cost = spicemanip.main([lootitem, duels_loot_items, duels_loot_cost], 'index')
            if current_loot_cost != 'no':

                # Cost of item
                current_loot_cost = eval(str("merchinv."+lootitem+"_cost"))
                current_loot_cost = current_loot_cost / targetbio.charisma
                current_loot_cost = int(current_loot_cost)

                # Merchant Quantity
                merchquant = eval(str("merchinv."+lootitem))
                if merchquant > 0:
                    merchantarray.append(lootitem.title() + ": "+str(current_loot_cost) + "$ [" + str(merchquant) + "]")
        osd(bot, duels.channel_current, 'say', merchantarray)
        duels.command_stamina_cost = 0
        return

    # plural loot
    plural_loot = []
    for item in duels_loot_items:
        itemname = str(item+"s")
        plural_loot.append(itemname)

    # Main transaction item
    lootitem = spicemanip.main([x for x in duels.command_restructure if x in duels_loot_items or x in plural_loot], 1)
    if not lootitem:
        osd(bot, duels.instigator, 'notice', "What do you want to " + str(lootcommand) + "?")
        duels.command_stamina_cost = 0
        return

    # How many of that item
    gethowmanylootitem = get_database_value(bot, targetbio.actual, lootitem) or 0
    if not gethowmanylootitem and lootcommand != 'buy':
        osd(bot, duels.instigator, 'notice', "You do not have any " + lootitem + "!")
        duels.command_stamina_cost = 0
        return

    # The quantity the player is applyint to this transaction
    quantity = spicemanip.main([x for x in duels.command_restructure if x == 'all' or str(x).isdigit()], 1) or 1
    if quantity == 'all':
        quantity = gethowmanylootitem

    if lootitem in plural_loot:
        for loots in duels_loot_items:
            similarlevel = similar(lootitem.lower(), loots)
            if similarlevel >= .75:
                lootitem = loots
        if quantity == 1:
            quantity = 2
    lootitemvalue = get_database_value(bot, 'duelsmerchant', str("vendor_track_value_"+lootitem)) or 1

    # Block for if the quantity above is greater than the players inventory
    if int(quantity) > int(gethowmanylootitem) and lootcommand != 'buy':
        osd(bot, duels.instigator, 'notice', "You do not have enough " + lootitem + " to use this command! You only have " + str(gethowmanylootitem) + ".")
        duels.command_stamina_cost = 0
        return

    quantity = int(quantity)

    # Buying
    if lootcommand == 'buy':

        current_loot_cost = eval(str("merchinv."+lootitem+"_cost"))
        current_loot_cost = current_loot_cost / targetbio.charisma
        coinrequired = int(current_loot_cost) * int(quantity)

        merchquant = eval(str("merchinv."+lootitem))
        if merchquant < quantity:
            osd(bot, duels.instigator, 'notice', "The Merchant does not have enough inventory to meet this request.")
            duels.command_stamina_cost = 0
            return

        # Block transaction if player doesn not have enough coin
        if int(targetbio.coin) < coinrequired:
            osd(bot, duels.instigator, 'notice', "You do not have enough coin for this action.")
            duels.command_stamina_cost = 0
            return

        # Apply cost, adjust inventory, and display accordingly
        adjust_database_value(bot, targetbio.actual, 'coin', -abs(coinrequired))
        adjust_database_value(bot, targetbio.actual, lootitem, quantity)
        adjust_database_value(bot, 'duelsmerchant', lootitem, -abs(quantity))
        adjust_database_value(bot, 'duelsmerchant', str("vendor_track_value_"+lootitem), int(quantity))
        osd(bot, duels.channel_current, 'say', targetbio.nametext + " bought " + str(quantity) + " "+lootitem + "s for " + str(coinrequired) + " coins.")
        osd(bot, duels.channel_current, 'say', 'The Merchant says "Thank you, come again"')

    #  Selling lootitem
    if lootcommand == 'sell':

        # Charisma rate
        charismapricing = targetbio.charisma / 100
        current_loot_cost = eval(str("merchinv."+lootitem+"_cost"))
        current_loot_cost = current_loot_cost * charismapricing
        current_loot_cost = int(current_loot_cost)
        reward = current_loot_cost * int(quantity)

        merchquant = eval(str("merchinv."+lootitem))
        combinedquant = int(merchquant) + quantity
        if combinedquant > duels_merchant_inv_max:
            osd(bot, duels.instigator, 'notice', "The Merchant does not have enough inventory space to meet this request.")
            duels.command_stamina_cost = 0
            return

        # Apply payment, adjust inventory, and display accordingly
        adjust_database_value(bot, targetbio.actual, 'coin', reward)
        adjust_database_value(bot, targetbio.actual, lootitem, -abs(quantity))
        adjust_database_value(bot, 'duelsmerchant', lootitem, quantity)
        adjust_database_value(bot, 'duelsmerchant', str("vendor_track_value_"+lootitem), -abs(quantity))
        osd(bot, duels.channel_current, 'say', targetbio.actual + " sold " + str(quantity) + " " + lootitem + "s for " + str(reward) + " coins.")
        osd(bot, duels.channel_current, 'say', 'The Merchant says "Thank you, come again"')


def duels_docs_merchant(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to purchase loot items.")
    return dispmsgarray


""" Locker """


def duels_command_function_locker(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Get The Command Used
    valid_comms = ['store', 'take']
    lootcommand = spicemanip.main([x for x in duels.command_restructure if x in valid_comms], 1) or 'view'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    if target != duels.instigator:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        if lootcommand == 'buy':
            if not duels.admin:
                osd(bot, duels.instigator, 'notice', "you cannot adjust lockers for other players.")
                duels.command_stamina_cost = 0
                return
    if target != duels.instigator:
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    # View target/own inventory
    if lootcommand == 'view':

        # Block viewing of other players inventories at lower levels
        if int(duels.tiercommandeval) > int(duels.currenttier) and targetbio.actual != duels.instigator:
            if duels.channel_current in duels.duels_dev_channels or duels.admin:
                allowpass = 1
            elif not duels.inchannel and len(duels.duels_dev_channels) > 0:
                allowpass = 1
            else:
                osd(bot, duels.instigator, 'notice', "Lockers for other players cannot be viewed until somebody reaches " + str(duels.tierpepperrequired.title()) + ". "+str(duels.tiermath) + " tier(s) remaining!")
                duels.command_stamina_cost = 0
                return

        # Process quantities of items in inventory
        dispmsgarray = []
        for x in duels_loot_view:
            gethowmany = get_database_value(bot, targetbio.actual, str(x+"_locker"))
            if gethowmany:
                xname = x.title()
                if gethowmany == 1:
                    loottype = str(xname)
                else:
                    loottype = str(str(xname)+"s")
                dispmsgarray.append(str(loottype) + "=" + str(gethowmany))

        # Display above info
        dispmsgarrayb = []
        if dispmsgarray != []:
            dispmsgarrayb.append(targetbio.nametextpos + " Locker:")
            for y in dispmsgarray:
                dispmsgarrayb.append(y)
        else:
            dispmsgarrayb.append(duels.instigator + ", It looks like " + targetbio.nametextpos + " locker is empty.")
        osd(bot, duels.channel_current, 'say', dispmsgarrayb)
        duels.command_stamina_cost = 0
        return

    # plural loot
    plural_loot = []
    for item in duels_loot_view:
        itemname = str(item+"s")
        plural_loot.append(itemname)

    # Main transaction item
    lootitem = spicemanip.main([x for x in duels.command_restructure if x in duels_loot_view or x in plural_loot or x == 'everything'], 1)
    if not lootitem:
        osd(bot, duels.instigator, 'notice', "What do you want to " + str(lootcommand) + "?")
        duels.command_stamina_cost = 0
        return

    if lootitem == 'everything':
        if lootcommand == 'store':
            for x in duels_loot_view:
                gethowmanylootitem = get_database_value(bot, duels.instigator, x) or 0
                if gethowmanylootitem:
                    adjust_database_value(bot, duels.instigator, x, -abs(gethowmanylootitem))
                    adjust_database_value(bot, duels.instigator, x+"_locker", gethowmanylootitem)
            osd(bot, duels.channel_current, 'say', duels.instigator + " stores all of their loot in their locker.")
        if lootcommand == 'take':
            for x in duels_loot_view:
                gethowmanylootitem = get_database_value(bot, duels.instigator, x+"_locker") or 0
                if gethowmanylootitem:
                    adjust_database_value(bot, duels.instigator, x, gethowmanylootitem)
                    adjust_database_value(bot, duels.instigator, x+"_locker", -abs(gethowmanylootitem))
            osd(bot, duels.channel_current, 'say', duels.instigator + " takes all their loot from their locker.")
        duels.command_stamina_cost = 0
        return

    # The quantity the player is applyint to this transaction
    if lootcommand == 'store':
        gethowmanylootitem = get_database_value(bot, duels.instigator, lootitem) or 0
    if lootcommand == 'take':
        gethowmanylootitem = get_database_value(bot, duels.instigator, lootitem+"_locker") or 0

    quantity = spicemanip.main([x for x in duels.command_restructure if x == 'all' or str(x).isdigit()], 1) or 1
    if quantity == 'all':
        quantity = gethowmanylootitem

    if lootitem in plural_loot:
        for loots in duels_loot_items:
            similarlevel = similar(lootitem.lower(), loots)
            if similarlevel >= .90:
                lootitem = loots
        if quantity == 1:
            quantity = 2

    # How many of that item
    if not gethowmanylootitem:
        if lootcommand == 'store':
            osd(bot, duels.instigator, 'notice', "You do not have any " + lootitem + "!")
        if lootcommand == 'take':
            osd(bot, duels.instigator, 'notice', "You do not have any " + lootitem + " in your locker!")
        duels.command_stamina_cost = 0
        return

    # Block for if the quantity above is greater than the players inventory
    if int(quantity) > int(gethowmanylootitem):
        if lootcommand == 'store':
            osd(bot, duels.instigator, 'notice', "You do not have enough " + lootitem + " to use this command! You only have " + str(gethowmanylootitem) + ".")
        if lootcommand == 'take':
            osd(bot, duels.instigator, 'notice', "You do not have enough " + lootitem + " in your locker to use this command! You only have " + str(gethowmanylootitem) + ".")
        duels.command_stamina_cost = 0
        return

    quantity = int(quantity)

    if lootcommand == 'store':
        adjust_database_value(bot, duels.instigator, lootitem, -abs(quantity))
        adjust_database_value(bot, duels.instigator, lootitem+"_locker", quantity)
        osd(bot, duels.channel_current, 'say', duels.instigator + " stores " + str(quantity) + " " + lootitem + " in their locker.")
    if lootcommand == 'take':
        adjust_database_value(bot, duels.instigator, lootitem, quantity)
        adjust_database_value(bot, duels.instigator, lootitem+"_locker", -abs(quantity))
        osd(bot, duels.channel_current, 'say', duels.instigator + " takes " + str(quantity) + " " + lootitem + " from their locker.")


def duels_docs_locker(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to store loot items long term.")
    return dispmsgarray


""" Craft """


def duels_command_function_craft(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    if target != duels.instigator:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        if not duels.admin:
            osd(bot, duels.instigator, 'notice', "you cannot craft for other players.")
            duels.command_stamina_cost = 0
            return
    if target != duels.instigator:
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    validlist = spicemanip.main(duels_craft_valid, "list")

    lootcommand = spicemanip.main([x for x in duels.command_restructure if x == 'recipe' or x == 'create' or x == 'list'], 1) or 'create'

    if lootcommand == 'list':
        osd(bot, duels.channel_current, 'say', "Valid Crafting Recipes include: " + validlist)
        duels.command_stamina_cost = 0
        return

    lootitem = spicemanip.main([x for x in duels.command_restructure if x in duels_craft_valid], 1)
    if not lootitem:
        osd(bot, duels.instigator, 'notice', "what type of loot item would to like to " + lootcommand + "?")
        duels.command_stamina_cost = 0
        return

    if lootcommand == 'recipe':
        recipe_required = eval("duel_craft_"+lootitem+"_required")
        recipe_quantity = eval("duel_craft_"+lootitem+"_quantity")
        recipe = []
        recipe.append(lootitem+" requires the following items:")
        for part, number in zip(recipe_required, recipe_quantity):
            recipe.append(part+"="+str(number))
        osd(bot, duels.channel_current, 'say', recipe)
        duels.command_stamina_cost = 0
        return

    quantity = spicemanip.main([x for x in duels.command_restructure if str(x).isdigit()], 1) or 1
    quantity = int(quantity)

    if lootcommand == 'create':
        recipe_required = eval("duel_craft_"+lootitem+"_required")
        recipe_quantity = eval("duel_craft_"+lootitem+"_quantity")
        recipe = []
        for part, number in zip(recipe_required, recipe_quantity):
            quantityneeded = int(number) * quantity
            gethowmanypart = get_database_value(bot, duels.instigator, part) or 0
            if int(gethowmanypart) < quantityneeded:
                recipe.append(part)
        if recipe != []:
            osd(bot, duels.instigator, 'notice', "you don't have the required components for this recipe")
            duels.command_stamina_cost = 0
            return
        for part, number in zip(recipe_required, recipe_quantity):
            quantityneeded = int(number) * quantity
            adjust_database_value(bot, duels.instigator, part, -abs(quantityneeded))
        adjust_database_value(bot, duels.instigator, lootitem, quantity)
        osd(bot, duels.channel_current, 'say', duels.instigator + " has successfully crafted "+str(quantity)+" " + lootitem + "(s)!")
        duels.command_stamina_cost = 0
        return


def duels_docs_craft(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to craft loot items.")
    return dispmsgarray


""" Tavern """


def duels_command_function_tavern(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    beveragetype = spicemanip.main([x for x in duels.command_restructure if x in duels_tavern_items], 1) or 'view'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    if target != duels.instigator:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        if not duels.admin:
            osd(bot, duels.instigator, 'notice', "you cannot drink for other players.")  # TODO admin
            duels.command_stamina_cost = 0
            return
    if target != duels.instigator:
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    if beveragetype == 'view':
        beveragelisting = []
        for beverage in duels_tavern_items:
            effectsarray = []
            for stat in stats_character:
                firstletter = stat[:1].title()
                current_stat_tavern = eval("duels_tavern_special_"+stat)
                currenteffect = spicemanip.main([beverage, duels_tavern_items, current_stat_tavern], 'index')
                if currenteffect != 0:
                    if currenteffect > 0:
                        currenteffect = str("+"+str(currenteffect))
                    currenteffect = str(str(currenteffect)+firstletter)
                    effectsarray.append(currenteffect)
            effectslist = spicemanip.main(effectsarray, "list")
            currentcost = spicemanip.main([beverage, duels_tavern_items, duels_tavern_cost], 'index')
            beveragelisting.append(beverage.title() + "=(" + str(effectslist) + ")" + "[" + str(currentcost) + "$]")
        osd(bot, duels.channel_current, 'say', beveragelisting)
        duels.command_stamina_cost = 0
        return

    current_loot_cost = spicemanip.main([beveragetype, duels_tavern_items, duels_tavern_cost], 'index')

    # The quantity the player is applyint to this transaction
    quantity = spicemanip.main([x for x in duels.command_restructure if x == 'all' or str(x).isdigit()], 1) or 1
    quantity = int(quantity)

    coinrequired = int(current_loot_cost) * int(quantity)

    # Block transaction if player doesn not have enough coin
    if int(targetbio.coin) < coinrequired:
        osd(bot, duels.instigator, 'notice', "You do not have enough coin for this action.")
        duels.command_stamina_cost = 0
        return
    adjust_database_value(bot, targetbio.actual, 'coin', -abs(coinrequired))

    mainlootusemessage = []
    if quantity > 1:
        mainlootusemessage.append(targetbio.actual + " bought " + str(quantity) + " " + beveragetype + "s for " + str(coinrequired) + "$")
    else:
        mainlootusemessage.append(targetbio.actual + " bought a " + beveragetype + " for " + str(coinrequired) + "$")

    lootusing = class_create('loot_use')
    for x in loot_use_effects:
        currentvalue = str("lootusing."+x+"=0")
        exec(currentvalue)

    for stat in stats_character:
        current_stat_tavern = eval("duels_tavern_special_"+stat)
        currenteffect = spicemanip.main([beveragetype, duels_tavern_items, current_stat_tavern], 'index')
        if currenteffect != 0:
            currenteffect = int(currenteffect) * int(quantity)
            currentvalue = str("lootusing."+stat+"="+str(currenteffect))
            exec(currentvalue)

    for x in loot_use_effects:
        currenteval = eval("lootusing."+x)
        if currenteval != 0:
            effectinflictarray = duels_effect_inflict(bot, duels,  instigatorbio, targetbio, 'all',  x, currenteval, 'tavern')
            for k in effectinflictarray:
                mainlootusemessage.append(k)
    osd(bot, duels.channel_current, 'say', mainlootusemessage)


def duels_docs_tavern(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to relax your character with a pint.")
    return dispmsgarray


"""
Channel Based Subcommands
"""


""" Tier """


def duels_command_function_tier(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    command = spicemanip.main(triggerargsarray, 2) or 'view'
    dispmsgarray = []
    currenttierpepper = duels_tier_number_to_pepper(bot, duels.currenttier)
    dispmsgarray.append("The current tier is " + str(duels.currenttier) + " (" + str(currenttierpepper.title()) + ").")

    # Display current/future features
    if command.lower() == 'view':
        currenttierlistarray = []
        futuretierlistarray = []
        for i in range(0, 16):
            tiercheck = eval("duels_commands_tier_unlocks_"+str(i))
            for x in tiercheck:
                if i <= duels.currenttier:
                    currenttierlistarray.append(x)
                else:
                    futuretierlistarray.append(x)
        if currenttierlistarray != []:
            currenttierlist = spicemanip.main(currenttierlistarray, "list")
            dispmsgarray.append("Feature(s) currently available: " + currenttierlist + ".")
        if futuretierlistarray != []:
            futuretierlist = spicemanip.main(futuretierlistarray, "list")
            dispmsgarray.append("Feature(s) not yet unlocked: " + futuretierlist + ".")

    # What tier is next
    elif command.lower() == 'next':
        nexttier = duels.currenttier + 1
        if nexttier > 15:
            osd(bot, duels.channel_current, 'say', "Tiers do not got past 15 (Pure Capsaicin).")
            duels.command_stamina_cost = 0
            return
        nextpepper = duels_tier_number_to_pepper(bot, nexttier)
        tiercheck = eval("duels_commands_tier_unlocks_"+str(nexttier))
        if tiercheck != []:
            tierlist = spicemanip.main(tiercheck, "list")
            dispmsgarray.append("Feature(s) that are available at tier " + str(nexttier) + " (" + str(nextpepper.title()) + "): " + tierlist + ".")
        else:
            dispmsgarray.append("No New Feature(s) available at tier " + str(nexttier) + " (" + str(nextpepper.title()) + ").")

    # Find what tier a command is in
    elif command.lower() in duels.commands_valid:
        commandtier = duels_tier_command_to_number(bot, command)
        commandpepper = duels_tier_number_to_pepper(bot, commandtier)
        dispmsgarray.append("The " + str(command) + " is unlocked at tier " + str(commandtier) + " (" + str(commandpepper.title()) + ").")
        tiercheck = eval("duels_commands_tier_unlocks_"+str(commandtier))
        tiermath = commandtier - duels.currenttier
        if tiermath > 0:
            dispmsgarray.append(str(tiermath) + " tier(s) remaining!")

    # find what tier a pepper level is
    elif command.lower() in duels_commands_pepper_levels:
        commandtier = duels_tier_number_to_pepper_index(bot, command)
        tiercheck = eval("duels_commands_tier_unlocks_"+str(commandtier))
        if tiercheck != []:
            tierlist = spicemanip.main(tiercheck, "list")
            dispmsgarray.append("Feature(s) that are available at tier " + str(commandtier) + " (" + str(command.title()) + "): " + tierlist + ".")
        else:
            dispmsgarray.append("No New Feature(s) available at tier " + str(commandtier) + " (" + str(command.title()) + ").")
        tiermath = int(commandtier) - duels.currenttier
        if tiermath > 0:
            dispmsgarray.append(str(tiermath) + " tier(s) remaining!")

    # process a tier number
    elif command.isdigit():
        command = int(command)
        if int(command) > 15:
            osd(bot, duels.channel_current, 'say', "Tiers do not got past 15 (Pure Capsaicin).")
            duels.command_stamina_cost = 0
            return
        commandpepper = duels_tier_number_to_pepper(bot, command)
        tiercheck = eval("duels_commands_tier_unlocks_"+str(command))
        if tiercheck != []:
            tierlist = spicemanip.main(tiercheck, "list")
            dispmsgarray.append("Feature(s) that are available at tier " + str(command) + " (" + str(commandpepper.title()) + "): " + tierlist + ".")
        else:
            dispmsgarray.append("No New Feature(s) available at tier " + str(command) + " (" + str(commandpepper.title()) + ").")
        tiermath = int(command) - duels.currenttier
        if tiermath > 0:
            dispmsgarray.append(str(tiermath) + " tier(s) remaining!")

    # find the player with the most xp, and how long until they reach a new tier
    elif command.lower() == 'closest':

        nexttier = duels.currenttier + 1
        if int(nexttier) > 15:
            osd(bot, duels.channel_current, 'say', "Tiers do not got past 15 (Pure Capsaicin).")
            duels.command_stamina_cost = 0
            return

        playerarray, statvaluearray = [], []
        for user in duels.users_current_allchan:
            statamount = get_database_value(bot, user, 'xp')
            if statamount > 0:
                playerarray.append(user)
                statvaluearray.append(statamount)

        if playerarray != [] and statvaluearray != []:
            statvaluearray, playerarray = array_arrangesort(bot, statvaluearray, playerarray)
            statleadername = spicemanip.main(playerarray, 'last')
            statleadernumber = spicemanip.main(statvaluearray, 'last')

            tierxprequired = spicemanip.main(duels_commands_xp_levels, nexttier)
            tierxpmath = tierxprequired - statleadernumber
            dispmsgarray.append("The leader in xp is " + statleadername + " with " + str(statleadernumber) + ". The next tier is " + str(abs(tierxpmath)) + " xp away.")
            nextpepper = duels_tier_number_to_pepper(bot, nexttier)
            tiercheck = eval("duels_commands_tier_unlocks_"+str(nexttier))
            if tiercheck != []:
                tierlist = spicemanip.main(tiercheck, "list")
                dispmsgarray.append("Feature(s) that are available at tier " + str(nexttier) + " (" + str(nextpepper.title()) + "): " + tierlist + ".")
            else:
                dispmsgarray.append("No New Feature(s) available at tier " + str(nexttier) + " (" + str(nextpepper.title()) + ").")
        else:
            dispmsgarray.append("Nobody is the closest to the next pepper level.")

    # anything else is deemed a target, see what tier they are on if valid
    else:
        validtarget, validtargetmsg = duels_target_check(bot, command, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        targettier = get_database_value(bot, command, 'tier') or 0
        dispmsgarray.append(command + "'s current tier is " + str(targettier) + ". ")

    # display the info
    osd(bot, duels.channel_current, 'say', dispmsgarray)


def duels_docs_tier(bot):
    dispmsgarray = []
    dispmsgarray.append("This will display information about the channels progress in the game.")
    return dispmsgarray


""" War Room """


def duels_command_function_warroom(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Get The Command Used
    subcommand = spicemanip.main([x for x in duels.command_restructure if x in duels_commands_events or x in duels.users_all_allchan or x in duels.commands_alt or x in duels_commands_locations], 1) or 'list'
    if subcommand in duels.commands_alt:
        for subcom in duels_commands_alternate_list:
            duels_commands_alternate_eval = eval("duels_commands_alternate_"+subcom)
            if subcommand.lower() in duels_commands_alternate_eval:
                subcommand = subcom

    if subcommand in duels_commands_locations:
        commandlocation = eval("duels.users_current_allchan_" + subcommand)
        if commandlocation == []:
            osd(bot, duels.channel_current, 'say', "The following nobody is located in " + subcommand + ".")
        else:
            displaymessage = spicemanip.main(commandlocation, "list")
            osd(bot, duels.channel_current, 'say', "The following users are located in " + subcommand + ": " + str(displaymessage))
        duels.command_stamina_cost = 0
        return

    if subcommand == 'list':
        if duels.instigator not in duels.users_canduel_allchan:
            canduel, validtargetmsg = duels_criteria(bot, duels.instigator, duels, 1)
            duels.command_stamina_cost = 0
            return
        if duels.instigator in duels.users_canduel_allchan:
            duels.users_canduel_allchan.remove(duels.instigator)
        if bot.nick in duels.users_canduel_allchan:
            duels.users_canduel_allchan.remove(bot.nick)
        if duels.users_canduel_allchan != []:
            displaymessage = spicemanip.main(duels.users_canduel_allchan, "list")
            osd(bot, duels.channel_current, 'say', duels.instigator + ", you may duel the following users: " + str(displaymessage))
        else:
            osd(bot, duels.instigator, 'notice', "It looks like you can't duel anybody at the moment.")
        duels.command_stamina_cost = 0
        return

    if subcommand in duels_commands_events:
        executedueling, executeduelingmsg = duels_events_check(bot, subcommand, duels)
        if not executedueling:
            osd(bot, duels.instigator, 'notice', executeduelingmsg)
        else:
            osd(bot, duels.instigator, 'notice', "It looks like full channel " + subcommand + " event can be used.")
        duels.command_stamina_cost = 0
        return

    if subcommand in duels.users_all_allchan:
        validtarget, validtargetmsg = duels_target_check(bot, subcommand, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        target = nick_actual(bot, subcommand)
        if target in duels.users_canduel_allchan and duels.instigator in duels.users_canduel_allchan:
            osd(bot, duels.instigator, 'notice', "It looks like you can duel " + target + ".")


def duels_docs_warroom(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to see what channel users are opted into the game and can be challenged.")
    return dispmsgarray


""" Leaderboard """


def duels_command_function_leaderboard(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    subcommand = spicemanip.main([x for x in duels.command_restructure if x == 'lowest' or x == 'highest' or x in duels.users_all_allchan or str(x).isdigit()], 1) or 'main'
    if subcommand != 'main' and subcommand not in duels.users_all_allchan:
        stat = spicemanip.main([x for x in duels.command_restructure if x in duels.stats_valid or x == 'health'], 1)
        if not stat:
            osd(bot, duels.channel_current, 'say', "What stat do you want to check?")
            duels.command_stamina_cost = 0
            return

    if bot.nick in duels.users_current_allchan_opted:
        duels.users_current_allchan_opted.remove(bot.nick)

    leaderscript = []
    leaderboardarraystats = ['winlossratio', 'kills', 'respawns', 'health', 'streak_win_best', 'streak_loss_best', 'bounty']
    streak_loss_bestdispmsg, streak_loss_bestdispmsgb = "Worst Losing Streak:", ""
    winlossratiodispmsg, winlossratiodispmsgb = "Wins/Losses:", ""
    killsdispmsg, killsdispmsgb = "Most Kills:", "kills"
    respawnsdispmsg, respawnsdispmsgb = "Most Deaths:", "respawns"
    healthdispmsg, healthdispmsgb = "Closest To Death:", "health"
    streak_win_bestdispmsg, streak_win_bestdispmsgb = "Best Win Streak:", ""
    bountydispmsg, bountydispmsgb = "Largest Bounty:", "coins"
    playerarray, statvaluearray = [], []

    if subcommand == 'main':
        for x in leaderboardarraystats:
            currentdispmsg = eval(x+"dispmsg")
            currentdispmsgb = eval(x+"dispmsgb")
            playerarray = []
            statvaluearray = []
            for u in duels.users_current_allchan_opted:
                if x != 'winlossratio' and x != 'health':
                    statamount = get_database_value(bot, u, x)
                else:
                    scriptdef = str('duels_get_' + x + '(bot,u)')
                    statamount = eval(scriptdef)
                if statamount > 0:
                    playerarray.append(u)
                    statvaluearray.append(statamount)
            if playerarray != [] and statvaluearray != []:
                statvaluearray, playerarray = array_arrangesort(bot, statvaluearray, playerarray)
                if x == 'health':
                    statleadername = spicemanip.main(playerarray, 1)
                    statleadernumber = spicemanip.main(statvaluearray, 1)
                    leaderclass = get_database_value(bot, statleadername, 'class') or 'unknown'
                    leaderrace = get_database_value(bot, statleadername, 'race') or 'unknown'
                    if leaderclass == 'vampire':
                        statleadernumber = int(statleadernumber)
                        statleadernumber = -abs(statleadernumber)
                elif x == 'winlossratio':
                    statleadername = spicemanip.main(playerarray, 'last')
                    statleadernumber = spicemanip.main(statvaluearray, 'last')
                    statleadernumber = format(statleadernumber, '.3f')
                else:
                    statleadername = spicemanip.main(playerarray, 'last')
                    statleadernumber = spicemanip.main(statvaluearray, 'last')
                leaderscript.append(str(currentdispmsg) + " " + str(statleadername) + " at " + str(statleadernumber) + " " + str(currentdispmsgb))
        if leaderscript == []:
            leaderscript.append("Leaderboard appears to be empty")
        osd(bot, duels.channel_current, 'say', leaderscript)
        duels.command_stamina_cost = 0
        return

    if str(subcommand).isdigit():
        if len(duels.users_current_allchan_opted) >= int(subcommand):
            for u in duels.users_current_allchan_opted:
                if stat.lower() != 'winlossratio' and stat.lower() != 'health':
                    statamount = get_database_value(bot, u, stat.lower())
                else:
                    scriptdef = str('duels_get_' + stat.lower() + '(bot,u)')
                    statamount = eval(scriptdef)
                if statamount > 0:
                    playerarray.append(u)
                    statvaluearray.append(statamount)
            if playerarray != [] and statvaluearray != []:
                statvaluearray, playerarray = array_arrangesort(bot, statvaluearray, playerarray)
                if stat != 'health':
                    statvaluearray = spicemanip.main(statvaluearray, 'reverse')
                    playerarray = spicemanip.main(playerarray, 'reverse')
                numberstat = int(subcommand)
                playeratrankno = spicemanip.main(playerarray, numberstat)
                currentranking = spicemanip.main([playeratrankno, playerarray, statvaluearray], 'index')
                if stat == 'health':
                    playerclass = get_database_value(bot, playeratrankno, 'class') or 'unknown'
                    if playerclass == 'vampire':
                        currentranking = int(currentranking)
                        currentranking = -abs(currentranking)
                elif stat == 'winlossratio':
                    currentranking = format(currentranking, '.3f')
                leaderscript.append("Leaderboard ranking number "+str(subcommand)+" for "+stat+": " + playeratrankno+" with "+str(currentranking))
        if leaderscript != []:
            osd(bot, duels.channel_current, 'say', leaderscript)
        else:
            osd(bot, duels.channel_current, 'say', "There appears to be no ranking for "+stat+" number "+str(subcommand)+".")
        duels.command_stamina_cost = 0
        return

    if subcommand in duels.users_all_allchan:
        target = subcommand
        if target != duels.instigator:
            validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
            if not validtarget:
                osd(bot, duels.instigator, 'notice', validtargetmsg)
                duels.command_stamina_cost = 0
                return
        target = nick_actual(bot, target)
        for x in leaderboardarraystats:
            currentdispmsg = eval(x+"dispmsg")
            currentdispmsgb = eval(x+"dispmsgb")
            playerarray = []
            statvaluearray = []
            for u in duels.users_current_allchan_opted:
                if x != 'winlossratio' and x != 'health':
                    statamount = get_database_value(bot, u, x)
                else:
                    scriptdef = str('duels_get_' + x + '(bot,u)')
                    statamount = eval(scriptdef)
                if statamount > 0:
                    playerarray.append(u)
                    statvaluearray.append(statamount)
            if playerarray != [] and statvaluearray != [] and target in playerarray:
                statvaluearray, playerarray = array_arrangesort(bot, statvaluearray, playerarray)
                if x != 'health':
                    statvaluearray = spicemanip.main(statvaluearray, 'reverse')
                    playerarray = spicemanip.main(playerarray, 'reverse')
                currentranking = spicemanip.main([target, playerarray, statvaluearray], 'index')
                playernumber, targetnumber = 0, 0
                for player in playerarray:
                    playernumber = playernumber + 1
                    if player == target:
                        targetnumber = playernumber
                        continue
                if x == 'health':
                    targetclass = get_database_value(bot, target, 'class') or 'unknown'
                    if targetclass == 'vampire':
                        currentranking = int(currentranking)
                        currentranking = -abs(currentranking)
                elif x == 'winlossratio':
                    currentranking = format(currentranking, '.3f')
                leaderscript.append(currentdispmsg + " Rank " + str(targetnumber) + " with "+str(currentranking) + " "+currentdispmsgb)
        if leaderscript != []:
            dispmsgarrayb = []
            dispmsgarrayb.append(target + "'s leaderboard ranking:")
            for x in leaderscript:
                dispmsgarrayb.append(x)
        else:
            dispmsgarrayb.append(target + " has no ranking.")
        osd(bot, duels.channel_current, 'say', dispmsgarrayb)

    if subcommand == 'highest' or subcommand == 'lowest':
        playerarray, statvaluearray = [], []
        for u in duels.users_current_allchan_opted:
            if stat.lower() != 'winlossratio' and stat.lower() != 'health':
                statamount = get_database_value(bot, u, stat.lower())
            else:
                scriptdef = str('duels_get_' + stat.lower() + '(bot,u)')
                statamount = eval(scriptdef)
            if statamount > 0:
                playerarray.append(u)
                statvaluearray.append(statamount)
        if playerarray != [] and statvaluearray != []:
            statvaluearray, playerarray = array_arrangesort(bot, statvaluearray, playerarray)
            if subcommand.lower() == 'lowest':
                statleadername = spicemanip.main(playerarray, 1)
                statleadernumber = spicemanip.main(statvaluearray, 1)
            else:
                statleadername = spicemanip.main(playerarray, 'last')
                statleadernumber = spicemanip.main(statvaluearray, 'last')
            if stat.lower() == 'health':
                leaderclass = get_database_value(bot, statleadername, 'class') or 'unknown'
                leaderrace = get_database_value(bot, statleadername, 'race') or 'unknown'
                if leaderclass == 'vampire':
                    statleadernumber = int(statleadernumber)
                    statleadernumber = -abs(statleadernumber)
            osd(bot, duels.channel_current, 'say', "The " + subcommand + " amount for " + stat + " is " + statleadername + " with " + str(statleadernumber) + ".")
        else:
            osd(bot, duels.channel_current, 'say', "There doesn't appear to be a " + subcommand + " amount for " + stat + ".")
        duels.command_stamina_cost = 0
        return


def duels_docs_leaderboard(bot):
    dispmsgarray = []
    dispmsgarray.append("This shows the top scores/stats of the game.")
    return dispmsgarray


""" Bounty """


def duels_command_function_bounty(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    bountytype = spicemanip.main([x for x in duels.command_restructure if x == 'bug'], 1) or 'normal'
    if bountytype == 'bug' and not duels.admin:
        osd(bot, duels.instigator, 'notice', "Bug Bounty is for bot admins only.")
        duels.command_stamina_cost = 0
        return

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    if target != duels.instigator:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
    target = nick_actual(bot, target)

    amount = spicemanip.main([x for x in duels.command_restructure if str(x).isdigit()], 1) or 0
    if not amount:
        if bountytype == 'normal':
            osd(bot, duels.instigator, 'notice', "How much of a bounty do you wish to place on "+target+".")
            duels.command_stamina_cost = 0
            return
        else:
            amount = spicemanip.main(['bugbounty', duels_ingame_coin_usage, duels_ingame_coin], 'index')
    amount = int(amount)

    if bountytype == 'bug':
        osd(bot, duels.channel_current, 'say', target + ' is awarded ' + str(amount) + " coin for finding a bug in duels.")
        adjust_database_value(bot, target, 'coin', amount)
        duels.command_stamina_cost = 0
        return

    instigatorcoin = get_database_value(bot, duels.instigator, 'coin') or 0
    if int(instigatorcoin) < int(amount):
        osd(bot, duels.instigator, 'notice', "Insufficient Funds.")
        duels.command_stamina_cost = 0
        return

    adjust_database_value(bot, duels.instigator, 'coin', -abs(amount))
    bountyontarget = get_database_value(bot, target, 'bounty') or 0
    if not bountyontarget:
        osd(bot, duels.channel_current, 'say', duels.instigator + " places a bounty of " + str(amount) + " on " + target + ".")
    else:
        osd(bot, duels.channel_current, 'say', duels.instigator + " adds " + str(amount) + " to the bounty on " + target + ".")
    adjust_database_value(bot, target, 'bounty', amount)


def duels_docs_bounty(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows you to place a bounty on another player. This bounty can be won by the player that kills them. This should be incentive for players to gang up on another.")
    return dispmsgarray


"""
Admin Subcommands
"""


""" Enable game in specific channels """


def duels_command_function_game(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Channel
    channeltarget = spicemanip.main([x for x in triggerargsarray if x.startswith('#')], 1)
    if not channeltarget:
        if duels.channel_current.startswith('#'):
            channeltarget = duels.channel_current
        else:
            osd(bot, duels.instigator, 'notice', "You must specify a valid channel.")
            duels.command_stamina_cost = 0
            return

    # on or off
    command = spicemanip.main([x for x in triggerargsarray if x == 'on' or x == 'off'], 1)
    if not command:
        osd(bot, duels.instigator, 'notice', "you must specify if you want the channel on or off.")
        duels.command_stamina_cost = 0
        return

    # bot channels
    if channeltarget.lower() not in [x.lower() for x in duels.valid_channel_list]:
        osd(bot, duels.instigator, 'notice', "I don't appear to be in that channel.")
        duels.command_stamina_cost = 0
        return

    # Verify capitalization
    for botchannel in duels.valid_channel_list:
        if botchannel.lower() == channeltarget.lower():
            channeltarget = botchannel

    # make the change
    if command == 'on':
        if channeltarget.lower() in [x.lower() for x in duels.duels_enabled_channels]:
            osd(bot, duels.instigator, 'notice', "Duels is already on in " + channeltarget + ".")
            duels.command_stamina_cost = 0
            return
        adjust_database_array(bot, 'duelrecorduser', [channeltarget], 'gameenabled', 'add')
        osd(bot, channeltarget, 'say', "Duels has been enabled in " + channeltarget + "!")
    elif command == 'off':
        if channeltarget.lower() not in [x.lower() for x in duels.duels_enabled_channels]:
            osd(bot, duels.instigator, 'notice', "Duels is already off in " + channeltarget + ".")
            duels.command_stamina_cost = 0
            return
        adjust_database_array(bot, 'duelrecorduser', [channeltarget], 'gameenabled', 'del')
        osd(bot, channeltarget, 'say', "Duels has been disabled in " + channeltarget + "!")
    else:
        osd(bot, duels.instigator, 'notice', "Invalid command.")


def duels_docs_game(bot):
    dispmsgarray = []
    dispmsgarray.append("This is used by bot admins to enable/disable the game for a specific channel.")
    return dispmsgarray


""" Development rooms that can bypass many game setbacks """


def duels_command_function_devmode(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Channel
    channeltarget = spicemanip.main([x for x in triggerargsarray if x.startswith('#')], 1)
    if not channeltarget:
        if duels.channel_current.startswith('#'):
            channeltarget = duels.channel_current
        else:
            osd(bot, duels.instigator, 'notice', "You must specify a valid channel.")
            duels.command_stamina_cost = 0
            return

    # on or off
    command = spicemanip.main([x for x in triggerargsarray if x == 'on' or x == 'off'], 1)
    if not command:
        osd(bot, duels.instigator, 'notice', "you must specify if you want the channel on or off.")
        duels.command_stamina_cost = 0
        return

    # bot channels
    if channeltarget.lower() not in [x.lower() for x in duels.valid_channel_list]:
        osd(bot, duels.instigator, 'notice', "I don't appear to be in that channel.")
        duels.command_stamina_cost = 0
        return

    # Verify capitalization
    for botchannel in duels.valid_channel_list:
        if botchannel.lower() == channeltarget.lower():
            channeltarget = botchannel

    # make the change
    if command == 'on':
        if channeltarget.lower() in [x.lower() for x in duels.duels_dev_channels]:
            osd(bot, duels.instigator, 'notice', "Duels devmode is already on in " + channeltarget + ".")
            duels.command_stamina_cost = 0
            return
        adjust_database_array(bot, 'duelrecorduser', [channeltarget], 'devenabled', 'add')
        osd(bot, channeltarget, 'say', "Duels devmode has been enabled in " + channeltarget + "!")
    elif command == 'off':
        if channeltarget.lower() not in [x.lower() for x in duels.duels_dev_channels]:
            osd(bot, duels.instigator, 'notice', "Duels devmode is already off in " + channeltarget + ".")
            duels.command_stamina_cost = 0
            return
        adjust_database_array(bot, 'duelrecorduser', [channeltarget], 'devenabled', 'del')
        osd(bot, channeltarget, 'say', "Duels devmode has been disabled in " + channeltarget + "!")
    else:
        osd(bot, duels.instigator, 'notice', "Invalid command.")


def duels_docs_devmode(bot):
    dispmsgarray = []
    dispmsgarray.append("This is used by bot admins to cause the game to bypass game-limiting features for a specific channel.")
    return dispmsgarray


""" Admin """  # TODO


def duels_command_function_admin(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    subcommand = spicemanip.main(triggerargsarray, 2).lower()
    if subcommand not in duels.commands_valid and subcommand != 'bugbounty' and subcommand != 'channel':
        osd(bot, duels.instigator, 'notice', "What Admin adjustment do you want to make?")
        duels.command_stamina_cost = 0
        return

    if subcommand == 'tier':
        command = spicemanip.main(triggerargsarray, 3).lower()
        if not command:
            osd(bot, duels.instigator, 'notice', "What did you intend to do with tiers?")
            duels.command_stamina_cost = 0
            return
        target = spicemanip.main(triggerargsarray, 4).lower() or duels.instigator
        if target == 'channel':
            target = 'duelrecorduser'
        if command == 'view':
            viewedtier = get_database_value(bot, target, 'tier')
            osd(bot, duels.instigator, 'notice', target + " is at tier " + str(viewedtier) + ".")
        elif command == 'reset':
            osd(bot, duels.instigator, 'notice', target + "'s tier has been reset.")
            reset_database_value(bot, target, 'tier')
        elif command == 'set':
            newsetting = spicemanip.main(triggerargsarray, 5)
            if not newsetting or not newsetting.isdigit():
                osd(bot, duels.instigator, 'notice', "You must specify a number setting.")
                duels.command_stamina_cost = 0
                return
            osd(bot, duels.instigator, 'notice', target + "'s tier has been set to " + str(newsetting) + ".")
            set_database_value(bot, target, 'tier', int(newsetting))
        else:
            osd(bot, duels.instigator, 'notice', "This looks to be an invalid command.")

    elif subcommand == 'roulette':
        command = spicemanip.main(triggerargsarray, 3).lower()
        if command != 'reset':
            osd(bot, duels.instigator, 'notice', "What did you intend to do with roulette?")
            duels.command_stamina_cost = 0
            return
        osd(bot, duels.instigator, 'notice', "Roulette should now be reset.")
        reset_database_value(bot, 'duelrecorduser', 'roulettelastplayer')
        reset_database_value(bot, 'duelrecorduser', 'roulettechamber')
        reset_database_value(bot, 'duelrecorduser', 'roulettewinners')
        reset_database_value(bot, 'duelrecorduser', 'roulettecount')
        reset_database_value(bot, 'duelrecorduser', 'roulettespinarray')
        for user in duels.users_all_allchan:
            reset_database_value(bot, user, 'roulettepayout')

    elif subcommand == 'channel':
        settingchange = spicemanip.main(triggerargsarray, 3)
        if not settingchange:
            osd(bot, duels.instigator, 'notice', "What channel setting do you want to change?")
        elif settingchange == 'statreset':
            set_database_value(bot, 'duelrecorduser', 'chanstatsreset', duels.now)
        elif settingchange == 'lastassault':
            reset_database_value(bot, 'duelrecorduser', 'lastfullroomassultinstigator')
            osd(bot, duels.instigator, 'notice', "Last Assault Instigator removed.")
            reset_database_value(bot, 'duelrecorduser', 'lastfullroomassult')
        elif settingchange == 'lastroman':
            reset_database_value(bot, 'duelrecorduser', 'lastfullroomcolosseuminstigator')
            osd(bot, duels.instigator, 'notice', "Last Colosseum Instigator removed.")
            reset_database_value(bot, 'duelrecorduser', 'lastfullroomcolosseum')
        elif settingchange == 'lastinstigator':
            reset_database_value(bot, 'duelrecorduser', 'lastinstigator')
            osd(bot, duels.instigator, 'notice', "Last Fought Instigator removed.")
        elif settingchange == 'halfhoursim':
            osd(bot, duels.instigator, 'notice', "Simulating the half hour automated events.")
            duels_halfhourtimer(bot)
        else:
            osd(bot, duels.instigator, 'notice', "Must be an invalid command.")

    elif subcommand == 'deathblow':
        newsetting = spicemanip.main(triggerargsarray, 3).lower()
        set_database_value(bot, duels.instigator, 'deathblowtarget', newsetting)
        set_database_value(bot, duels.instigator, 'deathblowtargettime', duels.now)

    else:
        osd(bot, duels.instigator, 'notice', "An admin command has not been written for the " + subcommand + " command.")


def duels_docs_admin(bot):
    dispmsgarray = []
    dispmsgarray.append("This allows bot admins to make changes to the game.")
    return dispmsgarray


"""
Other Subcommands
"""


""" Author """


def duels_command_function_author(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):
    osd(bot, duels.channel_current, 'say', "The author of Duels is deathbybandaid. Credit to DGW for the original game. Run .duel classic to see his version.")


def duels_docs_author(bot):
    dispmsgarray = []
    dispmsgarray.append("This will display the author of Duels.")
    return dispmsgarray


""" Hotkey """


def duels_command_function_hotkey(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan and x != 'random' and x != 'monster'], 1) or duels.instigator
    if target != duels.instigator:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
        if not duels.admin:
            osd(bot, duels.instigator, 'notice', "you cannot adjust hotkeys for other players.")
            duels.command_stamina_cost = 0
            return
    if target != duels.instigator:
        targetbio = duel_target_playerbio(bot, duels, target)
    else:
        targetbio = instigatorbio

    numberused = spicemanip.main([x for x in duels.command_restructure if str(x).isdigit()], 1) or 'nonumber'
    hotkeyvalid = ['view', 'update', 'reset', 'list']
    hotkeysetting = spicemanip.main([x for x in duels.command_restructure if x in hotkeyvalid], 1) or 'view'

    if hotkeysetting == 'list':
        hotkeyslist = get_database_value(bot, targetbio.actual, 'hotkey_complete') or []
        if hotkeyslist == []:
            osd(bot, duels.instigator, 'notice', "looks like you have no hotkeys.")
            duels.command_stamina_cost = 0
            return
        hotkeyslist = spicemanip.main(hotkeyslist, 'list')
        osd(bot, duels.channel_current, 'say', "Your hotkey list: " + hotkeyslist)
        duels.command_stamina_cost = 0
        return

    if numberused == 'nonumber':
        osd(bot, duels.instigator, 'notice', "What number would you like to view/modify?")
        duels.command_stamina_cost = 0
        return
    number_command = get_database_value(bot, duels.instigator, 'hotkey_'+str(numberused)) or 0

    if hotkeysetting != 'update':
        if not number_command:
            osd(bot, duels.instigator, 'notice', "You don't have a command hotlinked to "+str(numberused)+".")
            duels.command_stamina_cost = 0
            return

    if hotkeysetting == 'view':
        osd(bot, duels.channel_current, 'say', "You currently have " + str(numberused) + " set to '" + number_command + "'")
        duels.command_stamina_cost = 0
        return

    if hotkeysetting == 'reset':
        reset_database_value(bot, duels.instigator, 'hotkey_'+str(numberused))
        adjust_database_array(bot, targetbio.actual, [numberused], 'hotkey_complete', 'del')
        osd(bot, duels.channel_current, 'say', "Your "+str(numberused)+" command has been reset")
        duels.command_stamina_cost = 0
        return
    if hotkeysetting == 'update':
        if target in duels.command_restructure:
            duels.command_restructure.remove(target)
        duels.command_restructure.remove(numberused)
        duels.command_restructure.remove(hotkeysetting)

        newcommandhot = spicemanip.main(duels.command_restructure, 0) or 0
        if not newcommandhot:
            osd(bot, duels.instigator, 'notice', "you can't set an empty hotkey.")
            duels.command_stamina_cost = 0
            return

        if [x for x in newcommandhot if x == "&&"]:
            osd(bot, duels.instigator, 'notice', "hotkeys do not support multicommands yet")
            duels.command_stamina_cost = 0
            return

        actualcommand_main = spicemanip.main(newcommandhot, 1) or 0
        if actualcommand_main not in duels.commands_valid and actualcommand_main not in duels.commands_alt:
            osd(bot, duels.instigator, 'notice', str(actualcommand_main) + " does not appear to be a valid command to hotkey.")
            duels.command_stamina_cost = 0
            return

        set_database_value(bot, duels.instigator, 'hotkey_'+str(numberused), newcommandhot)
        adjust_database_array(bot, targetbio.actual, [numberused], 'hotkey_complete', 'add')
        osd(bot, duels.channel_current, 'say', "Your "+str(numberused)+" command has been set to '" + newcommandhot+"'")
        duels.command_stamina_cost = 0
        return


def duels_docs_hotkey(bot):
    dispmsgarray = []
    dispmsgarray.append("This will allow you to set quick shortcuts for your common commands.")
    return dispmsgarray


""" Konami """


def duels_command_function_konami(bot, duels):
    konami_note_to_players = "DO NOT tell others about this command. This is meant to be found by players that read the code. Effort has been made to conceal it."
    konami_note_to_players_b = "DO NOT run in channel,,, run in a private message to the bot. DON'T be THAT person that spoils the secret."
    konami = get_database_value(bot, duels.instigator, 'konami')
    if not konami:
        konamiset = 600
        osd(bot, duels.instigator, 'notice', "you have found the cheatcode easter egg!!! For this, you gain " + str(konamiset) + " health restoration!!! DO NOT tell others about this command.")
        adjust_database_value(bot, duels.instigator, 'health', konamiset)
        splitdamage = int(konamiset) / len(duels_bodyparts)
        for part in duels_bodyparts:
            adjust_database_value(bot, duels.instigator, part, splitdamage)
        set_database_value(bot, duels.instigator, 'konami', 1)
    else:
        osd(bot, duels.instigator, 'notice', "you can only cheat once.")


""" Intent """


def duels_command_function_intent(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):
    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.instigator
    validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
    if not validtarget and not duels.admin:
        osd(bot, duels.instigator, 'notice', validtargetmsg)
        duels.command_stamina_cost = 0
        return
    target = nick_actual(bot, target)
    osd(bot, duels.channel_current, 'say', "The intent is to provide "+target+" with a sense of pride and accomplishment...")


def duels_docs_intent(bot):
    dispmsgarray = []
    dispmsgarray.append("A joke regarding EA games.")
    return dispmsgarray


""" About """


def duels_command_function_about(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):
    osd(bot, duels.channel_current, 'say', "The purpose behind duels is for deathbybandaid to learn python, while providing a fun, evenly balanced gameplay.")


def duels_docs_about(bot):
    dispmsgarray = []
    dispmsgarray.append("Basic Description of the games purpose.")
    return dispmsgarray


""" Version date """


def duels_command_function_version(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):
    versionfetch = versionnumber(bot)
    osd(bot, duels.channel_current, 'say', "The duels framework was last modified on " + str(versionfetch) + ".")


def duels_docs_template(bot):
    dispmsgarray = []
    dispmsgarray.append("This checks the last modified date of the Master branch of the game.")
    return dispmsgarray


""" Docs, dynamically created based on internal settings """


def duels_command_function_docs(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    endmessage = []

    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan], 1) or duels.channel_current
    if target != duels.instigator and target != duels.channel_current:
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
    target = nick_actual(bot, target)

    messageinput = spicemanip.main([x for x in duels.command_restructure if x in duels.commands_alt or x in duels.commands_valid], 1) or 'online'
    if messageinput == 'online':
        endmessage.append("Online Docs: " + GITWIKIURL)
        osd(bot, target, 'say', endmessage)
        duels.command_stamina_cost = 0
        return

    if messageinput in duels.commands_alt or messageinput in duels.commands_valid:
        messagetype = 'commands'
        if messageinput in duels.commands_alt:
            for subcom in duels_commands_alternate_list:
                duels_commands_alternate_eval = eval("duels_commands_alternate_"+subcom)
                if messageinput.lower() in duels_commands_alternate_eval:
                    messageinput = subcom
        endmessage = duels_docs_commands(bot, messageinput)
        osd(bot, target, 'say', endmessage)
        duels.command_stamina_cost = 0
        return


def duels_docs_docs(bot):
    dispmsgarray = []
    dispmsgarray.append("Helps display Dynamic help for ingame usage.")
    return dispmsgarray


""" Usage """


def duels_command_function_usage(bot, triggerargsarray, command_main, trigger, command_full, duels, instigatorbio):

    # Get The Command Used
    subcommand = spicemanip.main([x for x in duels.command_restructure if x in duels.commands_valid], 1) or 'total'

    # Who is the target
    target = spicemanip.main([x for x in duels.command_restructure if x in duels.users_all_allchan or x == 'channel'], 1) or duels.instigator
    if target != duels.instigator and target != 'channel':
        validtarget, validtargetmsg = duels_target_check(bot, target, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'notice', validtargetmsg)
            duels.command_stamina_cost = 0
            return
    target = nick_actual(bot, target)
    targetname = target
    if target == 'channel':
        target = 'duelrecorduser'
        targetname = "The channel"

    # Usage Counter
    totaluses = get_database_value(bot, target, 'usage_'+subcommand)

    # Display
    if subcommand == 'total':
        subcommand = 'a total of'
    else:
        subcommand = str(subcommand + ' a total of')
    osd(bot, duels.channel_current, 'say', targetname + " has used duel " + subcommand + " " + str(totaluses) + " times.")


def duels_docs_usage(bot):
    dispmsgarray = []
    dispmsgarray.append("This is used to track your usage of the game. You can also specify a subcommand.")
    return dispmsgarray
    duels


"""
Chance Events
"""


@sopel.module.interval(61)
@sopel.module.thread(True)
def duels_chanceevents(bot):
    return

    duels = class_create('main')

    # Timestamp
    duels.now = time.time()

    # Valid Commands and stats
    duels.commands_valid = duels_valid_commands(bot)
    duels.commands_alt = duels_valid_commands_alternative(bot)
    duels.stats_valid = duels_valid_stats(bot)

    duels.duels_enabled_channels = get_database_value(bot, 'duelrecorduser', 'gameenabled') or []

    # User lists
    duels.instigator = 'duelrecorduser'
    duels = duels_user_lists(bot, duels)

    duels.duels_enabled_channels = get_database_value(bot, 'duelrecorduser', 'gameenabled') or []
    runtheevent = 1

    chance_event_next_type = get_database_value(bot, 'duelrecorduser', "chance_event_next_type") or 0
    if not chance_event_next_type:
        runtheevent = 0

    chance_event_last_timesince = duels_time_since(bot, 'duelrecorduser', "chance_event_last_time") or 0
    chance_event_next_timeout = get_database_value(bot, 'duelrecorduser', "chance_event_next_timeout") or 0
    if chance_event_last_timesince <= chance_event_next_timeout and runtheevent > 0:
        return

    if runtheevent:
        current_chance_event_location = get_database_value(bot, 'duelrecorduser', "chance_event_next_location") or 'arena'
        current_chance_event_type = get_database_value(bot, 'duelrecorduser', "chance_event_next_type") or 'sandstorm'
        chance_event_run(bot, duels, current_chance_event_type, current_chance_event_location)

    # Set next run

    # set time to now
    set_database_value(bot, 'duelrecorduser', "chance_event_last_time", duels.now)

    # how long until next event
    chance_event_next_timeout = randint(1200, 7200)
    set_database_value(bot, 'duelrecorduser', "chance_event_next_timeout", chance_event_next_timeout)

    # next location to effect
    chance_event_next_location = spicemanip.main(duels_commands_locations, 'random')
    set_database_value(bot, 'duelrecorduser', "chance_event_next_location", chance_event_next_location)

    # next event type
    chance_event_next_type = spicemanip.main(duels_chance_events_types, 'random')
    set_database_value(bot, 'duelrecorduser', "chance_event_next_type", chance_event_next_type)


def chance_event_run(bot, duels, eventtype, eventlocation):

    dispmsgarray = []

    aoran = 'a'
    if eventtype.lower().startswith(('a', 'e', 'i', 'o', 'u')):
        aoran = 'an'

    dispmsgarray.append(aoran.title() + " " + str(eventtype) + " afflicts the " + str(eventlocation))

    current_location_list = eval("duels.users_current_allchan_" + eventlocation)

    if current_location_list != []:
        effectedplayers = spicemanip.main(current_location_list, 'list')

        chance_event_durationmax = spicemanip.main([eventtype, duels_chance_events_types, duels_chance_events_duration], 'index')
        chance_event_durationtime = randint(1200, chance_event_durationmax)
        chance_event_damage = spicemanip.main([eventtype, duels_chance_events_types, duels_chance_events_damage], 'index')
        chance_event_special = spicemanip.main([eventtype, duels_chance_events_types, duels_chance_events_effected], 'index')

        if len(current_location_list) > 1:
            dispmsgarray.append(str(effectedplayers) + " are unable to escape the " + str(eventtype) + " and have a " + str(chance_event_damage) + " to their " + str(chance_event_special) + " for " + str(duels_hours_minutes_seconds(chance_event_durationtime)))
        else:
            dispmsgarray.append(str(effectedplayers) + " is unable to escape the " + str(eventtype) + " and has a " + str(chance_event_damage) + " to their " + str(chance_event_special) + " for " + str(duels_hours_minutes_seconds(chance_event_durationtime)))

        for player in current_location_list:
            targetbio = duel_target_playerbio(bot, duels, player)
            damageinflictarray = duels_effect_inflict(bot, duels, targetbio, targetbio, chance_event_durationtime, chance_event_special,  chance_event_damage, 'chance_event')
    else:
        dispmsgarray.append("The " + str(eventtype) + " affected nobody.")

    osd(bot, duels.duels_enabled_channels, 'say', dispmsgarray)

    return


"""
30 minute automation
"""


@sopel.module.interval(59)
@sopel.module.thread(True)
def duels_halfhourtimer(bot):

    chance_event_last_timesince = duels_time_since(bot, 'duelrecorduser', "halfhour_last_time") or 0
    if chance_event_last_timesince > 1800:

        duels = class_create('main')

        duels.duels_enabled_channels = get_database_value(bot, 'duelrecorduser', 'gameenabled') or []

        duels.instigator = bot.nick
        duels.commands_valid = duels_valid_commands(bot)
        duels.commands_alt = duels_valid_commands_alternative(bot)
        duels.channel_current = spicemanip.main(duels.duels_enabled_channels, 1)
        duels.inchannel = 0
        if duels.channel_current.startswith("#"):
            duels.inchannel = 1
        duels = duels_user_lists(bot, duels)

        now = time.time()
        set_database_value(bot, 'duelrecorduser', "halfhour_last_time", now)

        # Who gets to win a mysterypotion?
        randomuarray = []

        # Log Out Array
        logoutarray = []

        for u in duels.users_current_allchan_opted:
            # Log out users that aren't playing
            lastcommandusedtime = duels_time_since(bot, u, 'lastcommand') or 0
            lastping = duels_time_since(bot, u, 'lastping') or 0
            if spicemanip.main(['auto-opt', duels_timeouts, duels_timeouts_duration], 'index') < lastcommandusedtime and lastping < spicemanip.main(['auto-opt', duels_timeouts, duels_timeouts_duration], 'index'):
                logoutarray.append(u)
                reset_database_value(bot, u, 'lastping')
            else:
                set_database_value(bot, u, 'lastping', now)

        # Log Out Users
        duels.duels_enabled_channels = get_database_value(bot, 'duelrecorduser', 'gameenabled') or []
        if logoutarray != []:
            dispmsgarray = []
            logoutusers = spicemanip.main(logoutarray, 'list')
            if len(logoutarray) > 1:
                dispmsgarray.append(logoutusers + " have been logged out of duels for inactivity!")
            else:
                dispmsgarray.append(logoutusers + " has been logged out of duels for inactivity!")
            osd(bot, duels.duels_enabled_channels, 'say', dispmsgarray)
            adjust_database_array(bot, 'duelrecorduser', logoutarray, 'users_opted_allchan', 'del')

        # Random winner select
        lasttimedlootwinner = get_database_value(bot, 'duelrecorduser', 'lasttimedlootwinner') or bot.nick
        recentwinnersarray = get_database_value(bot, 'duelrecorduser', 'lasttimedlootwinners') or []
        valid_winners = []
        for u in duels.users_current_allchan_opted:
            if u not in recentwinnersarray and u != lasttimedlootwinner:
                valid_winners.append(u)
        if valid_winners == []:
            reset_database_value(bot, 'duelrecorduser', 'lasttimedlootwinners')
            for u in duels.users_current_allchan_opted:
                if u != lasttimedlootwinner:
                    valid_winners.append(u)
        if valid_winners != []:
            lootwinner = spicemanip.main(valid_winners, 'random')
            adjust_database_value(bot, lootwinner, 'mysterypotion_locker', 1)
            adjust_database_array(bot, 'duelrecorduser', [lootwinner], 'lasttimedlootwinners', 'add')
            set_database_value(bot, 'duelrecorduser', 'lasttimedlootwinner', lootwinner)
            osd(bot, lootwinner, 'notice', "You have been awarded a mysterypotion!")


"""
channel enter/exit
"""

# @event('JOIN')
# @rule('.*')
# @sopel.module.thread(True)
# def duel_player_return(bot, trigger):
#    duels = class_create('main')
#    duels.admin = 0
#    duels.channel_current = trigger.sender
#    duels.inchannel = 0
#    if duels.channel_current.startswith("#"):
#        duels.inchannel = 1
#    duels.instigator = trigger.nick
#    duels.commands_valid = duels_valid_commands(bot)
#    duels.commands_alt = duels_valid_commands_alternative(bot)
#    duels.duels_enabled_channels = get_database_value(bot, 'duelrecorduser', 'gameenabled') or []
#    duels.duels_dev_channels = get_database_value(bot, 'duelrecorduser', 'devenabled') or []
#    duels = duels_user_lists(bot, duels)
#    if duels.instigator in duels.users_opted:
#        duels.instigator_location = duels_get_location(bot,duels,duels.instigator)
#        if duels.instigator_location == 'arena':
#            osd(bot, duels.duels_enabled_channels, 'say', duels.instigator + " has entered the arena!")

# @event('QUIT','PART')
# @rule('.*')
# @sopel.module.thread(True)
# def duel_player_leave(bot, trigger):
#    duels = class_create('main')
#    duels.admin = 0
#    duels.channel_current = trigger.sender
#    duels.inchannel = 0
#    if duels.channel_current.startswith("#"):
#        duels.inchannel = 1
#    duels.instigator = trigger.nick
#    duels.commands_valid = duels_valid_commands(bot)
#    duels.commands_alt = duels_valid_commands_alternative(bot)
#    duels.duels_enabled_channels = get_database_value(bot, 'duelrecorduser', 'gameenabled') or []
#    duels.duels_dev_channels = get_database_value(bot, 'duelrecorduser', 'devenabled') or []
#    duels = duels_user_lists(bot, duels)
#    if duels.instigator in duels.users_opted:
#        duels.instigator_location = duels_get_location(bot,duels,duels.instigator)
#        if duels.instigator_location == 'arena':
#            cowardterm = spicemanip.main(cowardarray, 'random')
#            osd(bot, duels.duels_enabled_channels, 'say', duels.instigator + " has left the arena! " + cowardterm)


"""
Internal Documentation
"""


def duels_docs_template(bot):
    dispmsgarray = []
    dispmsgarray.append("Basic Description.")
    dispmsgarray.append("Usage: ")
    dispmsgarray.append("Subcommand '': ")
    dispmsgarray.append("Additional Switches: " + 'You may use -insert="" to')
    return dispmsgarray


def duels_docs_commands(bot, command):
    endmessage = []

    # Admin Only
    if command.lower() in duels_commands_admin:
        endmessage.append("[ADMIN ONLY] {Duel " + command.title()+"}")
    else:
        endmessage.append("{Duel " + command.title()+"}")

    # Command Doc Function
    try:
        duels_command_function_run = str('duels_docs_' + command.lower() + '(bot)')
        endmessageeval = eval(duels_command_function_run)
        for commandappend in endmessageeval:
            endmessage.append(commandappend)
    except NameError:
        dummyvar = ""

    # Alternate Commands
    if command in duels_commands_alternate_list:
        duels_commands_alternate_evalb = eval("duels_commands_alternate_"+command)
        alternatelist = spicemanip.main(duels_commands_alternate_evalb, 'list')
        endmessage.append("Alternate Command(s) = "+alternatelist)

    # Tier
    commandtier = duels_tier_command_to_number(bot, command)
    commandpepper = duels_tier_number_to_pepper(bot, commandtier)
    endmessage.append("Unlocked at tier " + str(commandtier) + " (" + str(commandpepper.title()) + ").")

    # Stamina Costs
    commandstaminacost = 0
    try:
        commandstaminacost = spicemanip.main([command, duels_commands_stamina_required, duels_commands_stamina_cost], 'index')
    except NameError:
        commandstaminacost = 0
    if commandstaminacost > 0:
        endmessage.append("Costs " + str(commandstaminacost) + " stamina.")

    if command.lower() in duels_commands_inchannel:
        endmessage.append("Must be run in channel.")

    if command.lower() in duels_commands_special_events:
        endmessage.append("Eligible for the 50th usage payout of " + str(spicemanip.main(['specialevent', duels_ingame_coin_usage, duels_ingame_coin], 'index')) + " coins!")

    # timeout TODO
    try:
        help_run = str('timeout_' + command.lower())
        endmessageeval = eval(help_run)
        endmessage.append("Has a timeout of " + str(duels_hours_minutes_seconds(endmessageeval)) + "between uses.")
    except NameError:
        dummyvar = ""

    return endmessage


"""
Initial Game checks
"""


# All valid subcummands
def duels_valid_commands(bot):
    duelcommandsarray = []
    for i in range(0, 16):
        tiercheck = eval("duels_commands_tier_unlocks_"+str(i))
        for x in tiercheck:
            duelcommandsarray.append(x)
    for j in duels_commands_tier_unlocks_none:
        duelcommandsarray.append(j)
    return duelcommandsarray


# All Alternative commands
def duels_valid_commands_alternative(bot):
    commands_alt = []
    for subcom in duels_commands_alternate_list:
        duels_commands_alternate_eval = eval("duels_commands_alternate_"+subcom)
        for x in duels_commands_alternate_eval:
            commands_alt.append(x)
    return commands_alt


# Pinpoint real command from alternate
def duels_valid_commands_alternative_find_match(bot, commandcompare):
    for subcom in duels_commands_alternate_list:
            duels_commands_alternate_eval = eval("duels_commands_alternate_"+subcom)
            if commandcompare.lower() in duels_commands_alternate_eval:
                commandcompare = subcom
                return commandcompare
    return 'invalidcommand'


# All valid character stats
def duels_valid_stats(bot):
    duelstatsadminarray = []
    for stattype in stats_admin_types:
        stattypeeval = eval("stats_"+stattype)
        for duelstat in stattypeeval:
            duelstatsadminarray.append(duelstat)
    return duelstatsadminarray


# channels the bot is in
def duels_valid_bot_channels(bot):
    valid_channel_list = []
    for c in bot.channels:
        valid_channel_list.append(c)
    return valid_channel_list


# All valid players, and categories they fall under
def duels_user_lists(bot, duels):

    duels.users_current_allchan = []
    duels.users_opted = get_database_value(bot, 'duelrecorduser', 'users_opted_allchan') or []
    duels.users_current_allchan_opted = []
    duels.users_canduel_allchan = []
    duels.botowners = []
    duels.botadmins = []
    duels.devteam = []
    duels.chanvoice = []
    duels.chanop = []

    for location in duels_commands_locations:
        exec("duels.users_current_allchan_" + location + " = []")

    for channel in bot.channels:
        current_channel = str(channel)
        if current_channel.startswith("#"):
            current_channel = current_channel.replace("#", "")
        current_channel = current_channel.strip()
        exec("duels.users_all_current_" + current_channel + " = []")

        # Current Channel users
        current_chan_str = str("duels.users_current_" + current_channel + " = []")
        exec(current_chan_str)
        users_current_channel = eval("duels.users_current_" + current_channel)
        for user in bot.privileges[channel]:
            if user not in duels.commands_valid and user not in duels.commands_alt and user.lower() not in target_ignore_list:
                users_current_channel.append(user)
        for user in users_current_channel:
            if user not in duels.users_current_allchan:
                duels.users_current_allchan.append(user)

        # All users the bot has seen
        if users_current_channel != []:
            adjust_database_array(bot, 'duelrecorduser', duels.users_current_allchan, 'users_all_'+current_channel, 'add')
            adjust_database_array(bot, 'duelrecorduser', duels.users_current_allchan, 'users_all_allchan', 'add')
        users_all_current_channel = get_database_value(bot, 'duelrecorduser', 'users_all_'+current_channel) or []

        # Opt-in
        exec("duels.users_opted_current_" + current_channel + " = []")
        users_opted_current_channel = eval("duels.users_opted_current_" + current_channel)
        for user in users_current_channel:
            if user in duels.users_opted:
                users_opted_current_channel.append(user)
                if user not in duels.users_current_allchan_opted:
                    duels.users_current_allchan_opted.append(user)

        # Some commands are valid targets for target check
        othervalidtargets = ['monster', 'random']
        for validtarget in othervalidtargets:
            if validtarget not in users_all_current_channel:
                users_all_current_channel.append(validtarget)
        users_all_current_class = eval("duels.users_all_current_" + current_channel)
        for user in users_all_current_channel:
            users_all_current_class.append(user)
        duels.users_all_allchan = get_database_value(bot, 'duelrecorduser', 'users_all_allchan') or []
        for validtarget in othervalidtargets:
            if validtarget not in duels.users_all_allchan:
                duels.users_all_allchan.append(validtarget)

        # Canduel Criteria
        exec("duels.users_canduel_current_" + current_channel + " = []")
        users_canduel_current_channel = eval("duels.users_canduel_current_" + current_channel)
        for user in users_opted_current_channel:
            if user != 'duelrecorduser':
                executedueling = duels_criteria(bot, user, duels, 0)
                if executedueling:
                    if user not in users_canduel_current_channel:
                        users_canduel_current_channel.append(user)
        random.shuffle(users_canduel_current_channel)
        for user in users_canduel_current_channel:
            if user not in duels.users_canduel_allchan:
                duels.users_canduel_allchan.append(user)

        # Players in locations
        locationunknown = []
        for user in users_opted_current_channel:
            locationunknown.append(user)
        for location in duels_commands_locations:
            currentlocationusers = get_database_value(bot, 'duelrecorduser', location+"_users") or []
            current_location_list = eval("duels.users_current_allchan_" + location)
            for user in currentlocationusers:
                if user in locationunknown:
                    locationunknown.remove(user)
                if user not in current_location_list:
                    current_location_list.append(user)
        if locationunknown != []:
            for user in locationunknown:
                duels.users_current_allchan_town.append(user)
            adjust_database_array(bot, 'duelrecorduser', locationunknown, "town_users", 'add')

        for location in duels_commands_locations:
            current_location_list = eval("duels.users_current_allchan_" + location)
            for user in current_location_list:
                if user not in duels.users_canduel_allchan:
                    current_location_list.remove(user)

        # Bot owner
        for user in users_current_channel:
            if user in bot.config.core.owner:
                if user not in duels.botowners:
                    duels.botowners.append(user)

        # Bot Admins
        for user in users_current_channel:
            if user in bot.config.core.admins:
                if user not in duels.botadmins:
                    duels.botadmins.append(user)

        # development_team
        for user in users_current_channel:
            if user in development_team:
                if user not in duels.devteam:
                    duels.devteam.append(user)

        # chan op
        for user in users_current_channel:
            if bot.privileges[channel][user] == OP:
                if user not in duels.chanop:
                    duels.chanop.append(user)

        # chan voice
        for user in users_current_channel:
            if bot.privileges[channel][user] == VOICE:
                if user not in duels.chanvoice:
                    duels.chanvoice.append(user)

    # Canduel Extra Shuffle
    random.shuffle(duels.users_canduel_allchan)

    return duels


# New Player Monologue
def duels_opening_monologue(bot, duels, user, opening_monologue, tierset, char_basics_array):

    # opt in
    adjust_database_array(bot, 'duelrecorduser', [user], 'users_opted_allchan', 'add')

    # spawn in town
    duels_location_move(bot, duels, user, 'town')

    # Current leveling average
    if tierset:
        tierarray = []
        for player in duels.users_current_allchan_opted:
            playertier = get_database_value(bot, player, 'tier')
            tierarray.append(playertier)
        if tierarray != []:
            playertierarrayaverage = mean(tierarray)
            playertierarrayaverage = int(playertierarrayaverage)
        else:
            playertierarrayaverage = 0
        set_database_value(bot, user, 'tier', playertierarrayaverage)

    # random Gender/Class/Race
    for char_basic in duels_character_basics:
        currentarraysetting = spicemanip.main([char_basic, duels_character_basics, char_basics_array], 'index')
        if currentarraysetting == '':
            if char_basic in opening_monologue:
                currentrandomarray = eval('duels_character_valid_'+char_basic)
                currentrandom = spicemanip.main(currentrandomarray, 'random')
                exec("random" + char_basic + " = " + "'"+currentrandom+"'")
                randomset = eval("random"+char_basic)
                set_database_value(bot, user, char_basic, randomset)
            else:
                currentrandom = get_database_value(bot, user, char_basic)
                exec("random" + char_basic + " = " + "'"+currentrandom+"'")
        else:
            exec("random" + char_basic + " = " + "'"+currentarraysetting+"'")
            randomset = eval("random"+char_basic)
            set_database_value(bot, user, char_basic, randomset)

    # Opening Remarks
    dispmsgarray = []
    dispmsgarray.append("Welcome to Duels, " + user + "!")
    dispmsgarray.append("You have spawned into town as a " + str(randomgender) + " level " + str(playertierarrayaverage) + " " + str(randomrace) + " " + str(randomclass))
    osd(bot, duels.channel_current, 'say', dispmsgarray)

    # Tutorial in Private message
    dispmsgarray = []
    dispmsgarray.append("You may switch to a new character sheet at any time. Simply run `.duel char setup` for further information.")
    dispmsgarray.append("If you would like a tutorial, run `.duel tutorial`.")  # TODO
    osd(bot, user, 'notice', dispmsgarray)


def duels_channel_lists(bot, trigger, duels):

    # Current Channel
    duels.channel_current = trigger.sender

    # In a channel or privmsg
    duels.inchannel = 0
    if duels.channel_current.startswith("#"):
        duels.inchannel = 1

    # All Bot Channels
    duels.valid_channel_list = duels_valid_bot_channels(bot)

    # Game Enabled
    duels.duels_enabled_channels = get_database_value(bot, 'duelrecorduser', 'gameenabled') or []

    # Development mode
    duels.duels_dev_channels = get_database_value(bot, 'duelrecorduser', 'devenabled') or []
    duels.dev_bypass_checks = 0
    if duels.channel_current.lower() in [x.lower() for x in duels.duels_dev_channels]:
        duels.dev_bypass_checks = 1

    return duels


# Verify instigator is allowed to run commands
def duels_check_instigator(bot, trigger, command_main, duels, instigatorbio):
    checkpass = 0

    # Instigator can't be a command, and can't enable duels
    if duels.instigator.lower() in duels.commands_valid or duels.instigator.lower() in duels.commands_alt:
        osd(bot, duels.instigator, 'notice', "Your nick is the same as a valid command for duels.")
        return checkpass

    # Instigator can't duelrecorduser
    if duels.instigator.lower() == 'duelrecorduser' or duels.instigator.lower() in target_ignore_list or duels.instigator.lower() == 'duelsmonster':
        osd(bot, duels.instigator, 'notice', "Your nick is not able to play duels.")
        return checkpass

    # Check if Instigator is Opted in
    if duels.instigator not in duels.users_opted:
        instigatoropttime = duels_time_since(bot, duels.instigator, 'timeout_opttimetime')
        if instigatoropttime < spicemanip.main(['opttime', duels_timeouts, duels_timeouts_duration], 'index') and duels.dev_bypass_checks == 1 and not trigger.admin:
            osd(bot, duels.instigator, 'notice', "You are not opted into duels. It looks like you can't enable/disable duels for " + str(duels_hours_minutes_seconds((spicemanip.main(['opttime', duels_timeouts, duels_timeouts_duration], 'index') - instigatoropttime))) + ".")
            return checkpass
        else:
            if command_main != 'off' and command_main != 'on':
                osd(bot, duels.instigator, 'notice', "Duels Has been enabled for you automatically. To disable, run .duel off.")
                if instigatorbio.location == 'arena':
                    dispmsgarray = []
                    dispmsgarray.append(duels.instigator + " has entered the arena!")
                    osd(bot, duels.duels_enabled_channels, 'say', dispmsgarray)
                adjust_database_array(bot, 'duelrecorduser', [duels.instigator], 'users_opted_allchan', 'add')
            checkpass = 1
            return checkpass

    deathblow = get_database_value(bot, duels.instigator, 'deathblow')
    if deathblow:
        deathblowtargettime = duels_time_since(bot, duels.instigator, 'deathblowtargettime') or 0
        if deathblowtargettime <= 120:
            deathblowkiller = get_database_value(bot, duels.instigator, 'deathblowkiller') or 'unknown'
            osd(bot, duels.instigator, 'notice', "you can't run duels for " + str(duels_hours_minutes_seconds((120 - deathblowtargettime))) + " due to a possible deathblow from " + deathblowkiller + ".")
            return checkpass

    checkpass = 1
    return checkpass


# Check for misspellings
def duels_command_spelling_check_main(bot, trigger, triggerargsarray, command_full, command_main, duels, instigatorbio):
    comorig = command_main

    # Check Commands
    for com in duels.commands_valid:
        similarlevel = similar(command_main.lower(), com)
        if similarlevel >= .75:
            command_main = com
            command_main_process(bot, trigger, triggerargsarray, command_full, command_main, duels, instigatorbio)
            return

    # Check alt commands
    if command_main == comorig:
        for com in duels.commands_alt:
            similarlevel = similar(command_main.lower(), com)
            if similarlevel >= .75:
                command_main = com
                command_main_process(bot, trigger, triggerargsarray, command_full, command_main, duels, instigatorbio)
                return

    # Check players, but only if we didn't alreayd match a command
    if command_main == comorig:
        for player in duels.users_all_allchan:
            similarlevel = similar(command_main.lower(), player)
            if similarlevel >= .75:
                command_main = player
                command_main_process(bot, trigger, triggerargsarray, command_full, command_main, duels, instigatorbio)
                return

    # Did we match?
    if command_main != comorig:
        command_main_process(bot, trigger, triggerargsarray, command_full, command_main, duels, instigatorbio)
    else:
        validtarget, validtargetmsg = duels_target_check(bot, command_main, duels, instigatorbio)
        if not validtarget:
            osd(bot, duels.instigator, 'say', validtargetmsg)
    return


"""
Player Bios
"""


def duel_combat_playerbios(bot, playerone, playertwo, typeofduel, duels):

    playersarray = [playerone, playertwo]
    selectedplayer = 0
    for player in playersarray:
        selectedplayer = selectedplayer + 1
        if selectedplayer == 1:
            playerbio = class_create('player_one')
        else:
            playerbio = class_create('player_two')

        # Actual Nick
        if player == 'monster' or player == 'duelsmonster':
            player == 'duelsmonster'
            playerbio.actual = 'duelsmonster'
            duelsmonstername = get_database_value(bot, 'duelsmonster', 'last_monster')
        else:
            playerbio.actual = nick_actual(bot, player)

        # Title
        playerbio.nicktitle = get_database_value(bot, player, 'title')

        # Starting pepper
        playerbio.pepperstart = duels_tier_nick_to_pepper(bot, player)

        playerbio.lastfoughtstart = get_database_value(bot, player, 'lastfought')

        playerbio.shield_start = get_database_value(bot, player, 'shield') or 0
        playerbio.curse_start = get_database_value(bot, player, 'curse') or 0

        playerbio.loss_streak_start = get_database_value(bot, playerbio.actual, 'streak_loss_current') or 0
        playerbio.win_streak_start = get_database_value(bot, playerbio.actual, 'streak_win_current') or 0

        if player == 'duelsmonster':
            playerbio.Class = 'monster'
            playerbio.race = 'monster'
        elif player == bot.nick:
            playerbio.Class = 'bot'
            playerbio.race = 'bot'
        else:
            playerbio.Class = get_database_value(bot, player, 'class') or 'unknown'
            playerbio.race = get_database_value(bot, player, 'race') or 'unknown'

        playerbio.special = duels_special_combination(bot, playerbio.actual)
        playerbio.strength, playerbio.perception, playerbio.endurance, playerbio.charisma, playerbio.intelligence, playerbio.agility, playerbio.luck, playerbio.magic = duels_special_humanize(bot, playerbio.special)

        playerbio.tier = get_database_value(bot, player, 'tier')

        playerbio.weaponslist = get_database_value(bot, player, 'weaponslocker_complete') or []

        # How to announce the player
        if player == 'duelsmonster':
            duelsmonstervarient = get_database_value(bot, 'duelsmonster', 'last_monster_varent')
            playerbio.announce = str(duelsmonstervarient+" "+duelsmonstername)
        elif selectedplayer == 2 and playertwo == playerone:
            playerbio.announce = "themself"
        else:
            playerbio.announce = duels_nick_names(bot, playerbio, duels)

        # Pretty Text Names when needed
        if player == 'duelsmonster':
            playerbio.nametext = str("The " + duelsmonstername)
            playerbio.nametextb = str("The " + duelsmonstername)
        elif selectedplayer == 2 and playertwo == playerone:
            playerbio.nametext = playerbio.actual
            playerbio.nametextb = "themself"
        else:
            playerbio.nametext = playerbio.actual
            playerbio.nametextb = playerbio.actual

        if playerbio.nametext.endswith("s"):
            playerbio.nametextpos = str(playerbio.nametext + "'")
        else:
            playerbio.nametextpos = str(playerbio.nametext + "s")

        playerbio.shield = playerbio.shield_start
        playerbio.curse = playerbio.curse_start

        # coin
        playerbio.coin = get_database_value(bot, player, 'coin') or 0

        # mana
        playerbio.mana = get_database_value(bot, player, 'mana') or 0

        # bounty
        playerbio.bounty = get_database_value(bot, player, 'bounty') or 0

        if selectedplayer == 1:
            playerbio_one = playerbio
        else:
            playerbio_two = playerbio

    return playerbio_one, playerbio_two


def duel_target_playerbio(bot, duels, player):

    # random
    if player == 'random':
        player = spicemanip.main(duels.users_canduel_allchan, 'random')

    # Open Class
    if player != duels.instigator:
        playerbio = class_create('targetbio')
    else:
        playerbio = class_create('instigatorbio')

    # Actual Nick
    if player == 'monster':
        player == 'duelsmonster'
        playerbio.actual = 'duelsmonster'
        duelsmonstername = get_database_value(bot, 'duelsmonster', 'last_monster')
        if not duelsmonstername:
            # Generate Monster's stats based on room average
            duels_monster_stats_generate(bot, duels, 1)
            # Monster's name
            duelsmonstervarient = spicemanip.main(duelsmonstervarientarray, 'random')
            set_database_value(bot, 'duelsmonster', 'last_monster_varent', duelsmonstervarient)
            duelsmonstername = spicemanip.main(monstersarray, 'random')
            set_database_value(bot, 'duelsmonster', 'last_monster', duelsmonstername)
    else:
        playerbio.actual = nick_actual(bot, player)

    # Title
    playerbio.nicktitle = get_database_value(bot, player, 'title') or ''

    # Pretty Text Names when needed
    if playerbio.actual == 'duelsmonster':
        playerbio.nametext = str("The " + (duelsmonstername))
        playerbio.nametextb = str("The " + (duelsmonstername))
    else:
        playerbio.nametext = playerbio.actual
        playerbio.nametextb = playerbio.actual

    if playerbio.nametext.endswith("s"):
        playerbio.nametextpos = str(playerbio.nametext + "'")
    else:
        playerbio.nametextpos = str(playerbio.nametext + "s")

    # Pepper
    playerbio.pepperstart = duels_tier_nick_to_pepper(bot, player)
    playerbio.pepper = playerbio.pepperstart

    # Magic attributes
    playerbio.shield_start = get_database_value(bot, player, 'shield') or 0
    playerbio.curse_start = get_database_value(bot, player, 'curse') or 0
    playerbio.shield = playerbio.shield_start
    playerbio.curse = playerbio.curse_start

    if player == 'duelsmonster':
        playerbio.Class = 'monster'
        playerbio.race = 'monster'
    elif player == bot.nick:
        playerbio.Class = 'bot'
        playerbio.race = 'bot'
    else:
        playerbio.Class = get_database_value(bot, player, 'class') or 'unknown'
        playerbio.race = get_database_value(bot, player, 'race') or 'unknown'
    playerbio.gender = get_database_value(bot, player, 'gender') or 'unknown'

    # pronouns for self # TODO

    # coin
    playerbio.coin = get_database_value(bot, player, 'coin') or 0

    # mana
    playerbio.mana = get_database_value(bot, player, 'mana') or 0

    # bounty
    playerbio.bounty = get_database_value(bot, player, 'bounty') or 0

    # SPECIAL+M
    playerbio.special = duels_special_combination(bot, playerbio.actual)
    playerbio.strength, playerbio.perception, playerbio.endurance, playerbio.charisma, playerbio.intelligence, playerbio.agility, playerbio.luck, playerbio.magic = duels_special_humanize(bot, playerbio.special)

    # Tier
    playerbio.tier = get_database_value(bot, player, 'tier')

    # Fancy Name
    playerbio.announce = duels_nick_names(bot, playerbio, duels)

    # location
    playerbio.location = duels_get_location(bot, duels, player)

    return playerbio


"""
Stat Checks
"""


# Bot no stats
def duels_refresh_bot(bot, duels):
    for x in duels.stats_valid:
        set_database_value(bot, bot.nick, x, None)


# Check stamina required for a command
def duels_stamina_check(bot, nick, command, duels):
    staminapass = 0

    stamina = get_database_value(bot, nick, 'stamina') or 0
    if command in duels_commands_stamina_required:
        commandstaminacost = spicemanip.main([command, duels_commands_stamina_required, duels_commands_stamina_cost], 'index')
    else:
        commandstaminacost = 0

    if commandstaminacost <= stamina:
        staminapass = 1

    # Devroom bypass
    if duels.channel_current in duels.duels_dev_channels or duels.admin:
        staminapass = 1
        return staminapass, stamina, commandstaminacost
    if not duels.inchannel and len(duels.duels_dev_channels) > 0:
        staminapass = 1
        return staminapass, stamina, commandstaminacost

    return staminapass, stamina, commandstaminacost


# Charge the appropriate stamina
def duels_stamina_charge(bot, nick, command):

    if command in duels_commands_stamina_required:
        commandstaminacost = spicemanip.main([command, duels_commands_stamina_required, duels_commands_stamina_cost], 'index')
    else:
        commandstaminacost = 0

    if commandstaminacost > 0:
        adjust_database_value(bot, nick, 'stamina', -abs(commandstaminacost))


# Verify nick condition
def duels_check_nick_condition(bot, nick, duels):

    # health regeneration per minute
    healthsplit = halfhour_regen_health / len(duels_bodyparts)
    healthsplit = healthsplit / 30
    manasmath = halfhour_regen_mage_mana / 30
    staminasmath = staminaregen / 30
    nick_regen_last = duels_time_since(bot, nick, 'nick_regen_last')
    nick_minutes_since_regen = nick_regen_last / 60
    health_to_regen = nick_minutes_since_regen * healthsplit
    mana_to_regen = nick_minutes_since_regen * manasmath
    mana_to_regen = int(mana_to_regen)
    health_to_regen = int(health_to_regen)
    stamina_to_regen = nick_minutes_since_regen * staminasmath
    stamina_to_regen = int(stamina_to_regen)

    # Verify succesful character setup
    setup_check_missing = []
    for setup_check in duels_character_basics:
        stat_there = get_database_value(bot, nick, setup_check)
        if not stat_there:
            setup_check_missing.append(stat_there)

    if setup_check_missing != []:
        missing_settings = spicemanip.main(setup_check_missing, "list")
        osd(bot, nick, 'notice', "you seem to be missing your "+str(missing_settings)+" setting(s). Please talk to " + str(duels_bot_owner) + " to get this fixed.")

    # New Player?
    playernew = get_database_value(bot, nick, 'newplayer')
    if not playernew:

        # new player max health
        for part in duels_bodyparts:
            maxhealthpart = spicemanip.main([part, duels_bodyparts, duels_bodyparts_health], 'index')
            currenthealthtier = duels.tierscaling * int(maxhealthpart)
            set_database_value(bot, nick, part, currenthealthtier)

        # New Player max stamina
        set_database_value(bot, nick, 'stamina', staminamax)

        # no longer a newbie
        set_database_value(bot, nick, 'newplayer', 1)
        return

    # Deathblow chance missed
    deathblow = get_database_value(bot, nick, 'deathblow')
    if deathblow:
        deathblowtargettime = duels_time_since(bot, nick, 'deathblowtargettime') or 0
        if deathblowtargettime > 120:
            deathblowkiller = get_database_value(bot, nick, 'deathblowkiller') or 'unknown'
            osd(bot, nick, 'notice', "it looks like you were almost killed by "+deathblowkiller+", but the deathblow command was not issued in time. Your health has been restored! You have been moved to town.")
            duels_location_move(bot, duels, nick, 'town')
            for part in duels_bodyparts:
                maxhealthpart = spicemanip.main([part, duels_bodyparts, duels_bodyparts_health], 'index')
                currenthealthtier = duels.tierscaling * int(maxhealthpart)
                set_database_value(bot, nick, part, currenthealthtier)
            reset_database_value(bot, nick, 'deathblow')
            reset_database_value(bot, nick, 'deathblowtargettime')
            reset_database_value(bot, nick, 'deathblowkiller')

    # Nick base
    nickclass = get_database_value(bot, nick, 'class') or 'unknown'
    nickrace = get_database_value(bot, nick, 'race') or 'unknown'

    # Check health
    simulatedrespawn = 0
    set_database_value(bot, nick, 'nick_regen_last', duels.now)
    for part in duels_bodyparts:

        # current health of part
        parthealth = get_database_value(bot, nick, part) or 0

        # find the maximum allowed health for part
        maxhealthpart = spicemanip.main([part, duels_bodyparts, duels_bodyparts_health], 'index')

        # scale the health maximum
        currenthealthtier = duels.tierscaling * int(maxhealthpart)

        # Verify alive status
        if part == 'head' or part == 'torso':
            if not simulatedrespawn:
                if not parthealth or parthealth <= 0:
                    simulatedrespawn = 1

        # verify part not negative
        if part != 'head' and part != 'torso' and not simulatedrespawn:
            if parthealth < 0:
                reset_database_value(bot, nick, part)

        # Health Regen
        if parthealth < currenthealthtier and not simulatedrespawn:
            combinedhealth = parthealth + health_to_regen
            if combinedhealth < currenthealthtier:
                adjust_database_value(bot, nick, part, health_to_regen)
            else:
                set_database_value(bot, nick, part, currenthealthtier)

        # Verify part not over max
        if parthealth > currenthealthtier and not simulatedrespawn:
            set_database_value(bot, nick, part, currenthealthtier)

    if simulatedrespawn:
        # fresh health
        for part in duels_bodyparts:
            maxhealthpart = spicemanip.main([part, duels_bodyparts, duels_bodyparts_health], 'index')
            currenthealthtier = duels.tierscaling * int(maxhealthpart)
            set_database_value(bot, nick, part, currenthealthtier)
        # fresh stamina
        set_database_value(bot, nick, 'stamina', staminamax)
        # no mana
        reset_database_value(bot, nick, 'mana')
        # no loot
        for loot in stats_loot:
            reset_database_value(bot, nick, loot)
        # respawn the user
        osd(bot, nick, 'notice', "it looks like duels missed one of your deaths and your health went negative. You have been respawned with full health, but you lost all of your items. Please let " + duels_bot_owner + " know what killed you, for improvement of the game.")
        adjust_database_value(bot, nick, 'respawns', 1)
        return

    # check for negative mana
    mana = get_database_value(bot, nick, 'mana')
    if int(mana) < 0:
        reset_database_value(bot, nick, 'mana')

    # mages regen mana
    if nickclass == 'mage':
        mana = get_database_value(bot, nick, 'mana')
        combinedmana = mana + mana_to_regen
        if combinedmana <= halfhour_regen_mage_mana_max:
            adjust_database_value(bot, nick, 'mana', halfhour_regen_mage_mana)

    # check stamina not negative and not above max, regen 30 per half hour
    stamina = get_database_value(bot, nick, 'stamina')
    if nickrace == 'centaur':
        stamina_to_regen = stamina_to_regen * 2
    if int(stamina) < 0:
        reset_database_value(bot, nick, 'stamina')
    if int(stamina) > staminamax:
        set_database_value(bot, nick, 'stamina', staminamax)
    combinedstamina = stamina + stamina_to_regen
    if combinedstamina <= staminamax:
        adjust_database_value(bot, nick, 'stamina', stamina_to_regen)

    # Check armor is positive
    for armor in stats_armor:
        armorstat = get_database_value(bot, nick, armor) or 0
        if armorstat < 0:
            reset_database_value(bot, nick, armor)

    # Check for negative loot
    for loot in stats_loot:
        lootstat = get_database_value(bot, nick, loot) or 0
        if lootstat < 0:
            reset_database_value(bot, nick, loot)

    # Check bounty
    bounty = get_database_value(bot, nick, 'bounty')
    if bounty < 0:
        reset_database_value(bot, nick, 'bounty')

    # Check coin
    coin = get_database_value(bot, nick, 'coin')
    if coin < 0:
        reset_database_value(bot, nick, 'coin')

    # check SPECIAL modifiers
    for effect in duels_special_full:
        geteffects = get_database_value(bot, nick, effect+"_effect") or 0
        if geteffects:
            geteffectstime = duels_time_since(bot, nick, effect+"_effect_time") or 0
            geteffectsduration = get_database_value(bot, nick, effect+"_effect_duration") or 0
            if geteffectstime > geteffectsduration:
                reset_database_value(bot, nick, effect+"_effect")
                reset_database_value(bot, nick, effect+"_effect_time")
                reset_database_value(bot, nick, effect+"_effect_duration")

    return


# combine class and race for SPECIAL
def duels_special_combination(bot, nick):

    nickclass = get_database_value(bot, nick, 'class') or 0
    nickrace = get_database_value(bot, nick, 'race') or 0

    if not nickclass:
        classstats = [0, 0, 0, 0, 0, 0, 0, 0]
    else:
        classstats = eval("duels_character_special_class_"+nickclass)

    if not nickrace:
        racestats = [0, 0, 0, 0, 0, 0, 0, 0]
    else:
        racestats = eval("duels_character_special_race_"+nickrace)

    combinedstats = []

    for statname, classstat, racestat in zip(duels_special_full, classstats, racestats):
        mathed = classstat + racestat

        # check SPECIAL modifiers
        geteffects = get_database_value(bot, nick, statname+"_effect") or 0
        if geteffects:
            geteffectstime = duels_time_since(bot, nick, statname+"_effect_time") or 0
            geteffectsduration = get_database_value(bot, nick, statname+"_effect_duration") or 0
            if geteffectstime > geteffectsduration:
                reset_database_value(bot, nick, statname+"_effect")
                reset_database_value(bot, nick, statname+"_effect_time")
                reset_database_value(bot, nick, statname+"_effect_duration")
            else:
                mathed = mathed + geteffects

        combinedstats.append(mathed)

    if combinedstats == []:
        combinedstats = [1, 1, 1, 1, 1, 1, 1, 1]
    return combinedstats


# cleaner display of SPECIAL
def duels_special_humanize(bot, statsarray):
    strength = spicemanip.main(statsarray, 1)
    perception = spicemanip.main(statsarray, 2)
    endurance = spicemanip.main(statsarray, 3)
    charisma = spicemanip.main(statsarray, 4)
    intelligence = spicemanip.main(statsarray, 5)
    agility = spicemanip.main(statsarray, 6)
    luck = spicemanip.main(statsarray, 7)
    magic = spicemanip.main(statsarray, 8)
    return strength, perception, endurance, charisma, intelligence, agility, luck, magic


def duels_special_get(bot, nick, typewanted):

    # Nick base
    nickclass = get_database_value(bot, nick, 'class') or 'unknown'
    nickrace = get_database_value(bot, nick, 'race') or 'unknown'

    # combined
    combinedstats = duels_special_combination(bot, nick)

    # humanized
    strength, perception, endurance, charisma, intelligence, agility, luck, magic = duels_special_humanize(bot, combinedstats)

    typewanted = eval(typewanted)

    return typewanted


# Player Death Handling
def duels_death_handling(bot, duels, inflicter, inflictee):

    textarray = []
    if inflicter.actual == inflictee.actual:
        textarray.append(inflictee.nametext + " committed suicide, forcing a respawn.")
    elif inflictee.actual == 'duelsmonster':
        textarray.append(inflictee.nametext + ' has been slain!!')
    else:
        textarray.append(inflictee.nametext + ' dies forcing a respawn!!')

    # Respawn location
    if inflictee.actual != 'duelsmonster':
        textarray.append(inflictee.nametext + ' respawns in town')
        duels_location_move(bot, duels, inflictee.actual, 'town')

    # Reset mana
    if inflictee.mana:
        reset_database_value(bot, inflictee.actual, 'mana')
        if inflictee.actual != 'duelsmonster':
            textarray.append(inflictee.nametext + " loses all mana.")

    # Health
    for part in duels_bodyparts:
        maxhealthpart = spicemanip.main([part, duels_bodyparts, duels_bodyparts_health], 'index')
        if inflicter.actual == inflictee.actual:
            healthtoset = maxhealthpart
        else:
            healthtoset = duels.tierscaling * int(maxhealthpart)
        set_database_value(bot, inflictee.actual, part, healthtoset)

    # update kills/deaths
    if inflicter.actual != inflictee.actual:
        adjust_database_value(bot, inflicter.actual, 'kills', 1)
    adjust_database_value(bot, inflictee.actual, 'respawns', 1)

    # bounty
    if inflictee.actual != 'duelsmonster':
        if inflictee.bounty:
            if inflicter.actual == inflictee.actual:
                textarray.append(inflictee.nametext + " wastes the bounty of " + str(inflictee.bounty) + " coin.")
            else:
                textarray.append(inflicter.nametext + " wins a bounty of " + str(inflictee.bounty) + " that was placed on " + inflictee.nametext + ".")
                adjust_database_value(bot, inflicter.actual, 'coin', inflictee.bounty)
            reset_database_value(bot, inflictee.actual, 'bounty')

    # Stamina
    if inflicter.actual == inflictee.actual:
        set_database_value(bot, inflictee.actual, 'stamina', 12)
    else:
        if inflictee.actual != 'duelsmonster':
            set_database_value(bot, inflictee.actual, 'stamina', staminamax)

    lootedarray = []
    if inflictee.Class != 'ranger' or inflictee.actual == inflicter.actual:
        for x in duels_loot_view:
            gethowmany = get_database_value(bot, inflictee.actual, x)
            if gethowmany:
                if gethowmany > 1:
                    lootedarray.append(str(str(gethowmany) + " "+x + "s"))
                else:
                    lootedarray.append(x)
                if inflicter.actual != inflictee.actual:
                    adjust_database_value(bot, inflicter.actual, x, gethowmany)
                reset_database_value(bot, inflictee.actual, x)
        if inflicter.actual == inflictee.actual:
            if lootedarray != []:
                textarray.append(inflictee.nametext + " loses all loot.")
        else:
            if lootedarray != []:
                illgottenbooty = spicemanip.main(lootedarray, "list")
                textarray.append(inflictee.nametext + " loses all loot to " + inflicter.nametext + ". Contents included: " + str(illgottenbooty))
    else:
        textarray.append(inflictee.nametextpos + " status as a ranger prevented the loss of loot, and is now stored in their locker in town.")
        for x in duels_loot_view:
            gethowmany = get_database_value(bot, inflictee.actual, x)
            if gethowmany:
                adjust_database_value(bot, inflictee.actual, x, -abs(gethowmany))
                adjust_database_value(bot, inflictee.actual, x+"_locker", gethowmany)

    if inflictee.actual == 'duelsmonster':
        textarray.append("Who's the real monster?")

    return textarray


# Total Health
def duels_get_health(bot, nick):
    totalhealth = 0
    for x in duels_bodyparts:
        gethowmany = get_database_value(bot, nick, x) or 0
        if gethowmany:
            totalhealth += gethowmany
    return totalhealth


# Non-Crippled Body Parts
def duels_nick_bodyparts_remaining(bot, nick):
    currentbodypartsarray = []
    for x in duels_bodyparts:
        gethowmany = get_database_value(bot, nick, x)
        if gethowmany:
            currentbodypartsarray.append(x)
    return currentbodypartsarray


# Inflicter causes damage to inflictee bodypart, and any defenses come into play
def duels_effect_inflict(bot, duels, inflicter, inflictee, bodypartselection, effect, effectamount, situation):

    # Basics
    dispmsgarray = []

    # Bodypart
    bodypartinflictarray = []
    if bodypartselection != 'none' and situation != 'chance_event':
        if bodypartselection == 'random':
            bodypart, bodypartname = duels_bodypart_select(bot, inflictee.actual)
            bodypartinflictarray.append(bodypart)
        elif bodypartselection != 'all':
            bodypartinflictarray.append(bodypartselection)
        else:
            for bodypart in duels_bodyparts:
                if effectamount > 0:
                    inflicteebodyparthealth = get_database_value(bot, inflictee.actual, bodypart)
                    if inflicteebodyparthealth > 0:
                        bodypartinflictarray.append(bodypart)
                else:
                    totalhealth = get_database_value(bot, inflictee.actual, bodypart)
                    gethowmanymax = spicemanip.main([bodypart, duels_bodyparts, duels_bodyparts_health], 'index')
                    gethowmanymax = gethowmanymax * duels.tierscaling
                    totalhealthmax = int(gethowmanymax)
                    if totalhealth < totalhealthmax:
                        bodypartinflictarray.append(bodypart)

    if situation in ['loot', 'magic']:
        if inflictee.race == 'fiend' and inflicter.actual != inflictee.actual:
            dispmsgarray.append(inflictee.nametext + "  is a fiend and can only self-use " + situation)
            return dispmsgarray

    if effect in duels_special_full:
        geteffects = get_database_value(bot, inflictee.actual, effect+"_effect") or 0
        if geteffects and situation != 'tavern':
            geteffectstime = duels_time_since(bot, inflictee.actual, effect+"_effect_time") or 0
            geteffectsduration = get_database_value(bot, inflictee.actual, effect+"_effect_duration") or 0
            if geteffectstime <= geteffectsduration:
                dispmsgarray.append(inflictee.nametextpos + " "+effect+" is unaffected due to an existing condition")
                return dispmsgarray
            reset_database_value(bot, inflictee.actual, effect+"_effect")
            reset_database_value(bot, inflictee.actual, effect+"_effect_time")
            reset_database_value(bot, inflictee.actual, effect+"_effect_duration")
        adjust_database_value(bot, inflictee.actual, effect+"_effect", effectamount)
        set_database_value(bot, inflictee.actual, effect+"_effect_time", duels.now)
        if situation == 'chance_event':
            durationtime = bodypartselection
        elif situation == 'tavern':
            durationtime = randint(900, 1800)
        else:
            antiagility = 10 - inflictee.agility
            if antiagility <= 0:
                durationtime = 0
            else:
                durationtime = randint(antiagility * 10, 1800)
        set_database_value(bot, inflictee.actual, effect+"_effect_duration", durationtime)
        if effectamount > 0:
            effectamounttext = str("+"+str(effectamount))
        else:
            effectamounttext = effectamount
        dispmsgarray.append(inflictee.nametextpos + " "+effect+" has a " + str(effectamounttext) + " effect for the next " + str(duels_hours_minutes_seconds(durationtime)))
        return dispmsgarray

    if effect == 'timepotion':
        dispmsgarray.append("Removal of Timeouts.")
        reset_database_value(bot, inflictee.actual, 'lastfought')
        channellastinstigator = get_database_value(bot, 'duelrecorduser', 'lastinstigator') or bot.nick
        if channellastinstigator == inflictee.actual:
            reset_database_value(bot, 'duelrecorduser', 'lastinstigator')
        for k in duels_loot_timepotion_targetarray:
            targetequalcheck = get_database_value(bot, bot.nick, k) or bot.nick
            if targetequalcheck == inflictee.actual:
                reset_database_value(bot, bot.nick, k)
        for j in duels_loot_timepotion_timeoutarray:
            reset_database_value(bot, inflictee.actual, j)
        return dispmsgarray

    if effect == 'stamina':
        dispmsgarray.append("Restoration of " + str(effectamount) + " stamina.")
        adjust_database_value(bot, inflictee.actual, 'stamina', effectamount)
        return dispmsgarray

    if effect == 'mana':
        dispmsgarray.append("Restoration of " + str(effectamount) + " mana.")
        adjust_database_value(bot, inflictee.actual, 'mana', effectamount)
        return dispmsgarray

    if effect in ['damage', 'healing', 'health']:

        # No effectamount
        if effectamount == 0 or bodypartinflictarray == []:
            dispmsgarray.append(inflictee.nametextpos + " health is unaffected")
            return dispmsgarray

        # effectamount is healing
        if effectamount < 0:

            effectamount = abs(effectamount)
            splitdamage = int(effectamount) / len(bodypartinflictarray)
            for bodypart in bodypartinflictarray:
                currentsplitdamage = int(splitdamage)

                # current health of part
                parthealth = get_database_value(bot, inflictee.actual, bodypart) or 0

                # find the maximum allowed health for part
                maxhealthpart = spicemanip.main([bodypart, duels_bodyparts, duels_bodyparts_health], 'index')

                # scale the health maximum
                currenthealthtier = duels.tierscaling * int(maxhealthpart)

                # Health Regen
                if parthealth < currenthealthtier:
                    combinedhealth = parthealth + currentsplitdamage
                    if combinedhealth < currenthealthtier:
                        adjust_database_value(bot, inflictee.actual, bodypart, currentsplitdamage)
                    else:
                        set_database_value(bot, inflictee.actual, bodypart, currenthealthtier)
            if len(bodypartinflictarray) > 1:
                totalhealth = 0
                totalhealthmax = 0
                for x in duels_bodyparts:
                    gethowmany = get_database_value(bot, inflictee.actual, x)
                    totalhealth = totalhealth + gethowmany
                    gethowmanymax = spicemanip.main([x, duels_bodyparts, duels_bodyparts_health], 'index')
                    gethowmanymax = gethowmanymax * duels.tierscaling
                    gethowmanymax = int(gethowmanymax)
                    totalhealthmax = totalhealthmax + gethowmanymax
                if totalhealth != totalhealthmax:
                    dispmsgarray.append(inflictee.nametext + " gains " + str(effectamount) + " health, bringing them to " + str(totalhealth) + " of " + str(totalhealthmax))
                else:
                    dispmsgarray.append(inflictee.nametext + " gains " + str(effectamount) + " health, bringing them to full health")
            else:
                singlebodypart = spicemanip.main(bodypartinflictarray, 1)
                totalhealth = get_database_value(bot, inflictee.actual, singlebodypart)
                gethowmanymax = spicemanip.main([singlebodypart, duels_bodyparts, duels_bodyparts_health], 'index')
                gethowmanymax = gethowmanymax * duels.tierscaling
                totalhealthmax = int(gethowmanymax)
                singlebodypart = singlebodypart.replace("_", " ")
                if totalhealth != totalhealthmax:
                    dispmsgarray.append(inflictee.nametext + " gains " + str(effectamount) + " health for their " + singlebodypart + ", bringing it to " + str(totalhealth) + " of " + str(totalhealthmax))
                else:
                    dispmsgarray.append(inflictee.nametext + " gains " + str(effectamount) + " health for their " + singlebodypart + ", bringing it to full health")

        else:

            # Rogues dont take effectamount from bot
            if inflicter.actual == bot.nick:
                if inflictee.Class == 'rogue':
                    dispmsgarray.append(inflictee.nametext + " takes no "+effect+" in this encounter")
                    return dispmsgarray

            # Rogues don't self-harm
            if inflicter.actual == inflictee.actual:
                if inflictee.Class == 'rogue':
                    dispmsgarray.append(inflictee.nametext + " takes no "+effect+" in this encounter")
                    return dispmsgarray

            # Agility roll away
            if effectamount > 0 and situation != 'loot' and inflictee.actual != 'duelsmonster' and inflicter.actual != inflictee.actual:
                if inflictee.agility * 10 > 100:
                    dodge = 100
                else:
                    dodge = randint(inflictee.agility * 10, 100)
                if dodge > 90:
                    effectamount = 0
                    dispmsgarray.append(inflictee.nametext + " manages to dodge out of the way. ")
                    return dispmsgarray

            # Shields
            if effectamount > 0 and situation != 'loot' and inflicter.actual != inflictee.actual:
                if inflictee.shield:
                    damagemath = int(inflictee.shield) - effectamount
                    if int(damagemath) > 0:
                        adjust_database_value(bot, inflictee.actual, 'shield', -abs(effectamount))
                        effectamount = 0
                        absorbed = 'all'
                    else:
                        absorbed = damagemath + effectamount
                        effectamount = abs(damagemath)
                        reset_database_value(bot, inflictee.actual, 'shield')
                    dispmsgarray.append(inflictee.nametext + " magic shield absorbs " + str(absorbed) + " of the "+effect+".")
                    if effectamount <= 0:
                        return dispmsgarray

            # Endurance check
            if effectamount > 0:
                endurancemath = inflictee.endurance * 10
                if effectamount <= endurancemath:
                    effectamount = 0
                else:
                    endurancemath = randint(int(endurancemath), int(effectamount))
                    damagenew = effectamount - endurancemath
                    if damagenew <= 0:
                        effectamount == 0
                    else:
                        effectamount = damagenew
                if effectamount <= 0:
                    dispmsgarray.append(inflictee.nametextpos + " thick skin allowed them to take no "+effect+".")
                    return dispmsgarray

            # Bodypart inflict array
            lootdamagetaken = 0
            inflicteedeath = 0
            if effectamount > 0:
                splitdamage = int(effectamount) / len(bodypartinflictarray)
                for bodypart in bodypartinflictarray:
                    if not inflicteedeath:
                        currentsplitdamage = int(splitdamage)

                        bodypartname = bodypart.replace("_", " ")

                        # Armor
                        if currentsplitdamage > 0 and situation != 'magic' and situation != 'loot':
                            armortype = spicemanip.main([bodypart, duels_bodyparts, stats_armor], 'index')
                            armorinflictee = get_database_value(bot, inflictee.actual, armortype) or 0
                            if armorinflictee:
                                armorname = armortype.replace("_", " ")
                                adjust_database_value(bot, inflictee.actual, armortype, -1)
                                damagepercent = randint(1, armor_relief_percentage) / 100
                                damagereduced = splitdamage * damagepercent
                                damagereduced = int(damagereduced)
                                currentsplitdamage = currentsplitdamage - damagereduced
                                if int(damagereduced) > 0:
                                    armorinflictee = get_database_value(bot, inflictee.actual, armortype) or 0
                                    if currentsplitdamage <= 0:
                                        damagereduced = "all"
                                    damagetext = str(inflictee.nametextpos + " " + armorname + " alleviated " + str(damagereduced) + " of the damage")
                                    if armorinflictee <= 0:
                                        reset_database_value(bot, inflictee.actual, armortype)
                                        damagetext = str(damagetext + ", causing the armor to break!")
                                    elif armorinflictee <= 5:
                                        damagetext = str(damagetext + ", causing the armor to be in need of repair!")
                                    else:
                                        damagetext = str(damagetext + ".")
                                    dispmsgarray.append(damagetext)
                                    if currentsplitdamage <= 0:
                                        return dispmsgarray

                        if currentsplitdamage > 0:
                            if situation == 'monster' or situation == 'random' or situation == 'combat' or situation == 'target' or situation in duels_commands_events:
                                dispmsgarray.append(inflicter.nametext + " manages to deal " + str(currentsplitdamage) + " "+effect+" to "+inflictee.nametextpos+" " + bodypartname)
                            elif situation == 'loot' or situation == 'magic':
                                lootdamagetaken = lootdamagetaken + currentsplitdamage
                            else:
                                dispmsgarray.append(inflictee.nametext + " takes " + str(currentsplitdamage) + " "+effect+" to the " + bodypartname)
                            adjust_database_value(bot, inflictee.actual, bodypart, -abs(currentsplitdamage))

                        if currentsplitdamage > 0:
                            if situation in duels_commands_events:
                                adjust_database_value(bot, inflicter.actual, 'combat_track_damage_dealt', currentsplitdamage)
                                adjust_database_value(bot, inflictee.actual, 'combat_track_damage_taken', currentsplitdamage)

                        finishthem = 0
                        if bodypart == 'head' or bodypart == 'torso':
                            inflicteecritical = get_database_value(bot, inflictee.actual, bodypart)
                            if inflicteecritical <= 0:
                                if inflictee.actual == 'duelsmonster' or inflicter.actual == 'duelsmonster' or inflicter.actual == bot.nick or inflicter.actual == inflictee.actual:
                                    killtextarray = duels_death_handling(bot, duels, inflicter, inflictee)
                                    for j in killtextarray:
                                        dispmsgarray.append(j)
                                    reset_database_value(bot, 'duelsmonster', 'last_monster')
                                else:
                                    finishthem = 1
                                if situation in duels_commands_events:
                                    if inflicter.actual != inflictee.actual:
                                        adjust_database_value(bot, inflicter.actual, 'combat_track_kills', 1)
                                    adjust_database_value(bot, inflictee.actual, 'combat_track_deaths', 1)
                                inflicteedeath = 1

                        if duels_get_health(bot, inflictee.actual) < deathblow_amount or finishthem:
                            if inflicter.actual != inflictee.actual and inflicter.actual != 'duelsmonster' and inflictee.actual != 'duelsmonster':
                                currentdeathblowcheck = get_database_value(bot, inflictee.actual, 'deathblow')
                                if not currentdeathblowcheck:
                                    adjust_database_array(bot, inflicter.actual, [inflictee.actual], 'deathblowtargetarray', 'add')
                                    set_database_value(bot, inflictee.actual, 'deathblow', 1)
                                    set_database_value(bot, inflictee.actual, 'deathblowkiller', inflicter.actual)
                                    set_database_value(bot, 'duelrecorduser', 'deathblowkiller', inflicter.actual)
                                    adjust_database_array(bot, 'duelrecorduser', [inflicter.actual], 'deathblowmessagepeoplearray', 'add')
                                    adjust_database_array(bot, inflicter.actual, [inflictee.actual], 'deathblowtargetsnew', 'add')
                            else:
                                killtextarray = duels_death_handling(bot, duels, inflicter, inflictee)
                                for j in killtextarray:
                                    dispmsgarray.append(j)
                            if not inflicteedeath:
                                inflicteedeath = 1

            if not inflicteedeath:

                if situation == 'loot' or situation == 'magic':
                    dispmsgarray.append(inflictee.nametext + " takes " + str(lootdamagetaken) + " " + effect)

                crippledarray = []
                for bodypart in bodypartinflictarray:
                    playercurrenthealthbody = get_database_value(bot, inflictee.actual, bodypart)
                    if playercurrenthealthbody <= 0:
                        crippledarray.append(bodypart)
                if crippledarray != []:
                    bodypartnamelist = spicemanip.main(crippledarray, "list")
                    dispmsgarray.append(inflictee.nametextpos + " now crippled bodyparts: " + bodypartnamelist)

    return dispmsgarray


# Stats View
def duels_stats_view(bot, duels, target_stats_view, targetbio, customview, actualstatsview):

    # empty array
    dispmsgarray = []

    # Get the amounts
    for x in target_stats_view:
        if x == 'health':
            gethowmany = duels_get_health(bot, targetbio.actual)
        elif x == 'location':
            gethowmany = duels_get_location(bot, duels, targetbio.actual)
        elif x == 'charsheet':
            gethowmany = 1
        elif x in stats_view_functions:
            scriptdef = str('duels_get_' + x + '(bot,targetbio.actual)')
            gethowmany = eval(scriptdef)
        elif x == 'pepper':
            gethowmany = targetbio.pepper
        elif x.startswith("timeout_") or x.startswith("lastfullroom"):
            gethowmany = duels_time_since(bot, 'duelrecorduser', x) or 0
            if gethowmany >= eval(x):
                gethowmany = 0
        elif x in stats_armor:
            gethowmany = get_database_value(bot, targetbio.actual, x)
            if not gethowmany:
                gethowmany = 'stockarmor'
        elif x in stats_character:
            gethowmany = eval("targetbio."+x)
            geteffects = get_database_value(bot, targetbio.actual, x+"_effect") or 0
            if geteffects:
                if geteffects > 0:
                    geteffectstext = str("+"+str(geteffects))
                else:
                    geteffectstext = str(geteffects)
                geteffectstime = duels_time_since(bot, targetbio.actual, x+"_effect_time") or 0
                geteffectsduration = get_database_value(bot, targetbio.actual, x+"_effect_duration") or 0
                if geteffectstime <= geteffectsduration:
                    gethowmany = gethowmany - geteffects
                    gethowmany = str(str(gethowmany) + "[" + str(geteffectstext) + "]")
        else:
            gethowmany = get_database_value(bot, targetbio.actual, x)

        # display those amounts
        if gethowmany:
            statname = x
            if x == 'charsheet':
                statname = 'statsviewignoreme'
                dispmsgarray.append(targetbio.nametext + " is a " + targetbio.gender + " level " + str(targetbio.tier) + " " + targetbio.race + " " + targetbio.Class + ".")
            if x == 'streak_type_current':
                statname = 'statsviewignoreme'
                if gethowmany == 'win':
                    streak_count = get_database_value(bot, targetbio.actual, 'streak_win_current') or 0
                    typeofstreak = 'winning'
                elif gethowmany == 'loss':
                    streak_count = get_database_value(bot, targetbio.actual, 'streak_loss_current') or 0
                    typeofstreak = 'losing'
                else:
                    streak_count = 0
                if streak_count > 1 and gethowmany != 'none':
                    dispmsgarray.append("Currently on a " + typeofstreak + " streak of " + str(streak_count) + ".")
            if x == 'streak_win_best':
                statname = 'Best Win streak'
            if x == 'streak_loss_best':
                statname = 'Worst Losing streak'
            if x == 'weaponslocker_lastweaponused':
                statname = "Last Weapon Used"
            if x == 'winlossratio':
                gethowmany = format(gethowmany, '.3f')
            if x.startswith("timeout_") or x.startswith("lastfullroom"):
                xname = x.replace("timeout_", " ")
                xname = x.replace("lastfullroom", " ")
                statname = str(xname + " timeout")
                gethowmany = str(duels_hours_minutes_seconds((eval(x) - gethowmany)))
            if x in duels_bodyparts:
                statname = x.replace("_", " ")
                gethowmanymax = spicemanip.main([x, duels_bodyparts, duels_bodyparts_health], 'index')
                gethowmanymax = gethowmanymax * duels.tierscaling
                gethowmanymax = int(gethowmanymax)
                if targetbio.race == 'vampire':
                    gethowmany = -abs(gethowmany)
                    gethowmanymax = -abs(gethowmanymax)
                gethowmany = str(str(gethowmany) + "/" + str(gethowmanymax))
            if x in stats_armor:
                if gethowmany == 'stockarmor':
                    statname = spicemanip.main([x, stats_armor, duels_default_armor], 'index')
                    statname = statname.replace("_", " ")
                    gethowmany = 'poor'
                else:
                    statname = x.replace("_", " ")
                    gethowmanymax = spicemanip.main([x, duels_forge_items, duels_armor_durabilitymax], 'index')
                    if targetbio.Class == 'blacksmith':
                        gethowmanymax = gethowmanymax + 5
                    gethowmanymax = gethowmanymax * duels.tierscaling
                    gethowmanymax = int(gethowmanymax)
                    gethowmany = str(str(gethowmany) + "/" + str(gethowmanymax))
            if x == 'health':
                statname = 'Total Health'
                totalhealthmax = 0
                for j in duels_bodyparts:
                    gethowmanymax = spicemanip.main([j, duels_bodyparts, duels_bodyparts_health], 'index')
                    gethowmanymax = gethowmanymax * duels.tierscaling
                    gethowmanymax = int(gethowmanymax)
                    totalhealthmax += gethowmanymax
                if targetbio.race == 'vampire':
                    gethowmany = -abs(gethowmany)
                    totalhealthmax = -abs(totalhealthmax)
                gethowmany = str(str(gethowmany) + "/" + str(totalhealthmax))
            if not str(gethowmany).isdigit() and str(gethowmany) not in duels.users_all_allchan:
                gethowmany = str(gethowmany).title()
            if statname != 'statsviewignoreme':
                statname = statname.title()
                dispmsgarray.append(statname + "=" + str(gethowmany))

    # Display begginning
    dispmsgarrayb = []
    target_stats_view = get_database_value(bot, targetbio.actual, 'stats_view')
    if dispmsgarray != []:
        if not customview and actualstatsview == 'stats':
            dispmsgarrayb.append("("+targetbio.pepper.title() + ") " + targetbio.nametextpos + " " + actualstatsview.title() + ":")
        elif actualstatsview == 'armor':
            dispmsgarrayb.append(targetbio.nametextpos + " " + actualstatsview.title() + " Durability:")
        else:
            dispmsgarrayb.append(targetbio.nametextpos + " " + actualstatsview.title() + ":")
        for y in dispmsgarray:
            dispmsgarrayb.append(y)
    else:
        if customview and actualstatsview == 'stats':
            dispmsgarrayb.append(duels.instigator + ", It looks like your current stats settings don't have values.")
        else:
            dispmsgarrayb.append(duels.instigator + ", It looks like " + targetbio.nametext + " has no " + actualstatsview.title() + ".")
    osd(bot, duels.channel_current, 'say', dispmsgarrayb)
    return


"""
Tiers
"""


# command to number
def duels_tier_command_to_number(bot, command):
    tiercommandeval = 0
    for i in range(0, 16):
        tiercheck = eval("duels_commands_tier_unlocks_"+str(i))
        if command.lower() in tiercheck:
            tiercommandeval = int(i)
            continue
    return tiercommandeval


# number to pepper
def duels_tier_number_to_pepper(bot, tiernumber):
    if not tiernumber:
        pepper = 'n00b'
    else:
        pepper = spicemanip.main(duels_commands_pepper_levels, tiernumber + 1)
        pepper = pepper.title()
    return pepper


# number to pepper
def duels_tier_number_to_pepper_index(bot, pepper):
    tiernumber = duels_commands_pepper_levels.index(pepper.lower())
    return tiernumber


# xp to tiernumber
def duels_tier_xp_to_number(bot, xp):
    tiernumber = 0
    smallerxparray = []
    for x in duels_commands_xp_levels:
        if x <= xp:
            smallerxparray.append(x)
    if smallerxparray != []:
        bigestxp = max(smallerxparray)
        tiernumber = duels_commands_xp_levels.index(bigestxp)
    return tiernumber


# nick pepper
def duels_tier_nick_to_pepper(bot, nick):
    if nick == bot.nick:
        pepper = 'Dragon Breath Chilli'
        return pepper
    xp = get_database_value(bot, nick, 'xp') or 0
    if not xp:
        pepper = 'n00b'
        return pepper
    xptier = duels_tier_xp_to_number(bot, xp)
    pepper = duels_tier_number_to_pepper(bot, xptier)
    # advance respawn tier
    tiernumber = duels_tier_number_to_pepper_index(bot, pepper)
    currenttier = get_database_value(bot, 'duelrecorduser', 'tier') or 0
    if tiernumber > currenttier:
        set_database_value(bot, 'duelrecorduser', 'tier', tiernumber)
    nicktier = get_database_value(bot, nick, 'tier')
    if tiernumber != nicktier:
        set_database_value(bot, nick, 'tier', tiernumber)
    pepper = pepper.title()
    return pepper


# current tier to ratio
def duels_tier_current_to_ratio(bot):
    currenttier = get_database_value(bot, 'duelrecorduser', 'tier') or 1
    tierratio = spicemanip.main(duels_commands_tier_ratio, currenttier) or 1
    return tierratio


def duels_druid_current_array(bot, target):
    druidanimals = []
    targettier = get_database_value(bot, target, 'tier') or 0
    for i in range(0, targettier + 1):
        tiercheck = eval("duels_druid_creatures_"+str(i))
        for x in tiercheck:
            druidanimals.append(x)
    return druidanimals


"""
Location
"""


def duels_location_valid_commands(bot, duels, nick):

    nick_location = duels_get_location(bot, duels, nick)

    rebuiltcommandarray = []
    for validcommand in duels.commands_valid:
        rebuiltcommandarray.append(validcommand)

    removecommandsarray = []
    for location in duels_commands_locations:
        if location != nick_location:
            removecommandsarray.append(location)

    for location in removecommandsarray:
        locationcommands = eval("duels_commands_"+location)
        for command in locationcommands:
            if command in rebuiltcommandarray:
                rebuiltcommandarray.remove(command)

    return rebuiltcommandarray


def duels_location_search(bot, duels, command):
    commandlocation = 'arena'
    for location in duels_commands_locations:
        locationcommands = eval("duels_commands_"+location)
        if command.lower() in locationcommands:
            commandlocation = location
            continue
    return commandlocation


def duels_location_move(bot, duels, user, newlocation):

    for location in duels_commands_locations:
        current_location_list = eval("duels.users_current_allchan_" + location)
        if user in current_location_list:
            current_location_list.remove(user)
            adjust_database_array(bot, 'duelrecorduser', user, location+"_users", 'del')
    for location in duels_commands_locations:
        current_location_list = eval("duels.users_current_allchan_" + location)
        if location == newlocation:
            current_location_list.append(user)
            adjust_database_array(bot, 'duelrecorduser', user, location+"_users", 'add')


def duels_get_location(bot, duels, user):
    userlocation = 'town'
    for location in duels_commands_locations:
        current_location_list = eval("duels.users_current_allchan_"+location)
        if user in current_location_list:
            userlocation = location
    return userlocation


"""
Merchant
"""


@sopel.module.interval(3600)
@sopel.module.thread(True)
def duels_merchant_restock(bot):

    # Current inventory
    merchinv = duels_merchant_inventory(bot)

    # half full
    shelfhalf = duels_merchant_inv_max / 2

    for lootitem in duels_loot_items:
        current_loot_cost = spicemanip.main([lootitem, duels_loot_items, duels_loot_cost], 'index')
        if current_loot_cost != 'no':
            merchquant = eval(str("merchinv."+lootitem))

            # Refill shelf if half full or less
            if merchquant <= shelfhalf or merchquant == 0:
                set_database_value(bot, 'duelsmerchant', lootitem, duels_merchant_inv_max)

            # supply and demand, usage increases value, if inventory is high
            if merchquant >= duels_merchant_inv_max:
                adjust_database_value(bot, 'duelsmerchant', str("vendor_track_value_"+lootitem), -1)
            elif merchquant > shelfhalf and merchquant < duels_merchant_inv_max:
                adjust_database_value(bot, 'duelsmerchant', str("vendor_track_value_"+lootitem), 1)
            elif merchquant <= shelfhalf:
                adjust_database_value(bot, 'duelsmerchant', str("vendor_track_value_"+lootitem), 2)


# How much inventory does the merchant have?
def duels_merchant_inventory(bot):

    merchinv = class_create('merchant')

    # New Vendor?
    merchantinitialinv = get_database_value(bot, 'duelsmerchant', 'newvendor')
    if not merchantinitialinv:
        for x in duels_loot_items:
            current_loot_cost = spicemanip.main([x, duels_loot_items, duels_loot_cost], 'index')
            if current_loot_cost != 'no':
                set_database_value(bot, 'duelsmerchant', x, duels_merchant_inv_max)
                currentvalue = str("merchinv."+x+"="+str(duels_merchant_inv_max))
                exec(currentvalue)
                current_loot_value = get_database_value(bot, 'duelsmerchant', str("vendor_track_value_"+x))
                current_loot_value = current_loot_value / 100
                current_loot_value = current_loot_value * current_loot_cost
                current_loot_cost = current_loot_cost + current_loot_value
                if current_loot_cost < 10:
                    current_loot_cost = 10
                current_loot_cost = str("merchinv."+x+"_cost="+str(current_loot_cost))
                exec(current_loot_cost)
        set_database_value(bot, 'duelsmerchant', 'newvendor', 1)
        return merchinv

    # Normal vendor
    for x in duels_loot_items:
        current_loot_cost = spicemanip.main([x, duels_loot_items, duels_loot_cost], 'index')
        if current_loot_cost != 'no':
            gethowmany = get_database_value(bot, 'duelsmerchant', x)
            if not gethowmany:
                set_database_value(bot, 'duelsmerchant', x, duels_merchant_inv_max)
                gethowmany = duels_merchant_inv_max
            currentvalue = str("merchinv."+x+"="+str(gethowmany))
            exec(currentvalue)
            current_loot_value = get_database_value(bot, 'duelsmerchant', str("vendor_track_value_"+x))
            current_loot_value = current_loot_value / 100
            current_loot_value = current_loot_value * current_loot_cost
            current_loot_cost = current_loot_cost + current_loot_value
            if current_loot_cost < 10:
                current_loot_cost = 10
            current_loot_cost = str("merchinv."+x+"_cost="+str(current_loot_cost))
            exec(current_loot_cost)
    return merchinv


"""
Criteria to Run duels
"""


# Criteria to duel, verbose
def duels_criteria(bot, player_two, duels, verbose):

    targetbio = duel_target_playerbio(bot, duels, player_two)

    # Guilty until proven Innocent
    validtarget, validtargetmsg = 1, []

    # pending deathblow
    deathblow = get_database_value(bot, targetbio.actual, 'deathblow')
    if deathblow:
        deathblowtargettime = duels_time_since(bot, targetbio.actual, 'deathblowtargettime') or 0
        if deathblowtargettime <= 120:
            deathblowkiller = get_database_value(bot, targetbio.actual, 'deathblowkiller') or 'unknown'
            validtargetmsg.append(targetbio.nametext + " can't run duels for " + str(duels_hours_minutes_seconds((120 - deathblowtargettime))) + " due to a potential deathblow from " + deathblowkiller + ".")
            validtarget = 0

    # not in the arena
    if targetbio.location != 'arena':
        validtargetmsg.append(targetbio.nametext + " is not in the arena at the moment.")
        validtarget = 0

    # Offline
    if targetbio.actual in duels.users_all_allchan and targetbio.actual not in duels.users_current_allchan:
        validtargetmsg.append(targetbio.nametext + " is offline.")
        validtarget = 0

    if verbose and validtargetmsg != []:
        osd(bot, duels.instigator, 'notice', validtargetmsg)

    return validtarget, validtargetmsg


# Target
def duels_target_check(bot, target, duels, instigatorbio):

    # Guilty until proven Innocent
    validtarget = 1
    validtargetmsg = []

    # Target is instigator
    if target == duels.instigator:
        return validtarget, validtargetmsg

    # Null Target
    if not target:
        validtarget = 0
        validtargetmsg.append("You must specify a target.")

    # Bot
    if target == bot.nick or target.lower() in target_ignore_list:
        validtarget = 0
        validtargetmsg.append(target + " can't be targeted.")

    # Target can't be a valid command
    if target.lower() in duels.commands_valid and target.lower() != 'monster' and target.lower() != 'random':
        validtarget = 0
        validtargetmsg.append(target + "'s nick is the same as a valid command for duels.")

    if target.lower() == 'random':
        return validtarget, validtargetmsg

    targetlocation = duels_get_location(bot, duels, target)
    if target.lower() in [x.lower() for x in duels.users_current_allchan] and targetlocation != instigatorbio.location and not duels.admin:
        target = nick_actual(bot, target)
        validtargetmsg.append(target + " is in the "+targetlocation+" area. You are in the "+instigatorbio.location+" area.")
        validtarget = 0

    if target.lower() == 'monster' or target.lower() == 'duelsmonster':
        currentmonster = get_database_value(bot, 'duelsmonster', 'last_monster') or None
        if not currentmonster:
            validtargetmsg.append("There doesn't appear to be a current monster!")
            return validtarget, validtargetmsg
        targetlocation = 'arena'
        if targetlocation != instigatorbio.location and not duels.admin:
            validtargetmsg.append(target + " is in the "+targetlocation+" area. You are in the "+instigatorbio.location+" area.")
            validtarget = 0
        else:
            return validtarget, validtargetmsg

    # Target can't be duelrecorduser
    if target.lower() == 'duelrecorduser':
        validtarget = 0
        validtargetmsg.append(target + "'s nick is unusable for duels.")

    # Offline User
    if target.lower() in [x.lower() for x in duels.users_all_allchan] and target.lower() not in [y.lower() for y in duels.users_current_allchan]:
        validtarget = 0
        target = nick_actual(bot, target)
        validtargetmsg.append(target + " is offline right now.")

    # Opted Out
    if target.lower() in [x.lower() for x in duels.users_current_allchan] and target.lower() not in [j.lower() for j in duels.users_opted] and duels.optcheck:
        target = nick_actual(bot, target)
        validtarget = 0
        validtargetmsg.append(target + " has duels disabled.")

    # None of the above
    if target.lower() not in [y.lower() for y in duels.users_current_allchan] and validtargetmsg == []:
        target = nick_actual(bot, target)
        validtarget = 0
        validtargetmsg.append(target + " is either not here, or not a valid nick to target.")

    deathblow = get_database_value(bot, target, 'deathblow')
    if deathblow:
        deathblowtargettime = duels_time_since(bot, target, 'deathblowtargettime') or 0
        if deathblowtargettime <= 120:
            deathblowkiller = get_database_value(bot, target, 'deathblowkiller') or 'unknown'
            validtargetmsg.append(target + " can't run duels for " + str(duels_hours_minutes_seconds((120 - deathblowtargettime))) + " due to a potential deathblow from " + deathblowkiller + ".")
            validtarget = 0

    if target != duels.instigator and validtarget == 1:
        duels_check_nick_condition(bot, target, duels)

    return validtarget, validtargetmsg


# Events
def duels_events_check(bot, command_main, duels):

    # Guilty until proven Innocent
    validtarget = 1
    validtargetmsg = []

    if duels.users_canduel_allchan == []:
        validtarget = 0
        validtargetmsg.append(duels.instigator + ", It looks like the full channel " + command_main + " event target finder has failed.")
        return validtarget, validtargetmsg

    # Devroom bypass
    if duels.channel_current in duels.duels_dev_channels or duels.admin:
        validtarget = 1
        return validtarget, validtargetmsg
    if not duels.inchannel and len(duels.duels_dev_channels) > 0:
        validtarget = 1
        return validtarget, validtargetmsg

    if duels.instigator not in duels.users_canduel_allchan:
        validtarget = 0
        canduel, validtargetmsgb = duels_criteria(bot, duels.instigator, duels, 0)
        for x in validtargetmsgb:
            validtargetmsg.append(x)

    timeouteval = spicemanip.main([command_main.lower(), duels_timeouts, duels_timeouts_duration], 'index')
    getlastusage = duels_time_since(bot, 'duelrecorduser', str('lastfullroom' + command_main)) or timeouteval
    getlastinstigator = get_database_value(bot, 'duelrecorduser', str('lastfullroom' + command_main + 'instigator')) or bot.nick

    if getlastusage < timeouteval and duels.channel_current not in duels.duels_dev_channels and not duels.admin:
        validtargetmsg.append("Full channel " + command_main + " event can't be used for "+str(duels_hours_minutes_seconds((timeouteval - getlastusage)))+".")
        validtarget = 0

    if getlastinstigator == duels.instigator and duels.channel_current not in duels.duels_dev_channels and not duels.admin:
        validtargetmsg.append("You may not instigate a full channel " + command_main + " event twice in a row.")
        validtarget = 0

    return validtarget, validtargetmsg


"""
User Nicks
"""


# Outputs Nicks with correct capitalization
def nick_actual(bot, nick):
    nick_actual = nick
    for u in bot.users:
        if u.lower() == nick_actual.lower():
            nick_actual = u
            continue
    return nick_actual


# Build Duel Name Text
def duels_nick_names(bot, playerbio, duels):
    duel_nick_order = ['duels_nick_titles', 'duels_nick_character', 'duels_nick_nick', 'duels_nick_pepper', 'duels_nick_magic_attributes', 'duels_nick_armor']
    nickname = ''
    for q in duel_nick_order:
        nickscriptdef = str(q + "(bot, playerbio, duels)")
        nicknameadd = eval(nickscriptdef)
        if nicknameadd != '':
            if nickname != '':
                nickname = str(nickname + " " + nicknameadd)
            else:
                nickname = nicknameadd
    if nickname == '':
        nickname = playerbio.actual
    return nickname


# Titles
def duels_nick_titles(bot, playerbio, duels):

    try:
        # custom title
        if playerbio.nicktitle:
            if playerbio.nicktitle.lower().startswith("the"):
                nickname = str(playerbio.nicktitle)
            else:
                nickname = str("The "+playerbio.nicktitle)
        # duels_bot_owner
        elif playerbio.actual.lower() in bot.config.core.owner.lower():
            nickname = duels_custom_title_bot_owner
        # bot.admin
        elif playerbio.actual in bot.config.core.admins:
            nickname = duels_custom_title_bot_admin
        # development_team
        elif playerbio.actual in development_team:
            nickname = duels_custom_title_devteam
        # OP
        elif bot.privileges[duels.channel_current.lower()][playerbio.actual.lower()] == OP:
            nickname = duels_custom_title_chan_op
    # VOICE
        elif bot.privileges[duels.channel_current.lower()][playerbio.actual.lower()] == VOICE:
            nickname = duels_custom_title_chan_voice
    # else
        else:
            nickname = 'The'
    except KeyError:
        nickname = 'The'
    except AttributeError:
        nickname = 'The'
    return nickname


# Character
def duels_nick_character(bot, playerbio, duels):
    nickname = ''
    if playerbio.actual == bot.nick:
        nickname = ''
    elif playerbio.actual == 'duelsmonster':
        nickname = ''
    else:
        characterarray = []
        if playerbio.race:
            if playerbio.race != 'unknown':
                characterarray.append(playerbio.race.title())
        if playerbio.Class:
            if playerbio.Class != 'unknown':
                characterarray.append(playerbio.Class.title())
        if characterarray != []:
            for x in characterarray:
                if nickname != '':
                    nickname = str(nickname + " " + x)
                else:
                    nickname = x
        else:
            nickname = ''
    return nickname


# nick
def duels_nick_nick(bot, playerbio, duels):
    nickname = playerbio.actual
    return nickname


# Pepper
def duels_nick_pepper(bot, playerbio, duels):
    if not playerbio.pepperstart or playerbio.pepperstart == '':
        nickname = "(n00b)"
    else:
        nickname = str("(" + playerbio.pepperstart.title() + ")")
    return nickname


# Magic
def duels_nick_magic_attributes(bot, playerbio, duels):
    nickname = ''
    magicattrarray = []
    if playerbio.curse_start:
        magicattrarray.append("[Cursed " + str(playerbio.curse_start) + "]")
    if playerbio.shield_start:
        magicattrarray.append("[Magic Shielded " + str(playerbio.shield_start) + "]")
    if magicattrarray != []:
        for x in magicattrarray:
            if nickname != '':
                nickname = str(nickname + x)
            else:
                nickname = x
    else:
        nickname = ''
    return nickname


# Armored
def duels_nick_armor(bot, playerbio, duels):
    nickname = ''
    for x in stats_armor:
        gethowmany = get_database_value(bot, playerbio.actual, x)
        if gethowmany:
            nickname = "{Armored}"
    return nickname


"""
Combat
"""


# winner selection
def duels_combat_selectwinner(bot, competitors, duels, playerbio_maindueler, playerbio_target):
    statcheckarray = ['health', 'xp', 'kills', 'respawns', 'streak_win_current']

    # Bot.nick
    if bot.nick in competitors:
        winner = bot.nick
        return winner

    # Only one person
    uniqueplayers = []
    for user in competitors:
        if user not in uniqueplayers:
            uniqueplayers.append(user)
    if len(uniqueplayers) == 1:
        winner = spicemanip.main(uniqueplayers, 1)
        return winner

    # Dev_win
    maindueler_dev = get_database_value(bot, playerbio_maindueler.actual, 'dev_win')
    target_dev = get_database_value(bot, playerbio_target.actual, 'dev_win')
    if maindueler_dev or target_dev:
        if maindueler_dev and not target_dev:
            winner = playerbio_maindueler.actual
            return winner
        elif not maindueler_dev and target_dev:
            winner = playerbio_target.actual
            return winner

    # everyone gets a roll
    playerbio_maindueler.winnerselection = 1
    playerbio_target.winnerselection = 1

    # random roll
    randomrollwinner = spicemanip.main(competitors, 'random')
    if randomrollwinner == playerbio_maindueler.actual:
        playerbio_maindueler.winnerselection = playerbio_maindueler.winnerselection + 1
    else:
        playerbio_target.winnerselection = playerbio_target.winnerselection + 1

    # Special Stats Integration
    playerbio_maindueler.specialmax = 0
    playerbio_target.specialmax = 0
    for x in stats_character:
        gethowmany_maindueler = eval("playerbio_maindueler."+x)
        playerbio_maindueler.specialmax = playerbio_maindueler.specialmax + gethowmany_maindueler
        gethowmany_target = eval("playerbio_target."+x)
        playerbio_target.specialmax = playerbio_target.specialmax + gethowmany_target
    specialmaxarray = []
    specialmaxarray.append(playerbio_maindueler.specialmax)
    specialmaxarray.append(playerbio_target.specialmax)
    specialmaxarray, competitorsspecial = array_arrangesort(bot, specialmaxarray, competitors)
    specialleadername = spicemanip.main(competitorsspecial, 'last')
    if specialleadername == playerbio_maindueler.actual:
        playerbio_maindueler.winnerselection = playerbio_maindueler.winnerselection + 1
    else:
        playerbio_target.winnerselection = playerbio_target.winnerselection + 1

    # Stats
    playerarray, statvaluearray = [], []
    for x in statcheckarray:
        for u in competitors:
            if x != 'health':
                value = get_database_value(bot, u, x) or 0
            elif x == 'health':
                value = duels_get_health(bot, u)
            else:
                scriptdef = str('duels_get_' + x + '(bot,u)')
                value = eval(scriptdef)
            playerarray.append(u)
            statvaluearray.append(x)
        statvaluearray, playerarray = array_arrangesort(bot, statvaluearray, playerarray)
        if x == 'respawns' or x == 'streak_win_current':
            statleadername = spicemanip.main(playerarray, 1)
        else:
            statleadername = spicemanip.main(playerarray, 'last')
        if statleadername == playerbio_maindueler.actual:
            playerbio_maindueler.winnerselection = playerbio_maindueler.winnerselection + 1
        else:
            playerbio_target.winnerselection = playerbio_target.winnerselection + 1

    # weaponslocker not empty
    if playerbio_maindueler.weaponslist != []:
        playerbio_maindueler.winnerselection = playerbio_maindueler.winnerselection + 1
    if playerbio_target.weaponslist != []:
        playerbio_target.winnerselection = playerbio_target.winnerselection + 1

    # anybody rogue?
    if playerbio_maindueler.Class == 'rogue':
        playerbio_maindueler.winnerselection = playerbio_maindueler.winnerselection + 1
    if playerbio_target.Class == 'rogue':
        playerbio_target.winnerselection = playerbio_target.winnerselection + 1

    # Dice rolling occurs now
    playerbio_maindueler.winnerselection = duels_combat_winnerdicerolling(bot, playerbio_maindueler.winnerselection)
    playerbio_target.winnerselection = duels_combat_winnerdicerolling(bot, playerbio_target.winnerselection)

    # curse check
    if playerbio_maindueler.curse_start:
        playerbio_maindueler.winnerselection = 0
        adjust_database_value(bot, playerbio_maindueler.actual, 'curse', -1)
    if playerbio_target.curse_start:
        playerbio_target.winnerselection = 0
        adjust_database_value(bot, playerbio_target.actual, 'curse', -1)

    # who wins
    if playerbio_maindueler.winnerselection == playerbio_target.winnerselection:
        winner = spicemanip.main(competitors, 'random')
    else:
        rollsarray = []
        rollsarray.append(playerbio_maindueler.winnerselection)
        rollsarray.append(playerbio_target.winnerselection)
        rollsarray, competitors = array_arrangesort(bot, rollsarray, competitors)
        winner = spicemanip.main(competitors, 'last')

    return winner


# Max diceroll
def duels_combat_winnerdicerolling(bot, rolls):
    rolla = 0
    rollb = 20
    fightarray = []
    while int(rolls) > 0:
        fightroll = randint(rolla, rollb)
        fightarray.append(fightroll)
        rolls = int(rolls) - 1
    try:
        fight = max(fightarray)
    except ValueError:
        fight = 0
    return fight


# Damage from combat
def duels_combat_damage(bot, duels, playerbio_winner, playerbio_loser):

    # Rogue can't be hurt by themselves or bot
    if playerbio_loser.Class == 'rogue' and playerbio_winner.actual == playerbio_loser.actual:
        damage = 0
        return damage

    # Bot deals a set amount
    if playerbio_winner.actual == bot.nick:
        if playerbio_loser.Class == 'rogue':
            damage = 0
            return damage

    damage = randint(playerbio_winner.strength * 10, 120)

    # Damage Tiers
    if damage > 0:
        damage = duels.tierscaling * damage
        damage = int(damage)

    return damage


# bodypart selector
def duels_bodypart_select(bot, nick):
    # selection roll
    hitchance = randint(1, 101)
    if hitchance <= 50:
        bodypart = 'torso'
    elif hitchance >= 90:
        bodypart = 'head'
    else:
        currentbodypartsarray = duels_nick_bodyparts_remaining(bot, nick)
        bodypart = spicemanip.main(currentbodypartsarray, 'random')
    if "_" in bodypart:
        bodypartname = bodypart.replace("_", " ")
    else:
        bodypartname = bodypart
    return bodypart, bodypartname


# Magic attributes
def duels_magic_attributes_text(bot, playerbio_winner, playerbio_loser):
    playerbio_winner.shield_now = get_database_value(bot, playerbio_winner.actual, 'shield') or 0
    playerbio_winner.curse_now = get_database_value(bot, playerbio_winner.actual, 'curse') or 0
    playerbio_loser.shield_now = get_database_value(bot, playerbio_loser.actual, 'shield') or 0
    playerbio_loser.curse_now = get_database_value(bot, playerbio_loser.actual, 'curse') or 0
    magicattributesarray = ['shield', 'curse']
    nickarray = ['playerbio_winner', 'playerbio_loser']
    attributetext = []
    for j in nickarray:
        person = eval(str(j)+".nametext")
        for x in magicattributesarray:
            workingvarnow = eval(str(j)+"."+x+"_now")
            workingvarstart = eval(str(j)+"."+x+"_start")
            if workingvarnow == 0 and workingvarnow != workingvarstart:
                attributetext.append(person + " is no longer affected by " + str(x) + ".")
    return attributetext


"""
Loot
"""


def duels_use_loot_item(bot, duels, nickusing, target, lootitem, quantity, extramsg, lootusing):

    for x in loot_use_effects:
        currentvalue = str("loot"+x+"=0")
        exec(currentvalue)

    if lootitem in duels_loot_null and lootitem != 'water':
        potionworth = 2
    else:
        potionworth = spicemanip.main([lootitem, duels_loot_items, duels_loot_worth], 'index')
    potionmaths = int(quantity) * potionworth

    # Null loot
    if lootitem == 'water':
        lootstamina = abs(potionmaths)

    if lootitem == 'vinegar':
        lootdamage = abs(potionmaths)

    if lootitem == 'mud':
        lootdamage = abs(potionmaths)

    # tranquilizer
    if lootitem == 'tranquilizer':
        lootagility = potionmaths

    # steroid
    if lootitem == 'steroid':
        lootstrength = abs(potionmaths)

    # antimagic
    if lootitem == 'antimagic':
        lootmagic = potionmaths

    # garlic
    if lootitem == 'garlic' and target.race == 'vampire':
        lootendurance = potionmaths

    # Healthpotion
    if lootitem == 'healthpotion':
        lootdamage = -abs(potionmaths)

    # Poison Potion
    elif lootitem == 'poisonpotion':
        lootdamage = abs(potionmaths)

    elif lootitem == 'poisondart':
        lootdamage = abs(potionmaths)

    # Manapotion
    elif lootitem == 'manapotion':
        lootmana = abs(potionmaths)

    # Staminapotion
    elif lootitem == 'staminapotion':
        lootstamina = abs(potionmaths)

    # Timepotion
    elif lootitem == 'timepotion':
        loottimepotion = 1

    # Track usage for vendor
    adjust_database_value(bot, 'duelsmerchant', str("vendor_track_value_"+lootitem), int(quantity))

    for x in loot_use_effects:
        currentvalue = str("lootusing."+x+"=""lootusing."+x+" + "+"loot"+x)
        exec(currentvalue)

    return lootusing, extramsg


"""
Weaponslocker
"""


# allchan weapons
def duels_weaponslocker_channel(bot):
    allchanweaponsarray = []
    for u in bot.users:
        weaponslist = get_database_value(bot, u, 'weaponslocker_complete') or ['fist']
        for x in weaponslist:
            allchanweaponsarray.append(x)
    weapon = spicemanip.main(allchanweaponsarray, 'random')
    return weapon


def duels_weaponslocker_nick_selection(bot, nick):
    weaponslistselect = []
    weaponslist = get_database_value(bot, nick, 'weaponslocker_complete') or []
    lastusedweaponarry = get_database_value(bot, nick, 'weaponslocker_lastweaponusedarray') or []
    lastusedweapon = get_database_value(bot, nick, 'weaponslocker_lastweaponused') or 'fist'
    howmanyweapons = get_database_array_total(bot, nick, 'weaponslocker_complete') or 0
    if not howmanyweapons > 1:
        reset_database_value(bot, nick, 'weaponslocker_lastweaponused')
    for x in weaponslist:
        if len(x) > weapon_name_length:
            adjust_database_array(bot, nick, [x], 'weaponslocker_complete', 'del')
        if x not in lastusedweaponarry and x != lastusedweapon and len(x) <= weapon_name_length:
            weaponslistselect.append(x)
    if weaponslistselect == [] and weaponslist != []:
        reset_database_value(bot, nick, 'weaponslocker_lastweaponusedarray')
        return duels_weaponslocker_nick_selection(bot, nick)
    weapon = spicemanip.main(weaponslistselect, 'random') or 'fist'
    adjust_database_array(bot, nick, [weapon], 'weaponslocker_lastweaponusedarray', 'add')
    set_database_value(bot, nick, 'weaponslocker_lastweaponused', weapon)
    return weapon


def duels_weapons_formatter(bot, weapon):
    if weapon == '':
        weapon = weapon
    elif weapon.lower().startswith(('a ', 'an ', 'the ')):
        weapon = str('with ' + weapon)
    elif weapon.split(' ', 1)[0].endswith("'s"):
        weapon = str('with ' + weapon)
    elif weapon.lower().startswith(('a', 'e', 'i', 'o', 'u')):
        weapon = str('with an ' + weapon)
    elif weapon.lower().startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
        if weapon.endswith('s'):
            weapon = str("with " + weapon)
        else:
            weapon = str("with " + weapon + "s")
    elif weapon.lower().startswith('with'):
        weapon = str(weapon)
    elif weapon.lower().startswith(' with'):
        weapon = str(weapon).strip()
    else:
        weapon = str('with a ' + weapon)
    return weapon


"""
Monster
"""


def duels_monster_stats_generate(bot, duels, scale):
    monsterstatignore = ['curse', 'shield', 'class', 'race', 'gender']
    for x in duels.stats_valid:
        if x not in monsterstatignore and x not in stats_armor:
            currentstatarray = []
            for player in duels.users_current_allchan_opted:
                playernumber = get_database_value(bot, player, x)
                if str(playernumber).isdigit():
                    currentstatarray.append(playernumber)
            if currentstatarray != []:
                playerstatarrayaverage = mean(currentstatarray)
                playerstatarrayaverage = int(playerstatarrayaverage)
            else:
                playerstatarrayaverage = 0
            if playerstatarrayaverage > 0:
                scaledstat = int(playerstatarrayaverage * scale)
                set_database_value(bot, 'duelsmonster', x, scaledstat)


def duels_monster_stats_reset(bot, duels):
    for x in duels.stats_valid:
        set_database_value(bot, 'duelsmonster', x, None)


"""
Time
"""


# compare timestamps
def duels_time_since(bot, nick, databasekey):
    now = time.time()
    last = get_database_value(bot, nick, databasekey)
    return abs(now - int(last))


# Convert seconds to a readable format
def duels_hours_minutes_seconds(countdownseconds):
    time = float(countdownseconds)
    time = time % (24 * 3600)
    hour = time // 3600
    time %= 3600
    minute = time // 60
    time %= 60
    second = time
    displaymsg = ''
    timearray = ['hour', 'minute', 'second']
    for x in timearray:
        currenttimevar = eval(x)
        if currenttimevar >= 1:
            timetype = x
            if currenttimevar > 1:
                timetype = str(x+"s")
            displaymsg = str(displaymsg + str(int(currenttimevar)) + " " + timetype + " ")
    return displaymsg


"""
ScoreCard
"""


# compare wins/losses
def duels_get_winlossratio(bot, target):
    wins = get_database_value(bot, target, 'wins')
    wins = int(wins)
    losses = get_database_value(bot, target, 'losses')
    losses = int(losses)
    if not losses:
        if not wins:
            winlossratio = 0
        else:
            winlossratio = wins
    elif not wins:
        if not losses:
            winlossratio = 0
        else:
            winlossratio = int(losses) * -1
    else:
        winlossratio = float(wins)/losses
    return winlossratio


def duels_set_current_streaks(bot, nick, winlose):
    if winlose == 'win':
        beststreaktype = 'streak_win_best'
        currentstreaktype = 'streak_win_current'
        oppositestreaktype = 'streak_loss_current'
    elif winlose == 'loss':
        beststreaktype = 'streak_loss_best'
        currentstreaktype = 'streak_loss_current'
        oppositestreaktype = 'streak_win_current'

    # Update Current streak
    adjust_database_value(bot, nick, currentstreaktype, 1)
    set_database_value(bot, nick, 'streak_type_current', winlose)

    # Update Best Streak
    beststreak = get_database_value(bot, nick, beststreaktype) or 0
    currentstreak = get_database_value(bot, nick, currentstreaktype) or 0
    if int(currentstreak) > int(beststreak):
        set_database_value(bot, nick, beststreaktype, int(currentstreak))

    # Clear current opposite streak
    reset_database_value(bot, nick, oppositestreaktype)


def duels_get_current_streaks(bot, winner, loser):
    winner_loss_streak = get_database_value(bot, winner, 'streak_loss_current') or 0
    loser_win_streak = get_database_value(bot, loser, 'streak_win_current') or 0
    return winner_loss_streak, loser_win_streak


def duels_get_streaktext(bot, playerbio_winner, playerbio_loser):
    streaktext = []

    playerbio_winner.win_streak_end = get_database_value(bot, playerbio_winner.actual, 'streak_win_current') or 0
    playerbio_winner.loss_streak_end = get_database_value(bot, playerbio_winner.actual, 'streak_loss_current') or 0
    playerbio_loser.win_streak_end = get_database_value(bot, playerbio_loser.actual, 'streak_win_current') or 0
    playerbio_loser.loss_streak_end = get_database_value(bot, playerbio_loser.actual, 'streak_loss_current') or 0

    if playerbio_winner.loss_streak_start > 1:
        streaktext.append(playerbio_winner.nametext + " recovers from a streak of " + str(playerbio_winner.loss_streak_start) + " losses")

    if playerbio_loser.win_streak_start > 1:
        streaktext.append(playerbio_loser.nametext + "'s streak of " + str(playerbio_loser.win_streak_start) + " wins comes to an end")

    if playerbio_winner.win_streak_end > 1:
        streaktext.append("(Streak: "+str(playerbio_winner.win_streak_end)+")")

    return streaktext


"""
End-game
"""


def duels_endgame(bot, duels):

    # bot records
    duels_refresh_bot(bot, duels)

    # duelrecorduser records
    chanrecordsarray = ['gameenabled', 'devenabled', 'users_all_allchan', 'users_opted_allchan', 'tier', 'lastinstigator', 'specevent', 'roulettelastplayershot', 'roulettelastplayer', 'roulettecount', 'roulettechamber', 'roulettespinarray', 'roulettewinners', 'lasttimedlootwinner']
    for record in chanrecordsarray:
        reset_database_value(bot, 'duelrecorduser', record)
    for event in duels_commands_events:
        reset_database_value(bot, 'duelrecorduser', "lastfullroom" + event)
    for x in duels.stats_valid:
        reset_database_value(bot, 'duelrecorduser', x)
    set_database_value(bot, 'duelrecorduser', 'chanstatsreset', now)

    # duelsmonster records
    for astat in combat_track_results:
        reset_database_value(bot, 'duelsmonster', "combat_track_" + astat)
    duels_monster_stats_reset(bot, duels)

    # Players records
    for player in duels.users_all_allchan:
        for astat in combat_track_results:
            reset_database_value(bot, player, "combat_track_" + astat)
        for x in duels.stats_valid:
            reset_database_value(bot, player, x)


"""
Duels Version
"""


def versionnumber(bot):
    duels_version_plainnow = duels_version_plain
    page = requests.get(duels_version_github_page, headers=None)
    if not str(page.status_code).startswith(tuple(["4", "5"])):
        tree = html.fromstring(page.content)
        duels_version_plainnow = str(tree.xpath(duels_version_github_xpath))
        for r in (("\\n", ""), ("['", ""), ("']", ""), ("'", ""), ('"', ""), (',', ""), ('Commits on', "")):
            duels_version_plainnow = duels_version_plainnow.replace(*r)
        duels_version_plainnow = duels_version_plainnow.strip()
    return duels_version_plainnow


"""
Classic Duels by DGW
"""


def duelclassic_combat(bot, channel, instigator, target, duels_classic_timeout, trigger, is_admin=False, warn_nonexistent=True):
    if target == bot.nick:
        osd(bot, trigger.sender, 'say', "I refuse to duel with the yeller-bellied likes of you!")
        return module.NOLIMIT
    if target == instigator:
        osd(bot, trigger.sender, 'say', "You can't duel yourself, you coward!")
        return module.NOLIMIT
    time_since = duelclassic_time_since_duel(bot, channel, instigator)
    if time_since < duels_classic_timeout:
        osd(bot, instigator, 'priv', "Next duel will be available in %d seconds." % (duels_classic_timeout - time_since))
        return module.NOLIMIT
    msg = "%s vs. %s, " % (instigator, target)
    msg += "loser's a yeller belly!"
    osd(bot, trigger.sender, 'say', msg)
    combatants = sorted([instigator, target])
    random.shuffle(combatants)
    winner = combatants.pop()
    loser = combatants.pop()
    now = time.time()
    bot.db.set_nick_value(instigator, 'duel_last', now)
    bot.db.set_channel_value(channel, 'duel_last', now)
    winner_loss_streak = duelclassic_get_loss_streak(bot, winner)
    loser_win_streak = duelclassic_get_win_streak(bot, loser)
    duelclassic_duel_finished(bot, winner, loser)
    win_streak = duelclassic_get_win_streak(bot, winner)
    streak = ' (Streak: %d)' % win_streak if win_streak > 1 else ''
    broken_streak = ', recovering from a streak of %d losses' % winner_loss_streak if winner_loss_streak > 1 else ''
    broken_streak += ', ending %s\'s streak of %d wins' % (loser, loser_win_streak) if loser_win_streak > 1 else ''
    osd(bot, trigger.sender, 'say', "%s wins%s!%s" % (winner, broken_streak, streak))
    if loser == target:
        kmsg = "%s done killed ya!" % instigator
    else:
        kmsg = "You done got yerself killed!"
    osd(bot, trigger.sender, 'say', kmsg[:-1] + ", " + loser + kmsg[-1:])


def duelclassic_stats(bot, trigger, target):
    wins, losses = duelclassic_get_duels(bot, target)
    total = wins + losses
    if not total:
        osd(bot, trigger.sender, 'say', "%s has no duel record!" % target)
        return module.NOLIMIT
    streaks = duelclassic_format_streaks(bot, target)
    win_rate = wins / total * 100
    osd(bot, trigger.sender, 'say', "%s has won %d out of %d duels (%.2f%%), %s" % (target, wins, total, win_rate, streaks))


def duelclassic_format_streaks(bot, nick):
    # this started as a mess, and it only got messier from there
    streaks = ''

    # current streak
    streak_type = duelclassic_get_streak_type(bot, nick)
    if streak_type == 'win':
        streak_count = duelclassic_get_win_streak(bot, nick)
        streak_preposition = 'and'
        streak_type = 'win' if streak_count == 1 else 'wins'
    elif streak_type == 'lose':
        streak_count = duelclassic_get_loss_streak(bot, nick)
        streak_preposition = 'but'
        streak_type = 'loss' if streak_count == 1 else 'losses'
    else:
        return 'but has no streaks recorded yet.'
    if streak_count > 1:
        streaks += '%s is riding a streak of %d %s.' % (streak_preposition, streak_count, streak_type)
    elif streak_count == 1:
        streaks += 'but can only hope %sto start a %s streak.' % (
            'not ' if streak_type == 'loss' else '', 'winning' if streak_type == 'win' else 'losing')
    else:
        streaks += 'and has not achieved even a single %s? o_O' % streak_type
        return streaks

    # best/worst streaks
    best_wins = duelclassic_get_best_win_streak(bot, nick)
    worst_losses = duelclassic_get_worst_loss_streak(bot, nick)
    if best_wins or worst_losses:
        streaks += ' ('
        if best_wins and worst_losses:
            streaks += 'Best winning streak: %d; worst losing streak: %d.' % (best_wins, worst_losses)
        elif best_wins and not worst_losses:
            streaks += 'Best winning streak: %d.' % best_wins
        elif not best_wins and worst_losses:
            streaks += 'Worst losing streak: %d.' % worst_losses
        streaks += ')'
    return streaks


def duelclassic_get_duels(bot, nick):
    wins = bot.db.get_nick_value(nick, 'duel_wins') or 0
    losses = bot.db.get_nick_value(nick, 'duel_losses') or 0
    return wins, losses


def duelclassic_get_streak_type(bot, nick):
    return bot.db.get_nick_value(nick, 'duel_streak_cur') or None


def duelclassic_set_streak_type(bot, nick, t):
    if t not in ['win', 'lose']:
        raise ValueError("Cannot set unsupported streak type %s." % t)
    bot.db.set_nick_value(nick, 'duel_streak_cur', t)


def duelclassic_get_win_streak(bot, nick):
    return bot.db.get_nick_value(nick, 'duel_wins_streak') or 0


def duelclassic_set_win_streak(bot, nick, value):
    if value < 0:
        value = 0
    bot.db.set_nick_value(nick, 'duel_wins_streak', value)


def duelclassic_extend_win_streak(bot, nick):
    new_streak = duelclassic_get_win_streak(bot, nick) + 1
    duelclassic_set_win_streak(bot, nick, new_streak)
    if new_streak > duelclassic_get_best_win_streak(bot, nick):
        duelclassic_set_best_win_streak(bot, nick, new_streak)


def duelclassic_reset_win_streak(bot, nick):
    duelclassic_set_win_streak(bot, nick, 0)


def duelclassic_get_loss_streak(bot, nick):
    return bot.db.get_nick_value(nick, 'duel_losses_streak') or 0


def duelclassic_set_loss_streak(bot, nick, value):
    if value < 0:
        value = 0
    bot.db.set_nick_value(nick, 'duel_losses_streak', value)


def duelclassic_extend_loss_streak(bot, nick):
    new_streak = duelclassic_get_loss_streak(bot, nick) + 1
    duelclassic_set_loss_streak(bot, nick, new_streak)
    if new_streak > duelclassic_get_worst_loss_streak(bot, nick):
        duelclassic_set_worst_loss_streak(bot, nick, new_streak)


def duelclassic_reset_loss_streak(bot, nick):
    duelclassic_set_loss_streak(bot, nick, 0)


def duelclassic_get_best_win_streak(bot, nick):
    return bot.db.get_nick_value(nick, 'duel_wins_streak_record') or 0


def duelclassic_set_best_win_streak(bot, nick, value):
    if value < 0:
        value = 0
    bot.db.set_nick_value(nick, 'duel_wins_streak_record', value)


def duelclassic_get_worst_loss_streak(bot, nick):
    return bot.db.get_nick_value(nick, 'duel_losses_streak_record') or 0


def duelclassic_set_worst_loss_streak(bot, nick, value):
    if value < 0:
        value = 0
    bot.db.set_nick_value(nick, 'duel_losses_streak_record', value)


def duelclassic_time_since_duel(bot, channel, nick, nick_only=False):
    now = time.time()
    last = bot.db.get_nick_value(nick, 'duel_last') or 0
    return abs(now - last)


def duelclassic_update_duels(bot, nick, won=False):
    wins, losses = duelclassic_get_duels(bot, nick)
    if won:
        bot.db.set_nick_value(nick, 'duel_wins', wins + 1)
        duelclassic_reset_loss_streak(bot, nick)
        duelclassic_set_streak_type(bot, nick, 'win')
        duelclassic_extend_win_streak(bot, nick)
    else:
        bot.db.set_nick_value(nick, 'duel_losses', losses + 1)
        duelclassic_reset_win_streak(bot, nick)
        duelclassic_set_streak_type(bot, nick, 'lose')
        duelclassic_extend_loss_streak(bot, nick)


def duelclassic_duel_finished(bot, winner, loser):
    duelclassic_update_duels(bot, winner, True)
    duelclassic_update_duels(bot, loser, False)


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
            arraymarker = arraymarker + 1
            if partial.startswith(switchtofind):
                beguinemark = arraymarker
            if partial.endswith('"'):
                if not finishmark and beguinemark != 0:
                    finishmark = arraymarker
                    continue
        if finishmark != 0:
            exitoutputrange = str(str(beguinemark) + "^" + str(finishmark))
            exitoutput = spicemanip.main(inputarray, exitoutputrange)
            exitoutput = exitoutput.replace("-"+switch+'=', ' ')
            exitoutput = exitoutput.replace('"', '')
            exitoutput = exitoutput.strip()
    return exitoutput


"""
Small Functions
"""


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def countX(lst, x):
    count = 0
    for ele in lst:
        if (ele == x):
            count = count + 1
    return count


"""
Database
"""


# Get a value
def get_database_value(bot, nick, databasekey):
    databasecolumn = str('duels_' + databasekey)
    database_value = bot.db.get_nick_value(nick, databasecolumn) or 0
    return database_value


# set a value
def set_database_value(bot, nick, databasekey, value):
    databasecolumn = str('duels_' + databasekey)
    bot.db.set_nick_value(nick, databasecolumn, value)


# set a value to None
def reset_database_value(bot, nick, databasekey):
    databasecolumn = str('duels_' + databasekey)
    bot.db.set_nick_value(nick, databasecolumn, None)


# add or subtract from current value
def adjust_database_value(bot, nick, databasekey, value):
    oldvalue = get_database_value(bot, nick, databasekey) or 0
    databasecolumn = str('duels_' + databasekey)
    bot.db.set_nick_value(nick, databasecolumn, int(oldvalue) + int(value))


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
Array/List/String Manipulation
"""


def array_arrangesort(bot, sortbyarray, arrayb):
    sortbyarray, arrayb = (list(x) for x in zip(*sorted(zip(sortbyarray, arrayb), key=itemgetter(0))))
    return sortbyarray, arrayb


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
