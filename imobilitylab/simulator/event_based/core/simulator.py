from imobilitylab.simulator.event_based.supporting_libraries.priority_front import PriorityFront, ListItem


class Config(object):
    """This represent configurations during simulation can be extended by case-study specifs"""

    def __init__(self):
        self.detailed_terminal_print_of_simulation = False


class Event(object):
    """Event is basic class that is executed in time-order in simulation and added to simulation"""

    def __init__(self, execution_time:int, priority_for_same_execution_time:int = 0):
        self.execution_time = execution_time
        self.simulator = None
        self.priority = priority_for_same_execution_time

    def execute(self):
        pass


class WhatIfEvent(Event):
    """Event is basic class that is executed in time-order in simulation and added to simulation"""

    def __init__(self, execution_time:int):
        super(WhatIfEvent, self).__init__(execution_time)

    def is_expectation_valid(self):
        raise Exception('Class: "WahtIfEvent(Event)" implementation error, the "is_expectation_valid" function needs be re-define in child')

    def if_not(self):
        raise Exception('Class: "WahtIfEvent(Event)" implementation error, the "if_not" function needs be re-define in child')

    def if_yes(self):
        raise Exception('Class: "WahtIfEvent(Event)" implementation error, the "if_yes" function needs be re-define in child')

    def execute(self):
        if self.is_expectation_valid():
            self.if_yes()
        else:
            self.if_not()


class TimeLine(object):

    def __init__(self):
        self.list_of_events = PriorityFront(True)
        self.actual_time = 0

    def add_event(self, event: Event):
        self.list_of_events.AddItem(event, event.execution_time)

    def __process_event_for_exectuion__(self, event: Event):
        if self.actual_time > event.execution_time:
            # print('SSSSS-fail',self.actual_time, item[0].execution_time, item[0], item[0].vehicle.manager.departure_id, item[0].location.id)
            raise Exception(
                'ERROR: new event that should be executed should occure before: likely ERROR in priority front')
        self.actual_time = event.execution_time
        event.execute()

    def execute_event(self):

        if self.list_of_events is not None and self.list_of_events.num > 0:
            item = self.list_of_events.RemoveItem()
            # check if the next item does not have the same execution time; IF NOT -> we may execute this one directly
            if self.list_of_events.num == 0 or self.list_of_events.start.obj.execution_time != item[0].execution_time:
                self.__process_event_for_exectuion__(item[0])
            else:
            # if the next event has same exectution time; we need to consider exectution priority of the same time
            # defined by attribute self.priority -> so we create temporality PriorityFront -> Descending and execute
                # that order
                pf_t = PriorityFront()
                pf_t.AddItem(item[0], item[0].priority)
                if self.list_of_events.num > 0:
                    while self.list_of_events.start is not None and item[0].execution_time == self.list_of_events.start.obj.execution_time and self.list_of_events.num > 0:
                        item_t = self.list_of_events.RemoveItem()[0]
                        pf_t.AddItem(item_t, item_t.priority)
                        item_t = pf_t.start
                item_t = pf_t.start
                while item_t is not None:
                    self.__process_event_for_exectuion__(item_t.obj)
                    item_t = item_t.next
                del pf_t
            return True
        else:
            return False

    def is_empty(self):
        if self.list_of_events.num == 0:
            return True
        return False

    def num_events(self):
        return self.list_of_events.num

    def empty(self):
        del self.list_of_events
        self.list_of_events = PriorityFront(True)


