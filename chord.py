 

from random import randint, random, choice, paretovariate 
from pprint import pprint
from chordLogger import *

NUM_BITS                 = 16
NUM_NODES                = 1024               #The number of nodes in teh network
JOIN_LATENCY             = 10                 #latency between growing and starting sim, also used for churn_type apprx: log(NUM_NODES)
LENGTH_OF_SIMULATION     = 2000               #number of ticks to simulate
MESSAGE_RATE             = 0.2                #The frequency at which nodes send messages/lookups. i.e 20% that a node sends a new message each round
#CHURN_PROBABILITY        = 1.0/JOIN_LATENCY  #probability that churn will occur at all this tick
#MAX_CHURN_FRACTION       = 0.02              #max fraction of total number of nodes in the network that will join or leave
CHURN_TYPE               = 'adversarial'           #option are 'random', 'adversarial' or 'all'
ATTACK_INTERVAL          = 200                #attacker will atack evry ATTACK_RATE number of ticks
ATTACK_SIZE              = 5*10             #number of cocncurent, continuous nodes failed by the attacker 
MESSAGE_TTL              = 30
STABILIZE_FREQ           = 0.05      #The frequency at which nodes will run the fix_fingers protocol
FIX_FINGER_FREQ          = 0.05      #The frequency at which nodes will run the stabilize protocol
RANDOM_ROUTING_FREQ      = 0.4       #The frequency at which nodes will route a message to a less than optimal finger
CHURN_RATE = 2

#Working on
REPLICATION_TYPE         ='none'      # The type of replication used. options are:  'none', 'random', 'delta', 'popularity'
REPLICATION_K            = 16          #number of replicas K/2 into each direction\






#helper function for determining whether a key in teh identifier sapce falls between to others
#  returns true if x is strictly between i and j (x comes after i and before j, not equal to either i or j)
#  also returns False if x is None or False
def between(x, i, j):
    if (not x) or (not i) or (not j):
        return False
    
    if i <= j:
       return x > i and x <j
    else: #this spans the origin
       return x > i or x<j

message_ids = 0
NUM_REPLICAS = 0

class Message:
    
    def __init__(self, src, dest, type="lookup", callback=None, data=None):
        global message_ids
        self.src = src
        self.dest = dest
        self.route = [src]
        self.type = type
        self.callback = callback
        self.data = data 
        self.status = 'routing'
        self.id = message_ids 
        message_ids += 1
        
        
        
    def fail(self, reason='no reason given'):
        self.status = 'failed'
        if self.callback and self.type == 'lookup':
            self.callback(self)
            #print reason
        
    def arrive(self):
        #print self.type,"arrived", self.src, self.dest
        self.status = 'arrived'
        if self.callback:
            self.callback(self)
        

    def route_to(self, node_id):
        self.route.append(node_id)
        
            



