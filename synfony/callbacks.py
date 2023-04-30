from synfony.models import PauseEvent, PlayEvent, SeekEvent
from synfony.models import ChannelState


def playButtonTapped(channel_idx, timestamp, is_playing, eventQueue):
    if is_playing:
        print('Play Pressed')
        eventQueue.append(PlayEvent(
            channel_state = ChannelState(
                idx=channel_idx,
                timestamp=timestamp,
                playing=is_playing
            )
        ))
    else:
        print('Pause Pressed')
        eventQueue.append(PauseEvent(
            channel_state = ChannelState(
                idx=channel_idx,
                timestamp=timestamp,
                playing=is_playing
            )
        ))
    return eventQueue

def didSeekTo(channel_idx, seek_timestamp, is_playing, eventQueue):
    print('Did seek to: ' + str(seek_timestamp))
    eventQueue.append(SeekEvent(
        channel_state = ChannelState(
            idx=channel_idx,
            timestamp=seek_timestamp,
            playing=is_playing
        )
    ))
    return eventQueue
