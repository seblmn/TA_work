from imobilitylab.simulator.event_based.objects.location import Location
from imobilitylab.simulator.event_based.objects.trips import TripCollection, TripPassangerWithObservation
from imobilitylab.simulator.event_based.objects.trips import JourneyCollection
from imobilitylab.simulator.event_based.objects.trips import TripPassanger


class Passenger(object):

    def __init__(self, passenger_id: int, first_arrival_time_to_simulation: int, location: Location,
                 journey_collection=None):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        self.id = passenger_id
        self.first_arrival_time_to_simulation = first_arrival_time_to_simulation
        self.arrival_times = []
        if self.first_arrival_time_to_simulation is not None:
            self.arrival_times.append(first_arrival_time_to_simulation)
        self.alighting_times = []
        self.borded_times = []
        self.location = location
#        self.destination_location = destination_location
        self.processed_time = None
        self.total_travel_time_on_board_from_vehicleEvent = 0
        self.total_distance_on_board_from_vehicleEvent = 0
        self.total_distance_complete = True
        self.total_travel_time_complete = True
        self.vehicle = None
        self.manager = None
        self.case_study = None
        self.served = False
        #self.journey_in_progress = None
        #self.trip_in_progress = None
        self.in_simulation = False
        self.all_completed = False
        self.journey_collection = journey_collection

    def register_start_location_index(self,start_location:Location, start_location_index: int):
        act_trip = self.journey_collection.active_journey.active_trip
        if isinstance(act_trip, TripPassangerWithObservation):
            act_trip.observed_start_location = start_location
            act_trip.observed_start_location_index = start_location_index
        else:
            raise Exception('Class Error: The observed values can only be registered for TripClass: TripPassangerWithObservation which is not here', type(act_trip))

    def register_denied_bording(self):
        act_trip = self.journey_collection.active_journey.active_trip
        if isinstance(act_trip, TripPassangerWithObservation):
            act_trip.observed_denied_boarding += 1
        else:
            raise Exception('Class Error: The observed values can only be registered for TripClass: TripPassangerWithObservation which is not here', type(act_trip))


    def register_observed_trips(self, start_location:Location, end_location:Location,
                                trip_id: int, line_id: int, direction_id:int, start_time:int, end_time:int,
                                distance: int, distance_complete:bool, on_board:int, vehicle, manager):

        act_trip = self.journey_collection.active_journey.active_trip
        if isinstance(act_trip, TripPassangerWithObservation):
            act_trip.observed_start_location = start_location
            act_trip.observed_end_location = end_location
            act_trip.observed_trip_id = trip_id
            act_trip.observed_line_id = line_id
            act_trip.observed_direction_id = direction_id
            act_trip.observed_start_time = start_time
            act_trip.observed_end_time = end_time
            act_trip.observed_distance = distance
            act_trip.observed_distance_complete = distance_complete
            act_trip.observed_on_board = on_board
            act_trip.observed_vehicle = vehicle
            act_trip.observed_manager = manager
        else:
            raise Exception('Class Error: The observed values can only be registered for TripClass: TripPassangerWithObservation which is not here', type(act_trip))
        self.journey_collection.active_journey.move_active_trip_to_executed(self.journey_collection.active_journey.active_trip)

    def get_current_trip_in_progress(self):
        return self.journey_collection.active_journey.active_trip

    def get_current_journey_in_progress(self):
        return self.journey_collection.active_journey

    def get_next_trip(self):
        trip_t = self.journey_collection.get_next_trip()
        if trip_t is None:
            self.served = True
        return trip_t

    def add_journey(self, trip_collection: TripCollection):
        if self.journey_collection is None:
            self.journey_collection = JourneyCollection()
        self.journey_collection.register_journey(trip_collection)

    def add_next_trip_to_simulation(self, override_the_planned_time_with_this_time:int = None):
        last_journey = self.journey_collection.active_journey
        next_trip = self.get_next_trip()
        if next_trip is not None:
            if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                print('    * Passanger next trip OR journey',self.id,last_journey, self.journey_collection.active_journey,next_trip.start_time, override_the_planned_time_with_this_time)
            execution_time = next_trip.start_time
            if override_the_planned_time_with_this_time is not None:
                if override_the_planned_time_with_this_time > execution_time:
                    execution_time = override_the_planned_time_with_this_time

            if last_journey == self.journey_collection.active_journey:
                if self.case_study.passanger_can_be_delayed_but_never_arrive_earlier_as_planned_times_during_the_journey_execution:
                    self.case_study.add_passenger_next_trip_arrival_to_simulation(self,
                                                                                  execution_time,
                                                                                  next_trip, immediate_processing=False)
                else:
                    self.case_study.add_passenger_next_trip_arrival_to_simulation(self,
                                                                                      self.case_study.simulator.time_line.actual_time,
                                                                                      next_trip, immediate_processing=True)
            else:
                self.case_study.add_passenger_next_trip_arrival_to_simulation(self,
                                                                                  execution_time,
                                                                                  next_trip, immediate_processing=False)
            return False
        else:
            return True

