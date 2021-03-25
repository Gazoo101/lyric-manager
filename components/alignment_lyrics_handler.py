# Python


# 3rd Party
from recordtype import recordtype

# 1st Party


# AlignmentLyric is all data required to properly reassemble the full lyrics once the Aligner as processed the
# raw text.
AlignmentLyric = recordtype('AlignmentLyric',
    [
        ('word_original', ''),  # Includes apostrophe's, commas, and ()'s, e.g. "(bring", "one,", "Glancin'", "Jealousy!"
        ('word_single', ''),    # Doesn't contain commas, ()'s, but keeps short-hand apostrophes, e.g. "bring", "one", "Glancin'"
        ('word_alignment', ''), # Similar to word_single, except converts slangy words to full, e.g. "Glancing"
        ('char_pre_word', ''),  # Contain's connective characters, such as ",',(,),-, and , (commas) 
        ('char_post_word', ''), # Contain's connective characters, such as ",',(,),-, and , (commas)
        ('line_index', -1), 
        ('time_start', -1.0),
        ('time_end', -1.0)
    ]
)

class AlignmentLyricsHandler():
    ''' A class to deal with all the conversions to and from AlignmentLyric struct(s).

    Explain more here!
    '''

    # perhaps not needed?
    def __init__(self, json_schema_version):
        self.json_schema_version = json_schema_version

    def convert_lyrics_raw_to_alignmentlyrics(self, lyrics):
        '''

        Args:
            lyrics: A list of strings.
        
        Returns:
            A list of Alignment
        '''
        lyrics_structured_better = []

        for line_index, lyric_line in enumerate(lyrics):

            lyric_line_parts = lyric_line.split(' ')

            for word in lyric_line_parts:

                # _create_alignmentlyric() returns a list, because if a word ends up being hyphenated,
                # e.g. hiphy-hip-cat, the function will break up the word and return multiple words.
                aligned_lyrics = self._create_alignmentlyric(word, line_index)

                for a_lyric in aligned_lyrics:
                    lyrics_structured_better.append(a_lyric)


        return lyrics_structured_better

    def _create_alignmentlyric(self, word_original, line_index):
        ''' Coverts a single (possibly hyphenated) word to one or more AlignmentLyric's. '''

        # Copied from above:
        # ('word_original', ''),  # Includes apostrophe's, commas, and ()'s, e.g. "(bring", "one,", "Glancin'", "Jealousy!"
        # ('word_single', ''),    # Doesn't contain commas, ()'s, but keeps short-hand apostrophes, e.g. "bring", "one", "Glancin'"
        # ('word_alignment', ''), # Similar to word_single, except converts slangy words to full, e.g. "Glancing"

        word_single = word_original

        # We intentionally do not remove
        characters_to_remove = [',', '!', '(', ')', '"']

        for char in characters_to_remove:
            word_single = word_single.replace(char, '')

        # - Hyphenated word handling -
        # Our brief experimentation has shown that the lyric aligner doesn't change it's alignment-prediction if we pre-split
        # hyphenated words. Given that it makes lyric-to-alignment-timing matching far easier by pre-splitting the hyphenated
        # words, we prefer this approach.
        all_alignment_lyrics = []

        if '-' in word_single:
            pieces = word_single.split('-')

            # If the word is hyphenated we can't really use 'word_original' anymore

            for one_piece in pieces:
                alignment_lyric = AlignmentLyric(
                    word_original=one_piece,
                    word_single=one_piece,
                    word_alignment=one_piece, # Fix this once confirmed is working.
                    char_post_word='-', # Add post-dash to all pieces. Remove the last one later.
                    line_index=line_index
                )

                all_alignment_lyrics.append(alignment_lyric)
            
            # Remove last dash
            all_alignment_lyrics[-1].char_post_word = ''

            if word_original.startswith('"'):
                all_alignment_lyrics[0].char_pre_word = '"'

            if word_original.endswith('"'):
                all_alignment_lyrics[-1].char_post_word = '"'
        else:
            alignment_lyric = AlignmentLyric(
                word_original=word_original,
                word_single=word_single,
                word_alignment=word_single,
                line_index=line_index
            )

            if word_original.startswith('"'):
                alignment_lyric.char_pre_word = '"'

            if word_original.endswith('"'):
                alignment_lyric.char_post_word = '"'

            all_alignment_lyrics.append(alignment_lyric)


        # Fixing "in'" => "ing"
        for a_lyric in all_alignment_lyrics:
            # I think this makes a copy and won't work as intended...
            if a_lyric.word_alignment.lower().endswith("in'"):
                a_lyric.word_alignment = a_lyric.word_alignment[:-1] + "g"

        return all_alignment_lyrics

    def convert_aligmentlyrics_to_dict(self, all_lyrics):
        ''' Turning recordtype into python primitives
        '''

        # TODO: Update this text - it's not accurate anymore
        #   {
        #       lyric_full_sentence = "To the hip, the hippy"
        #       time_start = xxx.xxx,
        #       time_end = xxx.xxx,
        #       lyrics = [
        #           {
        #               word = "something",
        #               time_start = xxx.xxx,
        #               time_end = xxx.xxx
        #           },
        #           ...
        #       ]
        #
        #   }
        #
        #

        ready_to_export_lyrics = {
            "schema_version": self.json_schema_version,
            "lyric_lines": []
        }

        #lyrics_to_return = []

        for lyric in all_lyrics:
            # Assemble into sentences again for entry into dict / strings
            
            if lyric.line_index == len(ready_to_export_lyrics["lyric_lines"]):

                lyric_line = {
                    "text": lyric.word_original,
                    "text": self._get_alignment_lyric_with_pre_post_chars(lyric),
                    "time_start": lyric.time_start,
                    "time_end": lyric.time_end,
                    "lyric_words": [{
                        "original": lyric.word_original,
                        "single": lyric.word_single,
                        "char_pre_word": lyric.char_pre_word,
                        "char_post_word": lyric.char_post_word,
                        "time_start": lyric.time_start,
                        "time_end": lyric.time_end
                    }]
                }

                ready_to_export_lyrics["lyric_lines"].append(lyric_line)
            else:
                if ready_to_export_lyrics["lyric_lines"][lyric.line_index]["text"].endswith("-"):
                    ready_to_export_lyrics["lyric_lines"][lyric.line_index]["text"] += self._get_alignment_lyric_with_pre_post_chars(lyric)                
                else:
                    ready_to_export_lyrics["lyric_lines"][lyric.line_index]["text"] += " " + self._get_alignment_lyric_with_pre_post_chars(lyric)

                # If the time_start of the lyricLine is undefined, we grab the first available lyricWord time_start
                if (ready_to_export_lyrics["lyric_lines"][lyric.line_index]["time_start"] == -1):
                    ready_to_export_lyrics["lyric_lines"][lyric.line_index]["time_start"] = lyric.time_start

                # If the time_end of the lyricWord is undefined, we skip updating the lyricLine's time_end
                if (lyric.time_end != -1):
                    ready_to_export_lyrics["lyric_lines"][lyric.line_index]["time_end"] = lyric.time_end
                ready_to_export_lyrics["lyric_lines"][lyric.line_index]["lyric_words"].append({
                    "original": lyric.word_original,
                    "single": lyric.word_single,
                    "char_pre_word": lyric.char_pre_word,
                    "char_post_word": lyric.char_post_word,
                    "time_start": lyric.time_start,
                    "time_end": lyric.time_end
                })
            
        return ready_to_export_lyrics
    
    def _get_alignment_lyric_with_pre_post_chars(self, alignment_lyric):
        return alignment_lyric.char_pre_word + alignment_lyric.word_original + alignment_lyric.char_post_word
