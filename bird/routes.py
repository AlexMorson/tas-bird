import time

from flask import render_template, abort

from bird import app
from bird.db import get_db_cursor
from bird.levels import LEVELS
from bird.queries import RECENT_TOP_10, LEVEL_TOP_50


@app.route("/")
def recent_top_10():
    c = get_db_cursor()
    c.execute(RECENT_TOP_10)
    replays = []
    now = time.time()
    for rank, player, level, frame_count, timestamp in c.fetchall():
        replays.append({
            "rank": rank,
            "player": player,
            "level": level,
            "time": format_frame_count(frame_count),
            "date": format_timestamp(timestamp, now)
        })
    return render_template("recent_top_10.html", replays=replays)


@app.route("/level/<int:level_id>")
def level_leaderboard(level_id):
    if level_id not in LEVELS:
        return abort(404)
    level_name = LEVELS[level_id].split(" - ")[0]

    # Even numbers are the best-time leaderboards
    best_time_id = 2 * (level_id // 2)
    all_birds_id = best_time_id + 1

    best_time_replays = fetch_level_top_50(best_time_id)
    all_birds_replays = fetch_level_top_50(all_birds_id)

    replays = {
        "best_time": best_time_replays,
        "all_birds": all_birds_replays,
    }

    return render_template("level_leaderboard.html", level=level_name, replays=replays)


def fetch_level_top_50(level_id):
    c = get_db_cursor()
    c.execute(LEVEL_TOP_50, (level_id,))
    replays = []
    now = time.time()
    for rank, player, frame_count, timestamp in c.fetchall():
        replays.append({
            "rank": rank,
            "player": player,
            "time": format_frame_count(frame_count),
            "date": format_timestamp(timestamp, now)
        })
    return replays


def format_frame_count(frame_count):
    seconds, frames = divmod(frame_count, 48)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    milliseconds = round(1000 * frames / 48)
    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}.{milliseconds:03}"
    elif minutes > 0:
        return f"{minutes}:{seconds:02}.{milliseconds:03}"
    else:
        return f"{seconds}.{milliseconds:03}"


def format_timestamp(timestamp, now):
    def plural(n, s):
        if n == 1:
            return f"{n} {s} ago"
        return f"{n} {s}s ago"

    assert timestamp < now
    delta = int(now - timestamp)
    if delta < 60:
        return "Just now"
    elif delta < 60 * 60:
        return plural(delta // 60, "minute")
    elif delta < 60 * 60 * 24:
        return plural(delta // 60 // 60, "hour")
    elif delta < 60 * 60 * 24 * 7:
        return plural(delta // 60 // 60 // 24, "day")
    elif delta < 60 * 60 * 24 * 30:
        return plural(delta // 60 // 60 // 24 // 7, "week")
    elif delta < 60 * 60 * 24 * 365:
        return plural(delta // 60 // 60 // 24 // 30, "month")
    else:
        return plural(delta // 60 // 60 // 24 // 365, "year")
