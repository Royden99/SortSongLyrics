import json
import os
import glob
import bs4
from fuzzywuzzy import fuzz

# Our first task is to scrape songs from multiple databases in different formats,
#   and import the songs into a uniform format so that we can work with them.
#
# Load song info into python lists in the following format:
#   'XX_songs = [[lyrics, title, authors], [song1], ... [song'n']]
#   * lyrics (string)
#       - lyrics should be formatted such that a verse is made of lyric lines without
#           any blank lines in between, and verses are separated by one blank line i.e. ('\n\n')
#   * title (string)
#       - If no title available, it should be logged as 'Unknown' for now.
#   * authors (list)
#       - If no authors available, this list should have 1 entry 'Author Unknown' for now.

# HH Songs:
#   these are lyrics exported by Humphrystown House's 'NewSong' projection program to a text file
#
#   * The songs in this format are somewhat irregular:
#       - Some lyric lines are not separated by any blank lines;
#       - some lyric lines are separated by 1 or more blank lines;
#   * However:
#       - All verses are separated by 1 blank line;
#       - Lyric lines are separated uniformly per song;
#       - There is 1 blank line between the end of a song and its author & copyright info,
#           and 1 blank line between a song's author & copyright info and the beginning of the next song
#
#   Our task is to get all these songs written uniformly in the list 'HH_songs'.
#   Then we will do the same for LWS_songs and SI_songs, which are in different formats.

with open('/home/royden99/Documents/Songs/HH_songs.txt', 'r') as songfile:
    raw = songfile.readlines()

HH_songs = []
queue = []
for line in raw:
    if line[0] == '<':  # end of song
        # Assemble the contents of 'queue' into song lyrics
        # determine most and fewest blank lines separating lyric lines in raw song
        newlines = []
        most_newlines = 0
        fewest_newlines = 0
        newline_prev = False
        q = 0
        for text in queue:
            if text == '\n':
                if newline_prev == True:
                    q += 1
                else:
                    q = 1
                newline_prev = True
            else:
                newlines.append(q)
                q = 0
                newline_prev = False
        most_newlines = max(newlines)
        fewest_newlines = min(newlines)

        if most_newlines >= 2:   # lyric lines are separated by >= 2 blank lines
            # loop through queue, finding empty lines that we want to delete; 'delete_lines'
            #   holds the index of these lines
            delete_lines = []
            for i in range(len(queue)):
                if queue[i] == '\n' and queue[i-1] != '\n':
                    try:
                        if queue[i+1] == '\n':  # regular lyric line
                            n = 0 
                            while queue[i+n] == '\n':
                                delete_lines.append(i+n)
                                n += 1
                        else:                   # verse separator
                            pass
                    except IndexError:  # because 'queue[i+1]' fails at the last line
                        pass
            # now delete these lines in queue
            for n in delete_lines:
                queue.pop(n)
                # have to reduce the index values in 'delete_lines' to match the shrinking queue
                for i in range(len(delete_lines)):
                    delete_lines[i] = delete_lines[i] - 1
            # delete first and last blank line
            if queue[0] == "\n":
                queue.pop(0)
            if queue[len(queue)-1] == '\n':
                queue.pop(len(queue)-1)

        elif most_newlines == 1 and fewest_newlines == 1:   # all lines in song are 1 blank line apart
            # remove all blank lines
            while True:
                try:
                    queue.remove('\n')
                except ValueError:
                    break

        else:   # lyric lines are separated by 0 blank lines
            # remove first and last lines (if blank) from queue
            if queue[0] == "\n":
                queue.pop(0)
            if queue[len(queue)-1] == '\n':
                queue.pop(len(queue)-1)

        # find the author, if exists
        authors = []
        i = 1
        charbuff = []
        while line[i] != ',':
            charbuff.append(line[i])
            i += 1
        author = ''.join(charbuff)
        if 'nknown' not in author:  # avoid 'Unknown' (this is trying to be case insensitive)
            authors.append(author)
        else:
            authors.append('Author Unknown')

        # add song to list
        lyrics = ''.join(queue)
        HH_songs.append([lyrics, 'Unknown', authors]) # title info is not available
        queue = []

    else:               # gather lines of song in queue
        queue.append(line)

# LWS Songs:
#   this is the database for the 'Living Word Songbook' website; 
#   these songs are stored in a .json file
with open("/home/royden99/Documents/Songs/LWS_songs.json") as J:
    Json = J.read()

LWS_songs = []

