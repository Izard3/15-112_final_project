from cmu_graphics import *
import random, math


'''
Feature List: 
    1. Multiple screens - launch screen, info screen, and full game screen with
    music that transitions between them without restarting

    2. Block programming - right panel lets you build a Scratch-style program
    for the rover to execute autonomously

    3. BFS Pathfinding - rover navigates around obstacles, replans when new terrain
    is revealed, and guarantees all POIs are reachable on map generation

    4. Procedural Generation / Fog of War - map hidden until explored, terrain uses
    smoothed noise, rocks/craters/POIs randomly placed

    5. Rover movement animation - rotates toward movement direction, leaves a fading tire trail,
    drawn entirely with rotated polygons

    6. Other gameplay systems - battery drain/solar recharge, communication range, 
    POI scanning, and data transmission back to lander

To Grade:
    - Launch the game, build a program on the right panel, and press RUN. 
    - "Move" blocks will ask you to click a destination. Find the [!] POIs,
        scan them, then return to the white circle to transmit. Press ? for in-game help and Escape to pause/return home.
'''

'''
 - General Notes
    - This is a game about CMU's lunar rover MoonRanger! It's a super cool project that I'm so lucky to be a part of the team.
    - I got permission from my program director to create this, but it only uses open-source knowledge
    - I coded this in CS academy and only moved it to VSCode Thursday night due to efficiency concerns (meaning it was sadly coded by hand...)
    - There are a lot of magic-looking numbers, but they are actually scaling numbers always multiplying against app.width or app.height
        - I did this to prevent the game breaking with any scaling of the canvas. In the few spots I did it with AI and not by hand, I labled as such.
    - I'm pretty proud of the final outcome, and hope you enjoy looking through!
'''
'''
    Some notes about AI usage:
        - Obviously, noted where each instance occured. 
        - I really did my best to make this project my own, and thus any use was of perfecting, debugging ideas I already had
        - Only real exception to that is some graphics, where it just felt very tedious so I used AI to help fix up my ideas
        - bfs was perhaps only idea that wasn't originally mine, was a combination of claude and speaking with my TA mentor Nathan
            - was still coded by hand
'''

def onAppStart(app):
    app.rows = 12
    app.cols = 12
    app.boardLeft = 0
    app.boardTop = app.height * 0.05
    app.boardWidth = app.width * 0.727
    app.boardHeight = app.height * 0.95
    app.cellWidth = app.boardWidth/app.cols
    app.cellHeight = app.boardHeight/app.rows
    app.cellBorderWidth = 0
    app.stepsPerSecond = 20
    app.moveSpeed = 5
    app.maxBattery = 100
    app.solarRate = 0.1 #rate always refers to battery drain
    app.driveRate = 1.5
    app.autoShowInstructions = True
    app.commRange = 5
    app.allBlocks = [
    MoveBlock,
    SeekPOIBlock,
    ScanPOIBlock,
    WaitBatteryBlock,
    RTLBlock,
    ClearBlock
    ]
    app.maxProgramLen = 8
    #used chatGPT + gemini to pixelate the image from the internet and put title
    app.urlBackground = 'background.png'
    #used chatGPT to make background black
    app.urlLogo = 'logo.png'
    app.startSong = Sound('start_song.mp3')
    app.gameplaySong = Sound('gameplay_song.mp3') #this is from my favorite childhood roblox game
    app.gameplaySongPlaying = False
    app.startSongPlaying = False #don't want it to restart on info screen
    resetGame(app)
    
def resetGame(app):
    app.found = set()
    app.scanned = set()
    app.currRow, app.currCol = 0,0
    app.showTargets = False
    app.targetRow, app.targetCol = 0,0
    getObstacles(app)
    getPOIs(app)
    app.path = []
    app.autonomy = False
    app.scanning = False
    app.scanProgress, app.toScan = 0, 16 #progress bar steps
    app.lander = (0,0)
    app.battery = 100
    app.gameOver = False
    app.success = False
    app.transmitted = set()
    app.pendingTransmit = set()
    app.allScanned = False
    app.transmitProgress = 0
    app.program = []
    app.programIndex = 0
    app.pixelX, app.pixelY = getCellCenter(app, app.currRow, app.currCol)
    app.destPixelX, app.destPixelY = app.pixelX, app.pixelY
    app.selectingTarget = False
    app.showSlider = False
    app.sliderValue = 50
    app.prevFoundSize = 0
    app.roverAngle = 0
    app.paused = False
    app.showInstructions = True if app.autoShowInstructions else False
    app.trail = []
    getNoise(app)
                                #west berlin
#----------------------------------------------------------------------------
                                #east berlin
                                
    
def initial_redrawAll(app):
    drawImage(app.urlBackground,0,0 ,width = app.width, height = app.height)
    x0,y0 = app.width/4-28, app.height/2+10
    width0, height0 = 200, 50
    drawRect(x0-width0/2, y0-height0/2, width0, height0, fill = rgb(30,60,100),
                opacity = 90, border = rgb(100,160,220), borderWidth = 2)
    drawLabel('▶ Launch Mission', x0, y0, size = 16, fill = 'white', bold = True, font = 'segoe ui symbol')
    width1, height1 = 175, 40
    x1, y1 =  app.width/4-40, app.height/2 + 10 + height0/2 + height1/2 + 8
    drawRect(x1 - width1 / 2, y1-height1/2, width1, height1, 
            fill = rgb(30,60,100),opacity = 90, 
            border = rgb(100,160,220), borderWidth = 2)
    drawLabel('Learn More about Moonranger', x1, y1, fill = 'white', 
                bold=True, size = 11, font = 'segoe ui symbol')
    drawLabel('WVF', 20, app.height-10,font = 'montserrat', fill = 'white',
                bold=True, size = 13)
    
def initial_onScreenActivate(app):
    if app.gameplaySongPlaying:
        app.gameplaySong.pause()
    if not app.startSongPlaying:
        app.startSong.play(restart=True, loop = True)
        app.startSongPlaying = True
    
