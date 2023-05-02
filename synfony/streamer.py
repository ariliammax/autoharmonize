# streamer.py
# in synfony

from abc import ABC, abstractmethod
from synfony.config import Config
from synfony.models import ChannelState
from threading import Timer
from time import time

import pygame


class Streamer(ABC):
    def __init__(self, channel_id):
        self.channel_id = channel_id

    @classmethod
    def init(self):
        pygame.mixer.init()

    @abstractmethod
    def event(self, event):
        pass

    @abstractmethod
    def get_chunk(self, chunk):
        pass

    @abstractmethod
    def get_current_time(self):
        pass

    @abstractmethod
    def get_last_time(self):
        pass

    @classmethod
    def get_num_channels(self):
        return len(Config.CHANNELS)

    def get_title(self):
        return Config.CHANNELS[self.channel_id][0]

    def get_total_time(self):
        return Config.CHANNELS[self.channel_id][1] * Config.CHANNELS[self.channel_id][2]

    @abstractmethod
    def get_volume(self):
        pass

    @abstractmethod
    def is_playing(self):
        pass

    @abstractmethod
    def schedule_seek(self, chunk, interval, playing):
        pass

    @abstractmethod
    def seek(self, chunk, playing):
        pass

    @abstractmethod
    def sync(self, state):
        pass

    @classmethod
    def shutdown(self):
        pygame.mixer.stop()
        pygame.mixer.quit()


class LocalMusicStreamer(Streamer):
    current_chunk_index = 1
    current_chunk_realtime = 0.0
    current_chunk_timestamp = 0.0
    last_timestamp = 0.0
    playing = True
    timer = None
    volume = 50

    def __init__(self, channel_id):
        super().__init__(channel_id)
        channel = pygame.mixer.Channel(channel_id)
        channel.set_endevent(pygame.USEREVENT + channel_id)
        chunk = 1
        sound = self.get_chunk(chunk)
        if sound is None:
            interval = Config.CHANNELS[channel_id][2]
            self.schedule_seek(chunk, interval, True)
        else:
            channel.play(sound)
            self.current_chunk_realtime = time()

    def event(self, event):
        channel_id = event.type - pygame.USEREVENT
        if channel_id != self.channel_id:
            return
        chunk = self.current_chunk_index + 1
        if chunk > Config.CHANNELS[self.channel_id][1]:
            chunk = 1
        sound = self.get_chunk(chunk)
        if sound is None:
            interval = Config.CHANNELS[self.channel_id][2]
            self.schedule_seek(chunk, interval, True)
        else:
            channel = pygame.mixer.Channel(self.channel_id)
            channel.queue(sound)
            self.current_chunk_index = chunk
            self.current_chunk_realtime = time()
            self.current_chunk_timestamp = 0.0

    def get_chunk(self, chunk):
        file = Config.CHANNELS[self.channel_id][0]
        chunk_str = str(chunk) if chunk > 9 else "0" + str(chunk)
        return pygame.mixer.Sound(file + "-" + chunk_str + ".mp3")

    def get_current_time(self):
        inter_chunk_offset = (self.current_chunk_index - 1) * Config.CHANNELS[self.channel_id][2]
        intra_chunk_offset = self.current_chunk_timestamp
        realtime_offset = time() - self.current_chunk_realtime
        if not self.playing:
            realtime_offset = 0.0
        return inter_chunk_offset + intra_chunk_offset + realtime_offset

    def get_last_time(self):
        return self.last_timestamp

    def get_volume(self):
        return self.volume

    def is_playing(self):
        return self.playing

    def schedule_seek(self, chunk, interval, playing):
        chunk += 1
        if chunk > Config.CHANNELS[self.channel_id][1]:
            chunk = 1
        self.current_chunk_index = chunk
        self.current_chunk_timestamp = 0.0
        self.playing = False
        self.timer = Timer(interval, self.seek, [
            chunk,
            playing,
        ])
        self.timer.start()

    def seek(self, chunk, playing):
        self.current_chunk_index = chunk
        self.current_chunk_timestamp = 0.0
        self.playing = playing
        self.timer = None
        sound = self.get_chunk(chunk)
        if sound is None:
            interval = Config.CHANNELS[self.channel_id][2]
            self.schedule_seek(chunk, interval, playing)
        else:
            channel = pygame.mixer.Channel(self.channel_id)
            channel.set_endevent(pygame.USEREVENT + len(Config.CHANNELS))
            channel.play(sound)
            if playing:
                self.current_chunk_realtime = time()
            else:
                channel.pause()
            channel.set_endevent(pygame.USEREVENT + self.channel_id)

    def sync(self, state: ChannelState):
        last_timestamp = state.get_last_timestamp()
        playing = state.get_playing()
        timestamp = state.get_timestamp()
        volume = state.get_volume()
        chunk = 1
        delay = abs(timestamp - self.get_current_time())
        while timestamp > Config.CHANNELS[self.channel_id][2]:
            timestamp -= Config.CHANNELS[self.channel_id][2]
            chunk += 1
        channel = pygame.mixer.Channel(self.channel_id)
        if delay > Config.TOLERABLE_DELAY or self.timer is not None:
            if self.timer:
                self.timer.cancel()
            channel.set_endevent(pygame.USEREVENT + len(Config.CHANNELS))
            channel.stop()
            channel.set_endevent(pygame.USEREVENT + self.channel_id)
            interval = Config.CHANNELS[self.channel_id][2] - timestamp
            self.schedule_seek(chunk, interval, playing)
        elif self.playing and not playing:
            channel.pause()
            self.current_chunk_timestamp = time() - self.current_chunk_realtime
            self.playing = False
        elif not self.playing and playing:
            channel.unpause()
            self.current_chunk_realtime = time()
            self.playing = True
        self.last_timestamp = last_timestamp
        self.volume = volume
        channel.set_volume(volume)


class RemoteMusicStreamer(Streamer):
    pass