# Use python module 'json' to parse the json file, converting the data to python objects
raw = json.loads(Json)
# 'raw' is a list of songs; each song is a dict:
#   raw == [{song0}, {song1}, ... {song'n'}]
#   each song has the following keys:
#   'songbookEntryNumber':, 'englishTitle':, 'spanishTitle':, 'englishWords':, 'spanishWords':,
#   'tabsFlag':, 'englishTabsFlag':, 'spanishTabsFlag':, 'englishSheetMusic':, 'spanishSheetMusic':, 
#   'video':, 'audio':, 'keyableEnglishTitle':, 'keyableSpanishTitle':, 'searchableTitle':, 
#   'searchableText':, 'englishSortOrder':, 'spanishSortOrder':
#
#   * Inside the lyrics:
#       - newlines are represented as pipes ('|'); also it is not entirely predictable where these
#           will show up
#       - verses are separated by 1 blank line (just the way we like it!)

for song in raw:
    # get english and spanish lyrics together
    lyrics = song['englishWords'] 
    lyrics = lyrics.lstrip()    # remove any whitespace from the beginning
    espanol = song['spanishWords'].lstrip()
    if espanol != "":
        if lyrics[len(lyrics)-2:] == '| ':
            lyrics = lyrics + "\n" + espanol
        else:
            lyrics = lyrics + "\n\n" + espanol

    # remove tablatures (anything in brackets) from lyrics
    delete_lines = []
    for i in range(len(lyrics)-1):
        if lyrics[i] == '[':
            delete_lines.append(i)
            n = 0
            while lyrics[i+n] != ']':
                delete_lines.append(i+(n+1))
                n += 1
    for index in delete_lines:
        try:
            lyrics = lyrics[:index] + lyrics[index+1:]
        except IndexError:
            pass
        for i in range(len(delete_lines)):
            delete_lines[i] = delete_lines[i] - 1

    # newlines: replace '| ' with '\n'
    lyrics = lyrics.replace('| ', '\n')
    lyrics = lyrics.replace('|\t', '\n\t')  # sometimes that happens too
    lyrics = lyrics.replace('|', '')        # get rid of any remaining pipes !!

    # read title
    title = song['englishTitle']

    # add song to the list
    LWS_songs.append([lyrics, title, ['Author Unknown']])    # author info is not available

# SI songs:
#   these are songs originally from the Shepherd's Inn database
#   they are stored in 'openlyrics' XML format
#       * There is a separate XML file for each song;
#           title, author, and lyrics information is found in XML tags in the file.
#       * In the lyrics, newlines are represented as '<br/>'

# Use python modules 'os' and 'glob' to navigate the XML files in the specified directory
os.chdir('/home/royden99/Documents/Songs/SI_songs')
Songs = glob.glob('*.xml') # a list containing the XML filenames in the directory
SI_songs = []

for xmlfile in Songs:           # iterate over the list of filenames, processing each one in turn
    with open(xmlfile) as F:
        xml = F.read()

    # Use python module 'bs4' (BeautifulSoup) to parse the XML

    # read lyrics
    soup = bs4.BeautifulSoup(xml, 'lxml')
    lyrics = ''
    first_verse = True
    for verse in soup.song.lyrics.children: # lyrics are separated into verses -- so nice!
        if type(verse) == bs4.element.Tag:
            if first_verse == True:
                first_verse = False
            else:
                lyrics = lyrics + '\n\n'
            for line in verse.lines.children:
                if type(line) == bs4.element.Tag:
                    if line.name == 'br':           # treat '<br/>' as a newline
                        lyrics = lyrics + '\n'
                    else:
                        print('Error: unknown tag found in lyrics of song: ',
                                soup.song.properties.titles.title.string)
                        quit()
                else:
                    lyrics = lyrics + line

    # read title
    title = soup.song.properties.titles.title.string
    
    # read author(s)
    authors = []
   
    # look for authors in the title
    if '(' in title or '-' in title: 
        charbuff = []
        active = False
        for char in title:
            if char == '(' or char == '-':
                active = True
            else:
                if active == True:
                    if char == ')':
                        author = ''.join(charbuff)
                        if 'Spanish' not in author:     # happened a few times
                            authors.append(author)
                        charbuff = []
                        active = False
                    else:
                        charbuff.append(char)
        if charbuff != []:
            authors.append(''.join(charbuff[1:]))
        # delete parentheses and their contents from title
        try:
            title = title[0:title.index('(')]
        except ValueError:
            pass

    # look for authors where they actually should be
    for author in soup.song.properties.authors.children:
        if type(author) == bs4.element.Tag:
            if author.string != 'Author Unknown':
                authors.append(author.string)

    if authors == []:    # still empty
        authors.append('Author Unknown')
    
    SI_songs.append([lyrics, title, authors])
#_______________________________________________________________________________________

