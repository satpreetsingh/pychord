NUM_BITS = 16 

from random import randint, random, choice, paretovariate 
from pprint import pprint


def between(x, i, j):
   #print i,j, i==j 
   #if i == j:
   #   return False
   if i <= j:
      #print x >= i and x <=j
      return x >= i and x <=j
   else: #this spans the origin
      return x > i or x<= j


chord_messages = []

class Message:
    
    def __init__(self, src, dest, msg_type="find"):
        self.src = src
        self.dest = dest
        self.route = []
        self.message_type = msg_type
        self.status = 'routing'
        self.ttl = 10
        chord_messages.append(self)




class Node:
    
    def __init__(self, id, ttl=-1):
        self.id = id
        self.predec = None
        self.fingers = [None for i in range(NUM_BITS)]
        self.down = False
        self.ttl = ttl
        
        
    def find_successor(self, msg):
        if self.down:
            msg.status = 'fail'
            return None
        node = self.find_predecessor(msg) #get as close as possible
        if node==None or node.down:
            msg.status = 'fail'
            return None

        if node.id == msg.dest: #cool we got there
            msg.status = 'done'
            return node
        else: #almost, teh successor of this one is responsible for that key
            msg.status = 'done'
            msg.route.append(node.fingers[0].id)
            return node.fingers[0]
        
    def find_predecessor(self, msg):
        if self.down:
            msg.status = 'fail'
            return None
        id = msg.dest

        if id == self.id:
            return self
 
        node = self        
        if not node.fingers[0]: 
            msg.status = 'fail'
            node.stabilize()
            return None

        #print "before",node, node.fingers[0]
        while (node.id != node.fingers[0].id ) and not between(id, node.id, (node.fingers[0].id)):
    

            node = node.closest_preceding_finger(msg)
    
            if node==None or node.down or node.fingers[0] == None:
               msg.status = 'fail'
               return None

            msg.route.append(node.id)
            #print "inside",node, node.fingers[0]
            if node.id == id:
                return node
            


        return node
        
    def closest_preceding_finger(self, msg):
        if self.down:
            msg.status = 'fail'
            return None

        id = msg.dest
        for i in range(len(self.fingers)-1,-1,-1): #loop backwards
         if self.fingers[i] and between(self.fingers[i].id, self.id , id):
            return self.fingers[i]
        return self
    
    
    def join(self, intro_node):
        if intro_node:
            self.predec = None
            join_msg = Message(intro_node.id, self.id, 'join')
            self.fingers[0] = intro_node.find_successor(join_msg)
            self.init_fingers()
            #move keys ebwteen predec and self from succes to self
        else: # this is teh first node creating a network
            for i in range(NUM_BITS):
                self.fingers[i] = self
                self.predec = self
                
        self.fingers[0].notify(self)


    def check_dead_links(self):
        if self.predec == None or self.predec.down == True:
            self.predec = None
        for i in range(len(self.fingers)):
            if self.fingers[i]==None or self.fingers[i].down == True:
                self.fingers[i] = None

   
    def stabilize(self):
        self.check_dead_links()
        if not self.fingers[0]:
            init_msg = Message(self.id, self.id, 'fix')
            self.fingers[0] = self.find_successor(init_msg)
            self.fingers[0].notify(self)
        x = self.fingers[0].predec
        if x and between(x.id, self.id , self.fingers[0].id) and x.id != self.id:
            self.fingers[0] = x
            self.fingers[0].notify(self)
        
    def notify(self, pre_node):
        self.check_dead_links()
        if (self.predec == None) or between(pre_node.id, self.predec.id, (self.id-1)% (2**NUM_BITS)):
            self.predec = pre_node
            
    def init_fingers(self):
        for i in range(len(self.fingers)-1,-1,-1): #loop backwards
            i_finger_id = (self.id + 2**(i)) % 2**NUM_BITS
            init_msg = Message(self.id, i_finger_id, 'init')
            self.fingers[i] = self.find_successor(init_msg)
            
            
    def fix_fingers(self):
        self.check_dead_links()
        i = randint(1,NUM_BITS-1)
        #for i in range(NUM_BITS):
        #print "fixing node", self.id, i
        i_finger_id = (self.id + 2**(i)) % 2**NUM_BITS
        init_msg = Message(self.id, i_finger_id, 'fix')
        self.fingers[i] = self.find_successor(init_msg)
        #print "fix: successor of ", i_finger_id, "found as:", self.fingers[i].id, "   id:", self.id, "f: +",2**(i) 
        #pprint(init_msg.route)
            

    def shutdown(self):
        self.down = True



    def __str__(self):
        ret = "Node: " + str(self.id) +"\n"
        return ret
        if self.predec: ret += "Predecessor: "+str(self.predec.id)+" \n"
        else:           ret += "Predecessor: NONE \n"
        
        ret += "Fingers: "
        for f in self.fingers:
            if f: ret += str(f.id) + ", "
            else: ret += "-,"
        return ret
        
        
        
        
        
