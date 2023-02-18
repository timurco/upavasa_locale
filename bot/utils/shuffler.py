from random import choice, shuffle, seed, randrange


def flat(seq):
    for el in seq:
        if isinstance(el, list):
            yield from flat(el)
        else:
            yield el


def str_choice(text, sep='|'):
    return choice(text.split(sep)) if sep in text else text


class Shuffler:
    def __init__(self, *parts, shuffle=30):
        self.shuffle = shuffle
        self.parts = parts

    def sent_shuffle(self, tokens):
        seed(randrange(100))
        phrase = [tokens[0]]
        if len(tokens) > 1 and randrange(100) > self.shuffle:
            phrase.append(self.sent_shuffle(tokens[1:]))
            shuffle(phrase)
        return phrase

    def compile(self, last_rnd=None, sep=', ', cap=True):
        parts = []
        for text in self.parts:
            tokens = [str_choice(x, ) for x in text.split(" ")]
            sent = list(flat(self.sent_shuffle(tokens)))
            parts.append(' '.join(sent))
        # Перемешиваем
        shuffle(parts)
        # И делаем заглавную букву
        if cap:
            parts[0] = parts[0].capitalize()
        return sep.join(parts) + (choice(last_rnd) if last_rnd else '')


def shuffler(*parts, shuffle=30, last_rnd):
    return Shuffler(*parts, shuffle).compile()