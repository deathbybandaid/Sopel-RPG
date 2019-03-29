
"""
# pep ignores
"""
# pylama:ignore=W,E201,E202,E203,E221,E222,E231

"""
Easy Configurables
"""

osd_limit = 420  # Ammount of text allowed to display per line


# Valid settings
duels_character_valid_class = ['blacksmith','mage','scavenger','rogue','ranger','knight','paladin','bard','druid']
duels_character_valid_gender = ['male','female']
duels_character_valid_race = ['human','barbarian','fiend','vampire','centaur','gnome','dwarf']

# SPECIALM Dictionary
# Request items from this like so: class_special[class][type].
# For example, to get mage perception: class_special["mage"]["perception"]
# Could make it per stat, then you could call the total value as special["strength"][player_class] + special["strength"][player_race],
# rather than player_strength = class_special[player_class]["strength"] + race_special[player_class]["strength"]

class_special = {
    "mage":{
        "strength":1,
        "perception":1,
        "endurance":1,
        "charisma":3,
        "intelligence":3,
        "agility":1,
        "luck":3,
        "magic":5},
    "bard":{
        "strength":4,
        "perception":2,
        "endurance":4,
        "charisma":3,
        "intelligence":3,
        "agility":1,
        "luck":3,
        "magic":4},
    "druid":{
        "strength":4,
        "perception":2,
        "endurance":4,
        "charisma":3,
        "intelligence":3,
        "agility":1,
        "luck":3,
        "magic":4}
}
race_special = {
    "human":{
        "strength":2,
        "perception":3,
        "endurance":3,
        "charisma":2,
        "intelligence":3,
        "agility":4,
        "luck":3,
        "magic":3},
    "centaur":{
        "strength":5,
        "perception":4,
        "endurance":5,
        "charisma":2,
        "intelligence":3,
        "agility":1,
        "luck":1,
        "magic":1},
    "gnome":{
        "strength":2,
        "perception":3,
        "endurance":3,
        "charisma":2,
        "intelligence":3,
        "agility":5,
        "luck":3,
        "magic":3}
}
# SPECIAL+M
duels_special_full =                        ['strength', 'perception', 'endurance', 'charisma', 'intelligence', 'agility', 'luck', 'magic']
# Classes SPECIAL
duels_character_special_class_mage =        [    1     ,       1     ,      1     ,      3    ,        3      ,     1    ,    3  ,    5   ]
duels_character_special_class_bard =        [    4     ,       2     ,      4     ,      3    ,        3      ,     1    ,    3  ,    4   ]
duels_character_special_class_druid =       [    4     ,       2     ,      4     ,      3    ,        3      ,     1    ,    3  ,    4   ]
duels_character_special_class_blacksmith =  [    5     ,       1     ,      3     ,      2    ,        3      ,     1    ,    2  ,    1   ]
duels_character_special_class_scavenger =   [    2     ,       1     ,      2     ,      5    ,        2      ,     3    ,    5  ,    1   ]
duels_character_special_class_rogue =       [    3     ,       1     ,      2     ,      2    ,        2      ,     3    ,    3  ,    1   ]
duels_character_special_class_ranger =      [    3     ,       3     ,      2     ,      2    ,        5      ,     3    ,    2  ,    1   ]
duels_character_special_class_knight =      [    5     ,       2     ,      4     ,      2    ,        3      ,     2    ,    2  ,    1   ]
duels_character_special_class_paladin =     [    3     ,       5     ,      3     ,      2    ,        3      ,     2    ,    2  ,    1   ]
# Races SPECIAL
duels_character_special_race_human =        [    2     ,       3     ,      3     ,      2    ,        3      ,     4    ,    3  ,    3   ]
duels_character_special_race_centaur =      [    5     ,       4     ,      5     ,      2    ,        3      ,     1    ,    1  ,    1   ]
duels_character_special_race_gnome =        [    2     ,       3     ,      3     ,      2    ,        3      ,     5    ,    3  ,    3   ]
duels_character_special_race_dwarf =        [    5     ,       2     ,      5     ,      2    ,        2      ,     1    ,    1  ,    1   ]
duels_character_special_race_barbarian =    [    5     ,       1     ,      2     ,      1    ,        1      ,     1    ,    1  ,    1   ]
duels_character_special_race_fiend =        [    3     ,       3     ,      2     ,      2    ,        2      ,     4    ,    1  ,    2   ]
duels_character_special_race_vampire =      [    1     ,       2     ,      1     ,      2    ,        2      ,     1    ,    1  ,    2   ]
# Bot
duels_character_special_race_bot =          [    5     ,       5     ,      5     ,      5    ,        5      ,     5    ,    5  ,    5   ]
duels_character_special_class_bot =         [    5     ,       5     ,      5     ,      5    ,        5      ,     5    ,    5  ,    5   ]
# Monster
duels_character_special_race_monster =      [    3     ,       3     ,      3     ,      3    ,        3      ,     1    ,    3  ,    3   ]
duels_character_special_class_monster =     [    3     ,       3     ,      3     ,      3    ,        3      ,     1    ,    3  ,    3   ]
# Error Handling
duels_character_special_race_unknown =      [    1     ,       1     ,      1     ,      1    ,        1      ,     1    ,    1  ,    1   ]
duels_character_special_class_unknown =     [    1     ,       1     ,      1     ,      1    ,        1      ,     1    ,    1  ,    1   ]

