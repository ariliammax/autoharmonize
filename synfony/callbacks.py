from synfony.models import PauseEvent, PlayEvent, SeekEvent
from synfony.models import ChannelState


# TODO: add volume to all of these channel states... and a volume callback


def playButtonTapped(channel_idx, timestamp, is_playing, event_queue, streamer):
    if is_playing:
        print('Play Pressed')
        event_queue.append(PlayEvent(
            channel_state = ChannelState(
                idx=channel_idx,
                timestamp=timestamp,
                playing=is_playing
            )
        ))
    else:
        print('Pause Pressed')
        event_queue.append(PauseEvent(
            channel_state = ChannelState(
                idx=channel_idx,
                timestamp=timestamp,
                playing=is_playing
            )
        ))
    streamer.sync(
        [
            ChannelState(
                idx=channel_idx,
                timestamp=timestamp,
                playing=is_playing
            )
        ]
    )
    return event_queue


def didSeekTo(channel_idx, seek_value, is_playing, event_queue, streamer):
    print('Did seek to: ' + str(seek_value))
    event_queue.append(SeekEvent(
        channel_state = ChannelState(
            idx=channel_idx,
            timestamp=seek_value,
            playing=is_playing
        )
    ))
    streamer.sync(
        [
            ChannelState(
                idx=channel_idx,
                timestamp=seek_value,
                playing=is_playing
            )
        ]
    )
    return event_queue


def didChangeVolumeTo(channel_idx, seek_value, is_playing, event_queue, streamer):
    print('Did change volume to: ' + str(seek_value))
