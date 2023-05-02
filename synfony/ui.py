# callbacks.py
# in synfony

from synfony.callbacks import *
from synfony.config import UIConfig
from synfony.streamer import LocalMusicStreamer, Streamer

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
        self.font = pygame.font.SysFont('Arial', 40)

        self.fillColors = {
            'normal': '#ffffff',
            'hover': '#666666',
            'pressed': '#333333',
        }
        
        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.buttonSurf = self.font.render("Play", True, (20, 20, 20))
        self.ui.objects.append(self)
        
    def process(self):
        mousePos = pygame.mouse.get_pos()
        self.buttonSurface.fill(self.fillColors['normal'])

        # Set the state of the button
        self.isSelected = self.streamers[self.ui.channel].is_playing()

        if (self.isSelected):
            self.buttonSurf = self.font.render(self.selectedTxt, True, (20, 20, 20))
        else:
            self.buttonSurf = self.font.render(self.txt, True, (20, 20, 20))

        if not self.ui.is_loading:
            if self.buttonRect.collidepoint(mousePos):
                self.buttonSurface.fill(self.fillColors['hover'])
                if pygame.mouse.get_pressed(num_buttons=3)[0]:
                    self.buttonSurface.fill(self.fillColors['pressed'])
                    if not self.alreadyPressed:
                        self.alreadyPressed = True
                        self.ui.is_loading = True
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
        self.font = pygame.font.SysFont('Arial', 40)

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

        self.value_surface = self.font.render(str(self.value), True, (255, 255, 255))
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
            self.value_surface = self.font.render(str(self.value), True, (255, 255, 255))
            if self.onchange_function is not None:
                self.onchange_function(self.value)

    def _increment(self, **kwargs):
        if self.value < self.max_value:
            self.value += 1
            self.ui.channel += 1
            self.value_surface = self.font.render(str(self.value), True, (255, 255, 255))
            if self.onchange_function is not None:
                self.onchange_function(self.value)
    
    def process(self):
      self.ui.screen.blit(self.value_surface, self.value_rect)


class SeekSlider():
    def __init__(self, ui, x, y, width, height, min_val, max_val, streamers, stringify, onchangeFunction=None):
        self.ui = ui
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.streamers = streamers
        self.max_val = max_val or self.streamers[self.ui.channel].get_total_time()
        self.value = self.streamers[self.ui.channel].get_current_time()
        self.onchangeFunction = onchangeFunction
        self.isDragging = False
        self.stringify = stringify
        self.font = pygame.font.SysFont('Arial', 40)

        self.fillColors = {
            'background': '#000000',
            'bar': '#ffffff',
            'knob': '#333333',
        }

        self.sliderSurface = pygame.Surface((self.width, self.height))
        self.sliderRect = pygame.Rect(self.x, self.y, self.width, self.height)
        ui.objects.append(self)

    def process(self):
        mousePos = pygame.mouse.get_pos()
        self.sliderSurface.fill(self.fillColors['background'])

        self.max_val = self.streamers[self.ui.channel].get_total_time()
        range = self.max_val - self.min_val
        knob_x = int(((self.value - self.min_val) / range) * (self.width - self.height))

        barRect = pygame.Rect(self.height / 2, self.height / 2 - 2, self.width - self.height, 4)
        pygame.draw.rect(self.sliderSurface, self.fillColors['bar'], barRect)

        knobRect = pygame.Rect(knob_x, 0, self.height, self.height)
        pygame.draw.rect(self.sliderSurface, self.fillColors['knob'], knobRect)

        #draw left label
        self.leftLabelSurface = self.font.render(self.stringify(self.value), True, (255, 255, 255))
        self.leftLabelRect = self.leftLabelSurface.get_rect()
        self.leftLabelRect.x = self.x + 15
        self.leftLabelRect.y = self.y - self.height - 5
        
        #draw right label
        self.rightLabelSurface = self.font.render(self.stringify(self.max_val), True, (255, 255, 255))
        self.rightLabelRect = self.leftLabelSurface.get_rect()
        self.rightLabelRect.x = self.x + self.width - 100
        self.rightLabelRect.y = self.y - self.height - 5
  
        # handle input
        if not self.ui.is_loading:
            if self.sliderRect.collidepoint(mousePos):
                if pygame.mouse.get_pressed(num_buttons=3)[0]:
                    self.isDragging = True
                    # calculate the new value based on the position of the mouse
                    mouse_x = mousePos[0] - self.sliderRect.left - self.height / 2
                    new_value = (mouse_x / (self.width - self.height)) * range + self.min_val
                    new_value = max(min(new_value, self.max_val), self.min_val)
                    self.value = new_value
                    # update the position of the knob based on the new value
                    knob_x = int(((self.value - self.min_val) / range) * (self.width - self.height))
                elif self.isDragging:
                    self.isDragging = False

                    # call the onchange function if it exists
                    if self.onchangeFunction is not None:
                        self.ui.is_loading = True
                        self.onchangeFunction(
                            channel_idx=self.ui.channel,
                            event_queue=self.ui.event_queue,
                            seek_value=self.value,
                            streamer=self.streamers[self.ui.channel],
                        )
                else:
                    self.value = self.streamers[self.ui.channel].get_current_time()
                    # update the position of the knob based on the new value
                    knob_x = int(((self.value - self.min_val) / range) * (self.width - self.height))
            else:
                self.value = self.streamers[self.ui.channel].get_current_time()
                # update the position of the knob based on the new value
                knob_x = int(((self.value - self.min_val) / range) * (self.width - self.height))
  
        # redraw the knob with its new position
        knobRect = pygame.Rect(knob_x, 0, self.height, self.height)
        pygame.draw.rect(self.sliderSurface, self.fillColors['knob'], knobRect)

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
    is_loading = False

    def init(self):
        pygame.init()

        streamers = [LocalMusicStreamer(i) for i in range(Streamer.get_num_channels())]
        Streamer.init()

        title = streamers[0].get_title()
        songTitleSurface = pygame.font.SysFont('Arial', 40).render(title, True, (255, 255, 255))
        songTitleRect = songTitleSurface.get_rect()
        songTitleRect.x = (UIConfig.SCREEN_WIDTH / 2) - (songTitleRect.width / 2)
        songTitleRect.y = 0

        Loader(self, 0, 0, 50, 0.1)
        Button(self, 120, 190, 400, 100, "Play", "Pause", streamers, playButtonTapped)
        Picker(self, 120, 300, 400, 100, 0, 0, Streamer.get_num_channels() - 1, streamers, None)
        SeekSlider(self, 0, UIConfig.SCREEN_HEIGHT - 70, 640, 50, 0, None, streamers, self.stringify_time, didSeekTo)
        SeekSlider(self, (UIConfig.SCREEN_WIDTH / 2) - (300 / 2), songTitleRect.height + 70, 300, 50, 0, 100, streamers, self.stringify_volume, didChangeVolumeTo)

        while True:
            title = streamers[self.channel].get_title()
            songTitleSurface = pygame.font.SysFont('Arial', 40).render(title, True, (255, 255, 255))
            self.screen.fill((0, 0, 0))
            self.screen.blit(songTitleSurface, songTitleRect)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    Streamer.shutdown()
                    pygame.quit()
                    exit()
                else:
                    streamers[0].event(event)
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

    def stop_loading(self):
        self.is_loading = False