# Druid Tier Transform
duels_druid_creatures_0 = ['Baboon', 'Badger', 'Cat', 'Deer', 'Giant Fire Beetle', 'Goat', 'Hyena', 'Jackal', 'Lizard', 'Rat', 'Scorpion', 'Spider', 'Weasel']
duels_druid_creatures_1 = ['Camel', 'Giant Rat', 'Giant Weasel', 'Mastiff', 'Mule', 'Pony']
duels_druid_creatures_2 = ['Axe Beak', 'Boar', 'Draft Horse', 'Elk', 'Giant Badger', 'Giant Centipede', 'Giant Goat', 'Giant Lizard', 'Giant Wolf Spider', 'Panther', 'Riding Horse', 'Swarm of Rats', 'Wolf']
duels_druid_creatures_3 = ['Crab', 'Octopus', 'Quipper']
duels_druid_creatures_4 = ['Giant Crab', 'Poisonous Snake']
duels_druid_creatures_5 = ['Constrictor Snake', 'Giant Frog', 'Giant Poisonous Snake']
duels_druid_creatures_6 = ['Ape', 'Black Bear', 'Crocodile', 'Giant Sea Horse', 'Reef Shark', 'Swarm of Insects', 'Warhorse']
duels_druid_creatures_7 = ['Bat', 'Eagle', 'Hawk', 'Owl', 'Raven', 'Vulture']
duels_druid_creatures_8 = ['Blood Hawk', 'Flying Snake', 'Stirge']
duels_druid_creatures_9 = ['Giant Bat', 'Giant Owl', 'Pteranodon', 'Swarm of Bats', 'Swarm of Ravens']
duels_druid_creatures_10 = ['Giant Wasp', 'Swarm of Wasps']
duels_druid_creatures_11 = ['Brown Bear', 'Dire Wolf', 'Giant Eagle', 'Giant Hyena', 'Giant Octopus', 'Giant Spider', 'Giant Toad', 'Giant Vulture', 'Lion', 'Swarm of Quippers', 'Tiger']
duels_druid_creatures_12 = []
duels_druid_creatures_13 = []
duels_druid_creatures_14 = []
duels_druid_creatures_15 = []

"""
# Command Structure Settings #
"""
# Command ideas:
duel_commands = {
    "version":{
        "tier":"none",
        "admin":False,
        "stamina":0,
        "self":False,
        "special_event":False
    },
    "docs":{
        "tier":"none",
        "admin":False,
        "stamina":0,
        "self":False,
        "special_event":False
    },
    "about":{
        "tier":"none",
        "admin":False,
        "stamina":0,
        "self":True,
        "special_event":False
    },
    "intent":{
        "tier":"none",
        "admin":False,
        "stamina":0,
        "self":True,
        "special_event":False
    },
    "location":{
        "tier":0,
        "admin":False,
        "stamina":10,
        "self":False,
        "special_event":False
    },
    "assault":{
        "tier":7,
        "admin":False,
        "stamina":25,
        "self":False,
        "special_event":True
    },
}

