# -*- coding: utf-8 -*-

import sys
import re
import json

from urllib import urlencode
from urllib import quote
from urlparse import parse_qsl

import xbmcgui
import xbmcplugin
import requests

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

mediastore_url = "https://www.mediaklikk.hu/mediatar/"
all_programs_url = "https://www.mediaklikk.hu/iface/mediaklikk/allPrograms/allMusor.json"
filmstore_url = "https://www.mediaklikk.hu/iface/cover/cover_599.html"

mediastore_videos_url= "https://www.mediaklikk.hu/wp-content/plugins/hms-mediaklikk/interfaces/mediaStoreData.php?action=videos&id="

player_url = "https://player.mediaklikk.hu/playernew/player.php?video=_videoID_&flashmajor=31&flashminor=0&embedded=0"

video_programs = { "m1" : "M1", "m2" : "M2", "m4" : "M4", "m5" : "M5", "dn" : "Duna", "dw" : "Duna World"}

stream_matcher = re.compile(".*\\\"file\\\"\\:\\s\\\"(?P<streamurl>.*\\.m3u8).*", re.MULTILINE|re.DOTALL)
# .*\"file\"\:\s\"(?P<streamurl>.*\.m3u8).*
programs_matcher = re.compile(".*mediaStore\\(.*(?P<data>\\[.*\\])\\s*\\)\\;.*", re.MULTILINE|re.DOTALL)
# .*mediaStore\(.*(?P<data>\[.*\])\s*\)\;.*

series_delimiter_matcher = re.compile("\\<h2[^\\>]*\\>Sorozatok\\</h2\\>", re.MULTILINE)

films_matcher = re.compile("(\\<a\\s*(?:class\\=\\\"[^\\\"]*\\\"\\s*)?href\\=\\\"(?P<data>[^\\\"]*)[^\\<]*\\<div\\s*(?:class\\=\\\"[^\\\"]*\\\")?\\s*data-src\\=\\\"(?P<image>[^\\\"]*)\\\"[^\\>]*\\>\\s*(?:\\<div[^\\>]*\\>\\s*(?:\\</div\\>)?\\s*)*\\<h1[^\\>]*\\>\\s*(?P<title>[^\\<]*)\\</h1\\>)", re.MULTILINE|re.DOTALL)
# (\<a\s*(?:class\=\"[^\"]*\"\s*)?href\=\"(?P<data>[^\"]*)[^\<]*\<div\s*(?:class\=\"[^\"]*\"\s*)?data-src\=\"(?P<image>[^\"]*)\"[^\>]*\>\s*(?:\<div[^\>]*\>\s*(?:\</div\>)?\s*)*\<h1[^\>]*\>\s*(?P<title>[^\<]*)\</h1\>)

film_token_matcher = re.compile("\\\"token\\\":\\\"(?P<data>[^\\\"]*)\\\"")
# \"token\":\"(?P<data>[^\"]*)\"

VIDEOS = {'Live': [{'name': 'M1',
                       'thumb': '',
                       'video': 'mtv1live',
                       'genre': 'Live TV'},
                      {'name': 'M2',
                       'thumb': '',
                       'video': 'mtv2live',
                       'genre': 'Live TV'},
                      {'name': 'M4 Sport',
                       'thumb': '',
                       'video': 'mtv4live',
                       'genre': 'Live TV'},
                      {'name': 'M4 Sport Plusz',
                       'thumb': '',
                       'video': 'mtv4plus',
                       'genre': 'Live TV'},
                      {'name': 'M5',
                       'thumb': '',
                       'video': 'mtv5live',
                       'genre': 'Live TV'},
                      {'name': 'Duna',
                       'thumb': '',
                       'video': 'dunalive',
                       'genre': 'Live TV'},
                      {'name': 'Duna World',
                       'thumb': '',
                       'video': 'dunaworldlive',
                       'genre': 'Live TV'}
                      ],
          'Témák' : [],
          'Médiatár' : [],
          'Filmtár' : [],
          'Sorozatok' : []
          }

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.
    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_categories():
    """
    Get the list of video categories.
    Here you can insert some parsing code that retrieves
    the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
    from some site or server.
    .. note:: Consider using `generator functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.
    :return: The list of video categories
    :rtype: types.GeneratorType
    """
    return VIDEOS.keys()


def get_videos(category):
    """
    Get the list of videofiles/streams.
    Here you can insert some parsing code that retrieves
    the list of video streams in the given category from some site or server.
    .. note:: Consider using `generators functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.
    :param category: Category name
    :type category: str
    :return: the list of videos in the category
    :rtype: list
    """
    if category == "Live":
        return VIDEOS[category]
    elif category in ["Filmtár", "Sorozatok"]:
        response = get_filmstore_html()
        films = get_films(response, category.startswith("S"))
        videos = []
        for film in films:
            videos.append({"Title":film[0], "Image":film[1], "Token":film[2]})
        return videos
    else:
        response = requests.get(mediastore_videos_url + category).text
        data = json.loads(response)
        return data["Items"]


