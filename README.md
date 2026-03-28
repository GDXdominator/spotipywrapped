Title: Spotify Profile Data Visualizer
Author: Vince Abcede
Description: Similar to Spotify Wrapped, this app will analyze and visualize your top Spotify artists, albums, and songs, and deduce the kind of music you listen to based on your top genres and aspects like your top tracks' average tempo, danceability, and etc. You can choose to analyze the past year, 6 months, or 4 weeks. 
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
    * Data that is also provided includes a track's danceability, energy, acousticness, tempo, etc.
        * Can be interpreted and analyzed to describe the kind of music the user listens to
            * ex. data averaging high tempos and energy, text displays and chooses from tuple including things like "ambient listener", "energetic listener"
            * ex. an average of low acousticness across user's top tracks means user prefers electronic music
        * although spotify deprecated this a year ago, so something like reccobeats api needs to be used to get that