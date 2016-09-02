import sys
from random import choice, random, randint


class LetterContainer(object):
    def pick(self, exclude=None):
        raise NotImplementedError

    def get(self):
        raise NotImplementedError


class SingleLetter(LetterContainer):
    def __init__(self, letter):
        self.__letter__ = letter

    def pick(self, exclude=None):
        return self.__letter__

    def get(self):
        return [self.__letter__]


class LetterGroup(LetterContainer):
    def __init__(self, *args):
        self.__letters__ = list(args)

    def pick(self, exclude=None):
        if not exclude:
            exclude=[]
        while True:
            letter = choice(self.__letters__).pick()
            if letter not in exclude:
                return letter

    def get(self):
        letter_list = []
        for l in self.__letters__:
            letter_list.extend(l.get())
        return letter_list


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


def pick_syllable(dont_start_with=list()):
    syllable = []
    if random() < 0.6:
        letter = consonants.pick(exclude=dont_start_with)
        syllable.append(letter)
        letter = vowels.pick(exclude=[letter])
        syllable.append(letter)
        letter = consonants.pick(exclude=[letter])
        syllable.append(letter)
    else:
        letter = vowels.pick(exclude=dont_start_with)
        syllable.append(letter)
        letter = consonants.pick(exclude=[letter])
        syllable.append(letter)
        letter = vowels.pick(exclude=[letter])
        syllable.append(letter)
    return syllable


def pick_single_letter(exclude_letters=None, exclude_group_containing=None):
    if exclude_group_containing in consonants.get():
        letter_group = vowels
    elif exclude_group_containing in vowels.get():
        letter_group = consonants
    else:
        letter_group = consonants if random() < 0.6 else vowels
    return [letter_group.pick(exclude_letters)]



def get_name(max_syllables=2, dont_start_with=list(), dont_end_with=list()):
    middle_letters = []
    last_letter = ""

    for _ in range(randint(1, max_syllables)):
        syllable = pick_syllable(dont_start_with=[last_letter])
        middle_letters.extend(syllable)
        last_letter = syllable[-1]

    first_letter = pick_single_letter(dont_start_with, middle_letters[0])
    last_letter = pick_single_letter(dont_end_with, middle_letters[-1])

    return "".join(first_letter + middle_letters + last_letter).capitalize()


if __name__ == "__main__":
    names = []
    for _ in range(10):
        names.append(get_name(2, ["ck"], ["qu", "sp", "st"]))
    names.sort()
    print "\n".join(names)
