from nfl.possessions import timestamp


def entry_allowed(plays, entry_time, cutoff):
    known = [(timestamp(play['time_of_day']), play) for play in plays
             if play['time_of_day'] and timestamp(play['time_of_day']) <= entry_time]
    if not known:
        return False
    observed_at, play = max(known, key=lambda row: row[0])
    remaining = play.get('game_seconds_remaining')
    quarter = play.get('qtr')
    if remaining is None or quarter is None or quarter > 4:
        return False
    return remaining - (entry_time - observed_at) > cutoff