def initial_onMousePress(app, mouseX, mouseY):
    x0,y0 = app.width/4-28, app.height/2+10
    width0, height0 = 200, 50
    x1, y1 =  app.width/4-40, app.height/2 + 60
    width1, height1 = 175, 40
    if (x0-width0/2 <= mouseX <= x0 + width0/2 and
        y0 - height0/2 <= mouseY <= y0 + height0/2): 
            setActiveScreen('game')
    elif (x1-width1/2 <= mouseX <= x1 + width1/2 and
        y1 - height1/2 <= mouseY <= y1 + height1/2): 
            setActiveScreen('info')

                                #North Korea
#---------------------------------------------------------------- ----------
                                #DMZ                             𖨆
#----------------------------------------------------------------  ----------
                               #South Korea
                               
def info_redrawAll(app):
    drawRect(0,0,app.width, app.height, fill = 'black')
    drawRect(0,0,app.width,app.height*0.12,fill=rgb(20,40,80))
    drawLabel('ABOUT MOONRANGER', app.width/2, app.height*0.06, fill = 'white', 
                bold=True,size=0.03 * app.width)
    drawRect(8, app.height*0.02, 60, app.height*0.07, fill=rgb(30,60,100),
                border=rgb(100,160,220), borderWidth=1)
    drawLabel('Back', 38, app.height * 0.055, fill = 'white',
                size=11,bold = True)
    imageSize = min(app.width/2-25, app.height/2-25)
    drawImage(app.urlLogo, app.width-imageSize, app.height*0.14,
                width=imageSize, height = imageSize)
    x, y = 18, 90
    text = [
        'MoonRanger is a small robotic autonomous rover ', 
        'designed to explore the surface of the Moon. ',
        'Developed by Carnegie Mellon University, the ',
        'NASA-contracted mission will focus on testing ',
        'new low-cost ways to explore planetary surfaces.',
        '',
        "The rover is planned to land near the Moon's south",
        'polar region in an effort to search for water frozen on ',
        'the lunar surface. These icy resources could be ',
        'important for future astronauts and long-term lunar bases.',
        '',
        'MoonRanger is built to drive autonomously, meaning it can navigate',
        'with little to no human control. Using cameras, sensors, and onboard',
        'CMU-developed software, it can avoid hazards, map terrain, and',
        'investigate scientific points-of-interest.',
        '',
        "Slated to launch in summer of 2029, this mission will be CMU's second",
        'attempt at the Moon, after the lander carrying the Iris rover failed',
        'after launch. MoonRanger aims to become the first university-built',
        'rover to successfully operate on the Moon, marking a major milestone',
        "for Carnegie Mellon's role in space exploration."
        ]
    for line in text:
        if line =='':
            y += 0.015 * app.width
        else:
            drawLabel(line,x,y,align='left',fill='white',size = 0.025*app.width, 
                        bold=True)
        y += 0.025 * app.width

def info_onMousePress(app,mouseX,mouseY):
    if (8 <= mouseX <= 68 and app.height*0.02 <= mouseY <= app.height*0.02 
        + app.height*0.07):
        setActiveScreen('initial')
    

#----------------------------------------------------------------------------

def game_onScreenActivate(app):
    if app.startSongPlaying:
        app.startSong.pause()
    app.startSongPlaying = False
    app.gameplaySongPlaying = True
    app.gameplaySong.play(restart=True, loop = True)

def gameOver(app):
    app.gameOver = True
    app.path = []
    app.scanning = False
    app.autoShowInstructions = False

def getObstacles(app):
    app.obstacles = set()
    app.obstacleTypes = dict()
    for row in range(app.rows):
        for col in range(app.cols):
            if random.random() < 0.22: #22% chance of being a rock
                if (row,col) != (app.currRow, app.currCol):
                    app.obstacles.add((row,col))
                    app.obstacleTypes[(row,col)] = random.choice(['rock','crater'])
def getPOIs(app):
    app.POIs = set()
    for row in range(app.rows):
        for col in range(app.cols):
            if random.random() < 0.01: #3% chance of being a POI
                if ((row,col) != (app.currRow, app.currCol) and 
                    (row,col) not in app.obstacles):
                        app.POIs.add((row,col))
    #reset only if not reachable
    #fixed infinite recursion 
    if not allPOIsReachable(app): 
        getObstacles(app)
        getPOIs(app)
    if app.POIs == set(): getPOIs(app)
    
def allPOIsReachable(app):
    for (row,col) in app.POIs:
        app.targetRow, app.targetCol = row,col
        if bfsPath(app, checkFullMap = True) == []:
            return False
    return True
    
    
def getNoise(app):
    '''I passed this into claude with a general 'how can i make it better' 
        it gave me the idea for smooth which i like
        it's basically acting like a global average 
        (or at least that's how I think of it)
    '''
    app.tileNoise = dict()
    for row in range(app.rows):
        for col in range(app.cols):
            noise = random.randint(-8,8)
            neighbors = 0
            total = 0
            for drow in [-1, 0, +1]:
                for dcol in [-1,0,+1]:
                    r, c = row + drow, col + dcol
                    if 0 <= r < app.rows and 0 <= c < app.cols:
                        neighbors +=1
                        total += random.randint(-5,5)
            smooth = total // neighbors
            app.tileNoise[(row,col)] = noise + smooth

#it's oop time
class MoveBlock:
    def __init__(self, row, col):
        self.row = row
        self.col = col

class RTLBlock:
    #how strange it is
    pass

class ScanPOIBlock:
    #to be anything
    pass

class SeekPOIBlock:
    #at all
    pass

class ClearBlock:
    pass

class WaitBatteryBlock:
    def __init__(self, battLevel):
        self.battLevel = battLevel

