from cmu_graphics import *

def onAppStart(app):
    print('trying to load sound...')
    app.song = Sound('gameplay_song.wav')
    print(f'result: {app.song}')


def redrawAll(app):
    pass

def onKeyPress(app,key):
    if key =='s':
        app.song.play()
    if key =='p':
        app.song.pause()

runApp(width=400, height=300)