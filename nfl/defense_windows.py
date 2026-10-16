from nfl.possessions import timestamp


def defense_windows(plays, delay=30):
    possessions = []
    for play in plays:
        if not play['posteam'] or not play['time_of_day']:
            continue
        if not possessions or possessions[-1]['offense'] != play['posteam']:
            possessions.append(dict(offense=play['posteam'], defense=play['defteam'],
                start=timestamp(play['drive_real_start_time'] or play['time_of_day'])))
    end = max(timestamp(play['end_clock_time'] or play['time_of_day']) or 0 for play in plays)
    result = []
    for index, possession in enumerate(possessions):
        following = possessions[index + 1] if index + 1 < len(possessions) else None
        result.append(dict(game=plays[0]['game_id'], team=possession['defense'],
            defense_start_proxy=possession['start'], entry_time=possession['start'] + delay,
            exit_time=following['start'] if following else end,
            settlement=following is None,
            timing_source='First offensive play/drive start approximates possession acquisition'))
    return result
