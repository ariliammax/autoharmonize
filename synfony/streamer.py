# streamer.py
# in synfony

from abc import ABC, abstractmethod
from synfony.config import Config
from synfony.models import ChannelState
from threading import Timer
from time import time

import pygame


class Streamer(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def event(self, event):
        pass

    @abstractmethod
    def get_chunk(self, channel_id, chunk):
        pass

    @abstractmethod
    def get_current_time(self, channel_id):
        pass

    @abstractmethod
    def get_num_channels(self):
        pass

    @abstractmethod
    def get_title(self, channel_id):
        pass

    @abstractmethod
    def get_total_time(self, channel_id):
        pass

    @abstractmethod
    def get_volume(self, channel_id):
        pass

    @abstractmethod
    def is_playing(self, channel_id):
        pass

    @abstractmethod
    def schedule_seek(self, channel_id, chunk, interval, playing):
        pass

    @abstractmethod
    def seek(self, channel_id, chunk, playing):
        pass

    @abstractmethod
    def sync(self, states):
        pass

    @abstractmethod
    def shutdown(self):
        pass


class LocalMusicStreamer(Streamer):
    current_chunk_index = []
    current_chunk_realtime = []
    current_chunk_timestamp = []
    playing = []
    timer = []
    volume = []

    def __init__(self):
        self.current_chunk_index = [1 for _ in range(len(Config.CHANNELS))]
        self.current_chunk_realtime = [time() for _ in range(len(Config.CHANNELS))]
        self.current_chunk_timestamp = [0.0 for _ in range(len(Config.CHANNELS))]
        self.playing = [True for _ in range(len(Config.CHANNELS))]
        self.timer = [None for _ in range(len(Config.CHANNELS))]
        self.volume = [50 for _ in range(len(Config.CHANNELS))]

    def init(self):
        pygame.mixer.init()
        for channel_id in range(len(Config.CHANNELS)):
            channel = pygame.mixer.Channel(channel_id)
            channel.set_endevent(pygame.USEREVENT + channel_id)
            chunk = 1
            sound = self.get_chunk(channel_id, chunk)
            if sound is None:
                interval = Config.CHANNELS[channel_id][2]
                self.schedule_seek(channel_id, chunk, interval, True)
            else:
                channel.play(sound)
                self.current_chunk_realtime[channel_id] = time()

    def event(self, event):
        channel_id = event.type - pygame.USEREVENT
        if channel_id < 0 or channel_id >= len(Config.CHANNELS):
            return
        chunk = self.current_chunk_index[channel_id] + 1
        if chunk > Config.CHANNELS[channel_id][1]:
            chunk = 1
        sound = self.get_chunk(channel_id, chunk)
        if sound is None:
            interval = Config.CHANNELS[channel_id][2]
            self.schedule_seek(channel_id, chunk, interval, True)
        else:
            channel = pygame.mixer.Channel(channel_id)
            channel.queue(sound)
            self.current_chunk_index[channel_id] = chunk
            self.current_chunk_realtime[channel_id] = time()
            self.current_chunk_timestamp[channel_id] = 0.0

    def get_chunk(self, channel_id, chunk):
        file = Config.CHANNELS[channel_id][0]
        chunk_str = str(chunk) if chunk > 9 else "0" + str(chunk)
        return pygame.mixer.Sound(file + "-" + chunk_str + ".mp3")

    def get_current_time(self, channel_id):
        inter_chunk_offset = (self.current_chunk_index[channel_id] - 1) * Config.CHANNELS[channel_id][2]
        intra_chunk_offset = self.current_chunk_timestamp[channel_id]
        realtime_offset = time() - self.current_chunk_realtime[channel_id]
        if not self.playing[channel_id]:
            realtime_offset = 0.0
        return inter_chunk_offset + intra_chunk_offset + realtime_offset

    def get_num_channels(self):
        return len(Config.CHANNELS)

    def get_title(self, channel_id):
        return Config.CHANNELS[channel_id][0]

    def get_total_time(self, channel_id):
        return Config.CHANNELS[channel_id][1] * Config.CHANNELS[channel_id][2]

    def get_volume(self, channel_id):
        return self.volume[channel_id]

    def is_playing(self, channel_id):
        return self.playing[channel_id]

    def schedule_seek(self, channel_id, chunk, interval, playing):
        chunk += 1
        if chunk > Config.CHANNELS[channel_id][1]:
            chunk = 1
        self.current_chunk_index[channel_id] = chunk
        self.current_chunk_timestamp[channel_id] = 0.0
        self.playing[channel_id] = False
        self.timer[channel_id] = Timer(interval, self.seek, [
            channel_id,
            chunk,
            playing,
        ])
        self.timer[channel_id].start()

    def seek(self, channel_id, chunk, playing):
        self.current_chunk_index[channel_id] = chunk
        self.current_chunk_timestamp[channel_id] = 0.0
        self.playing[channel_id] = playing
        self.timer[channel_id] = None
        sound = self.get_chunk(channel_id, chunk)
        if sound is None:
            interval = Config.CHANNELS[channel_id][2]
            self.schedule_seek(channel_id, chunk, interval, playing)
        else:
            channel = pygame.mixer.Channel(channel_id)
            channel.set_endevent(pygame.USEREVENT + len(Config.CHANNELS))
            channel.play(sound)
            if playing:
                self.current_chunk_realtime[channel_id] = time()
            else:
                channel.pause()
            channel.set_endevent(pygame.USEREVENT + channel_id)

    def sync(self, states: list[ChannelState]):
        for channel_state in states:
            channel_id = channel_state.get_idx()
            playing = channel_state.get_playing()
            timestamp = channel_state.get_timestamp()
            volume = channel_state.get_volume()
            chunk = 1
            delay = abs(timestamp - self.get_current_time(channel_id))
            while timestamp > Config.CHANNELS[channel_id][2]:
                timestamp -= Config.CHANNELS[channel_id][2]
                chunk += 1
            channel = pygame.mixer.Channel(channel_id)
            if delay > Config.TOLERABLE_DELAY or self.timer[channel_id] is not None:
                if self.timer[channel_id]:
                    self.timer[channel_id].cancel()
                channel.set_endevent(pygame.USEREVENT + len(Config.CHANNELS))
                channel.stop()
                channel.set_endevent(pygame.USEREVENT + channel_id)
                interval = Config.CHANNELS[channel_id][2] - timestamp
                self.schedule_seek(channel_id, chunk, interval, playing)
            elif self.playing[channel_id] and not playing:
                channel.pause()
                self.current_chunk_timestamp[channel_id] = time() - self.current_chunk_realtime[channel_id]
                self.playing[channel_id] = False
            elif not self.playing[channel_id] and playing:
                channel.unpause()
                self.current_chunk_realtime[channel_id] = time()
                self.playing[channel_id] = True
            self.volume[channel_id] = volume
            channel.set_volume(volume)

    def shutdown(self):
        pygame.mixer.stop()
        pygame.mixer.quit()


class RemoteMusicStreamer(Streamer):
    pass


class LocalMIDIStreamer(Streamer):
    pass


class RemoteMIDIStreamer(Streamer):
    pass
