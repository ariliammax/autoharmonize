# main.py
# in synfony

from argparse import ArgumentParser, Namespace
from multiprocessing import Process
from socket import AF_INET, SOCK_STREAM, socket
from synfony.config import Config
from threading import Thread
from time import sleep
from typing import List, Tuple

import pygame

objects = []

fps = 60
fpsClock = pygame.time.Clock()
width, height = 640, 480
screen = pygame.display.set_mode((width, height))

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
                      print(self.isSelected)
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
  
      # calculate the position of the knob based on the value
      range = self.max_val - self.min_val
      knob_x = int(((self.value - self.min_val) / range) * (self.width - self.height))
  
      # draw the bar
      barRect = pygame.Rect(self.height / 2, self.height / 2 - 2, self.width - self.height, 4)
      pygame.draw.rect(self.sliderSurface, self.fillColors['bar'], barRect)
  
      # draw the knob
      knobRect = pygame.Rect(knob_x, 0, self.height, self.height)
      pygame.draw.rect(self.sliderSurface, self.fillColors['knob'], knobRect)
  
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
  
      # blit the slider to the screen
      screen.blit(self.sliderSurface, self.sliderRect)
        
    
def playButtonTapped():
    print('Button Pressed')

def didSeekTo(position):
    print('Did seek to: ' + str(position))


def make_parser():
    """Makes a parser for command line arguments (i.e. machine addresses).
    """
    parser = ArgumentParser()
    parser.add_argument('--idx',
                        required=False,
                        type=int)
    parser.add_argument('--machines',
                        default=Config.MACHINES,
                        required=False,
                        type=list)
    parser.add_argument('--multiprocess',
                        action='store_true',
                        default=False,
                        required=False)
    return parser


def parse_args():
    """Parse the command line arguments (i.e. host and port).

        Returns: an `argparse.Namespace` (filtering out `None` values).
    """
    parser = make_parser()
    return Namespace(**{k: (v if k != 'machines' else [(vv.split(':')[0],
                                                        int(vv.split(':')[1]))
                                                       for vv in v])
                        for k, v in parser.parse_args().__dict__.items()
                        if v is not None})


def accept_clients(other_machine_addresses, s: socket):
    """Called when the initial handshake between two machines begins.
    """
    for _ in other_machine_addresses:
        connection, _ = s.accept()
        Thread(target=listen_client, args=(connection,)).start()


def listen_client(connection):
    """For continued listening on a client.
    """
    while True:
        _ = connection.recv(Config.INT_LEN)


def handler(e, s: socket):
    """Handle any errors that come up.
    """
    s.close()
    if e is not None:
        raise e


def main(idx: int, machines: List[str]):
    """Start the connections and what not.
    """
    s = socket(AF_INET, SOCK_STREAM)
    try:
        machine_address = machines[idx]
        other_machine_addresses = machines[idx + 1:] + machines[:idx]
        s.bind(machine_address)
        s.listen()
        s.settimeout(None)
        sleep(Config.TIMEOUT)
        Thread(target=accept_clients,
               args=(other_machine_addresses, s)).start()
        sleep(Config.TIMEOUT)
        other_sockets = []
        for other_machine_address in other_machine_addresses:
            other_socket = socket(AF_INET, SOCK_STREAM)
            other_socket.settimeout(None)
            other_socket.connect(other_machine_address)
            other_sockets.append(other_socket)

        # UI
        pygame.init()

        Button(120, 190, 400, 100, 'Play', 'Pause', playButtonTapped)
        SeekSlider(0, 410, 640, 50, 0, 100, 50, didSeekTo)

        while True:
            screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
            for object in objects:
                object.process()
            pygame.display.flip()
            fpsClock.tick(fps)

    except Exception as e:
        handler(e=e, s=s)
    finally:
        handler(e=None, s=s)


if __name__ == '__main__':
    args = parse_args()
    if args.multiprocess:
        for idx in range(3):
            p = Process(
                target=main,
                args=(idx, args.machines)
            )
            p.start()
        while True:
            pass
    else:
        main(**args.__dict__)