class Network:
    
    def __init__(self, logger=None):

        self.name_space_size = 2**NUM_BITS
        self.t = 0

        self.logger = logger
        
        self.nodes = {}
        self.ids = []

        self.max_size = 500
        self.growing = False 

        self.new_messages = []
        
        #parameters for randomization/eventdistribution
        
        #exponential distributin. mostly one node will join per tick.  less often 2 nodes, less often 3 nodes...etc.
        self.concurent_join_alpha = 4
        
        #the rate at which nodes leave/join teh network
        self.churn_rate = 0.05
        
        #the rate at which nodes perform the fix_finger and stabilize protocol
        self.fix_rate = 0.4
        self.stabilize_rate = 0.3
        self.message_rate = 0.6
        
        
    def bootstrap(self, num_nodes=3):
    #bootstraps the network with num_nodes inital nodes evenly distriubuted, with predecessors set and finger spointing at successors

        last_node = None
        for i in range(1,self.name_space_size, self.name_space_size/num_nodes):
            self.nodes[i] = Node(i)
            self.ids.append(i)
            
            self.nodes[i].predec = last_node #set predecessor
            if last_node: #set finger table of predecessor to current node
                last_node.fingers = [self.nodes[i] for x in range(NUM_BITS)]
            last_node = self.nodes[i]
 
        self.nodes[self.ids[0]].predec = last_node #predecessor of first node is teh last one
        last_node.fingers = [self.nodes[self.ids[0]] for x in range(NUM_BITS) ] #finger table fo last node
      
      
    def add_node(self, node):
        hook = self.random_node()
        self.nodes[node.id] = node
        self.ids.append(node.id)
        if self.logger:
           self.logger.log_join(node.id) 
        return hook
      
      
    def add_joins(self, node_joins):
       for join in node_join:
            id, ttl = join
            node = Node(id, ttl)
            self.add_node(node)
      
    def add_leaves(self, leaves):
       for leave_id in node_join:
            self.remove_node(leave)
      
      
    def random_node(self):
        return self.nodes[choice(self.ids)]
      
        
    def get_unique_id(self):
        #returns an unused ID
        newID = randint(0,self.name_space_size)
        while self.nodes.has_key(newID):
            newID = randint(0,self.name_space_size)
        return newID
      
    def grow(self, num_nodes):
        self.growing = True
        #keep taking stes to grows teh network using random joins until num_nodes are participating
        while len(self.nodes) < num_nodes:
            
            #some joins will occur
            for i in range(paretovariate(self.concurent_join_alpha)):
                n = Node(self.get_unique_id())
                hook = self.add_node(n) #also returns a hook for the node to join at
                n.join(hook)
  
         
            self.tick()
        self.growing = False



    def remove_node(self, id):
       self.ids.remove(id)
       self.nodes[id].shutdown()
       del self.nodes[id]
       if self.logger:
           self.logger.log_leave(n.id) 


    def remove_random(self):
        node = self.random_node()
        self.remove_node(node.id)
        

    def add_messages(self, messages):
       self.new_messages = messages


    def tick(self):
        global chord_messages
        
        
        for n in self.nodes.values():
           n.check_dead_links()

        #add joins based on join rate
        #if len(self.nodes)<self.max_size and random() < self.churn_rate:
        #    for i in range(paretovariate(int(self.concurent_join_alpha))):
        #       n = Node(self.get_unique_id())
        #       hook = self.add_node(n) #also returns a hook for the node to join at
        #       n.join(hook)
        #       if self.logger:
        #           self.logger.log_join(n.id)
        
        consumed = []
        for m in chord_messages:
             m.ttl -= 1
             if m.ttl < 1:
                consumed.append(m)

        for m in consumed:
            chord_messages.remove(m)

         


      
        #run the stabilization and fix_finger protocol on soem of teh nodes in teh network
        num_fixes      = len(self.nodes)* self.fix_rate
        num_stabilizes = len(self.nodes)* self.stabilize_rate
        #num_messages   = len(self.nodes)* self.message_rate auto generate messages
        num_messages = len(self.new_messages)
        if self.growing: 
            num_messages = 0

        while num_fixes > 0 or num_stabilizes > 0 or num_messages > 0:
            

            if num_fixes > 0:
                self.random_node().fix_fingers()
                num_fixes = num_fixes -1
            if num_stabilizes > 0:
                self.random_node().stabilize()
                num_stabilizes = num_stabilizes -1        
            if num_messages > 0 :
                m = self.new_messages.pop()
                if self.logger:
                   self.logger.log_msg_sent(m.src, m.dest)
                self.nodes[m.src].find_successor(m)
                
                if m.status == 'done':
                  self.logger.log_msg_reached(m.src, m.dest, len(m.route))
                elif m.status == 'fail':
                  self.logger.log_msg_failed(m.src, m.dest, len(m.route))
                else:
                  "Message that isnt doing anything??"
                
                num_messages = num_messages -1 


            
        
        
        
        
        
        
        
if __name__ == "__main__":
    chord = Network()
    chord.bootstrap(3)
    chord.grow(1000)
        
    print "DONE"
    
    
    
    
    
    
    
    
    
    
            current = self.closest_preceding_finger(msg)
        while between(current, self.id, dest): 
            current = self.nw.nodes[current].closest_preceding_finger(msg.dest)
            if self.nw.nodes[current].fingers[0] >= msg.dest: #thats the successor we are looking for
                msg.route.append(self.nw.nodes[current].fingers[0])
                return self.nw.nodes[current].fingers[0]
    
        
