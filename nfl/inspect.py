import argparse
import json
from pathlib import Path
import pyarrow.parquet as parquet

FIELDS = ('game_id','play_id','season_type','posteam','defteam','qtr','time',
          'game_seconds_remaining','time_of_day','drive','fixed_drive',
          'play_type','desc','home_team','away_team')


def inspect(path):
    schema = parquet.read_schema(path)
    fields = [field for field in FIELDS if field in schema.names]
    table = parquet.read_table(path,columns=fields)
    rows = table.to_pylist()
    game_ids = {row['game_id'] for row in rows}
    report = dict(rows=len(rows),games=len(game_ids),columns=len(schema.names),
        available_fields=fields,missing_fields=sorted(set(FIELDS)-set(fields)),
        null_counts={field:table[field].null_count for field in fields},
        season_types=sorted({row['season_type'] for row in rows}),
        note='Historical play-by-play only; no tradable odds or live feed arrival timestamps')
    path.with_suffix('.inspection.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check NFL play-by-play coverage')
    parser.add_argument('path',type=Path)
    inspect(parser.parse_args().path)
