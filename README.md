Title: Spotify Profile Data Visualizer and Music Taste Interpreter
Author: Vince Abcede
Description: Similar to Spotify Wrapped, this app will analyze and visualize your top Spotify artists, albums, and songs as lists or charts. After analyzing this and the songs in your playlists and likes, the app will deduce the kind of music you listen to based on your top genres and aspects like your top tracks' average tempo, danceability, and etc according to Spotify's algorithm. Your music taste will also be compared to Spotify's global top artists to see how you compare to the average Spotify listener. You can choose to analyze the past year, 6 months, or 4 weeks, so either something like a Spotify Wrapped or quick recap of the past month.

Outline:
* Spotify's API provides a user's top items as an object
    * A time range can be passed (1 years, 6 months, 4 weeks), so user input can include the time range they want to view
    * Alongside this, we can gather the user's playlists (non-collaborative ones) and likes and check who shows up the most in them
* Spotipy API has methods that returns Spotiy objects, will be used to simplify data grabbing process
* Data can be divided into different sections/screens or windows: Top albums, artists, tracks
    * Each item, ex. an album, will have the same format
        * therefore a spreadsheet would be best for saving the data for each item type (ex. spreadsheet for albums includes columns for times played)
    * Each screen should display the corresponding images, ex. artist images, cover art
* Some data and trends that can be analyzed with the user's top items include average genres listened to (using both top artists and tracks), artists who frequently show up in playlists
    * Data such as most listened artists (by minutes) can be visualized with a bar graph (which matplotlib seems good for)
    * Popularity is also an attribute of artists, so whether or not a user listens to mainstream or underground artists can be analyzed
        * Can also web scrape a "Spotify top global artists" and compare it to user's top artists
    * Data that is also provided includes a track's danceability, energy, acousticness, tempo, etc.
        * Can be interpreted and analyzed to describe the kind of music the user listens to
            * ex. data averaging high tempos and energy, text displays and chooses from tuple including things like "ambient listener", "energetic listener"
            * ex. an average of low acousticness across user's top tracks means user prefers electronic music
        * although spotify deprecated this a year ago, so something like reccobeats api needs to be used to get that

Potential interface layout
* Enter username (as Entry), enter range of data (as Radiobutton: 1y, 6m, 4w)
(next menus in sequential order w/ back + forward Buttons)
* Top 10 artists (display as list, stored as spreadsheet)
    * Top artists in likes & playlists (pie chart w/ matplotlib?)
* Top 10 albums (list, stored as spreadsheet)
* Top 10 songs (list, stored as spreadsheet)
* Top 5 genres (list, stored as list of strings)
    * Top genres in likes, playlists & top artists (pie chart)
* "Your taste in music, according to Spotify" (based on numerous number values stored in a list of numbers)
    * (sentence describing how fast the user likes their music): (avg tempo of top tracks)
    * (sentence describing how long the user likes their music): (avg duration of top tracks)
    * (sentence describing how loud user likes their music): (avg)
    * "You seem to be more of a (acoustic / electronic) person" (based on avg acousticness of top tracks)
    * (something describing user's choice era of music)
        * based on avg year of release of top tracks.
            * Eras should be defined (ex. {(1920, 1960): "old soul", (2020, 2026): "young lad"})
* Your taste vs. the world's taste
    * user's top artists : spotify's global top artists, def needs web scraping
    * (something describing how mainstream or underground user's top artists are)
        * based on monthly listeners of top artists, spotify's "popularity" value of top tracks
        * be sure to define what is "underground" (ex. >10M monthly listeners: "mainstream listener," <50: "day 1 fan")
* "The past (year / 6 months / 4 weeks) appear(s) to have been (happy / calm / unkind)"
    * describes general vibe of the user's top songs
    * based on avg valence value, or "positiveness" of top tracks
* "thats a wrap"