# Command Tiers
duels_commands_tier_unlocks_none = ['version','docs','author','game','devmode','intent','about']
duels_commands_tier_unlocks_0 = ['opt','deathblow','combat','grenade','location','monster']
duels_commands_tier_unlocks_1 = ['tier','usage','classic','hotkey','tavern']
duels_commands_tier_unlocks_2 = ['bounty','harakiri','merchant','loot','locker']
duels_commands_tier_unlocks_3 = ['craft','weaponslocker','monster']
duels_commands_tier_unlocks_4 = ['leaderboard','warroom']
duels_commands_tier_unlocks_5 = ['character','health','streaks','stats','special']
duels_commands_tier_unlocks_6 = ['magic','forge','armor']
duels_commands_tier_unlocks_7 = ['assault']  # exploration_mode
duels_commands_tier_unlocks_8 = ['trebuchet']
duels_commands_tier_unlocks_9 = ['random']
duels_commands_tier_unlocks_10 = ['roulette']
duels_commands_tier_unlocks_11 = ['title']
duels_commands_tier_unlocks_12 = ['colosseum']
duels_commands_tier_unlocks_13 = ['mayhem']
duels_commands_tier_unlocks_14 = ['hungergames']
duels_commands_tier_unlocks_15 = []

# Stamina Requirements for Commands
duels_commands_stamina_required = ['location','combat','deathblow','classic','harakiri','magic','monster','assault','trebuchet','roulette','random','colosseum','mayhem','hungergames']
duels_commands_stamina_cost =     [   10     ,   5    ,    1      ,    1    ,    1     ,   2   ,   10    ,   10    ,    10     ,     2    ,   3    ,     20    ,   25   ,     20     ]

# Alternative Commands
duels_commands_alternate_list = ['opt','random','assault','author','docs','classic','weaponslocker','character','combat','location','hotkey']  # Main Commands that have alternates
duels_commands_alternate_opt = ['on','off','enable','activate','disable','deactivate']
duels_commands_alternate_random = ['anyone','somebody','available','someone']
duels_commands_alternate_assault = ['everyone','everybody','channel']
duels_commands_alternate_author = ['credit']
duels_commands_alternate_weaponslocker = ['weapons']
duels_commands_alternate_classic = ['retro']
duels_commands_alternate_hotkey = ['hotlink']
duels_commands_alternate_docs = ['help','man']
duels_commands_alternate_character = ['char','sheet']
duels_commands_alternate_combat = ['challenge','duel']
duels_commands_alternate_location = ['goto','travel','move']

# Commands that bypass tiers as long as self-used
duels_commands_self = ['loot','character','health','streaks','stats','special']

# Location based Commands
duels_commands_locations = ['town','arena']
duels_commands_town = ['merchant','forge','locker','craft','tavern']
duels_commands_arena = ['combat','classic','assault','trebuchet','roulette','monster','random','colosseum','mayhem','hungergames','grenade']

# Commands that must be run in channel and not in privmsg
duels_commands_inchannel = ['roulette','assault','colosseum','bounty','hungergames','devmode','deathblow','combat','grenade','classic','random']

# Commands that can only be run by bot.admin
duels_commands_admin = ['devmode','game']

# Command Checks
duels_commands_canduel_generate = ['mayhem','hungergames','monster','random']
duels_commands_canduel_remove_bot = ['mayhem','hungergames','colosseum','assault','warroom','grenade']
duels_commands_events = ['mayhem','hungergames','colosseum','assault']

duels_commands_special_events = ['combat','roulette','assault','roulette','monster','random','colosseum','mayhem','hungergames']

# Opt
opt_disable_array = ['off','disable','deactivate']
opt_enable_array = ['on','enable','activate']

# These Correlate together
duels_commands_xp_levels =     [  0   ,     1    ,  100   ,   250   ,   500   ,  1000   ,  2500    ,  5000   ,  7500    , 10000   ,   15000     , 25000 ,  45000   ,    70000    ,  100000 ,   250000       ]  # XP
duels_commands_tier_ratio =    [  1   ,    1.1   ,  1.2   ,   1.3   ,   1.4   ,   1.5    ,   1.6   ,   1.7    ,   1.8   ,   1.9   ,     2       , 2.1   ,   2.2    ,    2.3      , 2.4     ,     2.5        ]  # Tier Ratios
duels_commands_pepper_levels = ['n00b','pimiento','sonora','anaheim','poblano','jalapeno','serrano','chipotle','tabasco','cayenne','thai pepper','datil','habanero','ghost chili','mace'   ,'pure capsaicin']  # Pepper Levels

