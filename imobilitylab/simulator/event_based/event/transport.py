from imobilitylab.simulator.event_based.core.simulator import Event
from imobilitylab.simulator.event_based.objects.location import Location
from imobilitylab.simulator.event_based.objects.passenger import Passenger, PassengerWithTransfers
from imobilitylab.simulator.event_based.objects.vehicle import Vehicle

class VehicleEvent(Event):

    def __init__(self, execution_time: int, vehicle: Vehicle, priority_for_same_execution_time: int = 10):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(VehicleEvent, self).__init__(execution_time,priority_for_same_execution_time=priority_for_same_execution_time)
        self.vehicle = vehicle

    def execute(self):
        pass


class PassengerEvent(Event):

    def __init__(self, execution_time: int, passenger: Passenger, location: Location,
                 priority_for_same_execution_time: int = 5):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(PassengerEvent, self).__init__(execution_time,
                                             priority_for_same_execution_time=priority_for_same_execution_time)
        self.passenger = passenger
        self.location = location

    def execute(self):
        pass


class PassengerArrivalEvent(PassengerEvent):

    def __init__(self, execution_time: int, passenger: Passenger, location: Location,
                 priority_for_same_execution_time: int = 5):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(PassengerArrivalEvent, self).__init__(execution_time, passenger, location,
                                                    priority_for_same_execution_time=priority_for_same_execution_time)

    def execute(self):
        #if self.passenger.id == 1:
        #    print(' * Arrived passanger',self.passenger.id, self.simulator.time_line.actual_time)
        if self.simulator.config.detailed_terminal_print_of_simulation:
            print(self.simulator.time_line.actual_time, ' passenger arrived', self.passenger.id,
                  self.simulator.time_line.actual_time)
        self.passenger.location = self.location
        self.location.add_passenger(self.passenger)
        self.passenger.in_simulation = True


class PassengerUnloadEvent(PassengerEvent):

    def __init__(self, execution_time: int, passenger: Passenger, location: Location,
                 vehicle: Vehicle, travel_time: int, distance: int, on_board: int,
                 priority_for_same_execution_time: int = 6):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(PassengerUnloadEvent, self).__init__(execution_time, passenger, location,
                                                   priority_for_same_execution_time)
        self.vehicle = vehicle
        self.travel_time = travel_time
        self.distance = distance
        self.on_board = on_board

    def execute(self):
        if self.simulator.config.detailed_terminal_print_of_simulation:
            print('* Unloading passanger',self.passenger.id,'on location',self.location.id, 'at time',self.simulator.time_line.actual_time)
        org_pos = self.passenger.location
        act_trip = self.passenger.journey_collection.active_journey.active_trip
        #print(self.passenger.id, self.passenger.location.id,'planned:',act_trip.start_location.id,act_trip.end_location.id, 'observed:',act_trip.observed_start_location_index,act_trip.observed_end_location_index)

        if str(type(act_trip)) == 'TripPassangerWithObservation':
            dis, tt, dis_complete, tt_complete = self.vehicle.manager.get_distance_and_travel_time_between_passenger_origin_destination(act_trip.observed_start_location_index, act_trip.observed_end_location_index)

            tt += self.vehicle.manager.get_simulation_departure_time_by_locationindex(
                act_trip.observed_start_location_index) - self.passenger.borded_times[-1]
        else:
            dis, tt = self.vehicle.manager.get_distance_and_travel_time_between_passenger_origin_destination(act_trip.start_location, act_trip.end_location)
            dis_complete = True
            tt_complete = True

        if not tt_complete:
            raise Exception('ERROR the travel time is expected always to be Known, but it is not')
        self.passenger.location = self.location
        #self.passenger.total_travel_time_on_board_from_vehicleEvent += tt
        #self.passenger.total_distance_on_board_from_vehicleEvent += dis
        if dis is None:
            self.total_distance_complete = False
        else:
            self.passenger.total_distance_on_board_from_vehicleEvent += dis
        if tt is None:
            self.total_travel_time_complete = False
        else:
            self.passenger.total_travel_time_on_board_from_vehicleEvent += tt

        if tt != self.simulator.time_line.actual_time - self.passenger.borded_times[-1]:
            print(self.vehicle.manager.departure_id,  self.vehicle.manager.ordered_list_of_planned_observation[act_trip.observed_start_location_index].departure_time,self.vehicle.manager.simulation_observation[act_trip.observed_start_location_index].departure_time)
            print('tt vehicle ',self.vehicle.manager.get_departure_time_by_locationindex(act_trip.observed_start_location_index),' info',tt,self.simulator.time_line.actual_time - self.passenger.borded_times[-1],self.simulator.time_line.actual_time, self.passenger.borded_times[-1], self.passenger.borded_times, self.passenger.arrival_times,'waiting on board:',self.vehicle.manager.get_departure_time_by_locationindex(act_trip.observed_start_location_index) - self.passenger.borded_times[-1])
            raise Exception('ERROR: the travel time on vehicle should be the same with the shortest travel time between two sopts on line or in DRT as in matrix, but it is not!')
        self.vehicle.unload_passenger(self.passenger)
        self.passenger.register_alighting_time(self.simulator.time_line.actual_time)

        # CURRENT TRIP JOURNEY that should END
        intended_trip_destination = self.passenger.get_current_trip_in_progress().end_location
        intended_journey_destination = self.passenger.get_current_journey_in_progress().destination_location
        Passenger_with_defined_location_transfer = False

        # COLLECT TRIP, save observation and LABEL the trips as EXECTUDED
        if str(type(act_trip)) == 'TripPassangerWithObservation':
            self.simulator.case_study.register_passenger_observation(self.passenger, org_pos, self.location,
                                                                     self.passenger.borded_times[-1],
                                                                     self.simulator.time_line.actual_time, dis,
                                                                     dis_complete, self.on_board, self.vehicle,
                                                                     self.vehicle.manager)

