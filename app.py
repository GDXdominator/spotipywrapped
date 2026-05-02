from flask import Flask, request, render_template

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import matplotlib.pyplot as plt
import numpy as np

import requests, json

recco_base = "https://api.reccobeats.com/v1/"
recco_payload = {}
recco_headers = {
    'Accept': 'application/json'
}

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/top10', methods=['GET', 'POST'])
def top10():
    CLIENT_ID = request.args.get('client_id')
    CLIENT_SECRET = request.args.get('client_secret')
    REDIRECT_URI = request.args.get('redirect_uri')
    time_range = request.args.get('time_range')
    track_limit = request.args.get('track_limit')

    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope='user-top-read'
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    top_artists = sp.current_user_top_artists(limit=track_limit, time_range=time_range)['items']
    top_10_artists_list = []
    top_10_artists_imgs = []
    for artist in top_artists:
        top_10_artists_list.append(artist['name'])
        top_10_artists_imgs.append(artist['images'][0]['url'])

    top_tracks = sp.current_user_top_tracks(limit=track_limit, time_range=time_range)['items']
    top_track_names = []
    top_track_covers = []

    saved_tracks = sp.current_user_saved_tracks(limit=track_limit)['items']
    all_tracks = []
    artist_appearances = {}
    top_track_artist_appearances = {}
    for track_item in saved_tracks:
        all_tracks.append(track_item['track'])
    for track in top_tracks:
        all_tracks.append(track)
        artist = track['artists'][0]['name']
        if artist in top_track_artist_appearances:
            top_track_artist_appearances[artist] += 1
        else:
            top_track_artist_appearances[artist] = 1
    for track in all_tracks:
        artist = track['artists'][0]['name']
        if artist in artist_appearances:
            artist_appearances[artist] += 1
        else:
            artist_appearances[artist] = 1

    labels = []
    sizes = []
    def percent_to_int(percent):
        return int(np.round(percent / 100 * sum(sizes), 0))
    
    figsize = (9, 6)
    radius = 1.25
    legend_xOffset = -0.5
    title_yOffset = 1.1

    # Chart 1

    for artist in artist_appearances:
        sizes.append(artist_appearances[artist])
        labels.append(artist)
    greatest_slice = max(sizes)
    max_i = sizes.index(greatest_slice)
    explode_val = tuple([0 if i != max_i else 0.2 for i in range(len(sizes))])

    _, ax = plt.subplots(figsize=figsize)
    wedges, _, autotexts = ax.pie(sizes, autopct=percent_to_int, explode=explode_val, radius=radius)
    for txt in autotexts:
        txt.set_color('white')

    leg = ax.legend(wedges, labels, title='Artists (Counterclockwise)', loc='center left', fontsize=8)
    bb = leg.get_bbox_to_anchor().transformed(ax.transAxes.inverted())
    bb.x0 += legend_xOffset
    bb.x1 += legend_xOffset
    leg.set_bbox_to_anchor(bb, transform=ax.transAxes)

    title = ax.set_title(f"Artist appearances in top + past liked {int(track_limit) * 2} tracks", y=title_yOffset)
    title.set_color('white')
    plt.savefig('static/chart1.png', transparent=True)

    # Chart 2

    labels = []
    sizes = []
    for artist in top_track_artist_appearances:
        sizes.append(top_track_artist_appearances[artist])
        labels.append(artist)
    greatest_slice = max(sizes)
    max_i = sizes.index(greatest_slice)
    explode_val = tuple([0 if i != max_i else 0.2 for i in range(len(sizes))])

    _, ax = plt.subplots(figsize=figsize)
    wedges, _, autotexts = ax.pie(sizes, autopct=percent_to_int, explode=explode_val, radius=radius, textprops={'fontsize': 8})
    for txt in autotexts:
        txt.set_color('white')
    
    leg = ax.legend(wedges, labels, title='Artists (Counterclockwise)', loc='center left', fontsize=8)
    bb = leg.get_bbox_to_anchor().transformed(ax.transAxes.inverted())
    bb.x0 += legend_xOffset
    bb.x1 += legend_xOffset
    leg.set_bbox_to_anchor(bb, transform=ax.transAxes)

    title = ax.set_title('Artist appearances in top ' + str(track_limit) + ' tracks', y=title_yOffset)
    title.set_color('white')
    plt.savefig('static/chart2.png', transparent=True)

    for track in top_tracks:
        top_track_names.append(track['artists'][0]['name'] + ' - ' + track['name'])
        top_track_covers.append(track['album']['images'][0]['url'])

    return render_template('top10.html', top_10_artists_list=top_10_artists_list, top_10_artists_imgs=top_10_artists_imgs, top_track_names=top_track_names, top_track_covers=top_track_covers)

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
    app.run(debug=True)