def game_redrawAll(app):
    drawProgramBlocks(app)
    barHeight = app.height * 0.05
    drawRect(0,0,app.width, barHeight, fill = rgb(200,200,200))
    drawBoard(app)
    if app.showTargets:
        drawTargets(app)
    drawPath(app)
    drawRover(app)
    drawBoardBorder(app)
    drawLabel('Press R to Reset', 50,barHeight/2)
    drawLabel(f'To Scan: {len(app.POIs)}', app.width/2 -75, barHeight/2)
    drawLabel(f'To Transmit: {len(app.pendingTransmit)}', app.width/2, 
                barHeight/2)
    if app.selectingTarget:
        drawLabel('Press to select target, Esc to cancel', app.boardWidth/2, 
                app.boardTop + app.height/2, fill = 'white', size=15, 
                bold = True)
    if app.scanning: drawProgressBar(app)
    drawBatteryBar(app)
    if app.gameOver: drawGameOver(app)
    drawCommRange(app)
    if not inCommRange(app):
        drawLabel('OUT OF RANGE', app.boardWidth/2, app.boardTop + 15, 
                    fill = 'red',size = 14, bold = True)
    elif len(app.pendingTransmit) >0:
        drawLabel(f'Transmitting {len(app.pendingTransmit)} samples...',
                    app.boardWidth/2, app.boardTop + 15, fill = 'lightGreen', 
                    size=11)
    if inCommRange(app) and len(app.pendingTransmit) > 0: drawTransmitBar(app)
    if app.showSlider: drawSlider(app)
    if app.paused: drawPauseScreen(app)
    drawInstructionsButton(app)
    if app.showInstructions:
        drawInstructions(app)
        
def drawInstructionsButton(app):
    buttonSize = app.height * 0.05 * 0.72
    buttonY = (app.height * 0.05 - buttonSize) /2
    drawRect(app.width/2+50, buttonY, buttonSize, buttonSize, 
            fill = rgb(30,60,100), border = rgb(100,160,220), borderWidth=1)
    drawLabel('?', app.width/2+50+buttonSize/2,app.height*0.025,
                fill='white',bold=True,size=12)
    
def drawInstructions(app):
    width, height = 420, 320
    x,y = app.width/2-width/2, app.height/2 - height/2
    drawRect(x,y,width,height,fill=rgb(138,167,194),border=rgb(100,160,220),
                borderWidth=2)
    drawRect(x,y,width,30,fill=rgb(30,60,100))
    drawLabel('HOW TO PLAY', app.width/2, y+15, fill='white',bold=True,size=14)
    drawRect(x+width-25,y+3,22,22,fill=rgb(100,30,30),border=rgb(200,80,80),
                borderWidth=1)
    drawLabel('X', x+width-14,y+14,fill='white',bold=True,size=12)
    text=[
        ('GOAL', 'Scan all POIs [!] and transmit data back to the lander.'),
        ('BLOCKS','Click blocks on the right panel to build a program.'),
        ('Move','Click a grid cell to set a destination.'),
        ('Seek POI','Nagivate to the nearest discovered POI.'),
        ('Scan POI','Scan the POI at current position.'),
        ('Wait Batt.','Wait until battery recharges to certain level.'),
        ('RTL','Returns to lander (starting position)'),
        ('Delete [key]', 'Press the delete key to remove last block.'),
        ('Clear Prgm', 'Clears the current program list.'),
        ('RUN/STOP', 'Press the green button for rover to execute program.'),
        ('BATTERY','Driving costs battery. Solar charges it slowly.'),
        ('COMMS','Stay in white circle to program rover and transmit data.'),
        ('PAUSE', 'Press escape key to pause and return to home screen.')
        ]
    shift = y+45
    for (label, description) in text:
        indent = 0
        if label in ['Move', 'Scan POI','Seek POI','RTL', 
                    'Wait Batt.', 'Delete [key]', 'RUN/STOP', 'Clear Prgm']:
                            indent = 40
        drawLabel(label + ':',x+15 + indent,shift,align = 'left', fill='white',
                    bold=True,size=11)
        drawLabel(description, x+85 + indent,shift,align='left',fill='white',
                size=11,bold=True)
        shift +=22
    
    
def drawPauseScreen(app):
    drawRect(0,0,app.width,app.height,fill='black',opacity=75)
    drawLabel('PAUSED', app.width/2,app.height/2-50,fill='white',size=36,
                bold=True)
    drawRect(app.width/2-80,app.height/2-20,160,40,fill=rgb(30,60,100),
                border=rgb(100,160,220),borderWidth=2)
    drawLabel('Resume',app.width/2,app.height/2,fill='white',bold=True,
                size=14)
    drawRect(app.width/2-80,app.height/2-20+40+8,160,40,fill=rgb(30,60,100),
                border=rgb(100,160,220),borderWidth=2)
    drawLabel('Return to Home', app.width/2, app.height/2-20+40+8 + 20, 
                fill='white',bold = True, size = 14)
    
    
def drawSlider(app):
    width = app.boardWidth * 0.6
    x = app.boardLeft + app.boardWidth/2 - width/2
    y = app.boardTop + app.boardHeight/2
    drawRect(x-10, y-35, width + 20, 65, fill = 'black', border = 'white')
    drawLabel('Wait until battery is at least:', x+width/2,y-22, fill ='white', 
            size = 12, bold = True)
    drawLine(x,y,x+width,y,fill='gray', lineWidth=3)
    lineX = x + (app.sliderValue/100)*width
    drawLine(lineX, y+10, lineX, y -10, fill = 'white', lineWidth= 3)
    drawLabel(f'{app.sliderValue}%', x+width/2, y+15, fill = 'white', 
                size = 11, bold = True)
    drawLabel('Arrow keys to adjust, Enter to confirm, Esc to cancel', 
            x+width/2,y+45, fill = 'white',size = 13, bold = True)
    