#        if self.location.id != intended_destination.id:
#            if isinstance(self.passenger, PassengerWithTransfers):
#                Passenger_with_defined_location_transfer = True
#                transfer_location_to = self.passenger.switch_to_location_platform()
#                self.passenger.location = transfer_location_to
#                if self.simulator.config.detailed_terminal_print_of_simulation:
#                    print(' NOT A FINAL destination of passenger', org_pos.id,
#                          'observed:',self.location.id, 'indented:',intended_destination.id)
#                transfer_location_to.add_passenger(self.passenger)
#                if self.passenger.manager is not None:
#                    self.passenger.manager.register_passenger(self.passenger)
#            #else:
#            #    raise Exception('The')
#            #    self.simulator.case_study.add_next_trip_for_passenger_to_simulation(self.passenger)
        if self.simulator.config.detailed_terminal_print_of_simulation:
            if self.location.id == intended_trip_destination.id:
                print(' Passenger',self.passenger.id,' on intended TRIP destination obs:', self.location.id, 'intended:', intended_trip_destination.id)
            if self.location.id == intended_journey_destination.id:
                print(' Passenger',self.passenger.id,' on intended JOURNEY destination obs:', self.location.id, 'intended:', intended_journey_destination.id)

        completed_passenger = self.passenger.add_next_trip_to_simulation(override_the_planned_time_with_this_time=self.simulator.time_line.actual_time)

        #simulator.case_study.add_next_trip_for_passenger_to_simulation(self.passenger)

        if completed_passenger:
            #if self.location.id == intended_trip_destination.id:
            #    print(' Passenger', self.passenger.id, ' FULLY completed')
            self.passenger.served = True
            #if len(self.passenger.transfers) > 0:
            #    exit(0)

        # passenger is unregistered when it is borded
        #    self.passenger.manager.unregister_passenger(self.passenger)


class VehicleStationArrivalEvent(VehicleEvent):

    def __init__(self, execution_time: int, manager, vehicle: Vehicle, location: Location,
                 traveling_from_location: Location, distance: int, travel_time: int, passenger: Passenger = None,
                 artificial_trip: bool = False, priority_for_same_execution_time: int = 15):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(VehicleStationArrivalEvent, self).__init__(execution_time, vehicle,
                                                         priority_for_same_execution_time=
                                                         priority_for_same_execution_time)
        self.location = location
        self.traveling_from_location = traveling_from_location
        self.passenger = passenger
        self.distance = distance
        self.on_board = vehicle.total_boarded
        self.travel_time = travel_time
        self.artificial_trip = artificial_trip
        self.manager = manager
        if self.manager is None:
            self.manager = self.vehicle.manager
        #if self.manager is not None:
        #    if self.manager.departure_id == 18912:
        #        print('   - parent - Manager Even created for 12348',self.location.id, self.execution_time, self.manager.case_study.simulator.time_line.actual_time)
        #if self.vehicle.manager is not None:
        #    if self.vehicle.manager.departure_id == 18912:
        #        print('   - parent Vehicle.Manager - Arrival Event created for 12348',self.location.id, self.execution_time, self.vehicle.manager.case_study.simulator.time_line.actual_time)

    def assign_vehicle_to_location(self):
        #if self.manager.departure_id == 18912:
        #    print('XX3 Assign parent', self.simulator.time_line.actual_time, self, self.traveling_from_location, self.location.id)
        self.vehicle.location = self.location
        self.location.add_vehicle(self.vehicle)
        self.manager.vehicle_arrived_to_location(self)

    def execute(self):
        if not self.artificial_trip:
            if self.simulator.config.detailed_terminal_print_of_simulation:
                print('* vehicle',self.vehicle.id,' arrived to location', self.location.id,'with passangers',self.vehicle.total_boarded)
            if self.vehicle.total_boarded > 0:
                if self.distance is not None:
                    self.vehicle.total_distance_occupied += self.distance
                self.vehicle.total_travel_time_occupied += self.travel_time
                self.vehicle.number_of_occupied_trips += 1
            else:
                #print(self.manager.id, self.vehicle.id, self.distance, self.travel_time, self.location.id)
                if self.vehicle.location is None or (self.vehicle.location is not None and self.vehicle.location.id != self.location.id) \
                        or (self.traveling_from_location is not None and self.traveling_from_location.id != self.location.id):
                    if self.distance is not None:
                        self.vehicle.total_distance_empty += self.distance
                    self.vehicle.total_travel_time_empty += self.travel_time
                    self.vehicle.number_of_empty_trips += 1
            if self.vehicle.location is not None:
                self.vehicle.collect_trip(self.vehicle.location, self.location, self.distance, self.on_board,
                                          self.simulator.time_line.actual_time - self.travel_time,
                                          self.simulator.time_line.actual_time)
            elif self.traveling_from_location is not None:
                #if self.manager.departure_id == 18912:
                #    print('XX',self.simulator.time_line.actual_time,self, self.traveling_from_location.id, self.location.id)
                self.vehicle.collect_trip(self.traveling_from_location, self.location, self.distance, self.on_board,
                                          self.simulator.time_line.actual_time - self.travel_time,
                                          self.simulator.time_line.actual_time)
            else:
                raise Exception('Logic ERROR: trip for vehicle can not be collected because of missing from_location information')
        #if self.manager.departure_id == 12348:
        #    print('XX2 before assign', self.simulator.time_line.actual_time, self, self.traveling_from_location, self.location.id)
        self.assign_vehicle_to_location()


