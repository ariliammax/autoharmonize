from synfony.models import PauseEvent, PlayEvent, SeekEvent, VolumeEvent
from synfony.models import ChannelState


def playButtonTapped(channel_idx, event_queue, streamer):
    channel_state = ChannelState(
        idx=channel_idx,
        last_timestamp=streamer.get_last_time(channel_idx),
        timestamp=streamer.get_current_time(channel_idx),
        playing=not streamer.is_playing(channel_idx),
        volume=streamer.get_volume(channel_idx),
    )
    if not streamer.is_playing(channel_idx):
        print('Play Pressed')
        event_queue.append(PlayEvent(channel_state=channel_state))
    else:
        print('Pause Pressed')
        event_queue.append(PauseEvent(channel_state=channel_state))
    streamer.sync([channel_state])
    return event_queue


def didSeekTo(channel_idx, event_queue, seek_value, streamer):
    channel_state = ChannelState(
        idx=channel_idx,
        last_timestamp=streamer.get_last_time(channel_idx),
        timestamp=seek_value,
        playing=streamer.is_playing(channel_idx),
        volume=streamer.get_volume(channel_idx),
    )
    print('Did seek to: ' + str(seek_value))
    event_queue.append(SeekEvent(channel_state=channel_state))
    streamer.sync([channel_state])
    return event_queue


def didChangeVolumeTo(channel_idx, event_queue, seek_value, streamer):
    channel_state = ChannelState(
        idx=channel_idx,
        last_timestamp=streamer.get_last_time(channel_idx),
        timestamp=streamer.get_current_time(channel_idx),
        playing=streamer.is_playing(channel_idx),
        volume=seek_value,
    )
    print('Did change volume to: ' + str(seek_value))
    event_queue.append(VolumeEvent(channel_state=channel_state))
    streamer.sync([channel_state])
    return event_queue