def drawRover(app):
    #this was debuged using AI out of laziness, I hate drawing graphics
    #but all core concepts were mine i just kept defining wrong variables
    #except for the first loop right below!
    for i in range(len(app.trail) -1):
        x0,y0,a0  = app.trail[i]
        x1,y1,a1 = app.trail[i+1]
        opacity = (i / len(app.trail)) * 50
        for side in [-1,1]:
            #did have claude help debug this next line actually...
            ox, oy = math.cos(a0)*side*app.cellWidth*0.18, math.sin(a0)*side*app.cellWidth*0.18
            drawLine(x0+ox, y0+oy, x1+ox, y1+oy, fill=rgb(89,86,80), opacity=opacity, lineWidth=2)
    cx, cy = app.pixelX, app.pixelY
    cw, ch = app.cellWidth, app.cellHeight
    a = app.roverAngle
    bodyWidth = cw * 0.6
    bodyHeight = ch * 0.61
    wheelWidth = cw * 0.15
    wheelHeight = ch * 0.22
    for sx in [-1, +1]:
        for sy in [-1, +1]:
            wx = sx * (bodyWidth/2 +wheelWidth/2-1)
            wy = sy * (bodyHeight/2 - wheelHeight/2)
            rotateRect(cx,cy,wx,wy,wheelWidth,wheelHeight,a,fill=rgb(50,50,50),
                        border = rgb(30,30,30), borderWidth=0.5)
    rotateRect(cx,cy,0,0,bodyWidth,bodyHeight,a,
                rgb(220,185,20), rgb(150,120,10), 1)
    rotateRect(cx,cy,0,0,bodyWidth-6, bodyHeight-6, a, rgb(65,68,75), None, 0)
    rotateRect(cx,cy, -(bodyWidth/2+1.5), 0,3,bodyHeight, a, 
                fill = rgb(50,80,140), border=rgb(30,50,100), borderWidth=0.5)
    ax, ay = rotatePoint(cx,cy,0,bodyHeight/2 -4, a)
    drawCircle(ax,ay,2,fill = 'white')
    
def rotatePoint(cx,cy,ox,oy,a):
    rx = ox * math.cos(a) - oy * math.sin(a)
    ry = ox * math.sin(a) + oy * math.cos(a)
    return cx + rx, cy + ry
    
def rotateRect(cx,cy,ox,oy,w,h,a,fill,border,borderWidth):
    #claude helped me debug this heavily as I had a lot of wrong values the first time
    corners = [(-w/2, -h/2), (w/2,-h/2), (w/2,h/2),(-w/2,h/2)]
    pts = []
    for (px,py) in corners:
        rx = (ox+px)*math.cos(a)-(oy+py)*math.sin(a)
        ry = (ox+px)*math.sin(a) + (oy+py)*math.cos(a)
        pts += [cx+rx, cy+ry]
    drawPolygon(*pts, fill = fill, border = border, borderWidth = borderWidth)
    
def drawPath(app):
    if not app.autonomy or len(app.path) ==0: return
    points = [(app.pixelX, app.pixelY)] #start from rover cords
    for (row,col) in app.path:
        x,y = getCellCenter(app,row,col)
        points.append((x,y))
    for i in range(len(points)-1):
        x1, y1 = points[i] 
        x2, y2 = points[i+1]
        drawLine(x1,y1,x2,y2, fill = 'white', opacity = 50, lineWidth = 1.5,
                dashes = True)
  
def getProgramBlockNames(app, block):
    if block == MoveBlock:
        name = 'Move to X Position'
    elif block == RTLBlock:
        name = 'Return to Lander'
    elif block == ScanPOIBlock:
        name = 'Scan POI'
    elif block == SeekPOIBlock:
        name = 'Seek POI'
    elif block == ClearBlock:
        name = 'Clear Program'
    elif block == WaitBatteryBlock:
        name = 'Wait for X Batt. Level'
    return name
    
def drawProgramBlocks(app):
    drawRect(app.boardWidth, 0, app.width-app.boardWidth, 
                app.height, fill = rgb(45,50,55))
    width, height = (app.width-app.boardWidth)*0.83, app.height*0.05
    x, y = app.boardWidth + (app.width-app.boardWidth)/2, app.height*0.125
    for i in range(len(app.allBlocks)):
        name = getProgramBlockNames(app,app.allBlocks[i])
        color = getBlockColor(app.allBlocks[i])
        drawRect(x-width/2, y - height/2+ app.height*0.065*i, width, height, 
                fill = color, border = rgb(200,200,220), borderWidth = 1)
        drawLabel(name, x, y + app.height*0.065*i, 
                    fill = 'white', size = 11, bold = True)
    drawLine(app.boardWidth+(app.width-app.boardWidth)*0.07, app.height*0.49, 
            app.boardWidth + (app.width-app.boardWidth)*0.93, app.height*0.49, 
            fill = rgb(80,80,100), lineWidth = 1)
    drawEachBlock(app,x,y,width,height)
    drawAutonomyButton(app)

def drawEachBlock(app,x,y,width,height):
    for i in range(len(app.program)):
        block = app.program[i]
        if isinstance(block, MoveBlock):
            name = f'Move to ({block.row},{block.col})'
        elif isinstance(block, WaitBatteryBlock):
            name = f'Wait Until Batt: {block.battLevel}%'
        else: 
            name = getProgramBlockNames(app, type(block))
        color = getBlockColor(type(block))
        isActive = (i == app.programIndex and app.autonomy)
        drawScratchBlocks(x-width/2, app.height*0.51+i*app.height*0.045, width, 
                    app.height*0.045, color, 'white' if isActive 
                    else rgb(200,200,200), 2 if isActive else 0.5)
        drawLabel(name,x, app.height*0.531+i*app.height*0.045, 
                    fill = 'white', size = 10, bold = True)

def drawScratchBlocks(x,y,width, height, color, border, borderWidth):
    '''
    i hate this function 
    I tried to do the polygon for half an hour
    I rage quit came back later and had claude finish it
    generally my code though claude just rearanged what I kept messing up
    '''
    notchDepth = 4
    notchBumpStart = x + 10
    notchBumpEnd = x + 28
    drawPolygon(x,y,notchBumpStart, y, notchBumpStart, y + notchDepth,
                notchBumpEnd, y + notchDepth, notchBumpEnd, y, x + width,
                y, x + width, y + height, notchBumpEnd, y + height,
                notchBumpEnd, y + height + notchDepth, notchBumpStart, 
                y + height + notchDepth, notchBumpStart, y + height, 
                x, y + height, fill = color, border = border, 
                borderWidth = borderWidth)