# The next task is to fill an empty directory with all the songs found in each list.
#   However, we only want to write multiple versions of one song to our new database if
#       those versions do not identically match each other.  That way, the user of song
#       projection software can view separate versions of a song side-by-side, and decide
#       which one he wants to keep.
#   To complete this task, we need to index the song lists against each other and use 
#       'fuzzy string matching' (using the python module 'fuzzywuzzy') to determine how 
#       similar two songs are (whether they match).
#
# * Compare HH, LWS, and SI songs, and find songs from each list that match each other.
# * For each set of matched songs:
#   - if author or title is missing from a song, compare with the other songs to fill in the gaps.
#   - if matched songs have identical lyrics:
#       export only one version.
#   - otherwise if lyrics differ: 
#       export all versions so we have different versions of same song side by side
#       (title should be the same)

def export(song):
    """Arg 'song' should be an item in one of the 'XX_songs' lists.
    This function converts the song to openlyrics XML format and writes it to a specified filepath.
    """
    lyrics = song[0].replace('\n', '<br/>') # the OpenLyrics way of doing newlines
    title = song[1]
    authors = song[2]

    # forward slash in the title is problematic because linux interprets it as part of the filepath
    if '/' in title:
        title = title.replace('/', ';')
    # '&' character is apparently not allowed in text stored in XML
    if '&' in title:
        title = title.replace('&', 'and')
    if '&' in lyrics:
        lyrics = lyrics.replace('&', 'and')
    for author in authors:
        if '&' in author:
            author = author.replace('&', 'and')

    # convert lyrics from a single string into a list of verses
    charbuff = []
    verses = []
    i = 0
    while i != len(lyrics):
        char = lyrics[i]
        if char == '<':
            if lyrics[i:i+10] == '<br/><br/>':  # a blank line indicates the start of a new verse
                verses.append(''.join(charbuff))
                charbuff = []
                i += 9
            else:
                charbuff.append(char)
        else:
            charbuff.append(char)
        i += 1
    verses.append(''.join(charbuff))

    # Specify a filepath, with the song title as the file name
    filepath = '/home/royden99/Documents/Songs/SongDatabase/{}.xml'.format(title)
    i = 1
        # prevent separate versions of song with the same title from being overwritten:
        #   append a digit to the end of a filename if one of the same name exists already
    while os.path.exists(filepath):
        filepath = '/home/royden99/Documents/Songs/SongDatabase/{}_{}.xml'.format(title, i)
        i += 1

    # write some XML to the new file!
    with open(filepath, 'w') as xml:
        xml.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        xml.write("""<song xmlns="http://openlyrics.info/namespace/2009/song" version="0.8">\n""")
        xml.write("  <properties>\n    <titles>\n      <title>{}</title>\n    </titles>\n    <authors>\n"
                .format(title))
        for author in authors:
            xml.write("      <author>{}</author>\n".format(author))
        xml.write("    </authors>\n  </properties>\n  <lyrics>\n")
        for i in range(len(verses)):
            verse = verses[i]
            xml.write("""    <verse name="v{}">\n      <lines>{}</lines>\n    </verse>\n"""
                    .format(i+1, verse))
        xml.write("  </lyrics>\n</song>")

#---------------------------------------

HH_used = []    # store the indexes of already processed songs in here
LWS_used = []