class VehicleStationDepartureEvent(VehicleEvent):

    def __init__(self, execution_time: int, manager, vehicle: Vehicle, location: Location, stop_time: int,
                 passenger: Passenger = None, artificial_trip: bool = False,
                 priority_for_same_execution_time: int = 12):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(VehicleStationDepartureEvent, self).__init__(execution_time, vehicle,
                                                           priority_for_same_execution_time=
                                                           priority_for_same_execution_time)
        self.location = location
        self.passenger = passenger
        self.on_board = vehicle.total_boarded
        self.stop_time = stop_time
        self.artificial_trip = artificial_trip
        self.manager = manager
        if self.manager is None:
            self.manager = self.vehicle.manager

    def remove_vehicle_from_location(self):
        self.location.remove_vehicle(self.vehicle)

    def execute(self):
        if not self.artificial_trip:
            self.vehicle.total_travel_time += self.stop_time
            self.vehicle.total_time_at_stops += self.stop_time
        if self.manager.departure_id == 18912:
            print(' - event - VehicleStationDepartureEvent', self.simulator.time_line.actual_time)
        self.manager.vehicle_departured_the_location(self)
        self.remove_vehicle_from_location()

   #     if self.location.total_number_of_passangers > 0:
    #        pass
   #     else:
    #        self.location.add_vehicle(self.vehicle)
    #        self.vehicle.manager.register_vehicle_for_redistribution(self.vehicle)
#
    #    self.location.add_vehicle(self.vehicle)

    #    self.vehicle.location = self.location
    #    if self.vehicle.empty_space() > 0:
     #       t_array = self.vehicle.get_leaving_passengers(self.location)
    #        for i in range(0, len(t_array)):
     #           self.simulator.immediate_procees_event(PassengerUnloadEvent(self.simulator.time_line.actual_time,
     #                                                                       t_array[i], self.location))

     #   if self.vehicle.empty_space() > 0:
     #       self.simulator.immediate_procees_event(VehicleBoardingEvent(self.simulator.time_line.actual_time,
      #                                                                  self.vehicle, self.location))
     #   else:
#
     #       self.location.add_vehicle(self.vehicle)
     #       self.vehicle.manager.register_vehicle_for_redistribution(self.vehicle)


class VehicleBoardingEvent(VehicleEvent):

    def __init__(self, execution_time: int, vehicle: Vehicle, location: Location,
                 priority_for_same_execution_time: int = 11):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(VehicleBoardingEvent, self).__init__(execution_time, vehicle,
                                                   priority_for_same_execution_time=priority_for_same_execution_time)
        self.location = Location

    def execute(self):
        self.vehicle.manager.board_passengers(self.vehicle, self.location)
        empty_space = self.vehicle.empty_space()
        if empty_space > 0:
            while self.vehicle.empty_space > 0 or self.location.get_actual_number_of_passangers():
                passenger = self.location.get_passanger()
                passenger.register_borded_time(self.simulator.time_line.actual_time)
                self.vehicle.add_passenger(passenger)
        #self.simulator.add_event(VehicleStationArrivalEvent(self.simulator,,self.vehicle,))
