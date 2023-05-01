from synfony.models import PauseEvent, PlayEvent, SeekEvent, VolumeEvent
from synfony.models import ChannelState

def playButtonTapped(channel_idx, timestamp, is_playing, volume, event_queue, is_selected, streamer):
    if not is_selected:
        print('Play Pressed')
        event_queue.append(PlayEvent(
            channel_state = ChannelState(
                idx=channel_idx,
                timestamp=timestamp,
                playing=True,
                volume=volume
            )
        ))
    else:
        print('Pause Pressed')
        event_queue.append(PauseEvent(
            channel_state = ChannelState(
                idx=channel_idx,
                timestamp=timestamp,
                playing=False,
                volume=volume
            )
        ))
    streamer.sync(
        [
            ChannelState(
                idx=channel_idx,
                timestamp=timestamp,
                playing=not is_selected,
                volume=volume
            )
        ]
    )
    return event_queue

def didSeekTo(channel_idx, timestamp, is_playing, volume, event_queue, seek_value, streamer):
    print('Did seek to: ' + str(seek_value))
    event_queue.append(SeekEvent(
        channel_state = ChannelState(
            idx=channel_idx,
            timestamp=seek_value,
            playing=is_playing,
            volume=volume
        )
    ))
    streamer.sync(
        [
            ChannelState(
                idx=channel_idx,
                timestamp=seek_value,
                playing=is_playing,
                volume=volume
            )
        ]
    )
    return event_queue

def didChangeVolumeTo(channel_idx, timestamp, is_playing, volume, event_queue, seek_value, streamer):
    print('Did change volume to: ' + str(seek_value))
    event_queue.append(VolumeEvent(
        channel_state = ChannelState(
            idx=channel_idx,
            timestamp=timestamp,
            playing=is_playing,
            volume=seek_value
        )
    ))
    streamer.sync(
        [
            ChannelState(
                idx=channel_idx,
                timestamp=timestamp,
                playing=is_playing,
                volume=seek_value
            )
        ]
    )
    return event_queue
