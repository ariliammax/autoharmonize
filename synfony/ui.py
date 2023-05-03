# callbacks.py
# in synfony

from synfony.callbacks import *
from synfony.config import Config, UIConfig
from synfony.streamer import (
    AllStreamer,
    LocalMusicStreamer,
    RemoteMusicStream,
    RemoteMusicStreamer,
    Streamer
)

import math
import pygame

class Button():
    def __init__(self, ui, x, y, width, height, txt, selected_txt, streamers, on_click_function=None, should_load_on_click=True):
        self.ui = ui
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.on_click_function = on_click_function
        self.already_pressed = False
        self.is_selected = False
        self.streamers = streamers
        self.txt = txt
        self.selected_txt = selected_txt
        self.font = pygame.font.SysFont('Arial', 30)
        self.should_load_on_click = should_load_on_click

        self.fill_colors = {
            'normal': '#3498db',
            'hover': '#2980b9',
            'pressed': '#2980b9',
        }
        
        self.button_surface = pygame.Surface((self.width, self.height))
        self.button_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.button_surf = self.font.render("Play", True, (255, 255, 255))
        self.ui.objects.append(self)
        
    def process(self):
        mousePos = pygame.mouse.get_pos()
        self.button_surface.fill(self.fill_colors['normal'])

        # Set the state of the button
        if (not self.ui.get_is_loading()):
            self.is_selected = self.streamers[self.ui.channel].is_playing()

        if (self.is_selected):
            self.button_surf = self.font.render(self.selected_txt, True, (255, 255, 255))
        else:
            self.button_surf = self.font.render(self.txt, True, (255, 255, 255))

        if not self.should_load_on_click or not self.ui.get_is_loading():
            if self.button_rect.collidepoint(mousePos):
                self.button_surface.fill(self.fill_colors['hover'])
                if pygame.mouse.get_pressed(num_buttons=3)[0]:
                    self.button_surface.fill(self.fill_colors['pressed'])
                    if not self.already_pressed:
                        self.already_pressed = True
                        if Config.HANDSHAKE_ENABLED and self.should_load_on_click:
                            self.ui.start_loading()
                        self.on_click_function(
                            channel_idx=self.ui.channel,
                            event_queue=self.ui.event_queue,
                            streamer=self.streamers[self.ui.channel],
                        )
                else:
                    self.already_pressed = False

        self.button_surface.blit(self.button_surf, [
            self.button_rect.width/2 - self.button_surf.get_rect().width/2,
            self.button_rect.height/2 - self.button_surf.get_rect().height/2
        ])

        self.ui.screen.blit(self.button_surface, self.button_rect)


class Loader:
    def __init__(self, ui, x, y, size, speed):
        self.ui = ui
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.angle = 0
        self.color = (255, 255, 255)
        self.surface = pygame.Surface((size, size))
        self.rect = pygame.Rect(x, y, size, size)
        self.ui.objects.append(self)

    def process(self):
        self.surface.fill((0, 0, 0))
        pygame.draw.arc(self.surface, self.color, (0, 0, self.size, self.size),
                        self.angle, self.angle + math.pi/2, int(self.size/8))
        self.angle = (self.angle + self.speed) % (2*math.pi)
        if (self.ui.get_is_loading()):
            self.ui.screen.blit(self.surface, self.rect)


class Picker:
    def __init__(self, ui, x, y, width, height, initial_value, min_value, max_value, streamers, on_change_function=None):
        self.ui = ui
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.on_change_function = on_change_function
        self.already_pressed = False
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.font = pygame.font.SysFont('Arial', 25)
        self.streamers = streamers

        self.fill_colors = {
            'normal': '#ffffff',
            'hover': '#666666',
            'pressed': '#333333',
        }

        self.left_button = Button(
            self.ui,
            self.x,
            self.y,
            self.height,
            self.height,
            '<',
            '<',
            streamers,
            self._decrement,
            False
        )

        self.right_button = Button(
            self.ui,
            self.x + self.width - self.height,
            self.y,
            self.height,
            self.height,
            '>',
            '>',
            streamers,
            self._increment,
            False
        )

        self.value_surface = self.font.render(str(streamers[self.value].get_title()), True, (255, 255, 255))
        self.value_rect = self.value_surface.get_rect()
        self.value_rect.center = (
            self.x + self.width/2,
            self.y + self.height/2
        )
        
        self.ui.objects.append(self)

    def _decrement(self, **kwargs):
        self.value = (self.value - 1) % (Streamer.get_num_channels() + 1)
        self.ui.channel = (self.ui.channel - 1) % (Streamer.get_num_channels() + 1)

        self.value_surface = self.font.render(str(self.streamers[self.value].get_title()), True, (255, 255, 255))
        self.value_rect = self.value_surface.get_rect()
        self.value_rect.center = (
            self.x + self.width/2,
            self.y + self.height/2
        )
        if self.on_change_function is not None:
            self.on_change_function(self.value)

    def _increment(self, **kwargs):
        self.value = (self.value + 1) % (Streamer.get_num_channels() + 1)
        self.ui.channel = (self.ui.channel + 1) % (Streamer.get_num_channels() + 1)

        self.value_surface = self.font.render(str(self.streamers[self.value].get_title()), True, (255, 255, 255))
        self.value_rect = self.value_surface.get_rect()
        self.value_rect.center = (
            self.x + self.width/2,
            self.y + self.height/2
        )
        if self.on_change_function is not None:
            self.on_change_function(self.value)
    
    def process(self):
      self.ui.screen.blit(self.value_surface, self.value_rect)


