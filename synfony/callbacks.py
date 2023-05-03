from synfony.config import Config
from synfony.models import PauseEvent, PlayEvent, SeekEvent, VolumeEvent
from synfony.models import ChannelState


def playButtonTapped(channel_idx, event_queue, streamer):
    channel_state = ChannelState(
        idx=channel_idx,
        last_timestamp=streamer.get_last_time(),
        timestamp=streamer.get_current_time(),
        playing=not streamer.is_playing(),
        volume=streamer.get_volume(),
    )
    if not streamer.is_playing():
        event_queue.append(PlayEvent(channel_state=channel_state))
    else:
        event_queue.append(PauseEvent(channel_state=channel_state))
    if not Config.HANDSHAKE_ENABLED:
        streamer.sync(channel_state)


def didSeekTo(channel_idx, event_queue, seek_value, streamer):
    channel_state = ChannelState(
        idx=channel_idx,
        last_timestamp=streamer.get_last_time(),
        timestamp=seek_value,
        playing=streamer.is_playing(),
        volume=streamer.get_volume(),
    )
    event_queue.append(SeekEvent(channel_state=channel_state))
    if not Config.HANDSHAKE_ENABLED:
        streamer.sync(channel_state)


def didChangeVolumeTo(channel_idx, event_queue, seek_value, streamer):
    channel_state = ChannelState(
        idx=channel_idx,
        last_timestamp=streamer.get_last_time(),
        timestamp=streamer.get_current_time(),
        playing=streamer.is_playing(),
        volume=seek_value,
    )
    event_queue.append(VolumeEvent(channel_state=channel_state))
    if not Config.HANDSHAKE_ENABLED:
        streamer.sync(channel_state)