def getBlockColor(blockType):
    if blockType == MoveBlock: return rgb(50,100,180)
    elif blockType == SeekPOIBlock: return rgb(180, 100, 30)
    elif blockType == ScanPOIBlock: return rgb(40,140,60)
    elif blockType == RTLBlock: return rgb(130, 80, 30)
    elif blockType == ClearBlock: return rgb(150, 35, 35)
    elif blockType == WaitBatteryBlock: return rgb(180, 160, 20)
    return 'gray'
    
    
def drawAutonomyButton(app):
    x,y = app.boardWidth + (app.width-app.boardWidth)/2, app.height*0.94
    width, height = (app.width-app.boardWidth)*0.83, app.height*0.075
    color = 'darkGreen' if not app.autonomy else 'darkRed'
    if not inCommRange(app): color = 'gray'
    label =  ' RUN' if not app.autonomy else ' STOP'
    symbol = '▶' if not app.autonomy else '■'
    label = symbol + label
    drawRect(x-width/2, y- height/2, width, height, fill = color, 
            border = 'white', borderWidth = 1)
    drawLabel(label, x, y, fill = 'white', bold = True, size =13, font = 'segoe ui symbol')
    
def drawCommRange(app):
    cellWidth, cellHeight = app.cellWidth, app.cellHeight
    cx = app.boardLeft + app.lander[1] * cellWidth + cellWidth /2
    cy = app.boardTop + app.lander[0] * cellHeight + cellHeight/2
    r = app.commRange * cellWidth
    drawCircle(cx, cy, r, fill = None, border = 'white', opacity = 40, 
                borderWidth = 1)

def drawGameOver(app):
    drawRect(0,0, app.width, app.height, fill='black', opacity = 70)
    if app.success:
        drawLabel('MISSION COMPLETE', app.width/2, app.height/2 -3, 
                    fill = 'lightGreen', size = 30, bold = True)
        drawLabel(f'Samples transmitted: {len(app.transmitted)}', 
                app.width/2, app.height/2+20,fill = 'white', size = 16)
    else:
        drawLabel('MISSION FAILED', app.width/2, app.height/2-3, fill = 'red',
                    size = 30, bold = True)
    drawLabel('Press R to launch again', app.width/2, app.height/2+40, 
                fill = 'white', size = 14)

def drawBatteryBar(app):
    barWidth, barHeight = 98, 15.5
    barLeft = app.width - barWidth - 8
    barTop = (app.height * 0.05 - 15.5)/2
    percent = app.battery / app.maxBattery
    if percent > 0.5: barColor = 'green'
    elif percent > 0.2: barColor = 'yellow'
    else: barColor = 'red'
    drawRect(barLeft, barTop, barWidth, barHeight, fill = rgb(200,200,200))
    if percent > 0:
        drawRect(barLeft, barTop, barWidth * percent, barHeight, 
                fill = barColor)
    drawRect(barLeft, barTop, barWidth, barHeight, fill = None, 
            border='darkGray', borderWidth = 1)
    drawLabel('Battery:', barLeft -24, barTop + barHeight/2, fill = 'black')
    drawLabel(f'{int(percent*100)}%', barLeft+43, barTop + barHeight/2, 
                fill = 'black', size = 11)

def drawProgressBar(app):
    barWidth = 150
    barLeft = app.width/2 - barWidth/2
    barHeight = 12
    barTop = app.boardTop + app.boardHeight/2 - barHeight/2
    progress = app.scanProgress / app.toScan
    drawRect(barLeft, barTop, barWidth, barHeight, fill = 'darkGray')
    if progress > 0:
        drawRect(barLeft, barTop, barWidth * progress, barHeight, 
                fill = 'lightGreen')
    drawRect(barLeft, barTop, barWidth, barHeight, fill = None, border='black')
    drawLabel('Scanning...', app.width/2, barTop - 10, fill = 'white')
    
def drawTransmitBar(app):
    if app.battery ==0: return
    total = len(app.transmitted) + len(app.pendingTransmit)
    if total == 0: return
    barWidth = 150
    barLeft = app.width/2 - barWidth/2
    barHeight = 12
    barTop = app.boardTop + app.boardHeight/2 + 10
    progress = app.transmitProgress / app.toScan
    drawRect(barLeft, barTop, barWidth, barHeight, fill = 'darkGray')
    if progress > 0:
        drawRect(barLeft, barTop, barWidth * progress, barHeight, fill ='cyan')
    drawRect(barLeft, barTop, barWidth, barHeight, fill = None, border='black')
    drawLabel(f'Transmitted: {len(app.transmitted)}/{total}', app.width/2,
                barTop + barHeight + 10, fill = 'white', size = 11)

def getCellCenter(app,row,col):
    cellWidth, cellHeight = app.cellWidth, app.cellHeight
    x = app.boardLeft + col * cellWidth + cellWidth/2
    y = app.boardTop + row * cellHeight + cellHeight/2
    return x,y

def drawBoard(app):
    for row in range(app.rows):
        for col in range(app.cols):
            drawCell(app, row, col)

def drawBoardBorder(app):
  drawRect(app.boardLeft, app.boardTop, app.boardWidth, app.boardHeight,
           fill=None, border='black',
            borderWidth= 2*app.cellBorderWidth)

