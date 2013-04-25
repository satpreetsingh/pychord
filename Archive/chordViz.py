import pyglet
from pyglet.window import Window, key
from pyglet.gl import *
from math import sin, cos, radians
from random import randint
from pyglet.text import Label

from pychord import *


EDGE_COLOR = (1,1,1, 0.3)
NODE_COLOR = (0,1,0, 1)
STEP_TIME = 1.0

def drawLine(p1,p2, width=0.5):
   glLineWidth(width)
   glBegin(GL_LINES)
   glVertex2f(p1[0], p1[1])
   glVertex2f(p2[0], p2[1])      
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

def drawLabel(text, pos=(0,0), **kwargs):
    kwargs.setdefault('font_size', 16)
    kwargs.setdefault('center', False)
    if kwargs.get('center'):
        kwargs.setdefault('anchor_x', 'center')
        kwargs.setdefault('anchor_y', 'center')
    else:
        kwargs.setdefault('anchor_x', 'left')
        kwargs.setdefault('anchor_y', 'bottom')
    del kwargs['center']
    temp_label = Label(text, **kwargs)
    #temp_label.x, temp_label.y = pos
    glPushMatrix()
    #glTranslated(-pos[0]-8.5,-pos[1]-8,0)
    glScaled(0.02,0.02,0.02)
    temp_label.draw()
    glPopMatrix()
    return temp_label.content_width




class ChordWindow(Window):

   def __init__(self, chord):
      #config = Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True,)
      super(ChordWindow, self).__init__(caption="Chord visualization", fullscreen=False)
      #the chord model
      self.chord = chord
      self.messages = ["line 1", "line 2", "line 3"]

   def on_resize(self, width, height):
       glViewport(0, 0, width, height)
       glMatrixMode(gl.GL_PROJECTION)
       glLoadIdentity()
       ar = float(width)/height
       glOrtho(-12*ar, 12*ar, -12, 12, -1, 1)
       glMatrixMode(gl.GL_MODELVIEW)

   def print_line(self, str):
      self.messages.insert(0,str)
      while len(self.messages) > 20:
         self.messages.pop()

   def get_node_pos(self, i):
      print i
      try:
         #print "i as int", self.chord.nodes[i]
         n, size = self.chord.nodes[i].id, float(self.chord.size)
         return cos(radians( n/size*-360+90))*10,sin(radians( n/size*360+90))*10
      except:
         n, size = i.id, float(self.chord.size)
         return cos(radians( n/size*-360+90))*10,sin(radians( n/size*360+90))*10

   def on_key_press(self, symbol, modifiers):
      if symbol == key.ESCAPE:
         pyglet.app.exit()
      elif symbol == key.SPACE:
         #print "tick", self.chord.t 
         self.chord.tick()

   def on_draw(self):
      global chord_messages
      self.clear()

      glPushMatrix()
      glColor3f(0.4,0.4,0.4)
      glTranslated(-19,6,0)
      drawRectangle((0,0), 10,8)
      glTranslated(0.1,0,0)
      for m in self.messages:
         drawLabel(m, (0,0))
         glTranslated(0,0.4,0)
      glPopMatrix()

      #draw connections
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
      glColor4f(*EDGE_COLOR)
      for node in self.chord.nodes:
         x,y = self.get_node_pos(node)
         for dest in node.fingers:
            x2,y2 = self.get_node_pos(dest)
            drawLine((x,y),(x2,y2), 1)

      #draw nodes
      glColor4f(*NODE_COLOR)
      for node in self.chord.nodes:
         n, size = node.id, float(self.chord.size)
         x,y = self.get_node_pos(n)
         drawCircle((x,y),.05)

      #draw current messages
      glDisable(GL_DEPTH_TEST)
      #print chord_messages
      for node in chord_messages:
         #print "msgs of", node
         for m in chord_messages[node]:
            #print m
            if m.t > self.chord.t:
               continue #dont handle messages that are still waiing to start

            
            print self.chord.t, m.last_location, m.current_location
            src = self.get_node_pos(m.src)
            dst = self.get_node_pos(m.dest)
            fro = self.get_node_pos(m.last_location)
            to =  self.get_node_pos(m.current_location)

            glColor4f(1,0,1,0.5)
            drawLine(src,fro,3)
            drawLine(to,dst,3)
            glColor4f(0,1,1,0.5)
            drawLine(src,dst,3)

            glColor4f(0,0,1,1)
            if m.content == "OK":
               self.print_line("message arrived at:" + str(m.dest))
               glColor4f(1,1,0,1) #direct communication/response to src

            drawCircle(to,.2)                     
            #drawTriangle(fro, .2,.2)
            drawLine(fro,to,3)
            
      #self.flip()



if __name__ == "__main__":
   test = Network(32)
   win = ChordWindow(test)
   pyglet.app.run()
