import pyglet
from pyglet.window import Window, key
from pyglet.gl import *
from math import sin, cos, radians
from random import randint, choice
from pyglet.text import Label

from chord import *

_label = Label("", font_size=8, width=80, multiline=True)
win_width, win_height = 0,0



#drawing helper functins

def drawLine(p1,p2):

   glBegin(GL_LINES)
   glVertex2f(p1[0], p1[1])
   glVertex2f(p2[0], p2[1])      
   glEnd()
   

def drawLines(points):
   glBegin(GL_LINE_STRIP)
   for p in points:
      if p:
        x,y = node_pos_on_circle(p)
        glVertex2f(x,y)
   glEnd()

def drawTriangle(pos, w, h, style=GL_TRIANGLES):
    points = [pos[0]-w/2, pos[1], pos[0]+w/2, pos[1], pos[0], pos[1]+h]
    glBegin(GL_TRIANGLES)
    while len(points):
      glVertex2f(points.pop(), points.pop())
    glEnd()

def drawRectangle(pos, w, h, style=GL_QUADS):
    points = [pos[0], pos[1], pos[0], pos[1]+h, pos[0]+w, pos[1]+h, pos[0]+w, pos[1]]
    glBegin(GL_QUADS)
    while len(points):
      glVertex2f(points.pop(), points.pop())
    glEnd()

def drawCircle(pos=(0,0), radius=1.0):
   x, y = pos[0], pos[1]
   glPushMatrix()
   glTranslated(x,y, 0)
   glScaled(radius, radius, 1.0)
   gluDisk(gluNewQuadric(), 0, 1, 16,1)
   glPopMatrix()

def drawText(text, pos=(0,0)):
    
    glPushMatrix()
    glTranslated(pos[0],pos[1],0)
    _label.text = text
    _label.draw()
    glPopMatrix()


def node_direction_on_circle(i, scale=1.0):
        size = float(2**NUM_BITS)
        x,y = cos(radians( i/size*-360+90)),sin(radians( i/size*360+90))
        return (x*scale,y*scale)

def node_pos_on_circle(i):
        x,y = node_direction_on_circle(i)
        x,y = x*win_height/3 + win_width/2, y*win_height/3 + win_height/2
        return (x,y)



def set_message_style(type):
    glLineWidth(3)
    if type == 'finger':
        glColor4f(0,1,0,.4)
    if type == 'join':
        glColor4f(0,0,1,1)
    if type == 'init':
        glColor4f(0,1,1,1)
    if type == 'lookup':
        glColor4f(1,1,0,0.4)

def drawNode(node):
    
    glPushMatrix()
    x,y = node_pos_on_circle(node.id)
    glTranslated(x,y,0)
    
    glColor4f(.8,1,.8,1)
    drawCircle(radius=10)
    
    glColor4f(1,1,1,1)
    label_pos = node_direction_on_circle(node.id, 50)
    drawLine((0,0),label_pos)
    if label_pos[0] >=0:
        glTranslated(3,0,0)
    else:
        glTranslated(-83,0,0)
    drawText(str(node), pos=label_pos)

    glPopMatrix()
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1,1,1,0.4)
    glLineWidth(1)
    for f in node.fingers:
        if f: drawLine((x,y), node_pos_on_circle(f))
          
    for m in node.messages:
            set_message_style(m.type)
            drawLines(m.route)
            if m.status == 'failed':
                glColor4f(1,0,0,0.3)    
                glLineWidth(10)
                drawLines([m.src,m.dest])


class ChordWindow(Window):

    def __init__(self):
        try:
            config = Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True,)
            super(ChordWindow, self).__init__(caption="Chord visualization", config=config, fullscreen=False)
        except:
            super(ChordWindow, self).__init__(caption="Chord visualization", fullscreen=True)
  
        self.nw = Network()
        self.nw.bootstrap(3)
        self.nw.grow(100)
        
        pyglet.clock.schedule(self.update)
    
    
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            pyglet.app.exit()
        if symbol == key.A:
            self.nw.add_random_node()

        if symbol == key.D:
            self.nw.remove_random()


                
    
    def on_draw(self):
        glClearColor(0,0,0,0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        for node in self.nw.nodes.values():
            drawNode(node)

        self.nw.tick()
            
        
    def update(self,dt):
        pass
                
            

if __name__ == "__main__":
    win = ChordWindow()
    win_width, win_height = win.width, win.height
    pyglet.app.run()