def drawCell(app, row, col):
    cellLeft, cellTop = getCellLeftTop(app, row, col)
    cellWidth, cellHeight = app.cellWidth, app.cellHeight
    if (row,col) not in app.found:
        drawFogOfWar(app,row, col, cellLeft, cellTop, cellWidth, cellHeight)
        return
    if (row,col) in app.scanned: color = rgb(160, 185, 200)
    elif (row,col) in app.POIs: color= rgb(200,230,245)
    else: 
        v = app.tileNoise[(row,col)]
        color = rgb(
            max(0,min(255,140+v)),
            max(0,min(255,138 + v)),
            max(0,min(255,132+v))
        )
    drawRect(cellLeft, cellTop, cellWidth+1, cellHeight+1,fill=color, 
                border=color, borderWidth=app.cellBorderWidth)
    if (row,col) in app.obstacles: 
        drawObstacles(app, cellLeft, cellTop, cellWidth,cellHeight, app.obstacleTypes[(row,col)])
    if (row,col) in app.POIs:
        cx,cy= cellLeft + cellWidth/2, cellTop + cellHeight/2
        r = min(cellWidth,cellHeight)*0.25
        drawCircle(cx,cy,r,fill=None,border=rgb(30,80,180),borderWidth=3)
        drawLabel('!',cx,cy,fill=rgb(30,80,180),bold=True,size=20)
    if (row,col) == app.lander:
        drawLander(app, cellLeft, cellTop, cellWidth,cellHeight)
    if app.selectingTarget:
        if (((row,col) not in app.obstacles and (row,col) in app.found) or
            (row,col) not in app.found):
            drawCircle(cellLeft + cellWidth/2, cellTop + cellHeight/2, 3, 
                        fill = 'darkRed')
            
def drawObstacles(app,cellLeft,cellTop,cellWidth,cellHeight, obstacleType):
    cx, cy = cellLeft + cellWidth/2, cellTop + cellHeight/2
    s = min(cellWidth, cellHeight)
    if obstacleType == 'crater':
        drawCircle(cx+2, cy+2, s*0.38, fill=rgb(30,30,30), opacity=50)
        drawCircle(cx, cy, s*0.38, fill=rgb(55,52,50))
        drawCircle(cx+s*0.08, cy+s*0.08, s*0.22, fill=rgb(35,33,31))
    else:  
        drawCircle(cx+2, cy+2, s*0.38, fill=rgb(40,40,40), opacity=50)
        drawCircle(cx, cy, s*0.38, fill=rgb(105,101,95))
        drawCircle(cx-s*0.1, cy-s*0.1, s*0.18, fill=rgb(135,130,122))

def drawFogOfWar(app, row, col, cellLeft, cellTop, cellWidth, cellHeight):
    drawRect(cellLeft, cellTop, cellWidth+1, cellHeight+1, fill = rgb(38,36,36), 
                border=rgb(38,36,36), borderWidth=app.cellBorderWidth)
    if app.selectingTarget:
        if (((row,col) not in app.obstacles and (row,col) in app.found) or
            (row,col) not in app.found):
            drawCircle(cellLeft + cellWidth/2, cellTop + cellHeight/2, 3, 
                        fill = 'darkRed')

def drawLander(app, cellLeft, cellTop, cellWidth, cellHeight):
    #used claude to generalize values to fit all size windows
    cx, cy = cellLeft + cellWidth/2, cellTop + cellHeight/2
    s = min(cellWidth, cellHeight) * 0.5
    drawRect(cx-s*0.45, cy-s*0.35, s*0.9, s*0.65, fill=rgb(190,190,200))
    drawRect(cx-s*1.1, cy-s*0.1, s*0.55, s*0.25, fill=rgb(40,60,140))
    drawRect(cx+s*0.55, cy-s*0.1, s*0.55, s*0.25, fill=rgb(40,60,140))
    drawLine(cx-s*0.35, cy+s*0.3, cx-s*0.6, cy+s*0.7, fill='white', lineWidth=1.5)
    drawLine(cx+s*0.35, cy+s*0.3, cx+s*0.6, cy+s*0.7, fill='white', lineWidth=1.5)
    drawLine(cx, cy-s*0.35, cx, cy-s*0.8, fill='white', lineWidth=1.5)


def drawTargets(app):
    colors = ['red', 'yellow','green', 'orange', 'purple', 'salmon']
    justMoveBlocks = [(block.row, block.col) for block in app.program if isinstance(block, MoveBlock)] #bang.
    for i in range(len(app.program)):
        block = app.program[i]
        if i < app.programIndex or not isinstance(block, MoveBlock): continue
        cellLeft, cellTop = getCellLeftTop(app, block.row, block.col)
        cellWidth, cellHeight = app.cellWidth, app.cellHeight
        if isinstance(block, MoveBlock):
            cx, cy = cellLeft + cellWidth/2, cellTop + cellHeight/2
            r = min(cellWidth, cellHeight) / 2 - app.cellBorderWidth#no overhang
            offset = r / (2 ** 0.5)
            drawCircle(cx, cy, r, fill=None, border = colors[i%len(colors)])
            drawLine(cx-offset, cy - offset, cx + offset, 
                    cy+offset, fill = colors[i%len(colors)])
            drawLine(cx+offset, cy-offset, cx-offset, 
                    cy+offset, fill = colors[i%len(colors)])
            offset = -0.045 * app.width if block.row > 0 else 0.045 * app.width
            drawLabel(f'P{justMoveBlocks.index((block.row,block.col))+1}', cx, 
                        cy+(offset), size = 12, fill ='white', bold = True)
        
def getCellLeftTop(app, row, col):
    cellWidth, cellHeight = app.cellWidth, app.cellHeight
    cellLeft = app.boardLeft + col * cellWidth
    cellTop = app.boardTop + row * cellHeight
    return (cellLeft, cellTop)
    
def game_onStep(app):
    if app.paused: return
    if app.gameOver: return
    if app.battery < 1: gameOver(app)
    moveRover(app)
    revealAround(app)
    app.battery += app.solarRate
    if app.battery > app.maxBattery: app.battery = app.maxBattery
    if app.scanning:
        scan(app)
    if inCommRange(app) and len(app.pendingTransmit) > 0:
        transmit(app)
    if (app.POIs == set() and len(app.scanned) > 0):
        app.allScanned = True
    if app.allScanned and app.pendingTransmit == set() and inCommRange(app):
        gameWon(app)
    runUserProgram(app)
    if app.autonomy and app.programIndex >= len(app.program): 
        app.autonomy = False
        app.programIndex = 0
        app.showTargets = False
        app.path = []
    
