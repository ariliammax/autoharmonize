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
    def __init__(self, ui, x, y, width, height, txt, selectedTxt, streamers, onclickFunction=None):
        self.ui = ui
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onclickFunction = onclickFunction
        self.alreadyPressed = False
        self.isSelected = False
        self.streamers = streamers
        self.txt = txt
        self.selectedTxt = selectedTxt
        self.font = pygame.font.SysFont('Arial', 30)

        self.fillColors = {
            'normal': '#3498db',
            'hover': '#2980b9',
            'pressed': '#2980b9',
        }
        
        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.buttonSurf = self.font.render("Play", True, (255, 255, 255))
        self.ui.objects.append(self)
        
    def process(self):
        mousePos = pygame.mouse.get_pos()
        self.buttonSurface.fill(self.fillColors['normal'])

        # Set the state of the button
        self.isSelected = self.streamers[self.ui.channel].is_playing()

        if (self.isSelected):
            self.buttonSurf = self.font.render(self.selectedTxt, True, (255, 255, 255))
        else:
            self.buttonSurf = self.font.render(self.txt, True, (255, 255, 255))

        if not self.ui.is_loading:
            if self.buttonRect.collidepoint(mousePos):
                self.buttonSurface.fill(self.fillColors['hover'])
                if pygame.mouse.get_pressed(num_buttons=3)[0]:
                    self.buttonSurface.fill(self.fillColors['pressed'])
                    if not self.alreadyPressed:
                        self.alreadyPressed = True
                        if Config.HANDSHAKE_ENABLED:
                            self.ui.start_loading()
                        self.onclickFunction(
                            channel_idx=self.ui.channel,
                            event_queue=self.ui.event_queue,
                            streamer=self.streamers[self.ui.channel],
                        )
                else:
                    self.alreadyPressed = False
        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width/2 - self.buttonSurf.get_rect().width/2,
            self.buttonRect.height/2 - self.buttonSurf.get_rect().height/2
        ])
        self.ui.screen.blit(self.buttonSurface, self.buttonRect)


class Picker:
    def __init__(self, ui, x, y, width, height, initial_value, min_value, max_value, streamers, onchange_function=None):
        self.ui = ui
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onchange_function = onchange_function
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
            self._decrement
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
            self._increment
        )

        self.value_surface = self.font.render(str(streamers[self.value].get_title()), True, (255, 255, 255))
        self.value_rect = self.value_surface.get_rect()
        self.value_rect.center = (
            self.x + self.width/2,
            self.y + self.height/2
        )
        
        self.ui.objects.append(self)

    def _decrement(self, **kwargs):
        if self.value > self.min_value:
            self.value -= 1
            self.ui.channel -= 1
            self.value_surface = self.font.render(str(self.streamers[self.value].get_title()), True, (255, 255, 255))
            self.value_rect = self.value_surface.get_rect()
            self.value_rect.center = (
                self.x + self.width/2,
                self.y + self.height/2
            )
            if self.onchange_function is not None:
                self.onchange_function(self.value)

    def _increment(self, **kwargs):
        if self.value < self.max_value:
            self.value += 1
            self.ui.channel += 1
            self.value_surface = self.font.render(str(self.streamers[self.value].get_title()), True, (255, 255, 255))
            self.value_rect = self.value_surface.get_rect()
            self.value_rect.center = (
                self.x + self.width/2,
                self.y + self.height/2
            )
            if self.onchange_function is not None:
                self.onchange_function(self.value)
    
    def process(self):
      self.ui.screen.blit(self.value_surface, self.value_rect)


