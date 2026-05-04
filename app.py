from flask import Flask, request, render_template

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import csv
import matplotlib.pyplot as plt
import numpy as np

import requests, json

recco_base = "https://api.reccobeats.com/v1/"
recco_payload = {}
recco_headers = {
    'Accept': 'application/json'
}

time_range = "medium_term"
track_limit = 10

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    msg = ""
    return render_template('home.html', msg=msg)

@app.route('/top10', methods=['POST'])
def top10():
    CLIENT_ID = request.form.get('client_id')
    CLIENT_SECRET = request.form.get('client_secret')
    REDIRECT_URI = request.form.get('redirect_uri')

    track_limit = request.form.get('track_limit')
    time_range = request.form.get('time_range')
    include_liked = request.form.get('include_liked')

    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope='user-top-read'
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    try:
        sp.current_user()
    except spotipy.exceptions.SpotifyOauthError:
        return render_template('home.html', msg="Please enter valid client credentials")
    
    print("Client authorized")

    top_artists = sp.current_user_top_artists(limit=track_limit, time_range=time_range)['items']
    data = []
    for artist in top_artists:
        data.append([artist['name'], artist['images'][0]['url']])
    with open('data/top_artists.tsv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerows(data)

    print("top_artists.tsv written")

    top_tracks = sp.current_user_top_tracks(limit=track_limit, time_range=time_range)['items']
    data = []
    for track in top_tracks:
        data.append([track['artists'][0]['name'] + ' - ' + track['name'], track['album']['images'][0]['url']])
    with open('data/top_tracks.tsv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerows(data)

    print("top_tracks.tsv written")
    
    avg_info = {
        'acousticness': 0,
        'danceability': 0,
        'energy': 0,
        'instrumentalness': 0,
        'loudness': 0,
        'tempo': 0,
        'valence': 0,
        'duration_ms': 0,
        'popularity': 0
    }
    avg_info_units = {
        'acousticness': '%',
        'danceability': '%',
        'energy': '%',
        'instrumentalness': '%',
        'loudness': ' db (-60 to 0)',
        'tempo': ' bpm (0-250)',
        'valence': '%',
        'duration_ms': ' (min:sec.ms)',
        'popularity': ' (0-100)'
    }
    years = []
    artist_appearances = {}
    top_track_artist_appearances = {}
    album_appearances = {}

    def set_score(field, value, track):
        if not include_liked and track not in top_tracks:
            return
        track_info = [track['artists'][0]['name'] + ' - ' + track['name'], track['album']['images'][0]['url']]
        lowest_score = song_scores[field][1]
        highest_score = song_scores[field][3]

        if value <= lowest_score:
            song_scores[field][0] = track_info
            song_scores[field][1] = value
        if value >= highest_score:
            song_scores[field][2] = track_info
            song_scores[field][3] = value
    song_scores = {}
    for field in avg_info:
        if isinstance(avg_info[field], int):
            song_scores[field] = ["Lowest scoring song", 9999999999, "Highest scoring song", -9999999999]
    song_scores['years'] = ["Lowest scoring song", 9999999999, "Highest scoring song", -9999999999]

    total_tracks_with_data = 0
    albums_with_popularity_data = 0

    top_tracks = sp.current_user_top_tracks(limit=track_limit, time_range=time_range)['items']
    saved_tracks = sp.current_user_saved_tracks(limit=track_limit)['items']
    all_tracks = []

    if len(top_tracks) == 0:
        return render_template('home.html', msg="You have no top tracks, get to listening!")

    print("Current user's top and saved tracks gathered")

    for track_item in saved_tracks:
        all_tracks.append(track_item['track'])
    for track in top_tracks:
        all_tracks.append(track)

        artist = track['artists'][0]['name']
        if artist in top_track_artist_appearances:
            top_track_artist_appearances[artist] += 1
        else:
            top_track_artist_appearances[artist] = 1

        album = track['album']
        str_rep = artist + ' - ' + album['name']
        if str_rep in album_appearances:
            album_appearances[str_rep][0] += 1
        else:
            album_appearances[str_rep] = [1, album['images'][0]['url']]

    sorted_dict = {key: val for key, val in sorted(album_appearances.items(), key=lambda item: item[1][0], reverse=True)}
    data = []
    for album in sorted_dict:
        data.append([album, sorted_dict[album][1]])
    with open('data/top_albums.tsv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerows(data)

    print("top_albums.tsv written")

    for track in all_tracks:
        audio_features = get_audio_features(track['id'])
        if (track in all_tracks and include_liked) or track in top_tracks:
            if audio_features != None:
                total_tracks_with_data += 1

                avg_info['duration_ms'] += track['duration_ms']
                set_score('duration_ms', track['duration_ms'], track)

                release_year = int(track['album']['release_date'][:4])
                years.append(release_year)
                set_score('years', release_year, track)
                for audio_feature in audio_features:
                    if audio_feature in avg_info:
                        value = audio_features[audio_feature]
                        avg_info[audio_feature] += value
                        set_score(audio_feature, value, track)
        
        popularity = get_album_popularity(track['album']['id'])
        avg_info['popularity'] += popularity
        if popularity > 0:
            set_score('popularity', popularity, track)
        albums_with_popularity_data += 1 if popularity != 0 else 0

        artist = track['artists'][0]['name']
        if artist in artist_appearances:
            artist_appearances[artist] += 1
        else:
            artist_appearances[artist] = 1
        
        print(f"Gathered data of {total_tracks_with_data}/{len(all_tracks)} songs")

    for info in avg_info:
        if total_tracks_with_data == 0:
            break
        if info == 'popularity':
            continue
        avg_info[info] /= total_tracks_with_data
    if albums_with_popularity_data > 0:
        avg_info['popularity'] /= albums_with_popularity_data

    print("Average song values gathered")

    data = []
    for info in avg_info:
        data.append([info, avg_info[info], avg_info_units[info]])
    with open('data/avg_data.tsv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerows(data)

    print("avg_data.tsv written")

    with open('data/years_listened.txt', 'w') as file:
        for year in years:
            file.write(str(year) + '\n')
    
    print("years_listened.txt written")

    with open('data/artist_appearances.tsv', 'w', newline='') as file:
        data = []
        for artist in artist_appearances:
            data.append({
                'Artist': artist,
                'Top Songs/Likes Appearances': artist_appearances[artist],
                "Top Songs Appearances": top_track_artist_appearances[artist] if artist in top_track_artist_appearances else 0
            })
        fieldnames = ["Artist", "Top Songs/Likes Appearances", "Top Songs Appearances"]
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='\t')
        writer.writerows(data)

    print("artist_appearances.tsv written")

    with open('data/song_scores.tsv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        data = []
        for field in song_scores:
            data.append([field, song_scores[field][0], song_scores[field][1], song_scores[field][2], song_scores[field][3]])
        writer.writerows(data)
    
    print("song_scores.tsv written")
    
    # DATA GATHERING

    artist_appearances = []
    with open('data/artist_appearances.tsv', 'r') as file:
        for line in file:
            line_split = line.split('\t')
            artist_appearances.append(line_split)

    top_artists = []
    with open('data/top_artists.tsv', 'r') as file:
        for line in file:
            line_split = line.split('\t')
            top_artists.append(line_split)
    
    top_tracks = []
    with open('data/top_tracks.tsv') as file:
        for line in file:
            line_split = line.split('\t')
            top_tracks.append(line_split)

    top_albums = []
    with open('data/top_albums.tsv') as file:
        for line in file:
            line_split = line.split('\t')
            top_albums.append(line_split)

    labels = []
    sizes = []
    def percent_to_int(percent):
        return int(np.round(percent / 100 * sum(sizes), 0))
    
    figsize = (9, 6)
    radius = 1.25
    legend_xOffset = -0.5
    title_yOffset = 1.1
    fontsize = 8

    def draw_chart(sizes, labels, title):
        colors = []
        sub_value = 215 / len(labels)
        for i in range(0, len(labels)):
            col_val = (215 - sub_value * i) / 255
            colors.append((30/255, col_val, 96/255))

        greatest_slice = max(sizes)
        max_i = sizes.index(greatest_slice)
        explode_val = tuple([0 if i != max_i else 0.2 for i in range(len(sizes))])

        _, ax = plt.subplots(figsize=figsize)
        wedges, _, autotexts = ax.pie(sizes, autopct=percent_to_int, explode=explode_val, radius=radius, textprops={'fontsize': fontsize}, colors=colors)
        for txt in autotexts:
            txt.set_color('white')
        
        leg = ax.legend(wedges, labels, title='Artists (Counterclockwise)', loc='center left', fontsize=fontsize)
        bb = leg.get_bbox_to_anchor().transformed(ax.transAxes.inverted())
        bb.x0 += legend_xOffset
        bb.x1 += legend_xOffset
        leg.set_bbox_to_anchor(bb, transform=ax.transAxes)
        leg_frame = leg.get_frame()
        leg_frame.set_facecolor((0.25, 0.25, 0.25))
        leg.get_title().set_color((0.95, 0.95, 0.95))
        for text in leg.get_texts():
            text.set_color('white')

        title = ax.set_title(title, y=title_yOffset)
        title.set_color('white')

    for info in artist_appearances:
        sizes.append(int(info[1]))
        labels.append(info[0])

    draw_chart(sizes, labels, f"Artist appearances in top + past liked {int(track_limit) * 2} tracks")
    plt.savefig('static/chart1.png', transparent=True)

    labels = []
    sizes = []
    for info in artist_appearances:
        if int(info[2]) == 0:
            continue
        sizes.append(int(info[2]))
        labels.append(info[0])

    draw_chart(sizes, labels, 'Artist appearances in top ' + str(track_limit) + ' tracks')
    plt.savefig('static/chart2.png', transparent=True)

    return render_template('top10.html', top_artists=top_artists, top_albums=top_albums, top_tracks=top_tracks)

@app.route('/avg_data', methods=['POST'])
def avg_data():
    avg_info = {}
    with open('data/avg_data.tsv', 'r') as file:
        for line in file:
            line_split = line.split('\t')
            field = line_split[0]
            value = line_split[1]
            units = line_split[2]
            avg_info[field] = [float(value), units]

    years = []
    with open('data/years_listened.txt', 'r') as file:
        for line in file:
            years.append(int(line))

    responses = {}

    acousticness = avg_info['acousticness'][0]
    if acousticness < 0.5:
        responses['acousticness'] = "You seem to like music with electronic, digital, or amplified elements the best!"
    elif acousticness < 0.8:
        responses['acousticness'] = "Your music seems to be in between electronic/digital and acoustic"
    else:
        responses['acousticness'] = "Seems you have a preference for purely acoustic music!"

    danceability = avg_info['danceability'][0]
    if danceability < 0.4:
        responses['danceability'] = "Your songs seem hard to dance to..."
    elif danceability < 0.65:
        responses['danceability'] = "If you try very hard, you <i>might</i> be able to dance to your songs..."
    elif danceability < 0.8:
        responses['danceability'] = "Your songs are great to dance to!"
    else:
        responses['danceability'] = "Your songs were made to be danced to!"

    energy = avg_info['energy'][0]
    if energy < 0.3:
        responses['energy'] = "You don't seem to be the energetic type"
    elif energy < 0.55:
        responses['energy'] = "There's slight energy in the music you listen to..."
    elif energy < 0.8:
        responses['energy'] = "Your music is fairly energetic!"
    else:
        responses['energy'] = "Your music is very energetic!"

    instrumentalness = avg_info['instrumentalness'][0]
    if instrumentalness < 0.3:
        responses['instrumentalness'] = "Either you're fan of clear rap or big on singing. You love to be able to hear vocals!"
    elif instrumentalness < 0.5:
        responses['instrumentalness'] = "Most of your favorite vocalists don't seem to be speaking clearly enough, are shouting or screaming, or are buried under the instruments"
    elif instrumentalness < 0.7:
        responses['instrumentalness'] = "Either most of your favorite vocalists are incomprehensible or you prefer to listen to instrumental music"
    else:
        responses['instrumentalness'] = "You much prefer instrumental music. Instruments over the voice!"

    loudness = avg_info['loudness'][0]
    if loudness < -25:
        responses['loudness'] = "Your music is very quiet... Perhaps a fan of ambient or calming music?"
    elif loudness < -15:
        responses['loudness'] = "Your music is quiet quiet. You love calming music, but not pure ambience"
    elif loudness < -10:
        responses['loudness'] = "Your music is at a fair volume"
    elif loudness < -7:
        responses['loudness'] = "You like your music fairly loud!"
    elif loudness < -5:
        responses['loudness'] = "You like it loud!! Most likely a rock, metal, or EDM fan!"
    else:
        responses['loudness'] = "You like it really loud!!! Most definitely a fan of metal, hardcore EDM, or other loud genres!"

    tempo = avg_info['tempo'][0]
    if tempo < 60:
        responses['tempo'] = "Most of your top songs are slower than a clock ticking!"
    elif tempo < 109:
        responses['tempo'] = "Your top songs are fairly slow"
    elif tempo < 120:
        responses['tempo'] = "Your top songs are at a moderately upbeat tempo"
    elif tempo < 158:
        responses['tempo'] = "Your top songs are fairly upbeat and fast!"
    elif tempo < 180:
        responses['tempo'] = "You like your songs quite fast and lively!"
    else:
        responses['tempo'] = "You like your songs really fast!"

    valence = avg_info['valence'][0]
    time_range_responses = {
        "short_term": "The past week has been ",
        "medium_term": "The past 6 months have been ",
        "long_term": "The past year has been "
    }
    time_range_response = time_range_responses[time_range]
    if valence < 0.25:
        responses['valence'] = time_range_response + "very unkind to you. Whatever emotions your top songs have, they definitely aren't happiness"
    elif valence < 0.5:
        responses['valence'] = time_range_response + "alright. Your top songs don't seem incredibly happy"
    elif valence < 0.75:
        responses['valence'] = time_range_response + "average, it seems. Your top songs don't seem too sad or dark, but not incredibly happy"
    else:
        responses['valence'] = time_range_response + "pretty good! Your top songs seem to be pretty happy and positive"

    duration_m = avg_info['duration_ms'][0] / 60000
    if duration_m < 1.5:
        responses['duration_m'] = "Most of your favorite tracks aren't even a minute long... You are absolutely a grindcore fan or are listening to sound effects."
    elif duration_m < 4.5:
        responses['duration_m'] = "Nothing much to say here, this is a fairly normal length for a song"
    elif duration_m < 8:
        responses['duration_m'] = "You like long songs, but not too long, I see"
    elif duration_m < 12:
        responses['duration_m'] = "You're in for the long run!"
    else:
        responses['duration_m'] = "Your music must send you in a trance if they go on for this long..."

    popularity = avg_info['popularity'][0]
    if popularity < 10:
        responses['popularity'] = "You are deep underground, no one knows your songs!"
    elif popularity < 25:
        responses['popularity'] = "Most of your music is quite underground"
    elif popularity < 50:
        responses['popularity'] = "Your top songs may be popular in specific spaces, but not quite mainstream"
    elif popularity < 80:
        responses['popularity'] = "Your top songs are popular, but not mainstream!"
    else:
        responses['popularity'] = "Your top songs are known by the masses!"

    eras = {
        (0, 1919): 0,
        (1920, 1949): 0,
        (1950, 1969): 0,
        (1970, 1979): 0,
        (1980, 1989): 0,
        (1990, 1999): 0,
        (2000, 2009): 0,
        (2010, 2015): 0,
        (2016, 2019): 0,
        (2020, 2021): 0,
        (2022, 2026): 0
    }
    eras_responses = {
        (0, 1919): "You are a dinosaur.",
        (1920, 1949): "You are a great grandparent. Did you live through the Great Depression or WW1?",
        (1950, 1969): "You have an old soul",
        (1970, 1979): "You have a 70s soul",
        (1980, 1989): "You have an 80s soul",
        (1990, 1999): "You have a 90s soul",
        (2000, 2009): "You have a 2000s soul",
        (2010, 2015): "You yearn for the early 2000s",
        (2016, 2019): "You yearn for the late 2000s",
        (2020, 2021): "You are quite fond of pandemic music",
        (2022, 2026): "You're in for the new! Your music taste is quite recent"
    }
    for year in years:
        for era in eras:
            if year >= era[0] and year <= era[1]:
                eras[era] += 1
    most_listened_era = max(eras, key=eras.get)
    avg_info['years'] = [f"{most_listened_era[0]} - {most_listened_era[1]}", ""]
    responses['years'] = eras_responses[most_listened_era]

    avg_info['duration_m'] = [ms_to_m(avg_info['duration_ms'][0]), ' ' + avg_info['duration_ms'][1]]

    for info in avg_info:
        value = avg_info[info][0]
        unit = avg_info[info][1]
        
        if unit == '%\n':
            value *= 100

        if isinstance(value, float):
            avg_info[info][0] = float(np.round(value, 2))

    song_scores = {}
    score_adjectives = {
        'acousticness': ("Least acoustic", "Most acoustic"),
        'danceability': ("Least danceable", "Most danceable"),
        'energy': ("Least energetic", "Most energetic"),
        'instrumentalness': ("Most vocals", "Most instrumental"),
        'loudness': ("Quietest song", "Loudest song"),
        'tempo': ("Slowest song", "Fastest song"),
        'valence': ("Least happy", "Brightest"),
        'duration_m': ("Shortest song", "Longest song"),
        'popularity': ("Least popular", "Most popular"),
        'years': ("Oldest song", "Newest song")
    }
    with open('data/song_scores.tsv', 'r') as file:
        for line in file:
            line_split = line.split('\t')
            field = line_split[0]
            if line_split[1][0] != '"':
                low_score_track_info = eval(line_split[1])
            else: # weird bug where tracks w/ apostrophes get formatted in the tsv like "[""track name"", ...]"
                low_score_track_info = eval(line_split[1].strip('"').replace('""', '"'))
            low_score = line_split[2]
            if line_split[3][0] != '"':
                high_score_track_info = eval(line_split[3])
            else:
                high_score_track_info = eval(line_split[3].strip('"').replace('""', '"'))
            high_score = line_split[4]

            unit = avg_info[field][1]

            if unit == '%\n':
                low_score = float(low_score) * 100
                high_score = float(high_score) * 100
            elif field == 'duration_ms':
                low_score = ms_to_m(float(low_score))
                high_score = ms_to_m(float(high_score))
                field = 'duration_m'

            if isinstance(low_score, float):
                low_score = str(float(np.round(low_score, 2)))
                high_score = str(float(np.round(high_score, 2)))
            
            low_score += unit
            high_score += unit

            song_scores[field] = [low_score_track_info, low_score, high_score_track_info, high_score, score_adjectives[field]]
    
    avg_info.pop('duration_ms')

    return render_template('avg_data.html', avg_info=avg_info, responses=responses, song_scores=song_scores)

def ms_to_m(ms):
    duration_m = ms / 60000
    seconds = np.round((duration_m % 1) * 60, 2)
    return str(int(duration_m)) + ':' + str(seconds)

def get_audio_features(id):
    url = "https://api.reccobeats.com/v1/audio-features?ids=" + id
    response = requests.get(url, headers=recco_headers, data=recco_payload)
    if response.status_code != 200:
        raise Exception("Error getting audio features from ReccoBeats:", response.status_code, response.reason, response.content)
    audio_features = json.loads(str(response.content, 'utf-8'))['content']
    if audio_features == []:
        return
    return audio_features[0]

def get_album_popularity(id):
    url = "https://api.reccobeats.com/v1/album?ids=" + id
    response = requests.get(url, headers=recco_headers, data=recco_payload)
    if response.status_code != 200:
        raise Exception("Error getting album from ReccoBeats:", response.status_code, response.reason, response.content)
    popularity = json.loads(str(response.content, 'utf-8'))['content']
    if popularity == []:
        return 0
    return popularity[0]['popularity']

if __name__ == '__main__':
    app.run(threaded=True, debug=True)