# Action Duels
duels_action_subcommands = ['combat','random','monster']

"""
#
# Merchant System #
#
"""

duels_merchant_transaction_types = ['buy','sell']
duels_loot_items =  ['grenade' ,'healthpotion','manapotion','poisonpotion','timepotion','staminapotion','mysterypotion','stimpack','poisondart','tranquilizer','garlic','antimagic','syringe','water','steroid']
duels_loot_cost =   [   1150   ,      460     ,    460     ,     460      ,     368    ,       460     ,       344     ,     'no' ,     'no'   ,      254     ,   460  ,     460   ,    200  ,   150 ,    'no' ]
duels_loot_worth =  [    100   ,      100     ,    100     ,     -50      ,     0      ,        15     ,        0      ,     100  ,    -200    ,       -2     ,   -1   ,     -2    ,     0   ,   2   ,     2   ]
duels_loot_view = ['coin','grenade','healthpotion','manapotion','poisonpotion','timepotion','staminapotion','mysterypotion','stimpack','poisondart','syringe','tranquilizer','garlic','antimagic','water','steroid']  # how to organize backpack
duels_loot_stat_modifiers = ['tranquilizer','garlic','antimagic']
duels_loot_potion_types = ['healthpotion','manapotion','poisonpotion','timepotion','staminapotion','mysterypotion']  # types of potions
duels_loot_winnable_lower = ['syringe','water','tranquilizer','garlic','antimagic']
duels_loot_winnable_norm = ['healthpotion','manapotion','poisonpotion','timepotion','staminapotion','mysterypotion']
duels_loot_winnable_plus = ['stimpack','grenade','poisondart','steroid']
duels_loot_null = ['water','vinegar','mud']
duels_grenade_damage_full = 100
duels_grenade_damage_half = 50
duels_loot_timepotion_targetarray = ['lastinstigator','lastfullroomcolosseuminstigator','lastfullroomassultinstigator']
duels_loot_timepotion_timeoutarray = ['lastfullroomcolosseum','lastfullroomassult','timeout_opttimetime','class_timeout']
duels_merchant_inv_max = 100
loot_use_effects = ['damage','stamina','mana','timepotion','strength','perception','endurance','charisma','intelligence','agility','luck','magic']

"""
#
# Crafting System #
#
"""

# Craftable list
duels_craft_valid = ['poisondart','stimpack','steroid']

# poisondart recipe
duel_craft_poisondart_required = ['syringe','poisonpotion']
duel_craft_poisondart_quantity = [    1    ,       3      ]

# stimpack recipe
duel_craft_stimpack_required = ['syringe','healthpotion']
duel_craft_stimpack_quantity = [    1    ,       2      ]

# steroid recipe
duel_craft_steroid_required = ['syringe','healthpotion','poisonpotion']
duel_craft_steroid_quantity = [    1    ,       1      ,       1      ]

"""
#
# Armor System #
#
"""

duels_forge_transaction_types = ['buy','sell','repair']
duels_default_armor =       [ 'cap'   ,'rag shirt' ,'left_sleeve'  ,'right_sleeve'  ,'left_pantleg' , 'right_pantleg'  ,'loin_cloth']
duels_forge_items =         ['helmet','breastplate','left_gauntlet','right_gauntlet','left_greave'  ,'right_greave'    ,'codpiece'  ]
duels_forge_cost =          [  1150  ,     1150     ,       460    ,        460     ,     368       ,       368        ,   150      ]
duels_armor_protection =    [   33   ,       33     ,        33    ,        33      ,     33        ,       33         ,   33       ]
duels_armor_durabilitymax = [   10   ,       10     ,        10    ,        10      ,     10        ,       10         ,   10       ]

# Body/Armor
armor_cost = 500
armor_repair_cost = .5
armor_cost_blacksmith_cut = .8
armor_sell_blacksmith_cut = 1.5
armor_durability = 10
armor_durability_blacksmith = 15
armor_relief_percentage = 33  # has to be converted to decimal later

"""
#
# Tavern System #
#
"""