class Node:
    
    def __init__(self, id, nw, ttl=-1,
                 stabilize_freq=STABILIZE_FREQ,
                 finger_fix_freq=FIX_FINGER_FREQ,
                 random_routing_freq=RANDOM_ROUTING_FREQ,
                 replication_type=REPLICATION_TYPE,
                 ):
    # id:  this nodes id/key in the identifier space of teh network
    # nw:  the network teh node is participating in (so we can get node objects by ID)
    # ttl: time to live.  if negative lives forever, decremented each tick. once ttl = 0 node dies
    # predec:   the node's predecessor (from its point of view)
    # fingers:  teh finger table (holds node ID's)
    # messages: a list of messages this node owns and handles at each tick
    # stabilize_freq/finger_fix_freq: used for determining when/whether to run stabilization protocol
    
        self.id = id
        self.nw = nw #so we can get other node objects by ID
        self.ttl = ttl
        self.predec = None
        self.fingers = [None for i in range(NUM_BITS)]
        self.sucessor_backups = [None for i in range(NUM_BITS)]
        self.messages = []
        self.joined = False
        
        
        
        #used for determining when/whether to run stabilization protocol
        self.stabilize_freq = stabilize_freq
        self.finger_fix_freq = finger_fix_freq
        self.random_routing_freq = random_routing_freq
        self.random_routing_type = 'uniform'
        
        
        # replication types:  'none', 'random', 'popularity', 'route_replication'
        self.replication_type = 'none'
        self.replicas = []

        
    def __str__(self):
    #so that we can print or cast the node to a string
        return "Node: " + str(self.id)
        
    
    def die(self):
        self.predec = None
        self.messages = None
        self.fingers = None
        self.nw.remove_node(self.id)
    
    def tick(self):
    #is called at each timestep of the network
    #performs one round of actions
        
        #unless we have succesfully joined teh network, we cant do maintanance
        if self.fingers[0] == None:
            return
        #if not self.nw.get_node(self.fingers[0]):
            #self.fix_sucessor()
        
        
        #handle this nodes messages 
        self.handle_messages()
            
        

            
        #perform some maintanance
        if random() < self.stabilize_freq:
            self.stabilize()
        if random() < self.finger_fix_freq:
            self.fix_fingers()
            
        if random() < MESSAGE_RATE and not self.nw.growing:
            #dest = randint(0,2**NUM_BITS-1)#self.nw.random_node().id
            dest = self.nw.random_node().id
            self.send_message(dest, callback=self.nw.log_message_result)
            self.nw.logger.log_msg_sent(self.id, dest)
            
        #one step closer to death..such is life
        self.ttl -= 1
        #if self.ttl == 0:
        #    self.die()
        
        
    def handle_messages(self):
    #iterates over all the messages this node owns
    #  if a message is routing:
    #  do next hop and remeber the message for the next round
    
        #still_alive = []
        #for msg in self.messages:
        #    if msg.status == 'routing':
        #        self.route_message(msg)
        #        still_alive.append(msg)
        #    if msg.status == 'arrived':
        #        pass #log arrive here?       
        #    if msg.status == 'failed':
        #        pass #log fail here?
        #print "before", len(self.messages)
        current_messages = self.messages
        self.messages = []
        num_messages_routed = 0
        while len(current_messages) and num_messages_routed < 50:
            msg = current_messages.pop()
            num_messages_routed += 1
            if len(msg.route) > MESSAGE_TTL:
                msg.fail('message timed out')
                
            if msg.status == 'routing':
                self.route_message(msg)
                self.messages.append(msg)
            if msg.status == 'arrived':
                pass #log arrive here?       
            if msg.status == 'failed':
                pass #log fail here?
           

        #print "after", len(self.messages)
            
    
    
    """
    Routing Protocol:
    ################################################################################################
    """
    
        
    def send_message(self, dest, type='lookup', callback=None, data=None):
    #Creates a new message orginating at this node
    #  dest: key/node this is meant for, message will get routed to dest or successor if no node at dest
    #  type: optional field describing what kind of message this is (used in visualizer to set color)
    #  callback: optional function pointer. Teh calback will be called with message as argument when it arrives at final destination
    #  data: optional anything, can be used to attach various data (e.g. finger index so callback knows which finger to update on response)
        if dest == self.id:
            return #no ned to send yourself a message
        m = Message(self.id, dest, type=type, callback=callback, data=data)
        self.messages.append(m)
        #print "sending new message", self.id, m.src, dest,m.dest, type, m.route, m.id
        return m
    
    def route_message(self, msg):
        global MESSAGE_TTL, NUM_REPLICAS
    #This function is called every tick by each node for every message it started
    #It routes each message one step closer until it reaches the 'successor'.
    #Messages are rourted until their location = dest or the first node with id > dest.
        

                
        
        #get the node our message is currently at
        current_node = self.nw.get_node(msg.route[-1])
        
        #maybe the node we are looking for doesnt exist in the network...the routing fails
        if (not current_node) :
            msg.fail('node died between ticks')
            #print " FAIL  :", msg.route, "from:", msg.src, " to:", msg.dest, msg.type
            return False
        
        if REPLICATION_TYPE == 'delta' and msg.type == 'lookup':
            key_index = self.nw.ids.index(current_node.id)
            first = self.nw.ids[(key_index-(REPLICATION_K/2)-1)%(len(self.nw.ids)-1)]
            last  = self.nw.ids[(key_index+(REPLICATION_K/2))%(len(self.nw.ids)-1)]
            if between(msg.dest, first, last):
                NUM_REPLICAS +=1
                msg.arrive()
                return
            
        if REPLICATION_TYPE == 'random' and msg.type == 'lookup':
            for repl_range in self.replicas:
                if between(msg.dest, repl_range[0], repl_range[1]):
                    NUM_REPLICAS +=1
                    msg.arrive()
                    return
        
        if (not current_node.fingers[0]):
            msg.fail('node doesnt have sucessor')
            #print " FAIL  :", msg.route, "from:", msg.src, " to:", msg.dest, msg.type
            return False
        if len(msg.route) > MESSAGE_TTL :
            msg.fail('message timed out')
            #print " FAIL  :", msg.route, "from:", msg.src, " to:", msg.dest, msg.type
            return False

        #check whether the current node is immediate predecesor.  in this case the target is its successor
        if between(msg.dest, current_node.id, current_node.fingers[0]+1):
            sucessor = self.nw.get_node(current_node.fingers[0])
            if sucessor  :
                msg.route_to(current_node.fingers[0])
                msg.arrive()
            else:
                msg.fail('sucessor pointer failed')
                current_node.fix_sucessor()
                
            
        #we are not there yet, in this case we make a hop to the closest node the current one knows about
        else:
            next_node_id = current_node.closest_preceding_finger(msg.dest)
            msg.route_to(next_node_id)
            return next_node_id
        
        
        
        


    def closest_preceding_finger(self, id):
    #Returns teh closest node to id this node knows about
    #Iterates over fingers in reverse and returns as soon as one is preceeding id.
    #Returns this nodes ID if no preceeding finger is known
    
        for finger in reversed(self.fingers): 
            if between(finger, self.id , id):
                if not self.nw.get_node(finger):
                    self.fix_finger(self.fingers.index(finger))
                    continue
                #this step will be skipped random;y sometimes
                if random() > self.random_routing_freq: #otherwise keep going
                    return finger
                
        for finger in self.fingers: 
            if self.nw.get_node(finger):
                return finger
            

        return self.id 
    
    

            
    
    
    
    """
    Join Protocol:
    ################################################################################################
    """
    def init_join(self, entry_node):
        self.entry = entry_node
        if entry_node:
            self.predec = None
            m = entry_node.send_message(self.id, type='join', callback=self.join_response)
        

    def join_response(self, msg):
        sucessor = self.nw.get_node(msg.route[-1])
        self.fingers[0] = sucessor.id
        self.sync_backups()
        sucessor.notify(self.id)
        self.init_fingers()
        self.joined = True
        if not self.nw.growing and REPLICATION_TYPE == 'random':
            self.get_replicas()
        

    def get_replicas(self):
        self.replicas = []
        for i in range(REPLICATION_K):
            repl = self.nw.random_node()
            i=0
            while not (self.nw.get_node(repl.fingers[0])) or i > 10:
                repl = self.nw.random_node()
                i+=1
            self.replicas.append((repl.predec, repl.id+1))

    def init_fingers(self):
        for finger_index in reversed( range(len(self.fingers)) ): 
            self.fix_finger(finger_index)
                    
    def finger_response(self, msg):
        self.fingers[msg.data] = msg.route[-1]
        if msg.data == 0:
            
            self.sync_backups()
    
    
    """
    Stabilization Protcol:
    ################################################################################################
    """
    def fix_fingers(self):
        #finger_index = randint(0,NUM_BITS-1)
        #self.fix_finger(finger_index)
        for i in range(NUM_BITS):
            if not self.nw.get_node(self.fingers[i]):
                self.fix_finger(i)

        
    def fix_finger(self, index):
        ideal_finger = (self.id + 2**(index)) % 2**NUM_BITS
        self.send_message(ideal_finger, type='finger', callback=self.finger_response, data=index)
 
    def stabilize(self):
        sucessor = self.nw.get_node(self.fingers[0])
        if not sucessor:
            return self.fix_sucessor()
        new_sucessor_id = sucessor.predec
        if between(new_sucessor_id, self.id , self.fingers[0]):
            self.fingers[0] = new_sucessor_id
            if self.nw.nodes.has_key(new_sucessor_id):
                self.nw.get_node(self.fingers[0]).notify(self.id)
        self.sync_backups()
        
    def notify(self, pre_node):
        if (self.predec == None) or between(pre_node, self.predec, self.id):
            self.predec = pre_node

    def fix_sucessor(self):
        for b in self.sucessor_backups:
            if self.nw.get_node(b):
                self.fingers[0] = b
                self.sync_backups()
                
    def sync_backups(self):
        sucessor = self.nw.get_node(self.fingers[0])
        if sucessor:
            self.sucessor_backups[0] = sucessor.id
            for i in range(1,len(self.sucessor_backups)):
                if sucessor:
                    self.sucessor_backups[i] = sucessor.id
                    sucessor = self.nw.get_node(sucessor.fingers[0])
                    

    



        
        
        
        
