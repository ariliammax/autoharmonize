# streamer.py
# in synfony

from abc import ABC, abstractmethod
from datetime import datetime
from synfony.config import Config
from synfony.models import ChannelState

import pygame


class Streamer(ABC):
    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def event(self, event):
        pass

    @abstractmethod
    def get_current_time(self, channel_id):
        pass

    @abstractmethod
    def get_title(self, channel_id):
        pass

    @abstractmethod
    def get_total_time(self, channel_id):
        pass

    @abstractmethod
    def is_playing(self, channel_id):
        pass

    @abstractmethod
    def sync(self, state):
        pass

    @abstractmethod
    def shutdown(self):
        pass


class LocalMusicStreamer(Streamer):
    current_chunk_index = []
    current_chunk_realtime = []
    current_chunk_timestamp = []
    playing = []

    def init(self):
        pygame.mixer.init()
        for channel_id, (file, _, _) in enumerate(Config.CHANNELS):
            sound = pygame.mixer.Sound(file + "-01.mp3")
            channel = pygame.mixer.Channel(channel_id)
            channel.set_endevent(pygame.USEREVENT + channel_id)
            channel.play(sound)
            self.current_chunk_index.append(1)
            self.current_chunk_realtime.append(datetime.now())
            self.current_chunk_timestamp.append(0.0)
            self.playing.append(True)

    def event(self, event):
        channel_id = event.type - pygame.USEREVENT
        if channel_id < 0 or channel_id >= len(Config.CHANNELS):
            return
        file = Config.CHANNELS[channel_id][0]
        chunk = self.current_chunk_index[channel_id] + 1
        if chunk > Config.CHANNELS[channel_id][1]:
            chunk = 1
        self.current_chunk_index[channel_id] = chunk
        chunk = str(chunk) if chunk > 9 else "0" + str(chunk)
        sound = pygame.mixer.Sound(file + "-" + chunk + ".mp3")
        channel = pygame.mixer.Channel(channel_id)
        channel.queue(sound)
        self.current_chunk_realtime[channel_id] = datetime.now()
        self.current_chunk_timestamp[channel_id] = 0.0
        self.playing.append(True)

    def get_current_time(self, channel_id):
        inter_chunk_offset = (self.current_chunk_index[channel_id] - 1) * Config.CHANNELS[channel_id][2]
        intra_chunk_offset = self.current_chunk_timestamp[channel_id]
        realtime_offset = datetime.now() - self.current_chunk_realtime[channel_id]
        return inter_chunk_offset + intra_chunk_offset + realtime_offset.total_seconds()

    def get_title(self, channel_id):
        return Config.CHANNELS[channel_id][0]

    def get_total_time(self, channel_id):
        return Config.CHANNELS[channel_id][1] * Config.CHANNELS[channel_id][2]

    def is_playing(self, channel_id):
        return self.playing[channel_id]

    def sync(self, state: list[ChannelState]):
        pass

    def shutdown(self):
        pygame.mixer.stop()
        pygame.mixer.quit()


class RemoteMusicStreamer(Streamer):
    pass


class LocalMIDIStreamer(Streamer):
    pass


class RemoteMIDIStreamer(Streamer):
    pass
