from imobilitylab.simulator.event_based.event.transport import VehicleStationArrivalEvent, PassengerArrivalEvent, VehicleStationDepartureEvent
from imobilitylab.simulator.event_based.objects.location import Location, MultiLineAndDirectionsLocation
from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.objects.vehicle import Vehicle


class VehicleStationArrivalEvent_line_with_direction(VehicleStationArrivalEvent):

    def __init__(self, execution_time: int, manager, vehicle: Vehicle, location: MultiLineAndDirectionsLocation,
                 traveling_from_location:MultiLineAndDirectionsLocation, distance: int, travel_time: int,
                 passenger: Passenger = None, artificial_trip:bool = False, priority_for_same_execution_time: int = 15):

        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(VehicleStationArrivalEvent_line_with_direction, self).__init__(execution_time, manager, vehicle, location,
                                                                             traveling_from_location,
                                                                             distance, travel_time, passenger,
                                                                             artificial_trip,
                                                                             priority_for_same_execution_time=
                                                                             priority_for_same_execution_time)

        #if self.manager.departure_id == 188:
        #    print('% Manager Arrival Event created for 188', self.location.id, self.execution_time, self.manager.case_study.simulator.time_line.actual_time)
        #if self.vehicle.manager is not None and self.vehicle.manager.departure_id == 188:
        #    print('%% Vehicle.Manager Arrival Event created for 188', self.location.id, self.execution_time, self.vehicle.manager.case_study.simulator.time_line.actual_time)

    def assign_vehicle_to_location(self):
        if self.manager.departure_id == 18912:
            print('XX3 line_with_direction No parent', self.simulator.time_line.actual_time, self, self.traveling_from_location, self.location.id)
        temp_loc = self.vehicle.location
        if temp_loc is None:
            temp_loc = self.traveling_from_location

        if isinstance(temp_loc, MultiLineAndDirectionsLocation):
            self.vehicle.location = self.location
            self.location.add_vehicle(self.vehicle, self.manager.transit_line_manager.line_manager.line_id,
                                      self.manager.transit_line_manager.direction_id)
            self.manager.vehicle_arrived_to_location(self)
        else:
            raise Exception('Error - the Event: "VehicleStationArrivalEvent_line_with_direction" is for "MultiLineAndDirectionsLocation" but Location is not it')


