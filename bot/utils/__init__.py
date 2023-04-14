from bot.settings import settings


# Maximum characters of telegram messages is 9500
def truncate_middle(s, n=settings.telegram_max_length):
    if len(s) <= n:
        # string is already short-enough
        return s
    # half of the size, minus the 3 .'s
    n_2 = int(n) // 2 - 3
    # whatever's left
    n_1 = n - n_2 - 3
    return '{0}...{1}'.format(s[:n_1], s[-n_2:])


def truncate_margiis(msg, num_msg, TG_MAX=settings.telegram_max_length):
    trun_msg_suffix = "\n<code>... И еще <b>NNNNN</b> сообщений остальным маргам.</code>"
    if len(msg) > TG_MAX - len(trun_msg_suffix) - 10:  # 10 запас
        truncated_msg = msg[:TG_MAX - len(trun_msg_suffix)]
        last_newline_index = truncated_msg.rfind("\n")
        truncated_msg = truncated_msg[:last_newline_index]

        truncated_messages_count = num_msg - len(truncated_msg.split("\n")) + 1
        msg = truncated_msg + trun_msg_suffix.replace("NNNNN", str(truncated_messages_count))
    return msg