class SeekSlider():
    def __init__(self, ui, x, y, width, height, streamers, get_val, get_max_val, stringify, on_change_function=None):
        self.ui = ui
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.streamers = streamers
        self.get_val = get_val
        self.get_max_val = get_max_val
        self.min_val = 0
        self.max_val = get_max_val(self.streamers[self.ui.channel])
        self.value = get_val(self.streamers[self.ui.channel])
        self.on_change_function = on_change_function
        self.is_dragging = False
        self.stringify = stringify
        self.font = pygame.font.SysFont('Arial', 20)

        self.fill_colors = {
            'background': '#232323',
            'bar': '#ffffff',
            'knob': '#494949',
        }

        self.slider_surface = pygame.Surface((self.width, self.height))
        self.slider_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        ui.objects.append(self)
    
    def calculate_knob_pos(self):
        range = self.max_val - self.min_val
        self.value = self.get_val(self.streamers[self.ui.channel])
        if (self.height > self.width):
                self.value = self.max_val - self.value
        # update the position of the knob based on the new value
        return int(((self.value - self.min_val) / range) * (max(self.width, self.height) - min(self.width, self.height)))

    def process(self):
        mousePos = pygame.mouse.get_pos()
        self.slider_surface.fill(self.fill_colors['background'])

        self.max_val = self.get_max_val(self.streamers[self.ui.channel])
        range = self.max_val - self.min_val

        #draw left label
        if (self.height > self.width):
            self.left_label_surface = self.font.render(self.stringify(self.max_val - self.value), True, (255, 255, 255))
        else:
            self.left_label_surface = self.font.render(self.stringify(self.value), True, (255, 255, 255))
        self.left_label_rect = self.left_label_surface.get_rect()

        #draw right label
        self.right_label_surface = self.font.render(self.stringify(self.max_val), True, (255, 255, 255))
        self.right_label_rect = self.right_label_surface.get_rect()

        if (self.height > self.width):
            # Vertical
            knob_pos = int(((self.value - self.min_val) / range) * (self.height - self.width))
            bar_rect = pygame.Rect(self.width / 2 - 2, self.width / 2, 4, self.height - self.width)
            pygame.draw.rect(self.slider_surface, self.fill_colors['bar'], bar_rect)
            knob_rect = pygame.Rect(0, knob_pos, self.width, self.width)
            pygame.draw.rect(self.slider_surface, self.fill_colors['knob'], knob_rect, 0, 25)
            self.left_label_rect.centerx = (self.slider_rect.width) / 2 + 15
            self.left_label_rect.y = self.y + self.height
            self.right_label_rect.centerx = (self.slider_rect.width) / 2 + 15
            self.right_label_rect.y = self.y - 23
        else:
            # Horizontal
            knob_pos = int(((self.value - self.min_val) / range) * (self.width - self.height))
            bar_rect = pygame.Rect(self.height / 2, self.height / 2 - 2, self.width - self.height, 4)
            pygame.draw.rect(self.slider_surface, self.fill_colors['bar'], bar_rect)
            knob_rect = pygame.Rect(knob_pos, 0, self.height, self.height)
            pygame.draw.rect(self.slider_surface, self.fill_colors['knob'], knob_rect, 0, 25)
            self.left_label_rect.x = self.x + 25
            self.left_label_rect.y = self.y - self.height + 20
            self.right_label_rect.x = self.x + self.width - self.right_label_rect.width - 25
            self.right_label_rect.y = self.y - self.height + 20
  
        # handle input
        if not self.ui.get_is_loading():
            if self.slider_rect.collidepoint(mousePos):
                if pygame.mouse.get_pressed(num_buttons=3)[0]:
                    self.is_dragging = True
                    # calculate the new value based on the position of the mouse
                    if (self.height > self.width):
                        # Vertical
                        mouse_y = mousePos[1] - self.slider_rect.top - self.width / 2
                        new_value = (mouse_y / (self.height - self.width)) * range + self.min_val
                        new_value = max(min(new_value, self.max_val), self.min_val)
                        self.value = new_value
                        # update the position of the knob based on the new value
                        knob_pos = int(((self.value - self.min_val) / range) * (self.height - self.width))
                    else:
                        # Horizontal
                        mouse_x = mousePos[0] - self.slider_rect.left - self.height / 2
                        new_value = (mouse_x / (self.width - self.height)) * range + self.min_val
                        new_value = max(min(new_value, self.max_val), self.min_val)
                        self.value = new_value
                        # update the position of the knob based on the new value
                        knob_pos = int(((self.value - self.min_val) / range) * (self.width - self.height))
                elif self.is_dragging:
                    self.is_dragging = False

                    # call the onchange function if it exists
                    if self.on_change_function is not None:
                        if Config.HANDSHAKE_ENABLED:
                            self.ui.start_loading()
                        if (self.height > self.width):
                            self.on_change_function(
                                channel_idx=self.ui.channel,
                                event_queue=self.ui.event_queue,
                                seek_value=self.max_val - self.value,
                                streamer=self.streamers[self.ui.channel],
                            )
                        else:
                             self.on_change_function(
                                channel_idx=self.ui.channel,
                                event_queue=self.ui.event_queue,
                                seek_value=self.value,
                                streamer=self.streamers[self.ui.channel],
                            )
                else:
                    knob_pos = self.calculate_knob_pos()
            else:
                knob_pos = self.calculate_knob_pos()
  
        # redraw the knob with its new position
        if (self.height > self.width):
            # Vertical
            knob_rect = pygame.Rect(0, knob_pos, self.width, self.width)
        else:
            # Horizontal
            knob_rect = pygame.Rect(knob_pos, 0, self.height, self.height)

        pygame.draw.rect(self.slider_surface, self.fill_colors['knob'], knob_rect, 0, 25)

        self.ui.screen.blit(self.slider_surface, self.slider_rect)
        self.ui.screen.blit(self.left_label_surface, self.left_label_rect)
        self.ui.screen.blit(self.right_label_surface, self.right_label_rect)


