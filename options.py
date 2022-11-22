Music_Join = "```yaml\n .join ```\nMakes Helios join the caller's voice channel\n\nAlternatives: `.j`\n\n"
Music_Leave = "```yaml\n .leave ```\nMakes Helios leave the caller's voice channel\n\nAlternatives: `.l `\n\n"
Music_Play = "```yaml\n .play {song} ```\nPlays or queues requested song or playlist\n\n__Song Options__\n- Request a song by typing the name of it\n- Provide a Youtube or Spotify url (song or playlist)\n\nAlternatives: `.p`\n\n"
Music_Pause = "```yaml\n .pause ```\nPauses the currently playing song\n\nAlternatives: `.pa, .stop`\n\n"
Music_Resume = "```yaml\n .resume ```\nResumes the currently playing song\n\nAlternatives: `.re, .start`\n\n"
Music_Skip = "```yaml\n .skip {position in queue} ```\nSkips a song in the queue\n\n__Skip Options__\n- Provide a position for the queue to skip to\n- No position provided skips the currently playing song\n\nAlternatives: `.sk, .next`\n\n"
Music_Queue = "```yaml\n .queue {page number} ```\nDisplays the songs in the queue\n\n__Queue Options__\n- Provide a page number of the queue to display\n- No page provided displays the first page of the queue\n\nAlternatives: `.q, .playlist`\n\n"
Music_Loop = "```yaml\n .loop {loop mode} ```\nLoops or unloops a song or queue\n\n__Loop Options__\n(1, current, song) - Loops the current song\n(2, all, track) - Loops the entire queue\n(0, un, u) - Unloops the song or queue\n\nAlternatives: `.lop`\n\n"
Music_Shuffle = "```yaml\n .shuffle ```\nShuffles the songs in queue\n\nAlternatives: `.sh`\n\n"
Music_Remove = "```yaml\n .remove {position in queue} ```\nRemoves a song or all songs from a queue\n\n__Remove Options__\n- Provide a position of a song for it to be removed from the queue\n(all, a)- Removes all songs from queue\n\nAlternatives: `.rm, .delete`\n\n"
Music_Current = "```yaml\n .current_song ```\nDisplays information about the current song\n\nAlternatives: `.info, .cur`\n\n"
Music_Restart = "```yaml\n .restart {option} ```\nRestarts song or track\n\n__Restart Options__\n(all, a, track) - Restarts the track\n- Nothing provided restarts the song\n\nAlternatives: `.rep`\n\n"
Music_Lyrics = "```yaml\n .lyrics {title of song} ```\nFinds lyrics to a song\n\n__Lyrics Options__\n- Provide a song for for its lyrics\n- Nothing provided finds the lyrics of the song currently playing\n\nAlternatives: `.lyr, .lyric`\n\n"

Music_CMDS = Music_Join + Music_Leave + Music_Play + Music_Pause + Music_Resume + Music_Skip + Music_Queue + Music_Loop + Music_Shuffle + Music_Remove + Music_Current + Music_Restart + Music_Lyrics

SPOTIFY_ID = "683213a13d6a4b31bc92c32deef36b41"
SPOTIFY_SECRET = "fa14740a1e4846439685aeb8f3a048b0"
SPOTIFY_REDIRECT_URI = "https://localhost:88888/callback"

DISCORD_TOKEN = "OTY0Mzg1MDQ4MTEzNTg2MjU2.G_rvtz.zKrIEIGBhV0KG1jdB6bSAk6pnuQIAOzMbXKY2w"