class SeekSlider():
    def __init__(self, ui, x, y, width, height, streamers, get_val, get_max_val, stringify, onchangeFunction=None):
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
        self.onchangeFunction = onchangeFunction
        self.isDragging = False
        self.stringify = stringify
        self.font = pygame.font.SysFont('Arial', 20)

        self.fillColors = {
            'background': '#232323',
            'bar': '#ffffff',
            'knob': '#494949',
        }

        self.sliderSurface = pygame.Surface((self.width, self.height))
        self.sliderRect = pygame.Rect(self.x, self.y, self.width, self.height)
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
        self.sliderSurface.fill(self.fillColors['background'])

        self.max_val = self.get_max_val(self.streamers[self.ui.channel])
        range = self.max_val - self.min_val

        #draw left label
        if (self.height > self.width):
            self.leftLabelSurface = self.font.render(self.stringify(self.max_val - self.value), True, (255, 255, 255))
        else:
            self.leftLabelSurface = self.font.render(self.stringify(self.value), True, (255, 255, 255))
        self.leftLabelRect = self.leftLabelSurface.get_rect()

        #draw right label
        self.rightLabelSurface = self.font.render(self.stringify(self.max_val), True, (255, 255, 255))
        self.rightLabelRect = self.rightLabelSurface.get_rect()

        if (self.height > self.width):
            # Vertical
            knob_pos = int(((self.value - self.min_val) / range) * (self.height - self.width))
            barRect = pygame.Rect(self.width / 2 - 2, self.width / 2, 4, self.height - self.width)
            pygame.draw.rect(self.sliderSurface, self.fillColors['bar'], barRect)
            knobRect = pygame.Rect(0, knob_pos, self.width, self.width)
            pygame.draw.rect(self.sliderSurface, self.fillColors['knob'], knobRect, 0, 25)
            self.leftLabelRect.centerx = (self.sliderRect.width) / 2 + 15
            self.leftLabelRect.y = self.y + self.height
            self.rightLabelRect.centerx = (self.sliderRect.width) / 2 + 15
            self.rightLabelRect.y = self.y - 23
        else:
            # Horizontal
            knob_pos = int(((self.value - self.min_val) / range) * (self.width - self.height))
            barRect = pygame.Rect(self.height / 2, self.height / 2 - 2, self.width - self.height, 4)
            pygame.draw.rect(self.sliderSurface, self.fillColors['bar'], barRect)
            knobRect = pygame.Rect(knob_pos, 0, self.height, self.height)
            pygame.draw.rect(self.sliderSurface, self.fillColors['knob'], knobRect, 0, 25)
            self.leftLabelRect.x = self.x + 25
            self.leftLabelRect.y = self.y - self.height + 20
            self.rightLabelRect.x = self.x + self.width - self.rightLabelRect.width - 25
            self.rightLabelRect.y = self.y - self.height + 20
  
        # handle input
        if not self.ui.is_loading:
            if self.sliderRect.collidepoint(mousePos):
                if pygame.mouse.get_pressed(num_buttons=3)[0]:
                    self.isDragging = True
                    # calculate the new value based on the position of the mouse
                    if (self.height > self.width):
                        # Vertical
                        mouse_y = mousePos[1] - self.sliderRect.top - self.width / 2
                        new_value = (mouse_y / (self.height - self.width)) * range + self.min_val
                        new_value = max(min(new_value, self.max_val), self.min_val)
                        self.value = new_value
                        # update the position of the knob based on the new value
                        knob_pos = int(((self.value - self.min_val) / range) * (self.height - self.value))
                    else:
                        # Horizontal
                        mouse_x = mousePos[0] - self.sliderRect.left - self.height / 2
                        new_value = (mouse_x / (self.width - self.height)) * range + self.min_val
                        new_value = max(min(new_value, self.max_val), self.min_val)
                        self.value = new_value
                        # update the position of the knob based on the new value
                        knob_pos = int(((self.value - self.min_val) / range) * (self.width - self.height))
                elif self.isDragging:
                    self.isDragging = False

                    # call the onchange function if it exists
                    if self.onchangeFunction is not None:
                        if Config.HANDSHAKE_ENABLED:
                            self.ui.start_loading()
                        if (self.height > self.width):
                            self.onchangeFunction(
                                channel_idx=self.ui.channel,
                                event_queue=self.ui.event_queue,
                                seek_value=self.max_val - self.value,
                                streamer=self.streamers[self.ui.channel],
                            )
                        else:
                             self.onchangeFunction(
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
            knobRect = pygame.Rect(0, knob_pos, self.width, self.width)
        else:
            # Horizontal
            knobRect = pygame.Rect(knob_pos, 0, self.height, self.height)

        pygame.draw.rect(self.sliderSurface, self.fillColors['knob'], knobRect, 0, 25)

        self.ui.screen.blit(self.sliderSurface, self.sliderRect)
        self.ui.screen.blit(self.leftLabelSurface, self.leftLabelRect)
        self.ui.screen.blit(self.rightLabelSurface, self.rightLabelRect)

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
        if (self.ui.is_loading):
            self.ui.screen.blit(self.surface, self.rect)


class UI():
    channel = 0
    event_queue = []
    fpsClock = pygame.time.Clock()
    objects = []
    screen = pygame.display.set_mode((UIConfig.SCREEN_WIDTH, UIConfig.SCREEN_HEIGHT))
    streamers = []
    is_loading = False

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

        Loader(self, UIConfig.SCREEN_WIDTH / 2 - 25, UIConfig.SCREEN_HEIGHT / 2 - 125, 50, 0.1)
        Picker(self, 0, 0, UIConfig.SCREEN_WIDTH, 50, 0, 0, Streamer.get_num_channels(), self.streamers, None)
        SeekSlider(self, 15, UIConfig.SCREEN_HEIGHT / 2 - 150, 50, 300, self.streamers, (lambda s: s.get_volume()), (lambda s: 100), self.stringify_volume, didChangeVolumeTo)
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
            self.fpsClock.tick(UIConfig.fps)
    
    def stringify_time(self, time):
        minutes = int(time // 60)
        seconds = int(time - (minutes * 60))
        if (seconds < 10):
            return str(minutes) + ":0" + str(seconds)
        else:
            return str(minutes) + ":" + str(seconds)

    def stringify_volume(self, volume):
        if (volume == 0):
            return "MUTED"
        elif (volume == 100):
            return "MAX"
        else:
            return str(int(volume))

    def start_loading(self):
        self.is_loading = True

    def stop_loading(self):
        self.is_loading = False