duels_tavern_items =                ['beer','wine','mead','cider','pulque','gin']
duels_tavern_cost =                 [ 80   , 80   , 80   ,  80   ,  80    , 80  ]
duels_tavern_special_strength =     [  3   ,  0   ,  0   ,   0   ,   0    ,  0  ]
duels_tavern_special_perception =   [ -1   , -1   , -1   ,  -1   ,   3    , -1  ]
duels_tavern_special_endurance =    [  0   ,  0   ,  3   ,   0   ,   0    ,  0  ]
duels_tavern_special_charisma =     [  1   ,  3   ,  1   ,   1   ,   1    ,  0  ]
duels_tavern_special_intelligence = [ -1   , -1   , -1   ,  -1   ,  -1    , -1  ]
duels_tavern_special_agility =      [  0   ,  0   ,  0   ,   0   ,   0    ,  0  ]
duels_tavern_special_luck =         [  0   ,  0   ,  0   ,   3   ,   0    ,  0  ]
duels_tavern_special_magic =        [  0   ,  0   ,  0   ,   0   ,   0    ,  3  ]

"""
#
# Health System #
#
"""

duels_bodyparts =        ['head','torso','left_arm','right_arm','left_leg','right_leg','junk']
duels_bodyparts_health = [ 330  , 1000  ,   250    ,    250    ,   500    ,   500     ,  40  ]

"""
#
# Magic System #
#
"""

duels_magic_types =    ['curse','shield','attack','health']
duels_magic_required = [  500  ,   300  ,  250   ,   200  ]
duels_magic_damage =   [  -80  ,    80  , -200   ,   200  ]
duels_magic_duration = [   4   ,   200  ,  0     ,    0   ]

"""
#
# Chance Event System #
#
"""

duels_chance_events_types =    ['hailstorm' ,   'fog'    ,'sandstorm','windstorm','duststorm'   ,'snowstorm','thunderstorm']
duels_chance_events_damage =   [    -1      ,     -1     ,     -1    ,     -1    ,      -1      ,   -1      ,      -1      ]
duels_chance_events_effected = ['strength'  ,'perception','endurance','charisma' ,'intelligence','luck'     ,   'magic'    ]
duels_chance_events_duration = [  2400      ,   2400     ,   2400    ,  2400     ,   2400       , 2400      ,   2400       ]

"""
#
# Stats System #
#
"""

# Admin Stats Cycling
stats_admin_types = ['healthbodyparts','armor','loot','record','magic','streak','timeout','title','bounty','weaponslocker','leveling','other','stamina','character','character_initial','class','locker','special_full','special_fullb','special_fullc']
# Health Stats
stats_healthbodyparts = ['head','torso','left_arm','right_arm','left_leg','right_leg','junk']
# Armor Stats
stats_armor = ['helmet','breastplate','left_gauntlet','right_gauntlet','left_greave','right_greave','codpiece']
# Loot Stats
stats_loot = ['healthpotion','mysterypotion','timepotion','staminapotion','poisonpotion','manapotion','grenade','coin','stimpack','syringe','poisondart','water','tranquilizer','garlic','antimagic','steroid']
# Locker
stats_locker = ['healthpotion_locker','mysterypotion_locker','timepotion_locker','staminapotion_locker','poisonpotion_locker','manapotion_locker','grenade_locker','coin_locker','stimpack_locker']
# character stats
stats_character_initial = ['class','race','gender']
stats_character = ['strength', 'perception', 'endurance', 'charisma', 'intelligence', 'agility', 'luck', 'magic']
# Record Stats
stats_record = ['wins','losses','xp','respawns','kills','lastfought','konami','newplayer']
# Streak Stats
stats_streak = ['streak_loss_current','streak_win_current','streak_type_current','streak_win_best','streak_loss_best']
# Magic Stats
stats_magic = ['mana','curse','shield']
# Timeout Stats
stats_timeout = ['timeout_class','timeout_opttime']
# Class Stats
stats_class = ['class','class_freebie','class_timeout']
# Title Stats
stats_title = ['title']
# Bounty Stats
stats_bounty = ['bounty']
# Stamina
stats_stamina = ['stamina']
# Weaponslocker Stats
stats_weaponslocker = ['weaponslocker_complete','weaponslocker_lastweaponusedarray','weaponslocker_lastweaponused']
# Leveling Stats
stats_leveling = ['tier']
# Other
stats_other = ['chanstatsreset','dev_win']
stats_special_full = ['strength_effect', 'perception_effect', 'endurance_effect', 'charisma_effect', 'intelligence_effect', 'agility_effect', 'luck_effect', 'magic_effect']
stats_special_fullb = ['strength_effect_time', 'perception_effect_time', 'endurance_effect_time', 'charisma_effect_time', 'intelligence_effect_time', 'agility_effect_time', 'luck_effect_time', 'magic_effect_time']
stats_special_fullc = ['strength_effect_duration', 'perception_effect_duration', 'endurance_effect_duration', 'charisma_effect_duration', 'intelligence_effect_duration', 'agility_effect_duration', 'luck_effect_duration', 'magic_effect_duration']

