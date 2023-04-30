from abc import ABC, abstractmethod
from synfony.config import Config
from time import sleep

import pygame


class Streamer(ABC):
    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def event(self, event):
        pass

    @abstractmethod
    def get_current_time(self):
        pass

    @abstractmethod
    def get_total_time(self):
        pass

    @abstractmethod
    def is_playing(self):
        pass

    @abstractmethod
    def sync(self, state):
        pass

    @abstractmethod
    def shutdown(self):
        pass


class LocalMusicStreamer(Streamer):
    chunks = []

    def init(self):
        pygame.mixer.init()
        for channel_id, file in enumerate(Config.CHANNELS):
            channel = pygame.mixer.Channel(channel_id)
            channel.set_endevent(pygame.USEREVENT + channel_id)
            self.chunks.append(1)
            chunk = self.chunks[channel_id]
            chunk = str(chunk) if chunk > 9 else "0" + str(chunk)
            sound = pygame.mixer.Sound(file + "-" + chunk + ".mp3")
            channel.play(sound)

    def event(self, event):
        channel_id = event.type - pygame.USEREVENT
        if channel_id < 0 or channel_id >= len(Config.CHANNELS):
            return
        channel = pygame.mixer.Channel(channel_id)
        file = Config.CHANNELS[channel_id]
        self.chunks[channel_id] += 1
        chunk = self.chunks[channel_id]
        chunk = str(chunk) if chunk > 9 else "0" + str(chunk)
        sound = pygame.mixer.Sound(file + "-" + chunk + ".mp3")
        channel.queue(sound)

    def get_current_time(self, channel_id):
        return self.chunks[channel_id]

    def get_total_time(self, channel_id):
        return 100

    def is_playing(self, channel_id):
        return channel_id == 0

    def sync(self, state):
        pass

    def shutdown(self):
        pygame.mixer.stop()
        pygame.mixer.quit()
