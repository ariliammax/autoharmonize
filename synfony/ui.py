from synfony.config import UIConfig
from synfony.callbacks import *

import pygame

screen = pygame.display.set_mode((UIConfig.SCREEN_WIDTH, UIConfig.SCREEN_HEIGHT))
fpsClock = pygame.time.Clock()
objects = []

audio_duration = 105

def stringify_time(time):
  minutes = int(time // 60)
  seconds = int(time - (minutes * 60))
  if (seconds < 10):
    return str(minutes) + ":0" + str(seconds)
  else:
    return str(minutes) + ":" + str(seconds)

class Button():
    def __init__(self, x, y, width, height, text, selectedText, onclickFunction=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onclickFunction = onclickFunction
        self.alreadyPressed = False
        self.isSelected = False
        self.text = text
        self.selectedText = selectedText

        self.fillColors = {
            'normal': '#ffffff',
            'hover': '#666666',
            'pressed': '#333333',
        }
        
        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.buttonSurf = pygame.font.SysFont('Arial', 40).render(text, True, (20, 20, 20))
        objects.append(self)
        
    def process(self):
        mousePos = pygame.mouse.get_pos()
        self.buttonSurface.fill(self.fillColors['normal'])
        if self.buttonRect.collidepoint(mousePos):
            self.buttonSurface.fill(self.fillColors['hover'])
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.buttonSurface.fill(self.fillColors['pressed'])
                if not self.alreadyPressed:
                    self.isSelected = not self.isSelected
                    self.alreadyPressed = True
                    if (self.isSelected):
                      self.buttonSurf = pygame.font.SysFont('Arial', 40).render(self.selectedText, True, (20, 20, 20))
                    else:
                      self.buttonSurf = pygame.font.SysFont('Arial', 40).render(self.text, True, (20, 20, 20))
            else:
                self.alreadyPressed = False
        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width/2 - self.buttonSurf.get_rect().width/2,
            self.buttonRect.height/2 - self.buttonSurf.get_rect().height/2
        ])
        screen.blit(self.buttonSurface, self.buttonRect)
        
class SeekSlider():
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, onchangeFunction=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.onchangeFunction = onchangeFunction
        self.isDragging = False

        self.fillColors = {
            'background': '#000000',
            'bar': '#ffffff',
            'knob': '#333333',
        }

        self.sliderSurface = pygame.Surface((self.width, self.height))
        self.sliderRect = pygame.Rect(self.x, self.y, self.width, self.height)
        objects.append(self)

    def process(self):
      mousePos = pygame.mouse.get_pos()
      self.sliderSurface.fill(self.fillColors['background'])
  
      range = self.max_val - self.min_val
      knob_x = int(((self.value - self.min_val) / range) * (self.width - self.height))
  
      barRect = pygame.Rect(self.height / 2, self.height / 2 - 2, self.width - self.height, 4)
      pygame.draw.rect(self.sliderSurface, self.fillColors['bar'], barRect)

      knobRect = pygame.Rect(knob_x, 0, self.height, self.height)
      pygame.draw.rect(self.sliderSurface, self.fillColors['knob'], knobRect)

      #draw left label
      current_time = (self.value/self.max_val) * audio_duration
      self.leftLabelSurface = pygame.font.SysFont('Arial', 40).render(stringify_time(current_time), True, (255, 255, 255))
      self.leftLabelRect = self.leftLabelSurface.get_rect()
      self.leftLabelRect.x = self.x + 15
      self.leftLabelRect.y = self.y - self.height - 5
      
      #draw right label
      self.rightLabelSurface = pygame.font.SysFont('Arial', 40).render(stringify_time(audio_duration), True, (255, 255, 255))
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
                  self.onchangeFunction(self.value)
  
      # redraw the knob with its new position
      knobRect = pygame.Rect(knob_x, 0, self.height, self.height)
      pygame.draw.rect(self.sliderSurface, self.fillColors['knob'], knobRect)
  
      screen.blit(self.sliderSurface, self.sliderRect)
      screen.blit(self.leftLabelSurface, self.leftLabelRect)
      screen.blit(self.rightLabelSurface, self.rightLabelRect)
    
def initUI():
    pygame.init()

    songTitleSurface = pygame.font.SysFont('Arial', 40).render("song.mp3", True, (255, 255, 255))
    songTitleRect = songTitleSurface.get_rect()
    songTitleRect.x = (UIConfig.SCREEN_WIDTH / 2) - (songTitleRect.width / 2)
    songTitleRect.y = 0

    Button(120, 190, 400, 100, 'Play', 'Pause', playButtonTapped)
    SeekSlider(0, 410, 640, 50, 0, 100, 50, didSeekTo)

    while True:
        screen.fill((0, 0, 0))
        screen.blit(songTitleSurface, songTitleRect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        for object in objects:
            object.process()
        pygame.display.flip()
        fpsClock.tick(UIConfig.fps)