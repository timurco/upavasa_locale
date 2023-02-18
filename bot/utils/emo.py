from random import choices, randint, sample

namo = [
    ['🙏'],
    ['🙂', '🤗', '😊', '😌']
]

sad = [
    ['😩', '😔', '😞', '😢', '😟', '😞']
]
time = [
    ['💤', '😴', '⏳', '⌛', '🕰️']
]


def get(emoji_list, mn=1, mx=2, pre=' '):
    quantity = randint(mn, mx)
    e = [choices(n, k=quantity) for n in emoji_list]
    e = sample(e, k=randint(1, len(emoji_list)))
    e = ''.join([''.join(ee) for ee in e])
    return pre + e
