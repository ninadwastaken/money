from collections import defaultdict
from datetime import datetime
import pyarrow.parquet as parquet


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp() if value else None


def games(path, since):
    columns = ['game_id','game_date','play_id','posteam','defteam','fixed_drive',
               'drive_real_start_time','time_of_day','end_clock_time','home_team','away_team']
    grouped = defaultdict(list)
    for play in parquet.read_table(path,columns=columns).to_pylist():
        if play['game_date'] >= since:
            grouped[play['game_id']].append(play)
    return {game:sorted(plays,key=lambda p:p['play_id']) for game,plays in grouped.items()}


def windows(plays, delay=60):
    possessions = []
    for play in plays:
        if not play['posteam'] or not play['time_of_day']:
            continue
        if not possessions or possessions[-1]['offense'] != play['posteam']:
            possessions.append(dict(offense=play['posteam'],defense=play['defteam'],
                start=timestamp(play['drive_real_start_time'] or play['time_of_day']),last=play))
        else:
            possessions[-1]['last'] = play
    result = []
    game_end = max(timestamp(p['end_clock_time'] or p['time_of_day']) or 0 for p in plays)
    for index,possession in enumerate(possessions):
        following = possessions[index+1] if index+1<len(possessions) else None
        last_play = possession['last']
        exit_time = timestamp(last_play['end_clock_time'])
        approximate_exit = exit_time is None
        exit_time = exit_time or (following['start'] if following else game_end)
        entry_time = possession['start']+delay
        if entry_time >= exit_time:
            continue
        result.append(dict(game=plays[0]['game_id'],team=possession['defense'],
            defense_start=possession['start'],entry_time=entry_time,exit_time=exit_time,
            settlement=following is None,approximate_exit=approximate_exit))
    return result