def scan(app):
    if (app.currRow, app.currCol) not in app.POIs:
        app.scanning = False
        app.scanProgress = 0
    else:
        app.scanProgress +=1
        if app.scanProgress >= app.toScan:
            scanPOI(app)
            app.scanning = False
            app.scanProgress = 0
                
def transmit(app):
    app.transmitProgress +=1 
    if app.transmitProgress >= app.toScan:
        for poi in app.pendingTransmit:
            app.transmitted.add(poi)
            app.pendingTransmit = app.pendingTransmit - {poi}
            break
        app.transmitProgress = 0

def moveRover(app):
    #spoke with TA during Prof. Kosbie's OH about all this
    cellWidth, cellHeight = app.cellWidth, app.cellHeight
    pixelSpeed = app.moveSpeed * cellWidth/app.stepsPerSecond
    dx, dy = app.destPixelX - app.pixelX, app.destPixelY - app.pixelY
    distance = (dx**2 + dy**2) ** 0.5
    if distance < pixelSpeed:
        app.trail.append((app.pixelX, app.pixelY, app.roverAngle))
        if len(app.trail) > 3: app.trail.pop(0)
    if distance > 2:
        app.roverAngle = math.atan2(dy,dx) - math.pi/2
    if distance < pixelSpeed:
        app.pixelX, app.pixelY = app.destPixelX, app.destPixelY
        if app.autonomy and len(app.path) > 0: 
            app.currRow, app.currCol = app.path.pop(0)
            app.battery -= app.driveRate
            app.destPixelX, app.destPixelY = getCellCenter(app,app.currRow,app.currCol)
    elif distance > 0:
        app.pixelX += pixelSpeed * dx / distance
        app.pixelY += pixelSpeed * dy / distance
    
def runUserProgram(app):
    if app.autonomy and app.programIndex < len(app.program):
        block = app.program[app.programIndex]
        if isinstance(block, MoveBlock):
            moveBlockProgram(app, block)
        elif isinstance(block, RTLBlock):
            rtlBlockProgram(app, block)
        elif isinstance(block, ScanPOIBlock):
            scanPOIBlockProgram(app,block)
        elif isinstance(block, SeekPOIBlock):
            seekPOIBlockProgram(app,block)
        elif isinstance(block, WaitBatteryBlock):
            waitBatteryBlockProgram(app, block)
                
def moveBlockProgram(app, block):
    if (app.currRow, app.currCol) == (block.row, block.col):
        app.programIndex +=1
        app.path = []
    else:
        app.targetRow, app.targetCol = block.row, block.col
        app.showTargets = True
        if app.path == []: 
            app.path = bfsPath(app, checkFullMap = False)
            if app.path == []:
                app.programIndex += 1

def rtlBlockProgram(app, block):
    app.targetRow, app.targetCol = app.lander
    if (app.currRow, app.currCol) == app.lander:
        app.programIndex += 1
    elif app.path == []: app.path = bfsPath(app, checkFullMap = False)

def scanPOIBlockProgram(app,block):
    if (app.currRow, app.currCol) not in app.POIs:
        app.programIndex += 1
    elif not app.scanning and not app.scanProgress > 0:
        app.scanning = True
    elif not app.scanning:
        app.programIndex += 1

def seekPOIBlockProgram(app, block):
    nearest = None
    nearestDist = None
    for cell in app.found:
        if cell in app.POIs:
            d = manhattanDistance(cell[0], cell[1], app.currRow, app.currCol)
            if nearestDist == None or d < nearestDist:
                nearestDist = d
                nearest = cell
    if (nearest == None or 
        (app.currRow, app.currCol) == (nearest[0], nearest[1])):
        app.programIndex += 1
    else:
        app.targetRow, app.targetCol = nearest[0], nearest[1]
        if app.path == []:
            app.path = bfsPath(app, checkFullMap = False)
            
def waitBatteryBlockProgram(app, block):
    if app.battery >= block.battLevel:
        app.programIndex+=1

def gameWon(app):
    app.gameOver = True
    app.path = []
    app.success = True

def inCommRange(app): 
    row = app.currRow - app.lander[0]
    col = app.currCol - app.lander[1]
    return (row **2 + col ** 2) **0.5 <= app.commRange

def manhattanDistance(x0, y0, x1, y1):
    #wikipedia page for manhattan distance is very well done
    #download the wikipedia app! its local map feature is great
    #ok I had to modify it's now Chebyshev distance...
    return max(abs(x0-x1), abs(y0-y1))
    
def revealAround(app):
    for drow in [-1, 0, +1]:
        for dcol in [-1, 0, +1]:
            row, col = app.currRow + drow, app.currCol + dcol
            if 0 <= row and row < app.rows and 0 <= col and col < app.cols:
                app.found.add((row,col))
    if (app.autonomy and app.showTargets): 
        newSize = len(app.found)
        if newSize != app.prevFoundSize:
            app.prevFoundSize = newSize
            for cell in app.path:
                if cell in app.found and cell in app.obstacles:
                    app.path = bfsPath(app, checkFullMap = False)
                    break

def game_onKeyPress(app, key):
    if app.showSlider:
        if key =='enter':
            app.program.append(WaitBatteryBlock(app.sliderValue))
            app.showSlider = False
    if key == 'r': 
        app.autoShowInstructions = False
        resetGame(app)
    if app.gameOver: return
    if key == 'space' and (app.currRow, app.currCol) in app.POIs:
        app.scanning = True
    if key == 'delete':
        if len(app.program) > 0 and inCommRange(app):
            app.program.pop()
    if key == 'escape':
        if app.selectingTarget: 
            app.selectingTarget = False
            return
        if app.showSlider:
            app.showSlider = False
            return
        app.paused = not app.paused
        return
        