# Loop through SI_songs, indexing against both HH_songs and LWS_songs
for n in range(len(SI_songs)):
    SI_song = SI_songs[n]
    print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\tprocessing SI_song[{}]'.format(n))

    # index against HH_songs
    first_match = True
    HH_matched = False
    for i in range(len(HH_songs)):
        if i not in HH_used:
            HH_song = HH_songs[i]
            
            # Looking for fuzzy similarities -- a BIG task. 
            #   This function returns a number between 0 and 100,
            #   i.e. an indicator of how similar the two strings are.
            ratio = fuzz.token_sort_ratio(SI_song[0], HH_song[0])

            if ratio >= 70:     # probably a match
                if first_match == True:
                    HH_match = HH_song
                    HH_ratio = ratio
                    first_match = False
                    HH_matched = True
                    HH_used.append(i)
                # if two HH songs match SI song, use the one with highest ratio
                else:
                    if ratio > HH_ratio:
                        HH_match = HH_song
                        HH_ratio = ratio
                        HH_used[len(HH_used)-1] = i
    # index against LWS_songs
    first_match = True
    LWS_matched = False
    for i in range(len(LWS_songs)):
        if i not in LWS_used:
            LWS_song = LWS_songs[i]
            ratio = fuzz.token_sort_ratio(SI_song[0], LWS_song[0])
            if ratio >= 70:     # probably a match
                if first_match == True:
                    LWS_match = LWS_song
                    LWS_ratio = ratio
                    first_match = False
                    LWS_matched = True
                    LWS_used.append(i)
                # if two HH songs match LWS song, use the one with highest ratio
                else:
                    if ratio > LWS_ratio:
                        LWS_match = LWS_song
                        LWS_ratio = ratio
                        LWS_used[len(LWS_used)-1] = i

    # Export logic
    if HH_matched == True and LWS_matched == True:
        if HH_ratio == 100 and LWS_ratio == 100:
            # complete authors, export 1 version
            if SI_song[2][0] == 'Author Unknown' and HH_match[2][0] != 'Author Unknown':
                SI_song[2][0] = HH_match[2][0]
            export(SI_song)

        elif HH_ratio == 100 and LWS_ratio != 100:
            # share author info, export SI & HH as 1 version, export LWS
            if HH_match[2][0] != 'Author Unknown':
                if SI_song[2][0] == 'Author Unknown':
                    SI_song[2][0] = HH_match[2][0]
                LWS_match[2][0] = HH_match[2][0]
            else:
                LWS_match[2][0] = SI_song[2][0]

            LWS_match[1] = SI_song[1]       # make sure all versions have same title
            export(SI_song)
            export(LWS_match)

        elif HH_ratio != 100 and LWS_ratio == 100:
            # export SI & LWS as 1 version; export HH
            if HH_match[2][0] == 'Author Unknown':
                HH_match[2][0] = SI_song[2][0]
            elif SI_song[2][0] == 'Author Unknown':
                SI_song[2][0] = HH_match[2][0]
            HH_match[1] = SI_song[1]
            export(SI_song)
            export(HH_match)

        else:   # if none of the three are identical
            if HH_match[2][0] == 'Author Unknown':
                LWS_match[2][0] = HH_match[2][0] = SI_song[2][0]
            elif SI_song[2][0] == 'Author Unknown':
                LWS_match[2][0] = SI_song[2][0] = HH_match[2][0]
            HH_match[1] = LWS_match[1] = SI_song[1]
            # export all three versions
            export(SI_song)
            export(HH_match)
            export(LWS_match)

    elif HH_matched == True:    # there was a match in HH but not LWS
        if HH_ratio == 100:
            if SI_song[2][0] == 'Author Unknown' and HH_match[2][0] != 'Author Unknown':
                SI_song[2][0] = HH_match[2][0]
            export(SI_song)
            
        else:
            if HH_match[2][0] == 'Author Unknown':
                HH_match[2][0] = SI_song[2][0]
            elif SI_song[2][0] == 'Author Unknown':
                SI_song[2][0] = HH_match[2][0]
            HH_match[1] = SI_song[1]
            export(SI_song)
            export(HH_match)

    elif LWS_matched == True:   # there was a match in LWS but not HH
        if LWS_ratio == 100:
            export(SI_song)

        else:
            LWS_match[2] = SI_song[2]
            LWS_match[1] = SI_song[1]
            export(SI_song)
            export(LWS_match)

    else:                       # there were no matches in LWS or HH
        export(SI_song)

#--------------------------------------

# Loop through any remaining HH_songs, indexing them against LWS_songs
for i in range(len(HH_songs)-1):
    if i not in HH_used:    # don't process songs that were already dealt with
        print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\tprocessing HH_song[{}]'.format(i))
        HH_song = HH_songs[i]
        first_match = True
        LWS_matched = False
        # index against remaining LWS songs 
        for j in range(len(LWS_songs)):
            if j not in LWS_used:
                LWS_song = LWS_songs[j]
                ratio = fuzz.token_sort_ratio(HH_song[0], LWS_song[0])
                if ratio >= 70:     # probably a match
                    if first_match == True:
                        LWS_match = LWS_song
                        LWS_ratio = ratio
                        first_match = False
                        LWS_matched = True
                        LWS_used.append(j)
                    # if two HH songs match LWS song, use the one with highest ratio
                    else:
                        if ratio > LWS_ratio:
                            LWS_match = LWS_song
                            LWS_ratio = ratio
                            LWS_used[len(LWS_used)-1] = j

        # Export logic
        if LWS_matched == True:     # match between HH and LWS songs
            if LWS_ratio == 100:
                HH_song[1] = LWS_match[1]
                export(HH_song)
            else:
                HH_song[1] = LWS_match[1]
                LWS_match[2] = HH_song[2]
                export(HH_song)
                export(LWS_match)

        else:                       # no matches
            # HH songs have no title, and here we have no matched songs to compare it with;
            #   thus we take the first line of the lyrics as the title
            lyrics = HH_song[0]
            charbuff = []
            for char in lyrics:
                if char != '\n':
                    charbuff.append(char)
                else:
                    title = ''.join(charbuff)
                    break
            HH_song[1] = title
            export(HH_song)

#-----------------------------------------------

# Loop through any remaining LWS songs and export them
for i in range(len(LWS_songs)):
    if i not in LWS_used:  
        print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\tprocessing LWS_song[{}]'.format(i))
        LWS_song = LWS_songs[i]
        export(LWS_song)