class UI():
    channel = Streamer.get_num_channels()
    event_queue = []
    fps_clock = pygame.time.Clock()
    objects = []
    screen = pygame.display.set_mode((UIConfig.SCREEN_WIDTH, UIConfig.SCREEN_HEIGHT))
    streamers = []
    is_loading = [False for _ in range(Streamer.get_num_channels())]

    def init(self, machine_id):
        self.machine_id = machine_id
        pygame.init()

        RemoteMusicStream(machine_id)
        for i in range(Streamer.get_num_channels()):
            if i in Config.STREAMS[self.machine_id][1]:
                self.streamers.append(LocalMusicStreamer(i))
            else:
                self.streamers.append(RemoteMusicStreamer(i))
        self.streamers.append(AllStreamer(list(self.streamers)))
        Streamer.init()

        Loader(self, UIConfig.SCREEN_WIDTH / 2 - 25, 50, 50, 0.1)
        Picker(self, 0, 0, UIConfig.SCREEN_WIDTH, 50, self.channel, 0, Streamer.get_num_channels(), self.streamers, None)
        SeekSlider(self, 15, UIConfig.SCREEN_HEIGHT / 2 - 150, 50, 300, self.streamers, (lambda s: s.get_volume()), (lambda s: 1), self.stringify_volume, didChangeVolumeTo)
        Button(self, UIConfig.SCREEN_WIDTH / 2 - 125, UIConfig.SCREEN_HEIGHT / 2 - 50, 250, 100, "Play", "Pause", self.streamers, playButtonTapped)
        SeekSlider(self, 0, UIConfig.SCREEN_HEIGHT - 70, 640, 50, self.streamers, (lambda s: s.get_current_time()), (lambda s: s.get_total_time()), self.stringify_time, didSeekTo)

        while True:
            self.screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    Streamer.shutdown()
                    pygame.quit()
                    exit()
                else:
                    self.streamers[-1].event(event)
            for object in self.objects:
                object.process()
            pygame.display.flip()
            self.fps_clock.tick(UIConfig.fps)
    
    def stringify_time(self, time):
        minutes, seconds = divmod(int(time), 60)
        return f"{minutes}:{seconds:02d}"

    def stringify_volume(self, volume):
        match volume:
            case 0:
                return "MUTED"
            case 1:
                return "MAX"
            case _:
                return str(int(volume * 100))

    def get_is_loading(self):
        if (self.channel == Streamer.get_num_channels()):
            # ALL Channel
            return any(self.is_loading) or self.streamers[self.channel].is_seeking()
        else:
            return self.is_loading[self.channel] or self.streamers[self.channel].is_seeking()

    def start_loading(self):
        if (self.channel == Streamer.get_num_channels()):
            self.is_loading = [True for _ in range(Streamer.get_num_channels())]
        else:
            self.is_loading[self.channel] = True

    def stop_loading(self):
        if (self.channel == Streamer.get_num_channels()):
            self.is_loading = [False for _ in range(Streamer.get_num_channels())]
        else:
            self.is_loading[self.channel] = False