LEAVES = 0
        
class Network:
    
    def __init__(self, logger=None):

        if logger:
            self.logger = logger
        else:
            self.logger = chordLogger()

        #basic stuff
        self.name_space_size = 2**NUM_BITS
        self.t = 0
        self.nodes = {}
        self.growing = False 
        
        #parameters for randomization/event distribution
        
        #exponential distributin. mostly one node will join per tick.  less often 2 nodes, less often 3 nodes...etc.
        self.concurent_join_alpha = 4
        
        #the rate at which nodes leave/join teh network
        self.churn_rate = 0.05
        self.ids = None



    def tick(self):
        self.ids = self.nodes.keys()
        self.ids.sort()
        for n in self.nodes.values():
            n.tick()
            


    def get_node(self, node_id):
        if node_id in self.nodes:
            return self.nodes[node_id]
        else:
            #print "accessing missing node: ", node_id
            return None
        
    def random_node(self):
        return self.nodes[choice(self.nodes.keys())]
        
    def get_unique_id(self):
        #returns an unused ID
        newID = randint(0,self.name_space_size)
        while self.nodes.has_key(newID):
            newID = randint(0,self.name_space_size)
        return newID
        
        
    def bootstrap(self, num_nodes=3):
    #bootstraps the network with num_nodes inital nodes evenly distriubuted, with predecessors set and fingers pointing at successors
        last_node = None
        for i in range(1,self.name_space_size, self.name_space_size/num_nodes):
            #print "booting node:", i
            self.nodes[i] = Node(i, self)            
            
            if last_node: #set finger table of predecessor to current node
                self.nodes[i].predec = last_node.id #set predecessor
                last_node.fingers = [self.nodes[i].id for x in range(NUM_BITS)]
            last_node = self.nodes[i]
 
        self.nodes[1].predec = last_node.id #predecessor of first node is teh last one
        last_node.fingers = [self.nodes[1].id for x in range(NUM_BITS) ] #finger table fo last node
      
      
    def grow(self, num_nodes):
        self.growing = True
        #keep taking stes to grows teh network using random joins until num_nodes are participating
        i = 0
        while len(self.nodes) < num_nodes:
            self.tick()
            if random() < 0.3:
                id = self.get_unique_id()
                n = Node(id, self)
                
                self.add_node(n, log=False) #also returns a hook for the node to join at
                i+=1
                if i%50: print "current size:", i
                
        
        self.growing = False
        
        if REPLICATION_TYPE == 'random':
            for node in self.nodes.values():
                node.get_replicas()



    def add_node(self, node, log=True):
        node.init_join(self.random_node())
        self.nodes[node.id] = node
        if log:
            self.logger.log_join(node.id)
        
    def add_random_node(self):
        n = Node(self.get_unique_id(), self)
        self.add_node(n)

        
      
    def remove_node(self, id):
       
       #self.nodes[id].die()
       del self.nodes[id]
       self.logger.log_leave(id)
       
    def remove_random(self):
        node = self.random_node()
        #while not node.joined:
        node = self.random_node()
        self.remove_node(node.id)
       
    def adversary_attack(self):
        node_ids = self.nodes.keys()
        node_ids.sort()
        start_index = int(random()*(len(node_ids)-1))
        for i in range(ATTACK_SIZE):
            id = node_ids[(start_index+i)%(len(node_ids)-1)]
            self.remove_node(id)
        


        

    def add_messages(self, messages):
       for m in messages:
            self.nodes[m[0]].send_message(m[1], callback=self.log_message_result)
            self.logger.log_msg_sent(*m)
            
    def log_message_result(self, m):
        if m.status == 'arrived':
            self.logger.log_msg_reached(m.src, m.dest, len(m.route))
        if m.status == 'failed':
            self.logger.log_msg_failed( m.src, m.dest, len(m.route), m.route[-1], m.dest)
      
      
    def add_joins(self, node_joins):
       for join in node_join:
            id, ttl = join
            node = Node(id, self, ttl=ttl)
            node.init_join(self.random_node())
            self.add_node(node)
      
    def add_leaves(self, leaves):
       for leave_id in node_join:
            self.remove_node(leave)
      

