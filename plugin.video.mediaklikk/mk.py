import sys
import re
import json
from urllib import urlencode
from urlparse import parse_qsl

sys.path.append("../script.module.requests/lib")
sys.path.append("../script.module.urllib3/lib")
sys.path.append("../script.module.certifi/lib")

import xbmcgui
import xbmcplugin

import requests

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

mediastoreurl = "https://www.mediaklikk.hu/mediatar/"
mediastorevideosurl= "https://www.mediaklikk.hu/wp-content/plugins/hms-mediaklikk/interfaces/mediaStoreData.php?action=videos&id="

playerurl = "https://player.mediaklikk.hu/playernew/player.php?video=_videoID_&flashmajor=31&flashminor=0&embedded=0"

#playerurl = "https://player.mediaklikk.hu/playernew/player.php?video=_videoID_&flashmajor=31&flashminor=0&osfamily=Ubuntu&osversion=null&browsername=Kodi&browserversion=63.0&title=M1&contentid=_videoID_&embedded=0"


# "file": "\/\/c202-node62-cdn.connectmedia.hu\/1100\/7009c6254e877d9051ddeda3741275cf\/5bd5e317\/index.m3u8?v=5i",

videoprograms = { "m1", "m2", "m4", "m5", "dn", "dw" }

#streammatcher = re.compile(".*\\\"file\\\"\\:\\s\\\"(?P<streamurl>.*index\\.m3u8\\?v\\=5i).*", re.MULTILINE|re.DOTALL)
streammatcher = re.compile(".*\\\"file\\\"\\:\\s\\\"(?P<streamurl>.*\\.m3u8).*", re.MULTILINE|re.DOTALL)

programsmatcher = re.compile(".*mediaStore\\(.*(?P<data>\\[.*\\])\\s*\\)\\;.*", re.MULTILINE|re.DOTALL)
#programsmatcher = re.compile(".*new\\smediaStore\\((?P<data>\\[.*\\])\\)\\;.*", re.MULTILINE|re.DOTALL)

VIDEOS = {'Live': [{'name': 'M1',
                       'thumb': "", # 'https://www.mediaklikk.hu/wp-content/plugins/hms-mediaklikk/common/styles/images/mtva_logos_sprite_light_2x.png',
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
          'Media' : []}

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
    return VIDEOS.iterkeys()


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
    else:
        response = requests.get(mediastorevideosurl + category).text
        data = json.loads(response)
        return data["Items"]


def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'My Video Collection')
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
       #list_item.setArt({'thumb': VIDEOS[category][0]['thumb'],
       #                  'icon': VIDEOS[category][0]['thumb'],
       #                  'fanart': VIDEOS[category][0]['thumb']})
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
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def get_programs():
    response = requests.get(mediastoreurl).text
    rawdata = programsmatcher.match(response).group("data")
    
    data = json.loads(rawdata)

    programs = []

    for item in data:   
        if item["Channel"] in videoprograms:
            programs.append(item)
    
    return programs

def list_videos(category):
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
    elif category == "Media":
        programs=get_programs()

        for program in programs:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=program["Title"])
            # Set additional info for the list item.
            # 'mediatype' is needed for skin to display info for this ListItem correctly.
            list_item.setInfo('video', {'title': program["Title"],
                                        'genre': program["Title"],
                                        'mediatype': 'video'})
            # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
            # Here we use the same image for all items for simplicity's sake.
            # In a real-life plugin you need to set each image accordingly.
            #list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['thumb']})
            # Set 'IsPlayable' property to 'true'.
            # This is mandatory for playable items!
            list_item.setProperty('IsPlayable', 'false')
            # Create a URL for a plugin recursive call.
            # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4

            url = get_url(action='listing', category=program["Id"])
            # Add the list item to a virtual Kodi folder.
            # is_folder = False means that this item won't open any sub-list.
            is_folder = True
            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    else:
        videos = get_videos(category)
        for video in videos:
            list_item = xbmcgui.ListItem(label=category)
            list_item.setInfo('video', {'title': video["Title"],
                                        'genre': video["Title"],
                                        'mediatype': 'video'})
            list_item.setArt({'thumb': video["Image"], 'icon': video['Image'], 'fanart': video['Image']})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', video=video["Token"])#.replace("%25", "%") # bug in get_url ?
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
    url = playerurl.replace("_videoID_", path)
    response = requests.get(url).text

    streamurl = "http:" + streammatcher.match(response).group("streamurl").replace("\\/", "/")

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
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_videos(params['category'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
    