def list_main():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'MediaKlikk.hu')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get video categories
    categories = get_categories()
    # Iterate through categories
    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({"thumb": "icon.png",
                          "icon": "icon.png",
                          "fanart": "icon.png"})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
        # 'mediatype' is needed for a skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': category,
                                    'genre': category,
                                    'mediatype': 'video'})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='listing', category=category)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def get_filmstore_html():
    return requests.get(filmstore_url).text

def get_films(response, getseries=False):
    films = set()
    filmslen = series_delimiter_matcher.search(response).start()
    matches = films_matcher.findall(response[filmslen:] if getseries else response[:filmslen])
    for match in matches:
        films.add((match[3].strip().encode("latin_1").decode("utf-8"), match[2], match[1])) # codec problem in website answer
    return films

def get_film_token(film_url):
    response = requests.get(film_url).text
    match = film_token_matcher.findall(response)
    # todo - here also the plot can be checked
    return match[0]

def get_programs():
    response = requests.get(mediastore_url).text
    rawdata = programs_matcher.match(response).group("data")

    data = json.loads(rawdata)

    programs = []
    keys = video_programs.keys()

    for item in data:
        if item["Channel"] in keys:
            programs.append(item)

    return programs

def get_programs_by_topics():
    response = requests.get(all_programs_url).text
    programs = json.loads(response)

    result = { }

    for item in programs:
        for key in item["desc"]:
            if (result.get(key) == None): result[key] = []
            result[key] += [item]

    return result

def list_programs(programs):
    progs = json.loads(programs)

    for program in progs:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=program["title"])
        list_item.setProperty("IsPlayable", "false")

        list_item.setArt({"thumb": program["icon"], "icon": program["icon"], "fanart": program["icon"]})

        list_item.setInfo('video', {'title': program["title"],
                                    'genre': program["topic"] + "(" + program["channel"] + ")",
                                    'mediatype': 'video'})

        url = get_url(action="listing", category=program["id"])
        is_folder = True

        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_items(category):
    """
    Create the list of playable videos in the Kodi interface.
    :param category: Category name
    :type category: str
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, category)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')

    if category == "Live":
        # Get the list of videos in the category.
        videos = get_videos(category)
        # Iterate through videos.
        for video in videos:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=video['name'])
            # Set additional info for the list item.
            # 'mediatype' is needed for skin to display info for this ListItem correctly.
            list_item.setInfo('video', {'title': video['name'],
                                        'genre': video['genre'],
                                        'mediatype': 'video'})
            # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
            # Here we use the same image for all items for simplicity's sake.
            # In a real-life plugin you need to set each image accordingly.
            list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['thumb']})
            # Set 'IsPlayable' property to 'true'.
            # This is mandatory for playable items!
            list_item.setProperty('IsPlayable', 'true')
            # Create a URL for a plugin recursive call.
            # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
            url = get_url(action='play', video=video['video'])
            # Add the list item to a virtual Kodi folder.
            # is_folder = False means that this item won't open any sub-list.
            is_folder = False
            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    elif category == 'Médiatár':
        proginfos = get_programs()

        for program in proginfos:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=program["Title"])
            list_item.setProperty('IsPlayable', 'false')

            list_item.setInfo('video', {'title': program["Title"],
                                        'mediatype': 'video'})

            url = get_url(action='listing', category=program["Id"])
            is_folder = True

            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    elif category == 'Témák':
        proginfos = get_programs()
        programs = get_programs_by_topics()

        for topic in programs.keys():
            plist = []
            for program in programs[topic]:
                proginfo = next((item for item in proginfos if item["Title"]==program["value"]), None)
                if proginfo != None:
                    plist += [{
                            "title" : program["value"],
                            "id" : proginfo["Id"],
                            "icon" : "https://" + program["icon"],
                            "channel" : video_programs[proginfo["Channel"]],
                            "topic" : topic
                        }]


           # jsondump = json.dumps(plist)

            url = get_url(action='listprograms', programs=json.dumps(plist))
            is_folder = True

            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=topic)
            list_item.setProperty('IsPlayable', 'false')

            list_item.setInfo('video', {'title': topic,
                                        'genre': topic,
                                        'mediatype': 'video'})

            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
#    elif category == 'Filmtár':
#        pass
    else:
        videos = get_videos(category)
        for video in videos:
            list_item = xbmcgui.ListItem(label=category)
            list_item.setInfo('video', {'title': video["Title"],
                                        'genre': "Film" if category == 'Filmtár' else video["Title"],
                                        'mediatype': 'video'})
            list_item.setArt({'thumb': video["Image"], 'icon': video['Image'], 'fanart': video['Image']})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', video=video["Token"])
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    """
    Play a video by the provided path.
    :param path: Fully-qualified video URL
    :type path: str
    """

    url = player_url.replace("_videoID_", get_film_token(path) if path.startswith("https://mediaklikk.hu") else path)
    response = requests.get(url).text

    # parse stream url from player response
    streamurl = stream_matcher.match(response).group("streamurl").replace("\\/", "/")

    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=streamurl)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params["action"] == "listprograms":
            # Display the list of videos in a provided category.
            list_programs(params['programs'])
        elif params["action"] == "listing":
            # Display the list of videos in a provided category.
            list_items(params["category"])
        elif params["action"] == "play":
            # Play a video from a provided URL.
            play_video(params["video"])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_main()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])

