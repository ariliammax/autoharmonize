# callbacks.py
# in synfony

from synfony.callbacks import *
from synfony.config import UIConfig
from synfony.streamer import LocalMusicStreamer

import pygame


screen = pygame.display.set_mode((UIConfig.SCREEN_WIDTH, UIConfig.SCREEN_HEIGHT))
fpsClock = pygame.time.Clock()
objects = []

event_queue = []

def stringify_time(time):
  minutes = int(time // 60)
  seconds = int(time - (minutes * 60))
  if (seconds < 10):
    return str(minutes) + ":0" + str(seconds)
  else:
    return str(minutes) + ":" + str(seconds)

def stringify_volume(volume):
    if (volume == 0):
        return "MUTED"
    elif (volume == 100):
        return "MAX"
    else:
        return str(int(volume))

class PlayButton():
    def __init__(self, x, y, width, height, onclickFunction=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onclickFunction = onclickFunction
        self.alreadyPressed = False
        self.isSelected = False

        self.fillColors = {
            'normal': '#ffffff',
            'hover': '#666666',
            'pressed': '#333333',
        }
        
        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.buttonSurf = pygame.font.SysFont('Arial', 40).render("Play", True, (20, 20, 20))
        objects.append(self)
        
    def process(self, streamer):
        mousePos = pygame.mouse.get_pos()
        self.buttonSurface.fill(self.fillColors['normal'])

        # Set the state of the button
        self.isSelected = streamer.is_playing(0)

        if (self.isSelected):
            self.buttonSurf = pygame.font.SysFont('Arial', 40).render("Pause", True, (20, 20, 20))
        else:
            self.buttonSurf = pygame.font.SysFont('Arial', 40).render("Play", True, (20, 20, 20))

        if self.buttonRect.collidepoint(mousePos):
            self.buttonSurface.fill(self.fillColors['hover'])
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.buttonSurface.fill(self.fillColors['pressed'])
                if not self.alreadyPressed:
                    self.alreadyPressed = True
                    self.onclickFunction(0, streamer.get_current_time(0), not self.isSelected, event_queue)
            else:
                self.alreadyPressed = False
        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width/2 - self.buttonSurf.get_rect().width/2,
            self.buttonRect.height/2 - self.buttonSurf.get_rect().height/2
        ])
        screen.blit(self.buttonSurface, self.buttonRect)


class SeekSlider():
    def __init__(self, x, y, width, height, min_val, max_val, get_current_val, stringify, onchangeFunction=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = get_current_val(0)
        self.get_current_val = get_current_val
        self.onchangeFunction = onchangeFunction
        self.isDragging = False
        self.stringify = stringify

        self.fillColors = {
            'background': '#000000',
            'bar': '#ffffff',
            'knob': '#333333',
        }

        self.sliderSurface = pygame.Surface((self.width, self.height))
        self.sliderRect = pygame.Rect(self.x, self.y, self.width, self.height)
        objects.append(self)

    def process(self, streamer):
        mousePos = pygame.mouse.get_pos()
        self.sliderSurface.fill(self.fillColors['background'])

        range = self.max_val - self.min_val
        knob_x = int(((self.value - self.min_val) / range) * (self.width - self.height))

        barRect = pygame.Rect(self.height / 2, self.height / 2 - 2, self.width - self.height, 4)
        pygame.draw.rect(self.sliderSurface, self.fillColors['bar'], barRect)

        knobRect = pygame.Rect(knob_x, 0, self.height, self.height)
        pygame.draw.rect(self.sliderSurface, self.fillColors['knob'], knobRect)

        #draw left label
        self.leftLabelSurface = pygame.font.SysFont('Arial', 40).render(self.stringify(self.value), True, (255, 255, 255))
        self.leftLabelRect = self.leftLabelSurface.get_rect()
        self.leftLabelRect.x = self.x + 15
        self.leftLabelRect.y = self.y - self.height - 5
        
        #draw right label
        self.rightLabelSurface = pygame.font.SysFont('Arial', 40).render(self.stringify(self.max_val), True, (255, 255, 255))
        self.rightLabelRect = self.leftLabelSurface.get_rect()
        self.rightLabelRect.x = self.x + self.width - 100
        self.rightLabelRect.y = self.y - self.height - 5
  
        # handle input
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
                    self.onchangeFunction(0, self.value, streamer.is_playing(0), event_queue)
            else:
                self.value = self.get_current_val(0)
                # update the position of the knob based on the new value
                knob_x = int(((self.value - self.min_val) / range) * (self.width - self.height))
        else:
            self.value = self.get_current_val(0)
            # update the position of the knob based on the new value
            knob_x = int(((self.value - self.min_val) / range) * (self.width - self.height))
  
        # redraw the knob with its new position
        knobRect = pygame.Rect(knob_x, 0, self.height, self.height)
        pygame.draw.rect(self.sliderSurface, self.fillColors['knob'], knobRect)

        screen.blit(self.sliderSurface, self.sliderRect)
        screen.blit(self.leftLabelSurface, self.leftLabelRect)
        screen.blit(self.rightLabelSurface, self.rightLabelRect)


def initUI():
    pygame.init()

    streamer = LocalMusicStreamer()
    streamer.init()

    title = streamer.get_title(0)
    songTitleSurface = pygame.font.SysFont('Arial', 40).render(title, True, (255, 255, 255))
    songTitleRect = songTitleSurface.get_rect()
    songTitleRect.x = (UIConfig.SCREEN_WIDTH / 2) - (songTitleRect.width / 2)
    songTitleRect.y = 0

    PlayButton(120, 190, 400, 100, playButtonTapped)
    SeekSlider(0, 410, 640, 50, 0, streamer.get_total_time(0), streamer.get_current_time, stringify_time, didSeekTo)
    SeekSlider((UIConfig.SCREEN_WIDTH / 2) - (300 / 2), 100, 300, 50, 0, 100, (lambda _: 50), stringify_volume, (lambda _1, _2, _3, _4: 0))

    while True:
        screen.fill((0, 0, 0))
        screen.blit(songTitleSurface, songTitleRect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                streamer.shutdown()
                pygame.quit()
                exit()
            else:
                streamer.event(event)
        for object in objects:
            object.process(streamer)
        pygame.display.flip()
        fpsClock.tick(UIConfig.fps)