def game_onKeyHold(app, keys):
    if app.showSlider:
        if 'left' in keys:
            app.sliderValue = max(0, app.sliderValue - 1)
        elif 'right' in keys:
            app.sliderValue = min(100, app.sliderValue + 1)

def game_onMousePress(app, mouseX, mouseY):
    if app.showInstructions:
        x,y = app.width/2 - 210 + 420 -25, app.height/2-160+3
        if (x <= mouseX <= x+22) and (y<=mouseY<=y+22):
            app.showInstructions = False
        return
    buttonSize = app.height * 0.05 * 0.72
    buttonY = (app.height*0.05 - buttonSize) /2
    if (app.width/2+50<=mouseX<=app.width/2+50+buttonSize and 
        buttonY<=mouseY<=buttonY + buttonSize):
        app.showInstructions = not app.showInstructions
        return
    if app.paused: 
        pressesOnPause(app, mouseX, mouseY)
        return
    x,y = app.boardWidth + (app.width-app.boardWidth)/2, app.height*0.94
    width, height = (app.width-app.boardWidth)*0.83, app.height*0.075
    if app.gameOver or not inCommRange(app): return
    if (x-width/2 <= mouseX <= x+width/2 and y-height/2 <= mouseY<=y+height/2):
        app.autonomy = not app.autonomy
        if not app.autonomy: app.path = []
        return
    i = whichBlockIsIn(app, mouseX, mouseY)
    if len(app.program) < app.maxProgramLen:
        addBlockProgram(app,i, mouseX, mouseY)
        
        
def addBlockProgram(app,i, mouseX, mouseY):
    if   i == 0: selectTarget(app)
    elif i == 1: app.program.append(SeekPOIBlock())
    elif i == 2: app.program.append(ScanPOIBlock())
    elif i == 3: getUserBattLevel(app)
    elif i == 4: app.program.append(RTLBlock())
    if   i == 5: 
        app.program = []
        app.path = []
    if   i == None and app.selectingTarget:
        selectMoveSquare(app,mouseX,mouseY)


def selectMoveSquare(app,mouseX,mouseY):
    app.showTargets = True
    app.selectingTarget = False
    col = int((mouseX - app.boardLeft)/(app.boardWidth / app.cols))
    row = int((mouseY - app.boardTop) / (app.boardHeight / app.rows))
    if (0 <= row and row < app.rows and 0 <= col and col < app.cols
        and not ((row,col) in app.found and (row,col) in app.obstacles)):
        app.targetRow  = row
        app.targetCol = col
        app.program.append(MoveBlock(row,col))
            
def pressesOnPause(app, mouseX, mouseY):
    if ((app.width/2-80 <= mouseX <= app.width/2 + 80) and 
            (app.height/2 - 20 <= mouseY <= app.height/2+20)):
                app.paused = False
    elif ((app.width/2 - 80 <= mouseX <= app.width/2 + 80) and
            (app.height/2 + 35 <= mouseY <= app.height/2 + 75)):
                app.paused = False
                resetGame(app)
                setActiveScreen('initial')
        
def getUserBattLevel(app):
    app.showSlider = True
    app.sliderValue = 50
        
def selectTarget(app):
    app.selectingTarget = True
    app.showTargets = True

def whichBlockIsIn(app, mouseX, mouseY):
    width, height = (app.width-app.boardWidth)*0.83, app.height*0.05 
    x, y = app.boardWidth + (app.width-app.boardWidth)/2, app.height*0.125
    for i in range(len(app.allBlocks)):
        if (mouseX >= (x-width/2) and mouseX <= (x-width/2 + width) and
            mouseY >= (y - height/2 + app.height*0.065*i)
            and mouseY <= (y - height/2 + app.height*0.065*i)+height): 
                return i
    return None
    
    
    #Nathan (TA) told me i can use bfs to check full map
def bfsPath(app, checkFullMap):
    '''
    claude told me to use bfs and then I gave it the prompt:
    "give me a list of things the function needs to do and maybe some hints
    so i can code it myself", thus the function below is my own work
    i also looked up what bfs is to help. 
    Took a few variations to get where we are now
    i also modified the base bfs quite a bit to have a checkFullMap case
    '''
    queue = [(app.currRow, app.currCol)]
    visited = {(app.currRow, app.currCol)}
    cameFrom = dict()
    while len(queue) > 0:
        curr = queue.pop(0)
        if curr == (app.targetRow, app.targetCol):
            path = []
            cell = (app.targetRow, app.targetCol)
            while cell != (app.currRow, app.currCol):
                path.append(cell)
                cell = cameFrom[cell]
            path = path[::-1]
            return path
        (row,col) = curr
        nextTo = [(row+1, col), (row-1, col), (row, col+1), (row, col-1),
                    (row+1, col+1), (row+1, col-1),(row-1,col+1),(row-1,col-1)]
                    #^diagonals
        for space in nextTo:
            (nextRow, nextCol) = space
            drow, dcol = nextRow - row, nextCol - col
            isDiagonal = (drow != 0 and dcol != 0)
            cornerBlocked = (isDiagonal and (row+drow,col) in app.obstacles
                            and (row,col+dcol) in app.obstacles)
            if checkFullMap:
                if (0 <= nextCol and nextCol < app.cols and 0 <= nextRow and
                nextRow < app.rows and space not in visited and not 
                (space in app.obstacles) and not
                cornerBlocked):
                    visited.add(space)
                    queue.append(space)
                    cameFrom[space] = curr
            else:
                if (0 <= nextCol and nextCol < app.cols and 0 <= nextRow and
                    nextRow < app.rows and space not in visited and not 
                    (space in app.found and space in app.obstacles) and not
                    cornerBlocked):
                        visited.add(space)
                        queue.append(space)
                        cameFrom[space] = curr
    return []
    
def scanPOI(app):
    app.scanned.add((app.currRow, app.currCol))
    app.POIs.remove((app.currRow, app.currCol))
    app.pendingTransmit.add((app.currRow, app.currCol))
    
def main():
    runAppWithScreens('initial', 700, 500)

main()
