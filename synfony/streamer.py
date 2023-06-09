# streamer.py
# in synfony

from abc import ABC, abstractmethod
from synfony.config import Config
from synfony.models import ChannelState, MachineAddress, RemoteStreamRequest
from synfony.sockets import TCPSockets
from threading import Thread, Timer
from time import sleep, time

import pygame


class BaseStreamer(ABC):
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

    @abstractmethod
    def get_title(self):
        pass

    @abstractmethod
    def get_total_time(self):
        pass

    @abstractmethod
    def get_volume(self):
        pass

    @abstractmethod
    def is_playing(self):
        pass

    @abstractmethod
    def is_seeking(self):
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


class AllStreamer(BaseStreamer):
    def __init__(self, streamers):
        super().__init__(-1)
        self.streamers = streamers

    def event(self, event):
        for streamer in self.streamers:
            streamer.event(event)

    def get_chunk(self, chunk):
        assert False

    def get_current_time(self):
        current_times = [streamer.get_current_time()
                         for streamer in self.streamers]
        return sum(current_times) / len(current_times)

    def get_last_time(self):
        last_times = [streamer.get_last_time() for streamer in self.streamers]
        return max(last_times)

    def get_title(self):
        return "ALL"

    def get_total_time(self):
        total_times = [streamer.get_total_time()
                       for streamer in self.streamers]
        return min(total_times)

    def get_volume(self):
        volumes = [streamer.get_volume() for streamer in self.streamers]
        return sum(volumes) / len(volumes)

    def is_playing(self):
        return any([streamer.is_playing() for streamer in self.streamers])

    def is_seeking(self):
        return any([streamer.is_seeking() for streamer in self.streamers])

    def schedule_seek(self, chunk, interval, playing):
        assert False

    def seek(self, chunk, playing):
        assert False

    def sync(self, state):
        for streamer in self.streamers:
            streamer.sync(state)


class LocalMusicStreamer(BaseStreamer):
    def __init__(self, channel_id):
        super().__init__(channel_id)
        self.current_chunk_index = 1
        self.current_chunk_realtime = 0.0
        self.current_chunk_timestamp = 0.0
        self.last_timestamp = 0.0
        self.playing = False
        self.timer = None
        self.volume = 0.5
        channel = pygame.mixer.Channel(channel_id)
        channel.set_endevent(pygame.USEREVENT + channel_id)
        channel.set_volume(self.volume)
        chunk = 1
        sound = self.get_chunk(chunk)
        if sound is None:
            interval = Config.CHANNELS[channel_id][2]
            self.schedule_seek(chunk - 1, interval, False)
        else:
            channel.set_endevent(pygame.USEREVENT + len(Config.CHANNELS))
            channel.play(sound)
            channel.pause()
            channel.set_endevent(pygame.USEREVENT + channel_id)

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
        inter_chunk_offset = ((self.current_chunk_index - 1) *
                              Config.CHANNELS[self.channel_id][2])
        intra_chunk_offset = self.current_chunk_timestamp
        realtime_offset = time() - self.current_chunk_realtime
        if not self.playing:
            realtime_offset = 0.0
        return inter_chunk_offset + intra_chunk_offset + realtime_offset

    def get_last_time(self):
        return self.last_timestamp

    def get_title(self):
        return Config.CHANNELS[self.channel_id][0]

    def get_total_time(self):
        return (Config.CHANNELS[self.channel_id][1] *
                Config.CHANNELS[self.channel_id][2])

    def get_volume(self):
        return self.volume

    def is_playing(self):
        return self.playing

    def is_seeking(self):
        return self.timer is not None

    def schedule_seek(self, chunk, interval, playing):
        chunk += 1
        if chunk > Config.CHANNELS[self.channel_id][1]:
            chunk = 1
        self.current_chunk_index = chunk
        self.current_chunk_timestamp = 0.0
        self.playing = False
        self.timer = Timer(interval - Config.PYGAME_DELAY, self.seek, [
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
            self.schedule_seek(
                chunk if playing else chunk - 1,
                interval,
                playing
            )
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


class RemoteMusicStream():
    sockets = TCPSockets

    def accept(self):
        host, port = tuple(Config.STREAMS[self.machine_id][0].split(":"))
        machine_address = MachineAddress(host=host, port=int(port))
        s = self.sockets.start_socket(
            machine_address=machine_address,
            timeout=None,
            bind=True
        )
        while True:
            try:
                connection, _ = self.sockets.accept(s)
                Thread(target=self.recv, args=[connection]).start()
            except Exception:
                pass

    def recv(self, connection):
        while True:
            try:
                request = self.sockets.recv(connection)
                if len(request) == 0:
                    break
                request = RemoteStreamRequest.deserialize(request)
                chunk = request.get_chunk()
                if ((chunk + self.machine_id) %
                        Config.REMOTE_DELAY_LONG_FREQUENCY == 0):
                    sleep(Config.REMOTE_DELAY_LONG)
                else:
                    sleep(Config.REMOTE_DELAY_SHORT)
                response = b'1'
                self.sockets.send(connection, response)
            except Exception:
                pass

    def __init__(self, machine_id):
        self.machine_id = machine_id
        Thread(target=self.accept).start()


class RemoteMusicStreamer(LocalMusicStreamer):
    sockets = TCPSockets

    def connect(self):
        while True:
            try:
                host, port = tuple(
                    Config.STREAMS[self.machine_id][0].split(":")
                )
                machine_address = MachineAddress(host=host, port=int(port))
                s = self.sockets.start_socket(
                    machine_address=machine_address,
                    timeout=None,
                    connect=True
                )
                break
            except Exception:
                pass
        while True:
            try:
                if False not in self.downloaded:
                    break
                chunk = self.prioritized
                while self.downloaded[chunk]:
                    chunk += 1
                    if chunk > Config.CHANNELS[self.channel_id][1]:
                        chunk = 1
                request = RemoteStreamRequest(chunk=chunk)
                request = request.serialize()
                self.sockets.sendall(s, request)
                response = self.sockets.recv(s)
                if len(response) == 0:
                    break
                self.downloaded[chunk] = True
            except Exception:
                pass

    def __init__(self, channel_id):
        self.downloaded = [False
                           for _ in range(Config.CHANNELS[channel_id][1] + 1)]
        self.downloaded[0] = True
        self.machine_id = None
        self.prioritized = 1
        for i in range(len(Config.MACHINES)):
            if channel_id in Config.STREAMS[i][1]:
                self.machine_id = i
        super().__init__(channel_id)
        Thread(target=self.connect).start()

    def get_chunk(self, chunk):
        if not self.downloaded[chunk]:
            return None
        return super().get_chunk(chunk)

    def schedule_seek(self, chunk, interval, playing):
        chunk += 1
        if chunk > Config.CHANNELS[self.channel_id][1]:
            chunk = 1
        if not self.downloaded[chunk]:
            self.prioritized = chunk
        chunk -= 1
        return super().schedule_seek(chunk, interval, playing)
