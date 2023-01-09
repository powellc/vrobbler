def convert_to_seconds(run_time: str) -> int:
    """Jellyfin sends run time as 00:00:00 string. We want the run time to
    actually be in seconds so we'll convert it"""
    if ":" in run_time:
        run_time_list = run_time.split(":")
        run_time = (int(run_time_list[1]) * 60) + int(run_time_list[2])
    return int(run_time)
