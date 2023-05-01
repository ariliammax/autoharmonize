# streamer.py
# in synfony

from abc import ABC, abstractmethod
from synfony.config import Config
from synfony.models import ChannelState
from time import time

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
    volume = []

    def init(self):
        pygame.mixer.init()
        for channel_id, (file, _, _) in enumerate(Config.CHANNELS):
            sound = pygame.mixer.Sound(file + "-01.mp3")
            channel = pygame.mixer.Channel(channel_id)
            channel.set_endevent(pygame.USEREVENT + channel_id)
            channel.play(sound)
            self.current_chunk_index.append(1)
            self.current_chunk_realtime.append(time())
            self.current_chunk_timestamp.append(0.0)
            self.playing.append(True)
            self.volume.append(50)

    def event(self, event):
        channel_id = event.type - pygame.USEREVENT
        if channel_id < 0 or channel_id >= len(Config.CHANNELS):
            return
        file = Config.CHANNELS[channel_id][0]
        chunk = self.current_chunk_index[channel_id] + 1
        if chunk > Config.CHANNELS[channel_id][1]:
            chunk = 1
        chunk_str = str(chunk) if chunk > 9 else "0" + str(chunk)
        sound = pygame.mixer.Sound(file + "-" + chunk_str + ".mp3")
        channel = pygame.mixer.Channel(channel_id)
        channel.queue(sound)
        self.current_chunk_index[channel_id] = chunk
        self.current_chunk_realtime[channel_id] = time()
        self.current_chunk_timestamp[channel_id] = 0.0

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

    def sync(self, states: list[ChannelState]):
        for channel_state in states:
            channel_id = channel_state.get_idx()
            play = channel_state.get_playing()
            timestamp = channel_state.get_timestamp()
            chunk = 1
            while timestamp > Config.CHANNELS[channel_id][2]:
                timestamp -= Config.CHANNELS[channel_id][2]
                chunk += 1
            channel = pygame.mixer.Channel(channel_id)
            if self.playing[channel_id] and not play:
                self.current_chunk_index[channel_id] = chunk
                self.current_chunk_timestamp[channel_id] = timestamp
                channel.pause()
            elif not self.playing[channel_id] and play:
                self.current_chunk_index[channel_id] = chunk
                self.current_chunk_timestamp[channel_id] = timestamp
                channel.unpause()
                self.current_chunk_realtime[channel_id] = time()
            elif abs(timestamp - self.get_current_time(channel_id)) > Config.TOLERABLE_DELAY:
                self.current_chunk_index[channel_id] = chunk
                self.current_chunk_timestamp[channel_id] = 0.0 # timestamp
                file = Config.CHANNELS[channel_id][0]
                chunk_str = str(chunk) if chunk > 9 else "0" + str(chunk)
                sound = pygame.mixer.Sound(file + "-" + chunk_str + ".mp3")
                channel = pygame.mixer.Channel(channel_id)
                channel.play(sound)
                if self.playing[channel_id]:
                    self.current_chunk_realtime[channel_id] = time()
                else:
                    channel.pause()
            self.playing[channel_id] = play

    def shutdown(self):
        pygame.mixer.stop()
        pygame.mixer.quit()


class RemoteMusicStreamer(Streamer):
    pass


class LocalMIDIStreamer(Streamer):
    pass


class RemoteMIDIStreamer(Streamer):
    pass