class TimeLine_with_TimeBins(TimeLine):
    """This version of TimeLine provides more effective placement of event into time bins. It is designed to improve
    performance for time-limted simulation such 1 day or longer creating time bins of specific sizes, that get
    automaticlly created when new event comes."""

    def __init__(self, size_of_time_bin: 3600):
        super(TimeLine_with_TimeBins, self).__init__()
        self.size_of_time_bin = size_of_time_bin
        self.time_bins = {}
        self.time_bins_order = PriorityFront(True)

    def find_or_register_time_bin(self, new_time: int):
        bin_index = int(new_time / self.size_of_time_bin)
        if bin_index not in self.time_bins:
            bin_pf_item = self.time_bins_order.AddItem_with_return(bin_index, bin_index)
            self.time_bins[bin_index] = [bin_pf_item, None]
        return bin_index

    def add_event(self, event: Event):
        bin_index = self.find_or_register_time_bin(event.execution_time)
        bin_index_org = self.find_or_register_time_bin(event.execution_time)
        #print("Adding",event.execution_time)
        if self.list_of_events.num == 0:
            #print("Adding as new",event.execution_time)
            event_timeline_item = self.list_of_events.AddItem_with_return(event, event.execution_time)
            self.time_bins[bin_index][1] = event_timeline_item
        else:
            if self.time_bins[bin_index][1] is None:
                #print("A Bin exists but none PF reference insered yet - empty - Trying to insert frome earliers item")
                if self.time_bins[bin_index][0].previous is not None:
                    #print("A-1- Bin exists but none PF reference insered yet - empty - Trying to insert frome earliers item")
                    bin_index = self.time_bins[bin_index][0].previous.obj
                    if self.time_bins[bin_index][1] is not None:
                        #print("A-1-1 - Bin exists and item to refer to PF for insert as well -> inserting after",self.time_bins[bin_index][1].obj.execution_time)
                        event_timeline_item = self.list_of_events.AddItem_from_the_specific_location_with_return(self.time_bins[bin_index][1], event, event.execution_time)
                        self.time_bins[bin_index_org][1] = event_timeline_item
                    else:
                        raise Exception('Logic Error: bin created already before should have element in it')
                elif self.time_bins[bin_index][0].next is not None:
                    #print("A-2-1 - there is no previous -> so it will go to start")
                    event_timeline_item = self.list_of_events.AddItem_with_return(event, event.execution_time)
                    self.time_bins[bin_index_org][1] = event_timeline_item
                else:
                    raise Exception('Logic Error: this should not happen if there are items in PF and bins, there have to be some BINS already around if this BIN has no assignment yet')
            else:
                if self.time_bins[bin_index][1].obj.execution_time <= event.execution_time:
                    event_timeline_item = self.list_of_events.AddItem_from_the_specific_location_with_return(self.time_bins[bin_index][1],event,event.execution_time)
                    #print("There is already item that is smaller - no update needed",self.time_bins[bin_index][1].obj.execution_time, event.execution_time)
                else:
                    #print("New event is before main pointed in bin -> so updating to it ",event.execution_time,'old:',self.time_bins[bin_index][1].obj.execution_time)
                    event_timeline_item = self.list_of_events.InsertItem_Before_the_specific_location_with_return(self.time_bins[bin_index][1],event,event.execution_time)
                    self.time_bins[bin_index_org][1] = event_timeline_item
        #if event.execution_time == 19766:
        #    exit(0)

    def clean_timebins_if_needed(self, last_time:int):
        bin_index = int(last_time / self.size_of_time_bin)
        item = self.time_bins_order.start
        while item is not None and bin_index > item.obj:
            print('removing time-bin:',item.obj,bin_index)
            item_p = item.next
            del self.time_bins[item.obj]
            self.time_bins_order.RemoveItem()
            item = item_p

    def remove_all_bins(self):
        item = self.time_bins_order.start
        while item is not None:
            print('removing',item.obj)
            item_p = item.next
            del self.time_bins[item.obj]
            self.time_bins_order.RemoveItem()
            item = item_p

    def __process_event_for_exectuion__(self, event: Event):
        # print('last_time',self.actual_time,'executing at time',item[0].execution_time,item[0])
        next_pf_item = self.list_of_events.start
        bin_index = int(event.execution_time / self.size_of_time_bin)
        if next_pf_item is not None:
            bin_index_next = int(next_pf_item.obj.execution_time / self.size_of_time_bin)
            if bin_index == bin_index_next:
                # print('Updating pointer to new start object in the bin')
                self.time_bins[bin_index][1] = next_pf_item
            elif bin_index < bin_index_next:
                # print('BIN can be removed',bin_index,bin_index_next,next_pf_item.obj.execution_time)
                self.clean_timebins_if_needed(next_pf_item.obj.execution_time)
            else:
                raise Exception('Logical ERROR: there should not been index of removed item is larger as next one')
        else:
            # nothing next -> remove all bins
            self.remove_all_bins()
        if self.actual_time > event.execution_time:
            print('SIMULATOR-Execution-Event-fail', self.actual_time, event.execution_time,event)  # item[0].vehicle.manager.departure_id, item[0].location.id)
            raise Exception(
                'ERROR: new event that should be executed should occure before: likely ERROR in priority front')
        self.actual_time = event.execution_time
        event.execute()

    def empty(self):
        del self.list_of_events
        del self.time_bins
        self.list_of_events = PriorityFront(True)


class Simulator(object):

    def __init__(self, config: Config = None, time_line:TimeLine = None):
        self.time_line = None
        if time_line is not None:
            if not isinstance(time_line, TimeLine) or  not isinstance(time_line, TimeLine_with_TimeBins):
                raise Exception('time_line input have to be of class TimeLine or TimeLine_with_TimeBins')
            self.time_line = time_line
        if self.time_line is None:
            self.time_line = TimeLine()
        self.case_study = None
        if config is None:
            self.config = Config()
        else:
            self.config = config

    def add_event(self, event: Event):
        event.simulator = self
        if self.time_line.list_of_events is not None:
            self.time_line.add_event(event)

    def immediate_procees_event(self, event: Event):
        #print('!!! Immediate process')
        event.simulator = self
        event.execute()

    def start(self):
        while self.time_line.list_of_events is not None and not self.time_line.is_empty():
            self.time_line.execute_event()
        print('END time', self.time_line.actual_time)

    def stop(self):
        self.time_line.empty()
        self.time_line.list_of_events = None

