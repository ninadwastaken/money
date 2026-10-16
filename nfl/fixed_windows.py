from nfl.possessions import timestamp


TIMINGS = ((10, 60), (10, 30), (30, 90))


def fixed_windows(plays):
    result = []
    previous_offense = None
    for play in plays:
        offense = play['posteam']
        if not offense or not play['time_of_day']:
            continue
        if offense == previous_offense:
            continue
        previous_offense = offense
        start = timestamp(play['drive_real_start_time'] or play['time_of_day'])
        for entry_delay, exit_delay in TIMINGS:
            result.append(dict(
                game=play['game_id'], team=play['defteam'],
                defense_start_proxy=start,
                entry_delay=entry_delay, exit_delay=exit_delay,
                entry_time=start + entry_delay, exit_time=start + exit_delay,
                start_source='drive start or first offensive play; unverified possession time',
            ))
    return result
