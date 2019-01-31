import spotipy
import spotipy.util as util

# MUST ADD SORTED PLAYLISTS TO PL FOLDER


def print_dict(my_dict):
    """Prints all keys and values in dict"""

    for key, value in my_dict.items():
        print(str(key) + ' - ' + str(value))


def print_list(my_list):
    """Prints list items one by one"""

    for item in my_list:
        print(str(item))


def authenticate(username, scope, client_id, client_secret, redirect_uri):
    """Authenticates you to Spotify"""

    token = util.prompt_for_user_token(
            username=username,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri)

    return token


def check_singles(sp, album_dicts, remove_remix):
    """Checks single album to see if track appears on other album already added to playlist"""

    remove_list = []
    all_tracks = []
    for album_dict in album_dicts:

        # Getting tracks on single album
        track_dicts, track_names, track_ids = get_all_album_tracks(sp, album_dict['id'])

        if album_dict['album_group'] == 'album':
            all_tracks.extend(track_names)

        elif album_dict['album_group'] == 'single':

            # Looping through tracks and checking if we need to add or not
            for track in track_names:

                for added_track in all_tracks:
                    # Do not add
                    if added_track.lower() == track.lower():
                        remove_list.append(album_dict['name'].lower())
                    elif remove_remix:
                        if 'remix' in track.lower():
                            remove_list.append(album_dict['name'].lower())

    return [d for d in album_dicts if d.get('name').lower() not in remove_list]


def check_duplicate_albums(sp, album_dicts):
    """Checking literal double albums"""

    return_list = []
    for i in range(len(album_dicts) - 1):
        if album_dicts[i]['name'] != album_dicts[i+1]['name']:
            return_list.append(album_dicts[i])
    return return_list


def check_similar_albums(sp, album_dicts, dup_list):
    """Checks for similar albums: deluxe, explicit and remastered versions"""

    remove_list = []
    for item1 in album_dicts:
        for dup in dup_list:
            if dup.lower() in item1['name'].lower():
                index = item1['name'].lower().index(dup.lower())
                for item2 in album_dicts:
                    if (item2['name'][0:index].lower() in item1['name'][0:index].lower()) and (item2['name'].lower() != item1['name'].lower()):
                        remove_list.append(item2['name'].lower())

    # Returning list without removed dicts
    return [d for d in album_dicts if d.get('name').lower() not in remove_list]


def create_playlist(sp, user_id, name, is_public):
    """Creates a playlist given a spotify object and user id and returns playlist id
       If playlist already exists, simply return the id"""

    # Check if playlist exists
    id = get_playlist_id(sp, user_id, name)
    if id is not None:
        empty_playlist(sp, user_id, id)
        return id
    else:
        # Create new playlist
        sp.user_playlist_create(user_id, name, is_public)
        id = get_playlist_id(sp, user_id, name)
        return id


def get_user_playlists(sp, user_id):
    """Gets all user playlists and adds them to a dict with name and id keys"""

    # Empty lists
    playlist_dicts = []
    playlist_names = []
    playlist_ids = []

    # Getting playlist items from spotify
    playlist_items = sp.user_playlists(user_id)['items']

    # Looping through items and adding to lists
    for item in playlist_items:
        print(item)
        new_playlist = {'name': item['name'], 'id': item['id']}
        playlist_names.append(item['name'])
        playlist_ids.append(item['id'])
        playlist_dicts.append(new_playlist)

    return playlist_dicts, playlist_names, playlist_ids


def get_playlist_id(sp, user_id, name):
    """Returns the playlist id of given name"""

    # Getting playlist dicts, names and ids
    pl_dicts, pl_names, pl_ids = get_user_playlists(sp, user_id)

    # Checking if playlist exists, otherwise return None
    if name in pl_names:
        # Loping through dicts and checking for name to return id
        for pl_dict in pl_dicts:
            if pl_dict['name'] == name:
                return pl_dict['id']
    else:
        return None