"""
#
# In came Costs #
#
"""

duels_ingame_coin_usage = ['class','title','roulette','random','bugbounty','specialevent']
duels_ingame_coin =       [   100 ,  100  ,    5     ,    100 ,    100    ,    500       ]

"""
#
# Timeouts System #
#
"""

duel_combat_timeouts = 'false'
duels_timeouts =          ['class','roulette_death','auto-opt','opttime','roulette','assault','colosseum','hungergames','mayhem']
duels_timeouts_duration = [ 86400 ,     86400      ,  259200  ,   1800  ,    5     ,   1800  ,    1800   ,    1800     ,  1800  ]

"""
#
#
"""

# Roulette
roulette_revolver_list = ['.357 Magnum','Colt PeaceMaker','Colt Repeater','Colt Single Action Army 45','Ruger Super Blackhawk','Remington Model 1875','Russian Nagant M1895 revolver','Smith and Wesson Model 27']

# Assault
combat_track_results = ['wins','losses','loot_won','loot_lost','kills','deaths','damage_taken','damage_dealt','level_ups','xp_earned']

# Weapons Locker
weapon_name_length = 70  # prevents text that destroys OSD

# Stamina
staminamax = 60
staminaregen = 30

# Half Hour Timer
halfhour_regen_health, halfhour_regen_health_max = 50,500  # health regen rate
halfhour_regen_mage_mana, halfhour_regen_mage_mana_max = 50, 500  # mages regenerate mana: rate

# Main Duel Runs
duel_hit_types = ['hit','strike','beat','pummel','bash','smack','knock','bonk','chastise','clash','clobber','slug','sock','swat','thump','wallop','whop']
duel_hit_types_s = ['hits','strikes','beats','pummels','bashes','smacks','knocks','bonks','chastises','clashes','clobbers','slugs','socks','swats','thumps','wallops','whops']

deathblow_amount = 150

# Records
target_ignore_list = ['spiceduels']

stat_admin_commands = ['set','reset','view']  # valid admin subcommands
stats_view = ['health','class','race','curse','stamina','shield','mana','xp','wins','losses','winlossratio','respawns','kills','lastfought','bounty','location']
stats_view_functions = ['winlossratio']  # stats that use their own functions to get a value

# array of insulting departures
cowardarray = ["What a coward!","What a Woosy!","Run away, loser!","Shame on you!","Scaredy-cat!"]

# Trebuchet projectile list
trebuchet_projectiles_list = ['Large stone','dead deer head',"flaming ball o' fire"]