#some probability to average the number of leaves/joins over CHURN_TIME rounds to be churn rate i.e. CHURN_JOIN/CHURN_DIE
#calculates frequency of doing joins or not given that each round that does joins or leaves can do concurently e.g. MAX_JOINS of tehm
#AVERAGE_JOINS_PER_CHURN_ROUND = float(CHURN_JOIN)*NUM_NODES *LENGTH_OF_SIMULATION/float(CHURN_TIME) #thats how many noes should join on average per CHURN_TIME rounds
#AVERAGE_JOINS_PER_ROUND = float(MAX_CONCURENT_JOIN)*0.5 #since we pick randomly from 0 to max_joins, woudl be different for other probability distribution
#CHANCE_OF_JOINS = AVERAGE_JOINS_PER_ROUND/AVERAGE_JOINS_PER_CHURN_ROUND

#AVERAGE_DIE_PER_CHURN_ROUND = float(CHURN_DIE)*NUM_NODES *LENGTH_OF_SIMULATION/float(CHURN_TIME)
#AVERAGE_DIES_PER_ROUND = float(MAX_CONCURENT_DIE)*0.5 
#CHANCE_OF_DIES = AVERAGE_DIES_PER_ROUND/AVERAGE_DIE_PER_CHURN_ROUND

if __name__ == "__main__":
    chord = Network()
    print "boot"
    chord.bootstrap(3)
    
    print "growing"
    chord.grow(NUM_NODES)
    chord.logger.init_size(len(chord.nodes))

    for i in range(JOIN_LATENCY):
        chord.tick()

    attack_round = 0
    for i in range(LENGTH_OF_SIMULATION):
        chord.tick()
        chord.logger.update_state()

        

        
        if CHURN_TYPE == 'random' or CHURN_TYPE == 'all':
            if random() < CHURN_RATE*0.5:
                if random() < 0.5:
                    chord.remove_random()
                if random() < 0.5:
                    chord.remove_random()
    
            if random() < CHURN_RATE*0.5:
                if random() < 0.5:
                    chord.add_random_node()
                if random() < 0.5:
                    chord.add_random_node()
        """
        
        if random() < CHURN_PROBABILITY:
            num_fails = random()*MAX_CHURN_FRACTION*NUM_NODES/JOIN_LATENCY
            num_joins = random()*MAX_CHURN_FRACTION*NUM_NODES/JOIN_LATENCY
            for i in range(int(num_fails)):
                chord.remove_random()
            for i in range(int(num_joins)):
                chord.add_random_node()
        
        """
        
        if CHURN_TYPE == 'adversarial' or CHURN_TYPE == 'all':
            if attack_round == ATTACK_INTERVAL:
                chord.adversary_attack()
                attack_round = 0
            else:
                attack_round += 1
        

    

        print 'tick:',i
        
        
    chord.logger.print_state()

    print "Churn Type:", CHURN_TYPE
    print "Churn Rate:", CHURN_RATE, "  ATTACKER:", ATTACK_INTERVAL, ATTACK_SIZE
    print "Random Routing Frequency:",  RANDOM_ROUTING_FREQ
    print "Replication Mode:", REPLICATION_TYPE, "K:",REPLICATION_K, " Number of repicas found/used:", NUM_REPLICAS
    
    