#    def AddTrip(self, start_location: int, end_location: int, distance: int, on_board: float, start_time: int,
#                     end_time: int, vehicle, manager):
#        if self.trip_collection is not None:
#            self.trip_collection.register_trip(TripPassanger(start_location, end_location, distance, on_board,
#                                                             start_time, end_time, vehicle, manager))


    def will_you_board_departure(self, manager):
        trip_in_plan = self.get_current_trip_in_progress()
        if manager.is_trip_to_destination_from_location_possible(trip_in_plan.start_location,
                                                                 trip_in_plan.end_location):
            return True
        return False


    def get_total_waiting_time(self, end_time: int):
        #print('### waiting time of passenger', self.id)
        #print(self.arrival_times)
        #print(self.borded_times)
        waiting_time = 0
        if len(self.borded_times) > 0:
            #print('  borded > 0')
            for i in range(0, len(self.arrival_times)-1):
                if len(self.borded_times) >= i+1:
                    #print('         ', self.borded_times[i] - self.arrival_times[i])
                    waiting_time += self.borded_times[i] - self.arrival_times[i]
            #print('  borded > 0, waiting time',waiting_time)
            #waiting_time = waiting_time/float(len(self.borded_times))
        else:
            #print(' returning end time nor board at all',end_time)
            waiting_time = end_time
        if waiting_time < 0:
            print(self.arrival_times)
            print(self.borded_times)
            print(waiting_time)
            raise Exception('ERROR: waiting time of passenger can not be NEGATIVE')
        return waiting_time

    def get_travel_time_on_board(self, end_time: int):
        #print('### time on board of passenger', self.id)
        #print(self.arrival_times)
        #print(self.borded_times)
        travel_time = 0
        if len(self.borded_times) > 0:
            #print('  borded > 0')
            for i in range(0, len(self.borded_times)):
                if len(self.alighting_times) >= i:
                    #print('         ', self.arrival_times[i+1] - self.borded_times[i])
                    travel_time += self.alighting_times[i] - self.borded_times[i]
                else:
                    travel_time += end_time - self.borded_times[i]
            #print('  borded > 0, waiting time',travel_time)
        else:
            travel_time = None
        #if travel_time > 3000:
        #    print(self.id,self.location.id,self.destination_location.id)
        #    for i in range(0,len(self.transfers)):
        #        print(self.transfers[i][0].id, self.transfers[i][1].id)
        #    exit(0)
        if travel_time is not None and travel_time < 0:
            raise Exception('ERROR: on board time of passenger can not be NEGATIVE')
        return travel_time

    def get_total_time(self, end_time: int):
        travel_time = 0
        #print(self.id,self.arrival_times, self.borded_times, self.alighting_times)
        if len(self.arrival_times) > 0:
            # print('  borded > 0')
            for i in range(0, len(self.arrival_times)):
                if len(self.alighting_times) >= i:
                    #print('         ', self.arrival_times[i+1] - self.borded_times[i])
                    travel_time += self.alighting_times[i] - self.arrival_times[i]
                else:
                    travel_time += end_time - self.arrival_times[i]
            # print('  borded > 0, waiting time',travel_time)
        else:
            travel_time = None

        if travel_time < 0:
            raise Exception('ERROR: travel time of passenger can not be NEGATIVE')
        return travel_time

    def register_arrival_time(self, arrival_time):
        self.arrival_times.append(arrival_time)

    def register_alighting_time(self, alighting_time):
        self.alighting_times.append(alighting_time)

    def collect_trip(self, origin_id:int, destination_id: int, distance:int, on_board: int,
                     start_time:int,end_time: int, vehicle, manager):
        pass

    def register_borded_time(self, borded_time):
        if self.id == 62595908:
            print(self.id, self.arrival_times, self.borded_times)
        if borded_time < self.arrival_times[len(self.borded_times)]:
            raise Exception('ERROR: boarded time can be not before arrival time of passenger')
        self.borded_times.append(borded_time)

    def get_destination(self):
        return self.destination_location

    def select_destination(self):
        return self.destination_location

    def get_final_destination(self):
        return self.destination_location


class PassengerWithTransfers(Passenger):

    def __init__(self, passenger_id: int, arrival_time: int, location: Location, destination_location: Location,
                 transfers: list, trip_collection):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(PassengerWithTransfers, self).__init__(passenger_id, arrival_time, location, destination_location, trip_collection)
        self.transfers = transfers
        self.transfer_index = 0

    def switch_to_location_platform(self):
        #print('    switch from platform',self.transfers[self.transfer_index - 1][0].id,' to ',
        #      self.transfers[self.transfer_index - 1][1].id)
        return self.transfers[self.transfer_index - 1][1]

    def get_destination(self):
        if len(self.transfers) > 0 and self.transfer_index < len(self.transfers):
            obj_t = self.transfers[self.transfer_index][0]
            return obj_t
        else:
            return self.destination_location

    def select_destination(self):
        if len(self.transfers) > 0 and self.transfer_index < len(self.transfers):
            obj_t = self.transfers[self.transfer_index][0]
            self.transfer_index += 1
            return obj_t
        else:
            return self.destination_location

    def get_final_destination(self):
        return self.destination_location