class DepartureStartVehicleStationArrivalEvent_line_with_direction(VehicleStationArrivalEvent_line_with_direction):
    """Specific for this class is to be able to handle case when start of Departure can be delayed.
    Note, all the departure starts as planned are added to timeline at the start of simulation, if any change happens,
    event needs to be adjusted or delayed by creating new event at the time.
    Possible cause can be: vehicle delayed on another departure, departure cancelled because of disruption modeling ... """

    def __init__(self, execution_time: int, manager, vehicle: Vehicle, location: MultiLineAndDirectionsLocation,
                 traveling_from_location: MultiLineAndDirectionsLocation, distance: int, travel_time: int,
                 passenger: Passenger = None, artificial_trip:bool = False,
                 priority_for_same_execution_time: int = 10):

        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(DepartureStartVehicleStationArrivalEvent_line_with_direction, self).__init__(execution_time, manager, vehicle, location,
                                                                             traveling_from_location,
                                                                             distance, travel_time, passenger,
                                                                             artificial_trip,
                                                                             priority_for_same_execution_time=
                                                                             priority_for_same_execution_time)

        #if self.manager.departure_id == 188:
        #    print('% START Manager Arrival Event created for 188', self.location.id, self.execution_time, self.manager.case_study.simulator.time_line.actual_time)
        #if self.vehicle.manager is not None and self.vehicle.manager.departure_id == 188:
        #    print('%% START Vehicle.Manager Arrival Event created for 188', self.location.id, self.execution_time, self.vehicle.manager.case_study.simulator.time_line.actual_time)

    def assign_vehicle_to_location(self):
        if self.manager.departure_id == 18912:
            print(self.simulator.time_line.actual_time,'   * Vehicle arriving',self.manager.departure_id, 'veh:',self.vehicle.id, self.vehicle.available_for_assignment)

        #if self.manager.departure_id == 188:
        #    print(' (*)(*) First arrival on departure')
        if isinstance(self.location, MultiLineAndDirectionsLocation):
            will_be_available, possible_avaibility_time = self.manager.case_study.is_pt_vehicle_available_for_departure_manager(self.vehicle, self.manager)
            if self.manager.departure_id == 18912:
                print(self.manager.id, will_be_available, self.simulator.time_line.actual_time, possible_avaibility_time)
                #exit(0)
            if will_be_available:
                if self.manager.departure_id == 18912:
                    print('TTTTT',will_be_available,self.simulator.time_line.actual_time, possible_avaibility_time, self.vehicle.id)
                    #exit(0)
                if possible_avaibility_time is None or possible_avaibility_time == 0 or possible_avaibility_time == self.simulator.time_line.actual_time:
                    if self.vehicle.available_for_assignment: # IF IS available in this MOMENT
                        self.vehicle.available_for_assignment = False
                        self.vehicle.location = self.location
                        self.location.add_vehicle(self.vehicle, self.manager.transit_line_manager.line_manager.line_id,
                                                  self.manager.transit_line_manager.direction_id)
                        self.manager.vehicle_arrived_to_location(self)
                        self.manager.add_vehicle(self.vehicle)
                    else:
                        # at this moment it is still occupied needs to be deregistered first before assignment So
                        # sending this again for procesing so it would be here AFTER previous departure finish on
                        # same time point.
                        self.execution_time = possible_avaibility_time
                        self.simulator.add_event(self)
                elif self.simulator.time_line.actual_time < possible_avaibility_time:
                    delay_estimate = possible_avaibility_time - self.manager.get_start_departure_time()
                    if delay_estimate > self.manager.case_study.threshold_for_delayed_vehicle_to_start_departure:
                        self.manager.case_study.find_new_pt_vehicle_to_serve_departure(self.manager)
                    else:
                        if delay_estimate < 0:
                            if self.manager.departure_id == 18912:
                                print('XXX',self,self.traveling_from_location,self.location.id)
                                print('TTTTT-postponing_from NOT DELAYED departure',self.simulator.time_line.actual_time,' to ',possible_avaibility_time, self.vehicle.id)
                            self.execution_time = possible_avaibility_time
                            self.simulator.add_event(self)
                        else:
                            if self.manager.departure_id == 18912:
                                print('TTTTT-postponing_from AND WILL DELAYED departure',self.simulator.time_line.actual_time,' to ',possible_avaibility_time, self.vehicle.id)
                                #exit(0)
                            self.manager.departure_delayed = possible_avaibility_time - self.simulator.time_line.actual_time
                            self.execution_time = possible_avaibility_time
                            self.simulator.add_event(self)
                else:
                    raise Exception('Logical Error: In case intended vehicle is delayed it can not be before current time')
            else:

                delay_estimate = possible_avaibility_time - self.manager.get_start_departure_time()
                if delay_estimate > self.manager.case_study.threshold_for_delayed_vehicle_to_start_departure:
                    # new vehicle maybe needed
                    self.manager.case_study.find_new_pt_vehicle_to_serve_departure(self.manager)
                else:
                    if self.simulator.time_line.actual_time < possible_avaibility_time:
                        if delay_estimate < 0:
                            if self.manager.departure_id == 18912:
                                print('TTTTT-not-available yet by postponing_from NOT DELAYED departure', self.simulator.time_line.actual_time,' to ',possible_avaibility_time, self.vehicle.id)
                            self.execution_time = possible_avaibility_time
                            self.simulator.add_event(self)
                        else:
                            if self.manager.departure_id == 18912:
                                print('TTTTT-not-available yet by postponing_from DELAYED departure', self.simulator.time_line.actual_time,
                                      ' to ',
                                      possible_avaibility_time, self.vehicle.id)
                                # exit(0)
                            self.manager.departure_delayed = possible_avaibility_time - self.simulator.time_line.actual_time
                            self.execution_time = possible_avaibility_time
                            self.simulator.add_event(self)
                    else:
                        raise Exception('Logical Error: In case intended vehicle is delayed it can not be before current time')
        else:
            print(self.vehicle.id, self.vehicle.location)
            raise Exception('Error - the Event: "VehicleStationArrivalEvent_line_with_direction" is for "MultiLineAndDirectionsLocation" but Location is not it')


class VehicleStationDepartureEvent_line_with_direction(VehicleStationDepartureEvent):

    def __init__(self, execution_time: int, manager, vehicle: Vehicle, location: Location, stop_time: int,
                 passenger: Passenger = None, artificial_trip: bool = False):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(VehicleStationDepartureEvent_line_with_direction, self).__init__(execution_time, manager, vehicle, location, stop_time, passenger, artificial_trip)

        if self.manager.departure_id == 18912:
            print('% Manager departure event created for 18912',self.location.id, self.execution_time, self.manager.case_study.simulator.time_line.actual_time)
        #if self.vehicle.manager is not None:
        #    if self.vehicle.manager.departure_id == 188:
        #        print('% Vehicle.Manager departure event created for 188',self.location.id, self.execution_time, self.vehicle.manager.case_study.simulator.time_line.actual_time)

    def remove_vehicle_from_location(self):
        self.location.remove_vehicle(self.vehicle,self.manager.transit_line_manager.line_manager.line_id,
                                      self.manager.transit_line_manager.direction_id)


class PassengerArrivalEvent_line_with_direction(PassengerArrivalEvent):

    def __init__(self, execution_time: int, passenger: Passenger, location: Location, line_id:int, direction_id:int):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(PassengerArrivalEvent_line_with_direction, self).__init__(execution_time, passenger, location)
        self.line_id = line_id
        self.direction_id = direction_id

    def execute(self):
        if self.simulator.config.detailed_terminal_print_of_simulation:
            print(self.simulator.time_line.actual_time,' passenger arrived', self.passenger.id, self.simulator.time_line.actual_time)
        self.passenger.location = self.location
        self.passenger.register_arrival_time(self.simulator.time_line.actual_time)
        if self.passenger.id == 62595908:
            print(' ** Passanger 62595908 Arrival at loc:', self.location.id, 'time', self.simulator.time_line.actual_time, self.line_id, self.direction_id,self.passenger.arrival_times,self.passenger.borded_times,self.passenger.alighting_times)
        self.location.add_passenger(self.passenger, self.line_id, self.direction_id)
        self.passenger.in_simulation = True