"""
Chord Logging / Metrics collection tool

	- Set up metrics-collection & display for following:
		- Number of active/inactive nodes
		- Min/Avg/Max length of searches
	- Set up logging messages on GUI
		- Message @ start-nodes, @ destination-nodes (and hops), 
		- Joins, Leaves, 
		- Message-deaths?/time-outs

"""

#from chordTest import *

DISPLAY_INTERVAL = 5

class chordLogger:
    """ Logs simulation messages to visualizer +/ file + console
       Carries out metrics analysis  
    """
   
    def __init__(self):
        self.t = 0

        # Instantiate log-file / viz.
        #if VISUALIZE is True: 
        #  print "[chordLogger] Will visualize"
           #viz = ChordWindow()
        #if LOG_TO_FILE is True: 
        #   print "[chordLogger] Will log messages to file"
        #   """ Open file and stuff """
           
        # Initialize metrics collection variables
        # Nodes
        self.total_joins = 0
        self.total_leaves = 0
        self.total_fails = 0
        #Messages
        self.total_msgs_sent = 0       
        self.total_msgs_reached = 0
        self.total_hops_taken_for_reach = 0
        self.total_msgs_failed = 0
        self.total_hops_taken_before_failure = 0        
        # Averages
        self.current_nodes_in_network = 0
        self.avg_hops_to_reach = 0
        self.avg_hops_before_failure = 0
        self.initial_size = 0
        
    def log(self, logString):
       # to console
       #print logString 
       # to viz
       #if VISUALIZE is True: 
       #    print "[chordLogger] Will write to viz: ", logString 
       # to file
       #if LOG_TO_FILE is True: 
       #    print "[chordLogger] Will write to file: ", logString 
        pass

    def update_state(self):
        #""" Updates internal state variables a.k.a. Metrics collected """
        self.current_nodes_in_network = self.initial_size + self.total_joins - self.total_leaves - self.total_fails
        if self.total_msgs_reached != 0:
            self.avg_hops_to_reach = float(self.total_hops_taken_for_reach) / float(self.total_msgs_reached)
        if self.total_msgs_failed != 0:
            self.avg_hops_before_failure = self.total_hops_taken_before_failure / self.total_msgs_failed        
        #print "[chordLogger] Updating internal state variables " 
 
    def print_state(self):
        self.update_state()
        print "current_nodes_in_network ", self.current_nodes_in_network
        print "avg_hops_to_reach ", self.avg_hops_to_reach
        print "total_msgs_sent ", self.total_msgs_sent        
        print "total_msgs_reached ", self.total_msgs_reached
        print "total_node_joins ", self.total_joins
        print "total_node_leaves ", self.total_leaves
        print "failure rate: ", float(self.total_msgs_failed)/float(self.total_msgs_sent+1), "  ", self.total_msgs_failed,"/", self.total_msgs_sent
        
        
 
    def tick(self):
        self.t += 1
        self.update_state();
        
        if (self.t % DISPLAY_INTERVAL) == 0:
            print "[chordLogger] time: ", self.t
            self.print_state();
      
    """
    Network Log Methods:
    - log_join(nodeID)
    - log_leave(nodeID)
    - log_msg_sent(self, srcID, destID)
    - log_msg_reached(srcID, destID, hops)
    - log_msg_failed(srcID, destID, hops, failed_at, trying_to_reach)
    - log_message_route -- not sure
    """
   
    def init_size(self, size):
        self.initial_size = size
   
    def log_join(self, nodeID):
       self.total_joins += 1
       self.log("Node Join: " + str(nodeID))
       
    def log_leave(self, nodeID):
       self.total_leaves += 1
       self.log("Node Leave: " + str(nodeID))

    def log_fail(self, nodeID):
       self.total_fails += 1
       self.log("Node Fail: " + str(nodeID))
       
    def log_msg_sent(self, srcID, destID):
       self.total_msgs_sent += 1
       #self.log("Message sent from " + str(srcID) + " to " + str(destID))

    def log_msg_reached(self, srcID, destID, hops):
       self.total_msgs_reached += 1
       self.total_hops_taken_for_reach += hops
       #self.log("Message from " + str(srcID) + " to " + str(destID) + " reached in " + str(hops) + " hops")

    def log_msg_failed(self, srcID, destID, hops, failed_at, trying_to_reach):
       self.total_msgs_failed += 1
       self.total_hops_taken_before_failure += hops
       #self.log("Message from " + str(srcID) + " to " + str(destID) + " failed at node " + str(failed_at) + " trying to reach " + str(trying_to_reach))
       
""" Self-test: ignore for the purposes of the actual program ... """   
if __name__ == "__main__":
    log = chordLogger()
    print "[chordLogger] instance made"
    log.tick()
    
    log.log_join('1')
    log.log_join('2')
    log.tick()

    log.tick()
    log.tick()
    log.tick()
    
    log.log_join('3')
    log.log_join('4')
    log.tick()
    
    log.tick()
    log.tick()
    log.tick()
    
    log.log_msg_reached('1', '2', 1)
    log.tick()

    log.tick()
    log.tick()
    log.tick()
    
    log.log_msg_failed('1', '4', 2, '2', '3')
    log.tick()
    
    log.tick()
    log.tick()
    log.tick()
    
    
