



#’ into '


def simplify(text: str):
    """
    Borne out of "Can't Get Blue Monday Out of My Head" not matching "Can’t Get Blue Monday Out of My Head"

    This function is meant to simplify these frustrating collisions...
    """
    text = text.replace("’", "'")
    text = text.replace("D.J.", "dj")

    return text


def how_many_match_initially(text_one: str, text_two:str):
    """ Consider limiting this to the amount of text before 'Lyrics' and get a percentage... """

    matches = 0
    for one, two in zip(text_one.lower(), text_two.lower()):
        if one == two:
            matches += 1
        else:
            return matches

    # If either string 'runs out of chars'
    return matches


def percentage_song_name_match(song_name: str, text_with_song_name_in_it):
    matching_chars = how_many_match_initially(song_name, text_with_song_name_in_it)
    return matching_chars / len(song_name)


