# callbacks.py
# in synfony

from synfony.enums import EventCode


def playButtonTapped(eventQueue, didPlay):
    if didPlay:
        print('Play Pressed')
        eventQueue.append(EventCode.PLAY)
    else:
        print('Pause Pressed')
        eventQueue.append(EventCode.PAUSE)
    return eventQueue

def didSeekTo(position, eventQueue):
    print('Did seek to: ' + str(position))
    eventQueue.append(EventCode.SEEK)
    return eventQueue
