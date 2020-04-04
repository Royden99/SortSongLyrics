# Program Purpose
The whole point of *script.py* is to update a database of song lyrics to include songs from two other song databases as well.  The database being updated is *SI songs*, a directory full of individual song files in XML format.  These files were exported from **OpenLP**, a lyrics projection program.  The desired result is to fill an empty directory named *SongDatabase* with all songs from the three databases; this directory can then be imported back into the **OpenLP** program.
# Basic Program Operation
## Import songs into program memory in Python readable format
Each database of song lyrics is in a different format, and each in turn must be converted into a Python list.  Every entry in the resulting list contains the following information, if available:  
    a string which is the lyrics (verses are separated by one blank line),  
    a string which is the title, and  
    a list which contains the author(s) -- each author is a string.
* HH_songs  
    This database is in a text file format and requires a lot of processing to extract the lyrics in proper format; occasionally it is impossible to separate verses.
* LWS_songs  
    This database is a Json file.  The json module is used to convert the Javascript objects into a list of lovely Python dictionaries which contain the sought-after information (except none of these songs include the authors).
* SI_songs  
    This database, as stated previously, is a directory filled with individual song files in XML format.  This format is defined by *openlyrics* namespace; see [this link](http://api.openlp.io/api/openlp/plugins/songs/lib/openlyricsxml.html "openlyricsxml").  These files are pretty simple to parse using the *Beautiful Soup* library.
## Export function
The export function, defined midway through the source code, takes a song entry from one of the lists and writes it as an XML file to a specified destination, using the title of the song as the file name.  If a file with the same name already exists there, then a numeric digit is appended to the end of the file name, i.e. *filename_1* or *filename_2*.  See the above link for the XML format.
## Compare songs and decide which ones to export
* The Problem  
    In many cases, the same song will exist in each of the three lists, or at least in two of them.  Therefore, the main problem is to call the *export()* function only once on a song that exists in multiple places.  For the purpose of this script, I refer to these songs as being *matched* or having multiple *versions*.  
    A song with multiple versions usually does not have identical lyrics in each case.  This could happen for many reasons; perhaps there is a typo in one of the versions, or one of the versions does not have all the verses to the song, or maybe the song is simply sung differently by the people who use the separate databases.  Therefore, instead of taking action in the script to decide which version of the song to export, the problem in this case is to call *export()* on all versions of the song that are not identical.  That way, the person who operates the song projection software can choose which one to use.
* The Solution  
    In order to complete that objective, the script loops through one of the lists, comparing every song to all the songs in the other lists.  When the end of the first list is reached, the same process is performed on the remaining two lists; the script loops through one of them, comparing every song to all the songs in the other.  Finally, any remaining songs in the last list are exported.  The indexes of songs that have been matched are logged, and those songs are not processed in future iterations.  
    To compare songs, the Python module "fuzzywuzzy" is used as explained [here](https://www.datacamp.com/community/tutorials/fuzzy-string-python "Fuzzy String Matching in Python").  Very simply, the included function `token_sort_ratio(string1, string2)` returns a number indicating how similar the two strings are.  If the result of two songs is 70 or greater, it is counted as a match; if the result is 100, then the two versions are counted as identical.  Also, if more than one match is found in the same list, then the match with the highest result is used.  
    When the script has finished looking for matches to a song, the following logic is used:
    
  * If all versions have identical lyrics, export only one.
  * If not all versions have identical lyrics, export each differing version under the same title (so that they show up side-by-side when sorted alphabetically).
  * If there are no matches, simply export the one version of the song.
    Often, one version of a song does not have any author information while another one does.  Thus, whichever versions of a song are going to be exported are first updated with the conglomerate author information from all available sources.
