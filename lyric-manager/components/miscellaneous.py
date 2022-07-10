

def percentage(numerator, denominator):
    return 100 * float(numerator)/float(denominator) if denominator else 0


def get_percentage_and_amount_string(portion, total):
    percentage_value = percentage(portion, total)
    return f"{percentage_value :>6.2f}% ({portion:>4} / {total:>4})"