# Monster List
duelsmonstervarientarray = ["A Giant","A Young","A Fluffy","A Furry","An Itty Bitty"]
monstersarray = [
                 "Aboleth","Beholder","Blue slaad","Chuul","Cloaker","Death kiss","Death slaad","Elder brain","Gauth","Gazer","Gibbering mouther","Gray slaad","Green slaad","Grell","Intellect devourer","Mind flayer","Mind flayer arcanist","Mindwitness","Morkoth","Neogi","Neogi master","Neothelid","Nothic",
                 "Otyugh","Red slaad","Spectator","Ulitharid","Allosaurus","Ankylosaurus","Ape","Aurochs","Axe beak","Baboon","Badger","Bat","Black bear","Blood hawk","Boar","Brontosaurus","Brown bear","Camel","Cat","Constrictor snake","Cow","Crab","Cranium rat","Crocodile","Deer",
                 "Deinonychus","Dimetrodon","Dire wolf","Draft horse","Eagle","Elephant","Elk","Hadrosaurus","Hawk","Hunter shark","Hyena","Killer whale","Lion","Lizard","Mammoth","Octopus","Owl","Panther","Plesiosaurus","Polar bear","Pony",
                 "Quetzalcoatlus","Quipper","Rat","Reef shark","Rhinoceros","Saber-toothed tiger","Stegosaurus","Swarm of cranium rats","Swarm of insects","Swarm of poisonous snakes","Swarm of quippers","Swarm of rot grubs","Tiger","Triceratops","Tyrannosaurus rex","Couatl","Deva","Empyrean","Ki-rin","Pegasus",
                 "Planetar","Solar","Unicorn","Animated armor","Clay golem","Duodrone","Flesh golem","Flying sword","Helmed horror","Iron golem","Pentadrone","Quadrone","Rug of smothering","Scarecrow","Shield guardian","Stone golem","Tridrone","Adult black dragon","Adult blue dragon","Adult brass dragon",
                 "Adult bronze dragon","Adult copper dragon","Adult gold dragon","Adult green dragon","Adult red dragon","Adult silver dragon","Adult white dragon","Ancient black dragon","Ancient blue dragon","Ancient brass dragon","Ancient bronze dragon","Ancient copper dragon","Ancient gold dragon",
                 "Ancient green dragon","Ancient red dragon","Ancient silver dragon","Ancient white dragon","Black dragon wyrmling","Blue dragon wyrmling","Brass dragon wyrmling","Bronze dragon wyrmling","Copper dragon wyrmling","Dragon turtle","Faerie dragon","Gold dragon wyrmling","Green dragon wyrmling",
                 "Guard drake","Red dragon wyrmling","Silver dragon wyrmling","White dragon wyrmling","Wyvern","Young black dragon","Young blue dragon","Young brass dragon","Young bronze dragon","Young copper dragon","Young gold dragon","Young green dragon","Young red dragon","Young red shadow dragon",
                 "Young silver dragon","Young white dragon","Air elemental","Azer","Dao","Djinni","Dust mephit","Earth elemental","Efreeti","Fire elemental","Fire snake","Flail snail","Galeb duhr","Gargoyle","Ice mephit","Invisible stalker","Magma mephit","Magmin","Marid","Mud mephit","Salamander",
                 "Water elemental","Water weird","Xorn","Annis hag","Bheur hag","Blink dog","Darkling","Darkling elder","Dryad","Green hag","Korred","Meenlock","Pixie","Quickling","Redcap","Satyr","Sea hag","Yeth hound","Arcanaloth","Babau","Balor","Barbed devil","Barghest","Barlgura","Bearded devil",
                 "Bone devil","Cambion","Chain devil","Chasme","Devourer","Draegloth","Dretch","Erinyes","Glabrezu","Gnoll fang of Yeenoghu","Goristro","Hell hound","Hezrou","Horned devil","Ice devil","Imp","Incubus","Marilith","Maw demon","Mezzoloth","Nalfeshnee","Night hag","Nightmare","Nycaloth","Pit fiend",
                 "Quasit","Rakshasa","Shadow demon","Shoosuva","Spined devil","Succubus","Tanarukk","Ultroloth","Vargouille","Vrock","Yochlol","Cloud giant","Cloud giant smiling one","Cyclops","Ettin","Fire giant","Fire giant dreadnought","Fomorian","Frost giant","Frost giant everlasting one","Half-ogre",
                 "Hill giant","Mouth of Grolantor","Ogre","Oni","Stone giant","Stone giant dreamwalker","Storm giant","Storm giant quintessent","Troll","Aarakocra","Abjurer","Acolyte","Apprentice wizard","Archdruid","Archer","Archmage","Assassin","Bandit","Bandit captain","Bard","Berserker","Blackguard",
                 "Bugbear","Bugbear chief","Bullywug","Champion","Conjurer","Cult fanatic","Deep gnome","Deep scion","Diviner","Drow","Drow elite warrior","Drow mage","Drow priestess of Lolth","Druid","Duergar","Enchanter","Evoker","Firenewt","Firenewt warlock of Imix","Flind","Githyanki knight",
                 "Githyanki warrior","Githzerai monk","Githzerai zerth","Gladiator","Gnoll","Gnoll flesh gnawer","Gnoll hunter","Gnoll pack lord","Goblin","Goblin boss","Grimlock","Grung","Grung elite warrior","Grung wildling","Guard","Half-red dragon veteran","Hobgoblin","Hobgoblin captain",
                 "Hobgoblin devastator","Hobgoblin Iron Shadow","Hobgoblin warlord","Illusionist","Jackalwere","Kenku","Knight","Kobold dragonshield","Kobold inventor","Kobold scale sorcerer","Kraken priest","Kuo-toa","Kuo-toa archpriest","Kuo-toa monitor","Kuo-toa whip","Lizard king/queen","Lizardfolk",
                 "Lizardfolk shaman","Mage","Martial arts adept","Master thief","Necromancer","Nilbog","Orc","Orc Blade of Ilneval","Orc Claw of Luthic","Orc eye of Gruumsh","Orc Hand of Yurtrus","Orc Nurtured One of Yurtrus","Orc Red Fang of Shargaas","Orc war chief","Orog","Priest","Quaggoth",
                 "Quaggoth thonot","Sahuagin","Sahuagin baron","Sahuagin priestess","Sea spawn","Scout","Spy","Swashbuckler","Thri-kreen","Thug","Transmuter","Veteran","War priest","Warlock of the archfey","Warlock of the fiend","Warlock of the Great Old One","Warlord","Werebear","Wereboar","Wererat",
                 "Weretiger","Werewolf","Winged kobold","Xvart","Xvart warlock of Raxivort","Yuan-ti broodguard","Yuan-ti pureblood","Abominable yeti","Androsphinx","Ankheg","Banderhobb","Basilisk","Behir","Bulette","Carrion crawler","Catoblepas","Cave fisher","Centaur","Chimera","Chitine","Choldrith",
                 "Cockatrice","Darkmantle","Death dog","Displacer beast","Doppelganger","Drider","Ettercap","Froghemoth","Giant strider","Girallon","Gorgon","Grick","Grick alpha","Griffon","Guardian naga","Gynosphinx","Harpy","Hippogriff","Hook horror","Hydra","Kraken","Lamia","Leucrotta","Manticore",
                 "Medusa","Merrow","Mimic","Minotaur","Owlbear","Peryton","Phase spider","Piercer","Purple worm","Remorhaz","Roc","Roper","Rust monster","Shadow mastiff","Spirit naga","Tarrasque","Tlincalli","Trapper","Umber hulk","Winter wolf","Worg","Yeti","Young remorhaz","Yuan-ti abomination",
                 "Yuan-ti anathema","Yuan-ti malison","Yuan-ti mind whisperer","Yuan-ti nightmare speaker","Yuan-ti pit master","Black pudding","Gelatinous cube","Gray ooze","Ochre jelly","Slithering tracker","Awakened shrub","Awakened tree","Gas spore","Myconid adult","Myconid sovereign","Needle blight",
                 "Quaggoth spore servant","Shambling mound","Shrieker","Thorny","Treant","Twig blight","Vegepygmy chief","Wood woad","Alhoon","Adult blue dracolich","Banshee","Beholder zombie","Bodak","Bone naga","Crawling claw","Death knight","Death tyrant","Demilich","Flameskull","Ghast","Ghost","Ghoul",
                 "Gnoll witherling","Lich","Mind flayer lich","Minotaur skeleton","Mummy","Mummy lord","Ogre zombie","Poltergeist","Revenant","Shadow","Skeleton","Spawn of Kyuss","Specter","Vampire","Commoner","Frog","Goat","Homunculus","Jackal","Lemure","Myconid sprout","Raven","Scorpion",
                 "Sea horse","Spider","Vulture","Weasel","Boggle","Cultist","Dolphin","Flumph","Flying snake","Kobold","Manes","Mastiff","Merfolk","Monodrone","Mule","Neogi hatchling","Noble","Poisonous snake""Slaad tadpole","Stirge","Tribal warrior","Pseudodragon","Pteranodon","Riding horse",
                 "Smoke mephit","Sprite","Steam mephit","Swarm of bats","Swarm of rats","Swarm of ravens","Troglodyte","Vegepygmy","Velociraptor","Violet fungus","Wolf","Zombie","Vine blight","Warhorse","Warhorse skeleton"]
