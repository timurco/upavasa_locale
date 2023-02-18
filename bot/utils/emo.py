from random import choices, randint, sample

namo = """
🙏
🙂🤗😊😌
""".strip().split('\n')

sad = "😩😔😞😢😟😞".strip().split('\n')
time = "⏳⌛️💤🕰".strip().split('\n')


def get(emoji_list, mn=1, mx=2, pre=' '):
    e = [choices(n, k=randint(mn, mx)) for n in emoji_list]
    e = sample(e, k=randint(1, len(emoji_list)))
    e = ''.join([''.join(ee) for ee in e])
    return pre + e
