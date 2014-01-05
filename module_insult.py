"""
Module that, when called, insults people, in true Tumblr fashion.

Tumblr dictionary and logic shamelessly stolen from https://github.com/Lokaltog/tumblr-argument-generator, thank you!
"""

import random
import string

def command_insult(bot, user, channel, args):

    tumblrDictionary = {
        'insult': [
            'burn in hell',
            'check your {privilegedNoun} privilege',
            'die in a fire',
            'drop dead',
            'fuck off',
            'fuck you',
            'go drown in your own piss',
            'go play in traffic',
            'kill yourself',
            'light yourself on fire',
            'make love to yourself in a furnace',
            'please die',
            'rot in hell',
            'screw you',
            'shut the fuck up',
            'shut up',
        ],
        'insultAdverb': [
            'deluded',
            'entitled',
            'fucking',
            'goddamn',
            'ignorant',
            'inconsiderate',
            'judgemental',
            'oppressive',
            'pathetic',
            'worthless',
        ],
        'insultNoun': [
            'MRA',
            'asshole',
            'basement dweller',
            'bigot',
            'brogrammer',
            'creep',
            'dudebro',
            'fascist',
            'hitler',
            'lowlife',
            'nazi',
            'neckbeard',
            'oppressor',
            'pedophile',
            'piece of shit',
            'rape-apologist',
            'rapist',
            'redditor',
            'scum',
            'subhuman',
            'virgin',
        ],
        'marginalizedNoun': [
            'activist', 'agender', 'appearance', 'asian', 'attractive',
            'bi', 'bigender', 'black', 'celestial', 'chubby', 'closet',
            'color', 'curvy', 'dandy', 'deathfat', 'demi', 'differently abled',
            'disabled', 'diversity', 'dysphoria', 'estrogen-affinity', 'ethnic',
            'ethnicity', 'fat love', 'fat', 'fatty', 'female',
            'genderfuck', 'genderless', 'body hair', 'height',
            'indigenous', 'intersectionality', 'intersexual', 'invisible', 'kin',
            'little person', 'marginalized', 'minority',
            'multigender', 'non-gender', 'non-white', 'obesity', 'otherkin', 'omnisexual',
            'pansexual', 'polygender', 'polyspecies', 'privilege', 'prosthetic', 'queer',
            'radfem', 'skinny', 'smallfat', 'stretchmark', 'thin',
            'third-gender', 'trans*', 'transethnic', 'transgender', 'transman',
            'transwoman', 'trigger', 'two-spirit', 'womyn', 'wymyn', 'saami', 'native american',
            'hijra', 'transnormative', 'LGBTQIA+',
            'cross-dresser', 'androphilia', 'gynephilia', 'PoC', 'WoC',
        ],
        'personalPrefixes': [
            'dandy',
            'demi',
            'gender',
                ],
        'personalPostfixes': [
            'amorous',
            'femme',
            'fluid',
            'queer',
            'fuck',
        ],
        'sexualPrefixes': [
            'a',
            'bi',
            'demi',
            'multi',
            'non',
            'omni',
            'pan',
            'para',
            'poly',
        ],
        'sexualPostfixes': [
            'gender',
            'sexual',
            'romantic',
            'queer',
        ],
        'marginalizedAdverb': [
            'antediluvian',
            'attacking',
            'chauvinistic',
            'close-minded',
            'dehumanizing',
            'denying',
            'discriminating',
            'hypersexualizing',
            'ignoring',
            'intolerant',
            'misogynistic',
            'nphobic',
            'objectifying',
            'oppressive',
            'patriarchal',
            'phobic',
            'racist',
            'rape-culture-supporting',
            'sexist',
            'sexualizing',
            'shaming',
        ],
        'marginalizedIsm': [
            'fatist',
            'feminist',
            'freeganist',
            'lesbianist',
        ],
        'privilegedNoun': [
            'able-body',
            'binary',
            'cis',
            'cisgender',
            'cishet',
            'hetero',
            'male',
            'middle-class',
            'smallfat',
            'thin',
            'white',
        ],
        'privilegedAdverb': [
            'normative',
            'overprivileged',
            'privileged',
        ],
        'privilegedIsm': [
            'ableist',
            'ageist',
            'anti-feminist',
            'chauvinist',
            'classist',
            'kyriarchist',
            'misogynist',
            'nazi',
            'patriarchist',
            'sexist',
            'transmisogynist',
        ]
    }
    buildstr = ""
    insult = random.choice(tumblrDictionary['insult'])
    if "{privilegedNoun}" in insult:
        insult = string.replace(insult, "{privilegedNoun}", random.choice(tumblrDictionary['privilegedNoun']))
    buildstr = buildstr + insult + ', '
    buildstr = buildstr + args + ', '
    buildstr = buildstr + "you "
    if random.random() > 0.3:
        buildstr = buildstr + random.choice(tumblrDictionary['insultAdverb']) + ' '
    if random.random() > 0.3:
        if random.random() > 0.5:
            choice = random.choice(tumblrDictionary['marginalizedIsm'])
        else:
            choice = random.choice(tumblrDictionary['marginalizedNoun'])
    else:
        if random.random() > 0.5:
            choice = random.choice(tumblrDictionary['personalPrefixes']) + random.choice(tumblrDictionary['personalPostfixes'])
        else:
            choice = random.choice(tumblrDictionary['sexualPrefixes']) + random.choice(tumblrDictionary['sexualPostfixes'])

        buildstr = buildstr + choice + '-' + random.choice(tumblrDictionary['marginalizedAdverb']) + ', '
        
    buildstr = buildstr + random.choice(tumblrDictionary['privilegedNoun']) + '-' + random.choice(tumblrDictionary['privilegedAdverb']) + ' '
    buildstr = buildstr + random.choice(tumblrDictionary['insultNoun']) + " " + random.choice(tumblrDictionary['privilegedIsm']) + ' '


    bot.say(channel, buildstr.upper())