def get_artists_albums(sp, artist_uri, album_exclusions, name_exclusions):
    """Returns albums dicts, name and id given artist uri"""

    # Empty lists
    album_dicts = []
    album_names = []
    album_ids = []

    # Getting all albums
    results = sp.artist_albums(artist_uri)

    # Getting album items
    album_items = results['items']

    # Looping through all album items
    for item in album_items:
        can_add = True
        # Checking album_group exclusion like appears_on
        if item['album_group'] not in album_exclusions:
            for excluded_name in name_exclusions:
                # Checking album name not in exclude list like greatest hits, anniversary and best of
                if excluded_name.lower() in item['name'].lower():
                    can_add = False
                    continue
            if can_add:
                new_album = {'name': item['name'], 'rdate': item['release_date'], 'id': item['id'],
                             'album_type': item['album_type'], 'album_group': item['album_group'], 'type': item['type'],
                             'uri': item['uri']}
                album_dicts.append(new_album)
                album_names.append(item['name'])
                album_ids.append(item['id'])

    return album_dicts, album_names, album_ids


def get_all_album_tracks(sp, album_id):
    """Given an album id, get all tracks and track ids"""

    # Empty lists
    track_dicts = []
    track_names = []
    track_ids = []

    # Getting track items
    track_items = sp.album_tracks(album_id)['items']

    # Looping through all items
    for item in track_items:
        new_track = {'name': item['name'], 'id': item['id'], 'track_bumber': item['track_number'],
                     'type': item['type'], 'uri': item['uri']}
        track_dicts.append(new_track)
        track_names.append(item['name'])
        track_ids.append(item['id'])

        playlist_tracks.append(item['name'])

    return track_dicts, track_names, track_ids


def add_album_to_playlist(sp, user_id, playlist_id, album_dict):
    """Adds a album to a user playlist"""

    # Getting tracks from album to add
    track_dicts, track_names, track_ids = get_all_album_tracks(sp, album_dict['id'])

    # Adding tracks
    sp.user_playlist_add_tracks(user_id, playlist_id, track_ids)


def empty_playlist(sp, user_id, pl_id):
    """Delete all tracks from playlist"""

    sp.user_playlist_replace_tracks(user_id, pl_id, [])


def sort_dict_list_by_key(dict_list, sort_key, is_desc=False):
    """Sorting list of dicts by sort_key value and returning new list"""

    return sorted(dict_list, key=lambda i: i[sort_key], reverse=is_desc)


username = '8jktqsxmzbna995hozr8efo14'
scope = 'user-library-read,playlist-modify-private,playlist-modify-public'
client_id = '7c50c23c64d94a99a563e82bc6a3c910'
client_secret = 'a8c77a57ca504069ae503d185caeb82f'
redirect_uri = 'https://www.google.com/'

token = authenticate(username, scope, client_id, client_secret, redirect_uri)
sp = spotipy.Spotify(auth=token)

# User info
user = sp.user(username)
user_id = user['id']

# Exclusions
album_exclusions = ['appears_on']
name_exclusions = ['anniversary', 'best of', 'greatest hits']

# Artists to add sorted playlists for
#artist_uris = ['spotify:artist:5LfGQac0EIXyAN8aUwmNAQ', 'spotify:artist:6FBDaR13swtiWwGhX1WQsP',
#               'spotify:artist:7jy3rLJdDQY21OgRLCZ9sD', 'spotify:artist:256RIQ6zTG7LTrRlAxB5xw']

artist_uris = ['spotify:artist:6FBDaR13swtiWwGhX1WQsP']
#artist_uris = ['spotify:artist:5LfGQac0EIXyAN8aUwmNAQ']

# Looping through artists
for artist_uri in artist_uris:

    # Emptying playlist tracks
    playlist_tracks = []

    # Getting albums
    album_dicts, albums_names, album_ids = get_artists_albums(sp, artist_uri, album_exclusions, name_exclusions)

    # Check duplicate albums
    album_dicts = check_duplicate_albums(sp, album_dicts)

    # Checking singles (excluding remixes)
    album_dicts = check_singles(sp, album_dicts, True)

    # Checking duplicates
    album_dicts = check_similar_albums(sp, album_dicts, ['remaster', 'deluxe'])

    # Sorting albums
    sorted_albums = sort_dict_list_by_key(album_dicts, 'rdate')

    # Creating playlist
    artist = sp.artist(artist_uri)
    artist_name = artist['name']
    print(artist_name)
    pl_name = 'Sorted Playlists\\' + artist_name + ' Sorted'
    pl_id = create_playlist(sp, user_id, pl_name, True)

    # Adding album tracks to playlist
    for dict in sorted_albums:
       # print(dict)
        add_album_to_playlist(sp, user_id, pl_id, dict)

