from nfl.fixed_windows import fixed_windows


def test_fixed_exits_survive_early_possession_changes():
    plays = [
        dict(game_id='game', posteam='A', defteam='B',
             time_of_day='2026-10-11T17:00:00Z', drive_real_start_time=None),
        dict(game_id='game', posteam='B', defteam='A',
             time_of_day='2026-10-11T17:00:05Z', drive_real_start_time=None),
    ]
    windows = fixed_windows(plays)
    assert len(windows) == 6
    assert [(row['entry_time'] - row['defense_start_proxy'],
             row['exit_time'] - row['defense_start_proxy'])
            for row in windows[:3]] == [(10, 60), (10, 30), (30, 90)]
    assert windows[0]['exit_time'] > windows[3]['defense_start_proxy']


def test_repeated_offensive_plays_do_not_trigger_new_entries():
    play = dict(game_id='game', posteam='A', defteam='B',
                time_of_day='2026-10-11T17:00:00Z', drive_real_start_time=None)
    assert len(fixed_windows([play, dict(play)])) == 3
