import sys
from random import choice, random, randint


class SingleLetter(object):
    def __init__(self, letter):
        self.__letter__ = letter

    def __call__(self, *args, **kwargs):
        return self.__letter__


class LetterGroup(SingleLetter):
    def __init__(self, *args):
        self.__letters__ = list(args)

    def __call__(self, *args, **kwargs):
        exclude = kwargs.get("exclude", [])
        while True:
            letter = choice(self.__letters__)()
            if letter not in exclude:
                return letter


lg_a = LetterGroup(
        SingleLetter("a"),
        SingleLetter("a"),
        SingleLetter("a"),
        SingleLetter("a"),
        SingleLetter("ai"),
        SingleLetter("au")
)

lg_e = LetterGroup(
        SingleLetter("e"),
        SingleLetter("e"),
        SingleLetter("e"),
        SingleLetter("e"),
        SingleLetter("ei"),
        SingleLetter("eu")
)

lg_i = LetterGroup(
        SingleLetter("i"),
        SingleLetter("i"),
        SingleLetter("ie")
)

lg_o = LetterGroup(
        SingleLetter("o"),
        SingleLetter("o"),
        SingleLetter("ou")
)

vowels = LetterGroup(
    lg_a,
    lg_a,
    lg_e,
    lg_e,
    lg_i,
    lg_i,
    lg_o,
    lg_o,
    SingleLetter("u"),
    SingleLetter("u"),
    SingleLetter("y")
)

consonants = LetterGroup(
    SingleLetter("b"),
    LetterGroup(
        SingleLetter("c"),
        SingleLetter("c"),
        SingleLetter("c"),
        SingleLetter("c"),
        SingleLetter("ch"),
        SingleLetter("ck")
    ),
    SingleLetter("d"),
    SingleLetter("f"),
    SingleLetter("g"),
    SingleLetter("h"),
    SingleLetter("j"),
    SingleLetter("k"),
    SingleLetter("l"),
    SingleLetter("m"),
    SingleLetter("n"),
    SingleLetter("p"),
    LetterGroup(
        SingleLetter("qu"),
        SingleLetter("qu"),
        SingleLetter("q")
    ),
    SingleLetter("r"),
    LetterGroup(
        SingleLetter("s"),
        SingleLetter("s"),
        SingleLetter("s"),
        SingleLetter("s"),
        SingleLetter("s"),
        SingleLetter("s"),
        SingleLetter("s"),
        SingleLetter("sch"),
        SingleLetter("sh"),
        SingleLetter("sh"),
        SingleLetter("sp"),
        SingleLetter("sp"),
        SingleLetter("st"),
        SingleLetter("st")
    ),
    SingleLetter("t"),
    SingleLetter("v"),
    SingleLetter("w"),
    SingleLetter("x"),
    SingleLetter("z")
)


def get_syllable(start=False, end=False, dont_start_with=list()):
    retval = []
    if (start and not end) or (not start and end):
        retval.append(consonants(exclude=dont_start_with) if random() < 0.6 else vowels(exclude=dont_start_with))
    else:
        if random() < 0.6:
            letter = consonants(exclude=dont_start_with)
            retval.append(letter)
            letter = vowels(exlude=[letter])
            retval.append(letter)
            letter = consonants(exlude=[letter])
            retval.append(letter)
        else:
            letter = vowels(exclude=dont_start_with)
            retval.append(letter)
            letter = consonants(exlude=[letter])
            retval.append(letter)
            letter = vowels(exlude=[letter])
            retval.append(letter)
    return retval


def get_name(max_syllables=2, dont_start_with=list(), dont_end_with=list()):
    middle_syllables = []
    first_letter = get_syllable(start=True, dont_start_with=dont_start_with)
    last_letter = first_letter[-1]
    for _ in range(randint(1, max_syllables)):
        syl = get_syllable(dont_start_with=[last_letter])
        middle_syllables.extend(syl)
        last_letter = syl[-1]
    last_letter = get_syllable(end=True, dont_start_with=[last_letter] + dont_end_with)
    return "".join(first_letter + middle_syllables + last_letter).capitalize()


names = []
for _ in range(10):
    names.append(get_name(2, ["ck"], ["qu", "sp", "st"]))
names.sort()
print "\n".join(names)
