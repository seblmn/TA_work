
from imobilitylab.simulator.event_based.objects.fleet_management import FleetManager
from imobilitylab.simulator.event_based.objects.case_study import CaseStudy
from imobilitylab.simulator.event_based.objects.vehicle import Vehicle
from imobilitylab.simulator.event_based.objects.location import Location
from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.event.transport import VehicleStationArrivalEvent
from imobilitylab.simulator.event_based.public_transport.events import VehicleStationArrivalEvent_line_with_direction, \
    PassengerArrivalEvent_line_with_direction, VehicleStationDepartureEvent_line_with_direction, \
    DepartureStartVehicleStationArrivalEvent_line_with_direction
from imobilitylab.simulator.event_based.event.transport import PassengerUnloadEvent
from imobilitylab.simulator.event_based.objects.trips import TripVehicle,TripPassanger, TripCollection
from enum import Enum
import numpy as np


class DepartureManagerStatus(Enum):
    planned = 1
    in_progress = 2
    completed = 3


class TripVehiclePT(TripVehicle):

    def __init__(self, start_location: Location, end_location: Location, distance: int, on_board: int, start_time: int,
                 end_time: int, vehicle=None, manager=None, departure=None, segment_order_index:int=0):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(TripVehiclePT, self).__init__(start_location, end_location, distance, on_board,start_time,
                                            end_time,vehicle,manager)
        self.departure = departure
        self.segment_order_index = segment_order_index

    def to_csv_str(self):
        str_t = str(self.vehicle.id)+';'+str(self.manager.id)+';'+str(self.departure.departure_id)+';'\
               +str(self.departure.departure_time)+';'+str(self.segment_order_index)+';'+str(self.start_time)+';'\
               +str(self.end_time)+';'+str(self.end_time-self.start_time)+';' \
               +str(self.distance)+';'+str(self.pasengers_on_board)+';' \
               +str(round(self.pasengers_on_board/float(self.vehicle.capacity), 4))+';'+str(self.start_location.id)+';' \
               +str(self.end_location.id)+';'
        if self.manager is not None and isinstance(self.manager, TransitLineDepartureManager_with_planned_times):
            dep_t = self.manager.get_departure_time(self.start_location)
            arr_t = self.manager.get_arrival_time(self.end_location)
            start_location_index = self.manager.get_segment_index_first_occurance(self.start_location)
            end_location_index = self.manager.get_segment_index_last_occurance(self.start_location)
            tt_t = self.manager.get_travel_time(self.vehicle, self.start_location, self.end_location,start_location_index,end_location_index)
            dis_t = self.manager.get_distance(self.vehicle, self.start_location, self.end_location,start_location_index,end_location_index)
            str_t += str(dep_t) + ';' + str(arr_t) + ';' + str(tt_t) + ';' + str(dis_t)
        else:
            str_t += 'None;None;None;None'
        return str_t

class Departure(object):

    def __init__(self, id:int, manager, vehicle: Vehicle, departure_time: int, start_location: Location, end_location: Location,
                 trip_collection=None):
        self.departure_id = id
        self.vehicle = vehicle
        self.manager = manager
        self.served_passengers = 0
        self.n_segments = 0
        self.departure_time = departure_time
        self.start_location = start_location
        self.end_location = end_location
        self.end_time = None
        self.start_locations_in = {}
        self.end_locations_in = {}
        if trip_collection is not None:
            self.trip_collection = []

    def export_avg_occupancy_and_on_board_from_location_to_location(self, start_location: Location,
                                                                    end_location: Location):
        if self.trip_collection is not None:
            if start_location in self.start_locations_in and end_location in self.end_locations_in:
                n_segments = 0
                sum_avg_on_board = 0
                sum_occupancy_rate = 0
                travel_time = 0
                for i in range(self.start_locations_in[start_location], self.end_locations_in[end_location]+1):
                    if self.trip_collection[i].pasengers_on_board >= 0:
                        n_segments += 1
                        sum_avg_on_board += self.trip_collection[i].pasengers_on_board
                        sum_occupancy_rate += self.trip_collection[i].pasengers_on_board/float(self.vehicle.capacity)
                        travel_time += self.trip_collection[i].end_time - self.trip_collection[i].start_time
                if n_segments > 0:
                    return n_segments,sum_avg_on_board/float(n_segments),sum_occupancy_rate/float(n_segments),travel_time
                else:
                    return None, None, None, None
            else:
                return None, None, None, None
        else:
            return None, None, None, None



    def collect_trip(self, trip:TripVehiclePT):
        if self.trip_collection is not None:
            self.start_locations_in[trip.start_location.id] = len(self.trip_collection)
            self.end_locations_in[trip.end_location.id] = len(self.trip_collection)
            self.trip_collection.append(trip)

    def to_csv_str(self):
        start_location_index = self.manager.get_segment_index(self.start_location)
        tt = None
        if self.end_time is not None and self.departure_time is not None:
            tt = self.end_time-self.departure_time
        aggregated_part = str(self.departure_id)+';'+str(self.manager.id)+';'+str(self.vehicle.id)+';'+ \
                          str(self.departure_time)+';'+str(self.end_time)+';'+\
                          str(self.start_location.id)+';'+str(start_location_index)+';'+str(tt)+';'+str(self.n_segments)+';'+str(self.served_passengers)

        segment_by_segment_ridership = ''

        if len(self.trip_collection)>0:
            total_empty_trips = 0
            total_occupied_trips = 0
            served_from_trips = 0
            list_of_occupancies = []
            list_of_occupancies_rates = []
            for i in range(0,len(self.trip_collection)):
                if self.trip_collection[i].pasengers_on_board > 0:
                    total_occupied_trips += 1
                else:
                    total_empty_trips += 1
                served_from_trips += self.trip_collection[i].pasengers_on_board
                list_of_occupancies.append(self.trip_collection[i].pasengers_on_board)
                list_of_occupancies_rates.append(self.trip_collection[i].pasengers_on_board/float(self.vehicle.capacity))
            avg_occupancy = np.nanmean(list_of_occupancies)
            std_occupancy = np.nanstd(list_of_occupancies)
            max_occupancy = np.nanmax(list_of_occupancies)
            avg_occupancy_rate = np.nanmean(list_of_occupancies_rates)
            std_occupancy_rate = np.nanstd(list_of_occupancies_rates)
            max_occupancy_rate = np.nanmax(list_of_occupancies_rates)

            aggregated_part += ';'+str(total_empty_trips)+';'+str(total_occupied_trips)+';'+str(avg_occupancy)+';'+\
                              str(std_occupancy)+';'+str(max_occupancy)+';'+str(avg_occupancy_rate)+';'+\
                              str(std_occupancy_rate)+';'+str(max_occupancy_rate)+';'

            index_collected_trips = {}
            for i in range(0,len(self.trip_collection)):
                index_collected_trips[self.trip_collection[i].segment_order_index] = i

            for i in range(0, len(self.manager.ordered_list_of_locations)):
                if i in index_collected_trips:
                    segment_by_segment_ridership += ';'+str(self.trip_collection[index_collected_trips[i]].pasengers_on_board)
                else:
                    segment_by_segment_ridership += ';-1'

        return aggregated_part + segment_by_segment_ridership


class VehiclePT(Vehicle):

    def __init__(self, vehicle_id: int, location: Location, capacity: int, manager=None, trip_collection=None):
        super(VehiclePT, self).__init__(vehicle_id, location, capacity, manager, trip_collection)
        self.departure = None
        self.available_for_assignment = True
        self.type = 'pt_vehicle'

    def register_departure(self, departure: Departure):
        self.departure = departure

    def collect_trip(self, start_location: Location, end_location: Location, distance: int, on_board: int, start_time: int,
                     end_time: int):
        if self.trip_collection is not None:

            if self.departure is not None:
                segment_order_index = self.manager.get_segment_index(start_location)
                if segment_order_index is None:
                    raise Exception('Logic ERROR: there should not be unknown segment index for defined start_location of vehicle trip')
                trip_t = TripVehiclePT(start_location, end_location, distance, on_board,
                                       start_time, end_time, self, self.manager,self.departure,
                                       segment_order_index)
                self.trip_collection.append(trip_t)
                self.departure.collect_trip(trip_t)


class VehiclePT_with_departures_plan(VehiclePT):

    def __init__(self, vehicle_id: int, location: Location, capacity: int, manager=None, trip_collection=None):
        super(VehiclePT_with_departures_plan, self).__init__(vehicle_id, location, capacity, manager, trip_collection)
        self.departure_managers = TripCollection(vehicle_id)
        self.type = 'pt_vehicle_with_departure_plan'

    def register_departure_manager(self, manager, start_time: int, end_time: int):
        print('registering trip for vehicle:',self.id, ' for dep:',manager.departure_id, 'for line:',manager.transit_line_manager.line_manager.line_id, ' for direction:', manager.transit_line_manager.direction_id, 'start_time',start_time,'end_time',end_time)
        self.departure_managers.register_trip(TripVehiclePT(manager.ordered_list_of_locations[0], manager.ordered_list_of_locations[-1], None, None, start_time, end_time, self, manager, None, None))

    def get_active_departure_manager(self):
        if self.departure_managers.active_trip is not None:
            return self.departure_managers.active_trip.manager
        else:
            return None

    def move_active_departure_manager_completed(self,):
        return self.departure_managers.move_active_trip_to_executed(self.departure_managers.active_trip)

    def get_next_departure_manager(self):
        #print('geting_next_trip for',self.id,self.departure_managers.trips.num)
        trip_t = self.departure_managers.get_next_trip()
        if trip_t is not None:
            #print('geting_next_trip for',self.id,trip_t.manager.departure_id, self.departure_managers.trips.num)
            return trip_t.manager
        else:
            return None

    def is_departure_manager_in_plan(self, manager):
        item = self.departure_managers.trips.start
        while item is not None:
            if item.obj.manager == manager:
                return True
            item = item.next
        return False

    def is_departure_manager_next(self, manager):
        item = self.departure_managers.trips.start
        if item.next.obj.manager == manager:
                return True
        return False

    def get_active_departure_start(self):
        if self.departure.active_trip is not None:
            return self.departure.active_trip.start_time
        else:
            return None

    def collect_trip(self, start_location: Location, end_location: Location, distance: int, on_board: int, start_time: int,
                     end_time: int):
        if self.trip_collection is not None:
            if self.departure is not None:
                segment_order_index = self.manager.get_segment_index(start_location)
                if segment_order_index is None:
                    print('dep:', self.manager.departure_id, self.id, start_location.id, end_location.id)
                    raise Exception('Logic ERROR: there should not be unknown segment index for defined start_location of vehicle trip')
                trip_t = TripVehiclePT(start_location, end_location, distance, on_board,
                                       start_time, end_time, self, self.manager,self.departure,
                                       segment_order_index)
                self.trip_collection.append(trip_t)
                self.departure.collect_trip(trip_t)


class PublicTransportManager(FleetManager):

    def __init__(self, line_id, mode: str, case_study: CaseStudy, probability_send_vehicle_to_longest_waiting: float=0.0,
                 defualt_redistribution_algorithm=None):
        super(PublicTransportManager, self).__init__(case_study)
        self.id = line_id
        self.mode = mode
        self.line_id = line_id
        self.departure_last_id = 0
        self.departures = []
        self.type = 'public transport fleet manager'

    def get_segment_index(self, location):
        return self.location_id_to_index_in_list[location.id]

    def board_passengers(self, vehicle: Vehicle, location: Location):
        if self.simulator.config.detailed_terminal_print_of_simulation:
            print(' Boarding ...', vehicle.id, vehicle.empty_space(), 'num of waiting passengers:',
                  location.passangers.length,' on location ',location.id,' and line',self.line_id)
        if vehicle.empty_space() > 0:
            item = location.passangers.start
            if item is not None:
                while vehicle.empty_space() > 0 and item is not None:
                    if self.simulator.config.detailed_terminal_print_of_simulation:
                        print('   Boarding ...', vehicle.id, vehicle.empty_space(), 'passenger org', item.obj.location.id,
                              'des', item.obj.destination_location.id,'num of waiting passengers:',location.passangers.length)
                    ### IT MAY BE BETTER IF WE ASK passenger MANAGER if passenger should board so we can link it in future with choice model or deccisions
                    if item.obj.get_destination().id in self.location_id_to_index_in_list:
                        passenger = item.obj
                        if vehicle.id == -99:
                            print('      Boarding -99 pass', passenger.id)
                        destination = passenger.select_destination()
                        item.obj.register_borded_time(self.simulator.time_line.actual_time)
                        item = item.next_item
                        #self.unregister_passenger(passenger)
                        location.remove_passenger(passenger)
                        # !!! Unregister from DRS
                        if passenger.manager is not None:
                            passenger.manager.unregister_passenger(passenger)
                        if passenger.id == 62595908:
                            print(' &&& Boarding passanger 62595908', vehicle.id, location.id)
                            #exit(0)
                        vehicle.add_passenger(passenger, destination, self.simulator.time_line.actual_time)
                        if self.simulator.config.detailed_terminal_print_of_simulation:
                            print('   Boarded!', vehicle.id, vehicle.empty_space(), 'passenger ', passenger.id,' line',passenger.destination_location.id,'num of waiting passengers:',location.passangers.length)
                    else:
                        item = item.next_item
                while item is not None:
                    if item.obj.get_destination().id in self.location_id_to_index_in_list:
                        if self.simulator.config.detailed_terminal_print_of_simulation or item.obj.id == 62595908:
                            print('   Denied Boarding!', vehicle.id, vehicle.empty_space(), 'passenger ', item.obj.id,' line',item.obj.destination_location.id,'num of waiting passengers:',location.passangers.length)
                        item.obj.register_denied_bording()
                    item = item.next_item
            else:
                if self.simulator.config.detailed_terminal_print_of_simulation:
                    print(' No passenger on stations')

    def create_new_departure_for_vehicle(self, vehicle:VehiclePT, departure_time: int, start_location: Location, end_location: Location,
                                         manager = None):
        self.departure_last_id += 1
        trip_collection_p = None
        if vehicle.trip_collection is not None:
            trip_collection_p = True
        if manager is None:
            manager = self
        dep = Departure(self.departure_last_id, manager, vehicle, departure_time, start_location, end_location, trip_collection_p)
        self.departures.append(dep)
        vehicle.register_departure(dep)
        return dep



class TransitLineManager(PublicTransportManager):
    """This Line Manager is for FIXED loaded GTFS or AVL, so all times and locations are predetermined from data."""

    def __init__(self, line_id: int, line_number:str, mode: str, case_study: CaseStudy):
        super(TransitLineManager, self).__init__(line_id, mode, case_study)
        self.direction_managers = {}
        self.line_number = line_number

    def register_direction_manager(self, direction_manager):
        if direction_manager.direction_id not in self.direction_managers:
            self.direction_managers[direction_manager.direction_id] = direction_manager
        else:
            raise Exception('Logical ERROR: attempt to register again already registered direction on line')

    def get_the_next_stop_for_vehicle(self, vehicle: Vehicle, location:Location):
        # for loaded GTFS and AVL there is no managment around vehicle assignment,
        # assignment of vehicles is loaded and provided in data; so when departure serve ends,
        # we do not consider re-assignment, it should already be in data load
        pass

class TransitLineOneDirectionManager(PublicTransportManager):
    """This Line Manager is for FIXED loaded GTFS or AVL, so all times and locations are predetermined from data."""

    def __init__(self, line_id:int, line_number: str, mode: str, direction_id: int, line_manager: TransitLineManager,
                 ordered_list_of_locations: list, case_study: CaseStudy):
        super(TransitLineOneDirectionManager, self).__init__(line_id, mode, case_study)
        self.line_manager = line_manager
        self.line_number = line_number
        self.direction_id = direction_id
        self.ordered_list_of_locations = ordered_list_of_locations
        self.location_id_to_index = {}
        if ordered_list_of_locations is not None:
            for i in range(0, len(ordered_list_of_locations)):
                if ordered_list_of_locations[i].id in self.location_id_to_index:
                    if isinstance(self.location_id_to_index[ordered_list_of_locations[i].id], list):
                        self.location_id_to_index[self.ordered_list_of_locations[i].id].append(i)
                    else:
                        self.location_id_to_index[self.ordered_list_of_locations[i].id] = [
                            self.location_id_to_index[self.ordered_list_of_locations[i].id], i]
                else:
                    self.location_id_to_index[self.ordered_list_of_locations[i].id] = i
        self.line_manager.register_direction_manager(self)

    def get_segment_index(self, location: Location):
        if location.id in self.location_id_to_index:
            if isinstance(self.location_id_to_index[location.id], list):
                if self.last_location_index is None:
                    return self.location_id_to_index[location.id][0]
                else:
                    for i in range(0, len(self.location_id_to_index[location.id])):
                        if self.last_location_index < self.location_id_to_index[location.id][i]:
                            return self.location_id_to_index[location.id][i]
                    return None
            else:
                return self.location_id_to_index[location.id]
        else:
            return None

    def get_list_of_stops_btw_two_stops(self, from_index, to_index):
        stop_path = []
        for i in range(from_index, to_index + 1):
            stop_path.append(self.ordered_list_of_locations[i].id)
        return stop_path

    def get_segment_index_first_occurance(self, location: Location):
        if location.id in self.location_id_to_index:
            if isinstance(self.location_id_to_index[location.id], list):
                    return self.location_id_to_index[location.id][0]
            else:
                return self.location_id_to_index[location.id]
        else:
            return None

    def get_segment_index_last_occurance(self, location: Location):
        if location.id in self.location_id_to_index:
            if isinstance(self.location_id_to_index[location.id], list):
                    return self.location_id_to_index[location.id][-1]
            else:
                return self.location_id_to_index[location.id]
        else:
            return None

    def get_the_next_stop_for_vehicle(self, vehicle: Vehicle, location:Location=None):
        if vehicle.location is not None:
            current_location_index = self.get_segment_index(vehicle.location)
        else:
            current_location_index = self.get_segment_index(location)
        if current_location_index >= len(self.ordered_list_of_locations):
            return self.line_manager.get_the_next_stop_for_vehicle(vehicle, location)
        else:
            return current_location_index + 1

    def GetLocation(self, location_index: int):
        return self.ordered_list_of_locations[location_index]

    def GetIndexOfLocation(self, location: Location):
        pass


class TransitStopPlannedSegmentObservations(object):

    def __init__(self, arrival_time: int, departure_time: int, time_on_stop:int, travel_time_to_next_location: int,
                 distance_to_the_next_location: int, arrival_time_observed:bool = True,
                 departure_time_observed: bool = True, travel_time_observed:bool = True,
                 time_on_stop_observed:bool=True):

        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.time_on_stop = time_on_stop
        self.travel_time_to_next_location = travel_time_to_next_location
        self.distance_to_the_next_location = distance_to_the_next_location
        self.arrival_time_observed = arrival_time_observed
        self.departure_time_observed = departure_time_observed
        self.travel_time_observed = travel_time_observed
        self.time_on_stop_observed = time_on_stop_observed

    def to_string(self):
        return 'arrival_time: '+str(self.arrival_time) + ' departure_time: '+str(self.departure_time)+' time_on_stop: '+ str(self.time_on_stop) \
                +' time_to_next: '+str(self.travel_time_to_next_location)+' distance_to_next: ' + str(self.distance_to_the_next_location)


class TransitStopSimulationObservations(object):

    def __init__(self, arrival_time: int = None, departure_time: int = None, time_on_stop:int = None,
                 travel_time_to_next_location:int = None, distance_to_the_next_location: int = None):

        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.time_on_stop = time_on_stop
        self.travel_time_to_next_location = travel_time_to_next_location
        self.distance_to_the_next_location = distance_to_the_next_location

    def to_string(self):
        return 'arrival_time: '+str(self.arrival_time) + ' departure_time: '+str(self.departure_time)+' time_on_stop: '+ str(self.time_on_stop) \
                +' time_to_next: '+str(self.travel_time_to_next_location)+' distance_to_next: ' + str(self.distance_to_the_next_location)


class TransitLineDepartureManager(object):
    """This Line Manager is for FIXED loaded GTFS or AVL, so all times and locations are predetermined from data.
    Inputs: 1. transit_line_manager: to whiche Line-Direction Manager it belongs to
            2. departure_id: ID of this departure
            3. ordered_list_of_locations - order of location in travel sequence
            4. case_study - reference to case-study instance that defines all the simulation for certain decission tasks
            5. planned_vehicle - for specifying the vehicle
            6. fixed_vehicle - can planned vehicle change eventually if not available or delayed"""

    def __init__(self, transit_line_manager: TransitLineOneDirectionManager, departure_id,
                 ordered_list_of_locations: list, case_study: CaseStudy, planned_vehicle: Vehicle = None, fixed_vehicle:bool=False):
        if planned_vehicle is None and fixed_vehicle:
            raise Exception('Login Input ERROR: vehicle can not be fixed if planned_vehicle input is NONE: check the inputs')
        self.id = departure_id
        self.fixed_vehicle = fixed_vehicle
        self.type = 'PT line single departure manager'
        self.case_study = case_study
        self.simulator = case_study.simulator
        self.transit_line_manager = transit_line_manager
        self.departure_id = departure_id
        self.ordered_list_of_locations = ordered_list_of_locations
        self.location_id_to_index = {}
        for i in range(0, len(ordered_list_of_locations)):
            if ordered_list_of_locations[i].id in self.location_id_to_index:
                if isinstance(self.location_id_to_index[ordered_list_of_locations[i].id], list):
                    self.location_id_to_index[self.ordered_list_of_locations[i].id].append(i)
                else:
                    self.location_id_to_index[self.ordered_list_of_locations[i].id] = [self.location_id_to_index[self.ordered_list_of_locations[i].id], i]
            else:
                self.location_id_to_index[self.ordered_list_of_locations[i].id] = i
        if transit_line_manager is not None:
            if transit_line_manager.ordered_list_of_locations is None or len(transit_line_manager.ordered_list_of_locations) <= len(self.ordered_list_of_locations):
                transit_line_manager.ordered_list_of_locations = self.ordered_list_of_locations
                transit_line_manager.location_id_to_index = self.location_id_to_index
        self.planned_vehicle = planned_vehicle
        self.vehicle = None
        #if self.vehicle is not None:
        #    self.vehicle.manager = self
        #    self.transit_line_manager.add_vehicle(vehicle)
        self.last_location_index = None
        self.status = DepartureManagerStatus.planned.value
        self.departure_delayed = None
        self.passengers_served = 0
        self.simulation_observation = []

    def get_simulation_departure_time_by_locationindex(self, location_index: int):
        return self.simulation_observation[location_index].departure_time

    def get_simulation_arrival_time_by_locationindex(self, location_index: int):
        return self.simulation_observation[location_index].arrival_time

    def get_segment_index(self, location: Location):
        if location.id in self.location_id_to_index:
            if isinstance(self.location_id_to_index[location.id], list):
                if self.last_location_index is None:
                    return self.location_id_to_index[location.id][0]
                else:
                    for i in range(0, len(self.location_id_to_index[location.id])):
                        if self.last_location_index <= self.location_id_to_index[location.id][i]:
                            return self.location_id_to_index[location.id][i]
            else:
                return self.location_id_to_index[location.id]
        else:
            return None

    def get_segment_index_first_occurance(self, location: Location):
        if location.id in self.location_id_to_index:
            if isinstance(self.location_id_to_index[location.id], list):
                    return self.location_id_to_index[location.id][0]
            else:
                return self.location_id_to_index[location.id]
        else:
            return None

    def get_segment_index_last_occurance(self, location: Location):
        if location.id in self.location_id_to_index:
            if isinstance(self.location_id_to_index[location.id], list):
                    return self.location_id_to_index[location.id][-1]
            else:
                return self.location_id_to_index[location.id]
        else:
            return None

    def add_vehicle(self, vehicle: Vehicle):
        if self.vehicle is None:
            self.vehicle = vehicle
            vehicle.manager = self
            self.transit_line_manager.add_vehicle(vehicle)
        else:
            if self.vehicle.id == vehicle.id:
                vehicle.manager = self
            else:
                raise Exception('Logical ERROR: there can not be assign more as one vehicle to departure')

    def number_of_vehicles(self):
        if self.vehicle is not None:
            return 1
        else:
            return 0

    def get_the_next_stop_for_vehicle(self, vehicle: Vehicle, location:Location):
        if self.ordered_list_of_locations is not None:
            current_location_index = self.get_segment_index(location)
            if current_location_index >= len(self.ordered_list_of_locations) - 1:
                return self.transit_line_manager.line_manager.get_the_next_stop_for_vehicle(vehicle, location)
            else:
                return current_location_index + 1, False
        else:
            return self.transit_line_manager.get_the_next_stop_for_vehicle(vehicle, location)

    def GetLocation(self, location_index: int):
        if self.ordered_list_of_locations is not None:
            return self.ordered_list_of_locations[location_index]
        else:
            self.transit_line_manager.GetLocation(location_index)

    def GetIndexOfLocation(self, location: Location):
        pass

    def get_distance(self, vehicle: Vehicle, origin:Location, destination:Location, origin_index: int, destination_index: int):
        return self.case_study.get_distance(None, None, origin, destination, origin_index, destination_index)

    def get_travel_time(self, vehicle: Vehicle, origin:Location, destination:Location, origin_index: int, destination_index: int):
        return self.case_study.get_travel_time(None, None, origin, destination, origin_index, destination_index)

    def get_expected_departure_time_and_stop_time(self, loaded_passanger_numebr:int, location:Location, vehicle:Vehicle):
        if loaded_passanger_numebr >= 0:
            time_on_stop = self.case_study.get_boarding_time(loaded_passanger_numebr, self.transit_line_manager.line_manager.line_mode, location, vehicle)
            departure_time = self.simulator.time_line.actual_time + time_on_stop
            self.create_departure_event_from_the_location(vehicle, location, departure_time, time_on_stop)
            return departure_time, time_on_stop
        else:
            raise Exception('Logical ERROR: There should never be negative number of passangers on board')

    def create_new_arrival_event_to_location(self, vehicle:Vehicle, location: Location):
        if self.simulator.config.detailed_terminal_print_of_simulation:
            print('FM line',self.transit_line_manager.line_manager.line_id,
                  'dep',self.departure_id, 'making arrival event')
        if self.departure_id == 18912:
            print('* Create Arrival Event from location', location.id, self.departure_id)
        destination, artificial_trip = self.get_the_next_stop_for_vehicle(vehicle,location)
        location_index = self.get_segment_index(location)
        destination_index = self.get_segment_index(destination)
        if destination is not None:
            # dis and travel times ans arrival times are predeterminated take from GTFS AVL
            dis = self.case_study.get_distance(self, vehicle, location, destination, location_index, destination_index)
            tt = self.case_study.get_travel_time(self, vehicle, location, destination, location_index, destination_index)
            self.simulator.add_event(VehicleStationArrivalEvent_line_with_direction(self.simulator.time_line.actual_time + tt,
                                                                self, vehicle, destination, location, dis, tt, None, artificial_trip))
        else:
            raise Exception('Logical ERROR: There can not be crated Arrival Event to Location if destination is unknown')

    def create_departure_event_from_the_location(self, vehicle: Vehicle, location: Location, departure_time: int = None,
                                                 stop_time: int = None):
        if self.departure_id == 18912:
            print('* Create Departure Event from location', location.id, departure_time, self.departure_id)
        self.simulator.add_event(VehicleStationDepartureEvent_line_with_direction(departure_time, self, vehicle, location, stop_time))

    def get_status(self):
        return DepartureManagerStatus(self.status).name, self.status

    def is_trip_to_destination_from_location_possible(self, start_location: Location, end_location: Location):
        if end_location.id in self.location_id_to_index and start_location.id in self.location_id_to_index:
            start_location_index = self.get_segment_index(start_location)
            end_location_index = self.get_segment_index(end_location)
            if start_location_index is not None and end_location_index is not None:
                if end_location_index > start_location_index:
                    return True
        return False

    def board_passengers(self, vehicle: Vehicle, location: Location):
        location_index = self.get_segment_index(location)
        if self.simulator.config.detailed_terminal_print_of_simulation:
            print(' Boarding ...', vehicle.id, vehicle.empty_space(), 'num of waiting passengers:',
                  location.passangers.length,' on location ',location.id,' and line',
                  self.transit_line_manager.line_manager.line_id, 'dir:',self.transit_line_manager.direction_id,
                  'dep:', self.departure_id, ' dep on vehicle:', vehicle.manager)
            #item = location.passangers.start
            #if item is not None:
            #    while vehicle.empty_space() > 0 and item is not None:
            #        print('     passanger:',item.obj.id)
            #        item = item.next_item
        if vehicle.empty_space() > 0:
            item = location.passangers.start
            if item is not None:
                while vehicle.empty_space() > 0 and item is not None:
                    # vehicle has the capacity; Does passanger board
                    trip_in_plan = item.obj.get_current_trip_in_progress()
                    start_location = trip_in_plan.start_location
                    destination = trip_in_plan.end_location

                    if self.simulator.config.detailed_terminal_print_of_simulation or self.id == 18912:
                        print('@ Boarding ...', vehicle.id, vehicle.empty_space(), 'passenger ', item.obj.id,' org', start_location.id, 'des', destination.id, 'num of waiting passengers:',location.passangers.length)
                        #if item.next_item is not None:
                        #    print('   next passenger ', item.next_item.obj.id)

                    # asking if the boarding is accepted by passanger, vehicle provide information of stops it serves
                    # and passanger evaluates if the trip takes passanger to the intended destination
                    if item.obj.will_you_board_departure(self):
                            passenger = item.obj
                            if passenger.id == 62595908:
                                print('   - @@ Boarding 62595908', vehicle.id,location.id,location_index,self.last_location_index)
                            item = item.next_item
                            # operations about boarding passanger
                            vehicle.add_passenger(passenger, destination, self.simulator.time_line.actual_time)
                            passenger.register_borded_time(self.simulator.time_line.actual_time)
                            location.remove_passenger(passenger, self.transit_line_manager.line_manager.line_id, self.transit_line_manager.direction_id)
                            act_trip = passenger.journey_collection.active_journey.active_trip
                            act_trip.observed_start_location_index = location_index
                            if passenger.id == 62595908:
                                print('    - @@ Boarding2 62595908', vehicle.id,location.id,act_trip.start_location.id,act_trip.end_location.id,destination.id)
                                #exit(0)
                            # !!! Unregister from DRS
                            if passenger.manager is not None:
                                passenger.manager.unregister_passenger(passenger)
                            if self.simulator.config.detailed_terminal_print_of_simulation:
                                print('    - @@ Boarded!', vehicle.id, vehicle.empty_space(), 'passenger ', passenger.id,'line',self.transit_line_manager.direction_id, 'dep:', self.departure_id ,'des:',destination.id, 'dep at vehicle:', self.departure_id,'num of waiting passengers:',location.passangers.length)
                    else:
                        item = item.next_item
                while item is not None:
                    if item.obj.will_you_board_departure(self):
                        if self.simulator.config.detailed_terminal_print_of_simulation or passenger.id == 62595908:
                            print('   Denied boarding!', vehicle.id, vehicle.empty_space(), 'passenger ', passenger.id,' line',passenger.destination_location.id,'num of waiting passengers:',location.passangers.length)
                        item.obj.register_denied_bording()
                    item = item.next_item
            else:
                if self.simulator.config.detailed_terminal_print_of_simulation:
                    print(' No passenger on stations')

    def take_passenger_from_actual_station(self, vehicle:Vehicle, location: Location):
            if self.simulator.config.detailed_terminal_print_of_simulation or self.id == 18912:
                print('FM line',self.transit_line_manager.line_manager.line_id,'dep',self.departure_id,'taking passangers; vehicle_space',vehicle.empty_space(),'and waiting passangers',location.total_number_of_passangers, location.id, location, location.passangers.start, location.passangers.length, location.total_number_of_passangers)
            if vehicle.empty_space() > 0 and location.total_number_of_passangers > 0:
                self.board_passengers(vehicle, location)
            else:
                return 0

    def register_observation(self, location_index, arrival_time: int = None, time_on_stop: int = None,
                             departure_time: int = None, travel_time_to_next_location: int = None,
                             distance_to_the_next_location: int = None):

        #location_index = self.get_segment_index(location)
        if location_index > len(self.simulation_observation) - 1:
            obs = TransitStopSimulationObservations(arrival_time, time_on_stop, departure_time)
            self.simulation_observation.append(obs)
        else:
            if arrival_time is not None:
                self.simulation_observation[location_index].arrival_time = arrival_time
            if time_on_stop is not None:
                self.simulation_observation[location_index].time_on_stop = time_on_stop
            if departure_time is not None:
                self.simulation_observation[location_index].departure_time = departure_time
            if travel_time_to_next_location is not None:
                self.simulation_observation[location_index].travel_time_to_next_location = travel_time_to_next_location
            if distance_to_the_next_location is not None:
                self.simulation_observation[location_index].distance_to_the_next_location = distance_to_the_next_location


    def departure_completed(self, vehicle):
        if vehicle.id == -99:
            print('  - Completing departure :',self.departure_id,'n_pass',len(vehicle.passengers),vehicle.total_boarded)
        self.status = DepartureManagerStatus.completed.value
        vehicle.move_active_departure_manager_completed()
        vehicle.location.remove_vehicle(vehicle, self.transit_line_manager.line_manager.line_id,
                                             self.transit_line_manager.direction_id)
        vehicle.location = None
        vehicle.manager = vehicle.get_next_departure_manager()
        vehicle.available_for_assignment = True


    def vehicle_arrived_to_location(self, event: VehicleStationArrivalEvent_line_with_direction):
        if self.departure_id == 18912:
            print('* Arrival for 18912 veh:', event.vehicle.id, event.traveling_from_location, event.location.id, self.simulator.time_line.actual_time,'n_pass',len(event.vehicle.passengers),event.vehicle.total_boarded)
        if self.departure_id == 18912:
            print('* Arrival for 18912 veh:', event.vehicle.id, event.traveling_from_location, event.location.id, self.simulator.time_line.actual_time,'n_pass',len(event.vehicle.passengers),event.vehicle.total_boarded)
        if self.departure_id == 18912:
            print('BBB',self.departure_id, event.location.id,self.last_location_index, self.simulator.time_line.actual_time,'n_pass',len(event.vehicle.passengers),event.vehicle.total_boarded,'veh:', event.vehicle.id)
        last_location_index_t = self.get_segment_index(event.location)
        # THERE has beeen seen in GTFS-RT two same stops in sequence -> we need to iterate +1 by force as id_show not the true order from self.location_id_to_index
        if self.last_location_index == last_location_index_t and isinstance(self.location_id_to_index[event.location.id],list):
            #print('SAME two stops in sequence - force move in sequence')
            self.last_location_index += 1
        else:
            self.last_location_index = last_location_index_t
        if self.departure_id == 18912:
            print('AAAA',self.departure_id,event.location.id,self.last_location_index,'n_pass',len(event.vehicle.passengers),'veh:', event.vehicle.id)

        if self.last_location_index == 0 and event.location.id == self.ordered_list_of_locations[0].id:

            if len(event.vehicle.passengers) > 0:
                if self.departure_id == 18912:
                    print('  - 18912 not empty at the start','veh:', event.vehicle.id)
                if self.departure_id == 18912:
                    print('  - 18912 not empty at the start','veh:', event.vehicle.id)
                print('departure_id',self.departure_id,'n_pass',len(event.vehicle.passengers),'veh_id:',event.vehicle.id)
                raise Exception('Logic ERROR: vehicle at the start of the departure should be empty but there is someone on board')
            # this has been moved to new EVENT  StartArrival to ensure vehicle assignment
            ### We need to check if intended vehicle can start new departure on this time or is occupied and wait or find another -> go to case-study level to check
#            vehicle_t = self.case_study.PT_line_departure_manager_vehicle_request_and_decission(self, self.vehicle)
#            ### now we register vehicle for this departure
#            if not self.vehicle == vehicle_t:
#                self.remo
            self.status = DepartureManagerStatus.in_progress.value

            if self.simulator.config.detailed_terminal_print_of_simulation:
               print('DEP-START at', self.simulator.time_line.actual_time, 'FM line',
                     self.transit_line_manager.line_manager.line_id,
                     'dep', self.departure_id, ' vehicle_departures', event.vehicle.id,
                     'on location', event.location.id, 'status:', self.get_status(), 'current index', self.last_location_index,'/',len(self.ordered_list_of_locations)-1)
        #else:
        #    self.last_location_index = self.get_segment_index(event.location)

        # if self.line_id == 0:
        #if self.departure_id == 188:
        #        print('(*) Arrival EVENT for 188 to', event.location.id, self.simulator.time_line.actual_time,
        #              event.execution_time)

        ### START-registering observed travel times on arrival to location
        if self.last_location_index == 0:
            self.register_observation(self.last_location_index, arrival_time=self.simulator.time_line.actual_time)
        elif event.traveling_from_location is not None:
            from_location_index = self.get_segment_index(event.traveling_from_location)
            #print(self.departure_id, from_location_index, self.last_location_index, event.traveling_from_location.id)
            # this is the case if there are two stops in sequence the same the self.last_location_index close it from_location_index to be None so below constrain fix that
            if from_location_index is None and self.last_location_index is not None and isinstance(self.location_id_to_index[event.traveling_from_location.id], list):
                from_location_index = self.last_location_index - 1
            # this is the case if there are two stops in sequence the same the self.last_location_index not closed them yet but
            elif from_location_index >= self.last_location_index and isinstance(self.location_id_to_index[event.traveling_from_location.id], list):
                from_location_index = self.last_location_index - 1
            if from_location_index >= 0:
                travel_time_to_the_location = self.simulator.time_line.actual_time - self.simulation_observation[from_location_index].departure_time
                self.register_observation(from_location_index,
                                          travel_time_to_next_location = travel_time_to_the_location,
                                          distance_to_the_next_location = event.distance)
                self.register_observation(self.last_location_index, arrival_time=self.simulator.time_line.actual_time)
        ### END-registering observed travel times on arrival to location

        if self.simulator.config.detailed_terminal_print_of_simulation:
            print(self.simulator.time_line.actual_time, 'FM line', self.transit_line_manager.line_manager.line_id, ' vehicle_arrived', event.vehicle.id,
                  'dep',self.departure_id,
                  'on location',event.location.id, event.location.id, 'status:',self.get_status(), 'current index',self.last_location_index,'/',len(self.ordered_list_of_locations)-1)
        #if self.simulator.time_line.actual_time%1000 <= 100:
        #    self.case_study.stop_simulation_if_all_passengers_served()
        # try to unload the passengers with destination
        if event.vehicle.id == -99:
            print('* Vehicle -99 serving dep:',self.departure_id)
        if event.vehicle.total_boarded > 0:
            if self.departure_id == 18912:
                print('  * Unboardning 18912 serving dep:',self.departure_id,event.location.id, self.simulator.time_line.actual_time)
            if event.vehicle.location == event.location:
                #for j, obj in enumerate(event.vehicle.passengers):
                  #  if self.simulator.time_line.actual_time - event.vehicle.passengers[obj].borded_times[0] > 4000:
                  #      print(event.execution_time)
                  #      print('passenger still on board after 3000 seconds',
                  #            self.line_id,event.vehicle.id, event.vehicle.passengers[obj].id,
                  #            event.vehicle.passengers[obj].location.id,
                  #            event.vehicle.passengers[obj].destination_location.id)
                  #      print(event.vehicle.passengers[obj].transfers)
                  #      for i in range(0,len(event.vehicle.passengers[obj].transfers)):
                  #          print(event.vehicle.passengers[obj].transfers[i][0].id,event.vehicle.passengers[obj].transfers[i][1].id)
                  #      print('at the moment looking for des:', event.vehicle.passengers[obj].transfer_index)
                  #      for i, obj in enumerate(event.vehicle.passengers_leaving_on_location):
                  #          for j in range(0,len(event.vehicle.passengers_leaving_on_location[obj])):
                  #              print(obj,event.vehicle.passengers_leaving_on_location[obj][j].id)
                  #      exit(0)
                if self.simulator.config.detailed_terminal_print_of_simulation:
                    print(self.simulator.time_line.actual_time, ' FM line', self.transit_line_manager.line_manager.line_id,'dir',self.transit_line_manager.direction_id, 'dep', self.departure_id , 'unload', event.vehicle.id, event.location.id)
                t_array = event.vehicle.get_leaving_passengers(event.location)
                if t_array is not None and len(t_array) > 0:
                    if self.simulator.config.detailed_terminal_print_of_simulation:
                        print('     unloading :', len(t_array), 'number of passenger', 'on board',
                              event.vehicle.total_boarded, 'on vehicle:', event.vehicle.id)
                    for i in range(0, len(t_array)):
                        if self.departure_id == 18912:
                            print('  * Unboardning -99 pass:', t_array[i].id, self.simulator.time_line.actual_time)
                        if self.simulator.config.detailed_terminal_print_of_simulation:
                            print('         unload :', t_array[i].id)
                        if t_array[i].id == 62595908:
                           print('Unboarding 62595908',self.departure_id, event.traveling_from_location, event.location.id,self.last_location_index, self.simulator.time_line.actual_time)
                        act_trip = t_array[i].journey_collection.active_journey.active_trip
                        act_trip.observed_end_location_index = self.last_location_index
                        self.simulator.immediate_procees_event(PassengerUnloadEvent(self.simulator.time_line.actual_time,
                                                                                    t_array[i], event.location,
                                                                                    event.vehicle, event.travel_time,
                                                                                    event.distance,
                                                                                    event.on_board))
                        self.passengers_served += 1
                        event.vehicle.departure.served_passengers += 1
                else:
                    if self.simulator.config.detailed_terminal_print_of_simulation:
                        print(self.simulator.time_line.actual_time,' no one to leave taxi')
                if self.simulator.config.detailed_terminal_print_of_simulation:
                    print(self.simulator.time_line.actual_time,' served passengers', self.passengers_served)
            else:
                print(event.vehicle.location.id, event.passenger.location.id)
                raise Exception('ERROR: Vehicle is not on dedicated station as it should arrived')
        # if there is someone on stop with destination in plan take them
#        self.case_study.stop_simulation_if_all_passengers_served()
        #print('@@@@',event.vehicle)
        if event.vehicle.departure is None:
            dep = self.transit_line_manager.create_new_departure_for_vehicle(event.vehicle, self.simulator.time_line.actual_time,
                                                                             event.location, self.ordered_list_of_locations[-1])
        else:
            event.vehicle.departure.n_segments += 1

        if self.departure_id == 18912:
            print( '-progress',event.location.id, self.ordered_list_of_locations[-1].id, self.last_location_index, len(self.ordered_list_of_locations) - 1,'n_pass',len(event.vehicle.passengers))
        if event.location.id != self.ordered_list_of_locations[-1].id or self.last_location_index < len(self.ordered_list_of_locations) - 1:
            if self.departure_id == 18912:
                print('     -continuing')
            passag_before = len(event.vehicle.passengers)
            self.take_passenger_from_actual_station(event.vehicle, event.location)
            loaded_passanger_numebr = len(event.vehicle.passengers) - passag_before

            departure_time, time_on_stop = self.get_expected_departure_time_and_stop_time(loaded_passanger_numebr, event.location, event.vehicle)
            if self.departure_id == 18912:
                print('* Event created from arrival for 18912', event.location.id, self.simulator.time_line.actual_time)
            self.create_departure_event_from_the_location(event.vehicle, event.location, departure_time, time_on_stop)
        else:
            if self.departure_id == 18912:
                print('     -completeting ',len(event.vehicle.passengers))
            #print('@@@@ 22', event.vehicle)
            #self.last_location_index = self.location_id_to_index[event.location.id]
            self.departure_completed(event.vehicle)

            if len(event.vehicle.passengers) > 0:
                for i,obj in enumerate(event.vehicle.passengers):
                    print('        - passenger left on board:',event.vehicle.passengers[obj].id)
                if self.departure_id == 18912:
                    print('  - 18912 not empty at the end')
                print('dep:',self.departure_id, 'veh:', event.vehicle.id,'loc:',event.location.id,'n_pas:',len(event.vehicle.passengers))
                raise Exception('Logic ERROR: at the end of vehicle departure the vehicle should be empty but it is NOT')

            if self.simulator.config.detailed_terminal_print_of_simulation:
                print('DEP-END at', self.simulator.time_line.actual_time, 'FM line',
                      self.transit_line_manager.line_manager.line_id,
                      'dep', self.departure_id, ' vehicle_departures', event.vehicle.id,
                      'on location', event.location.id, 'status:',self.get_status(),
                      'current index',self.last_location_index,'/',len(self.ordered_list_of_locations)-1)

    def vehicle_departured_the_location(self, event: VehicleStationDepartureEvent_line_with_direction):
        if self.simulator.config.detailed_terminal_print_of_simulation:
            print(self.simulator.time_line.actual_time, 'FM line', self.transit_line_manager.line_manager.line_id,
                  'dep',self.departure_id,
                  ' vehicle_departures', event.vehicle.id,
                  'on location',event.location.id, 'status:',self.get_status(), 'current index',self.last_location_index,'/',len(self.ordered_list_of_locations))
        self.register_observation(self.last_location_index, departure_time=self.simulator.time_line.actual_time, time_on_stop=event.stop_time)
        self.create_new_arrival_event_to_location(event.vehicle, event.location)


class TransitLineDepartureManager_with_planned_times(TransitLineDepartureManager):

    def __init__(self, transit_line_manager: TransitLineOneDirectionManager, departure_id,
                 ordered_list_of_locations: list, ordered_list_of_planned_observation: list,
                 case_study: CaseStudy, vehicle: Vehicle = None):
        super(TransitLineDepartureManager_with_planned_times, self).__init__(transit_line_manager, departure_id, ordered_list_of_locations, case_study, vehicle)
        if len(ordered_list_of_locations) == len(ordered_list_of_planned_observation):
                pass
        else:
                raise Exception('logic Error: if times are planned the list needs to be same as list of stops, but it is not')
        self.ordered_list_of_planned_observation = ordered_list_of_planned_observation


    def start_departure_by_first_arrival_event(self, vehicle:Vehicle):
        print(vehicle.id, self.transit_line_manager.line_manager.line_id, ' dep',self.departure_id, ' dir',self.transit_line_manager.direction_id)
        vehicle.location = self.ordered_list_of_locations[0]
        if self.simulator.config.detailed_terminal_print_of_simulation:
            print('Scheduling departure on line', self.transit_line_manager.line_manager.line_id, ' dep',self.departure_id, ' dir',self.transit_line_manager.direction_id,
                  'arrival time', self.ordered_list_of_planned_observation[0].arrival_time)

        if self.departure_id == 18912:
            print(' ()()()()(*)(*)(*)(*)(*)(*)(*)(*)(*)(*) START INICIATED 18912 (*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)(*)')
            print(' arrival_time for first:',self.ordered_list_of_planned_observation[0].arrival_time)
        self.simulator.add_event(DepartureStartVehicleStationArrivalEvent_line_with_direction(self.ordered_list_of_planned_observation[0].arrival_time,
                                                            self, vehicle, self.ordered_list_of_locations[0], None, 0, 0, None, True))

    def create_new_arrival_event_to_location(self, vehicle:Vehicle, location: Location):
        if self.departure_id == 18912:
            print('XX call')
        destination, artificial_trip = self.get_the_next_stop_for_vehicle(vehicle, location)
        location_index = self.get_segment_index(location)
        destination_index = self.get_segment_index(destination)
        if destination is not None:
            if self.simulator.config.detailed_terminal_print_of_simulation:
                print('FM line', self.transit_line_manager.line_manager.line_id, 'making arrival event from location',
                      location.id, 'des:',destination.id)
            #print(vehicle, location, destination)
            # dis and travel times ans arrival times are predeterminated take from GTFS AVL
            if location_index == destination_index and location.id == destination.id and destination.id == self.ordered_list_of_locations[destination_index + 1].id:
                destination_index += 1
            dis = self.case_study.get_distance(self, vehicle, location, destination, location_index, destination_index)
            tt = self.case_study.get_travel_time(self, vehicle, location, destination, location_index, destination_index)

            arrival_time = self.ordered_list_of_planned_observation[destination_index].arrival_time
            if self.departure_id == 18912:
                print('XXX', location.id, destination.id, tt, self.simulator.time_line.actual_time, arrival_time, self.departure_delayed)
                #exit(0)
            #print(self.departure_id,self.simulator.time_line.actual_time, tt, arrival_time, self.departure_delayed)
            if self.simulator.time_line.actual_time + tt == arrival_time or (self.departure_delayed is not None and self.simulator.time_line.actual_time + tt <= arrival_time + self.departure_delayed):
                self.simulator.add_event(VehicleStationArrivalEvent_line_with_direction(self.simulator.time_line.actual_time + tt,
                                                                    self, vehicle, destination, location, dis, tt, None, artificial_trip))
            else:
                raise Exception('Logical ERROR: if planned observations used arrival_time and actual_time + tt '
                                'should be the same but it is not, IS there overruled by case_study setting? '
                                ' assumed tt:'+str(tt)+
                                ' current time:' + str(self.simulator.time_line.actual_time) +
                                ' assumed:'+str(self.simulator.time_line.actual_time + tt)+
                                ' expected:'+str(arrival_time)+'  At Line:'+
                                str(self.transit_line_manager.line_manager.line_id)+
                                ' dir:' + str(self.transit_line_manager.direction_id) +
                                ' dep:'+str(self.departure_id) + ' from:' + str(location.id) + ' to:' + str(destination.id), 'departure_delayed_at_start', self.departure_delayed)
        else:
            raise Exception('Logical ERROR: There can not be crated Arrival Event to Location if destination is unknown')

    def get_start_departure_time(self):
        location_index = self.get_segment_index(self.ordered_list_of_locations[0])
        return self.ordered_list_of_planned_observation[location_index].departure_time

    def get_departure_time(self, location: Location):
        location_index = self.get_segment_index(location)
        return self.ordered_list_of_planned_observation[location_index].departure_time

    def get_arrival_time(self, location:Location):
        location_index = self.get_segment_index(location)
        return self.ordered_list_of_planned_observation[location_index].arrival_time

    def get_estimated_time_to_end_departure(self):
        #print('!!! NOT TESTED YET estimated time to end of departure')
        if self.last_location_index is not None:
            if self.simulation_observation[self.last_location_index].arrival_time is not None and \
                self.ordered_list_of_planned_observation[self.last_location_index].arrival_time is not None:
                    return self.ordered_list_of_planned_observation[-1].arrival_time + (self.simulation_observation[self.last_location_index].arrival_time - self.ordered_list_of_planned_observation[self.last_location_index].arrival_time)
            else:
                    return None
        else:
            return self.ordered_list_of_planned_observation[-1].arrival_time

    def get_distance_and_travel_time_between_passenger_origin_destination(self, org_location_index:int, des_location_index:int):
        #print('TT measuring starts')
        if org_location_index <= des_location_index:
            dis = 0
            dis_complete = True
            tt_complete = True
            tt = 0
            for i in range(org_location_index, des_location_index):
                #if self.departure_id == 18912:
                    #print('@',self.simulation_observation[i].distance_to_the_next_location,self.simulation_observation[i].travel_time_to_next_location)
                dis_to_next = self.simulation_observation[i].distance_to_the_next_location
                tt_to_next = self.simulation_observation[i].travel_time_to_next_location
                if dis_to_next is not None:
                    dis += dis_to_next
                else:
                    dis_complete = False
                if tt_to_next is not None:
                    tt += tt_to_next
                else:
                    tt_complete = False
                if i > org_location_index:
                    t_stop = self.simulation_observation[i].time_on_stop
                    if t_stop is not None:
                        tt += t_stop
                    else:
                        tt_complete = False
                #print(org_location_index,i,des_location_index,tt,dis,self.simulation_observation[i].to_string())
            #print('TT measuring endss')
            return dis, self.simulation_observation[des_location_index].arrival_time - self.simulation_observation[org_location_index].departure_time, dis_complete, tt_complete
        else:
            print(self.departure_id,org_location_index, des_location_index)
            raise Exception('Logic Error: when measuring distance/tt from passenger trip origin to destination!')

    def get_distance(self, vehicle: Vehicle, origin:Location, destination:Location, origin_index: int, destination_index: int):
        if origin_index is None:
            origin_index = self.get_segment_index(origin)
        if destination_index is None:
            destination_index = self.get_segment_index(destination)
        #if self.departure_id == 33472:
        #    print('@@@@@@',self.departure_id,self.last_location_index, origin.id, destination.id, origin_index, destination_index)
        if origin_index + 1 == destination_index:
            return self.ordered_list_of_planned_observation[origin_index].distance_to_the_next_location
        else:
            raise Exception('Logic Error: when measuring distance for next segment trip in Departure , org + 1 index and des index should be same but it is NOT!')

    def get_travel_time(self, vehicle: Vehicle, origin:Location, destination:Location, origin_index: int, destination_index: int):
        if origin_index is None:
            origin_index = self.get_segment_index(origin)
        if destination_index is None:
            destination_index = self.get_segment_index(destination)
        #print('TT is ',self.ordered_list_of_planned_observation[org_location_index].travel_time_to_next_location)
        if origin_index + 1 == destination_index:
            return self.ordered_list_of_planned_observation[origin_index].travel_time_to_next_location
        else:
            raise Exception('Logic Error: when measuring travel_time for next segment trip in Departure , org + 1 index and des index should be same but it is NOT!')

    def get_the_next_stop_for_vehicle(self, vehicle: Vehicle, location:Location):
        if self.ordered_list_of_locations is not None:
            current_location_index = self.get_segment_index(location)
            if current_location_index >= len(self.ordered_list_of_locations) - 1:
                return None, False
            else:
                return self.ordered_list_of_locations[current_location_index + 1], False
        else:
            return None, False

    def get_expected_departure_time_and_stop_time(self, loaded_passanger_numebr:int, location:Location, vehicle:Vehicle):
        ### here it does not matter of boarded passengers but it is provided in planned times instead
        current_location_index = self.get_segment_index(vehicle.location)
        dep_t = self.ordered_list_of_planned_observation[current_location_index].departure_time
        stop_t = self.ordered_list_of_planned_observation[current_location_index].time_on_stop
        if self.departure_id == 18912:
            print('     expected time on stop and departure time', self.departure_id, current_location_index, dep_t, stop_t, self.simulator.time_line.actual_time)
        if dep_t < self.simulator.time_line.actual_time:
            if self.departure_delayed is not None:
                if current_location_index > 0:
                    dep_t = self.simulator.time_line.actual_time + stop_t
                else:
                    dep_t = self.simulator.time_line.actual_time
                    stop_t = 0
                    self.departure_delayed = self.simulator.time_line.actual_time - self.ordered_list_of_planned_observation[current_location_index].departure_time
                    #temp_stop_t = stop_t - (self.simulator.time_line.actual_time - dep_t)
                    #if temp_stop_t >= 0:
                    #    stop_t = temp_stop_t
                    #    self.departure_delayed = None
                    #else:
                    #    dep_t = self.simulator.time_line.actual_time
                    #    stop_t = 0
            else:
                raise Exception('Logic ERROR: this departure is not delayed as result of simulation, but input data does not give departure_time after current simulation time')

        if self.departure_id == 18912:
            print('  final stop and dep time on stop', self.departure_id, current_location_index, dep_t, stop_t)
        return dep_t, stop_t


class PublicTransporLineManager(PublicTransportManager):

    def __init__(self, line_id, mode:str, case_study: CaseStudy, ordered_locations_for_line:list,
                 artificial_movements_not_to_count: list = None):
        super(PublicTransporLineManager, self).__init__(line_id, mode, case_study)
        self.list_of_stops_in_order = ordered_locations_for_line
        self.location_id_to_index_in_list = {}
        self.distances = []
        self.travel_times = []
        self.type = 'public transport LINE fleet manager'
        for i in range(0, len(ordered_locations_for_line)):
            self.location_id_to_index_in_list[ordered_locations_for_line[i].id] = i
            if i < len(ordered_locations_for_line)-1:
                self.distances.append(case_study.get_distance(self, None, ordered_locations_for_line[i], ordered_locations_for_line[i+1], i, i+1))
                self.travel_times.append(case_study.get_travel_time(self, None, ordered_locations_for_line[i], ordered_locations_for_line[i+1], i, i+1))

        self.artificial_movements_not_to_count = {}
        if artificial_movements_not_to_count is not None:
            for i in range(0,len(artificial_movements_not_to_count)):
                self.artificial_movements_not_to_count[str(artificial_movements_not_to_count[i][0])
                                                       +'|'+ str(artificial_movements_not_to_count[i][1])] = True

    def get_the_distance_and_travel_time_from_stop_to_stop(self, start_location: Location, end_location: Location):
        index_start = self.location_id_to_index_in_list[start_location.id]
        index_end = self.location_id_to_index_in_list[end_location.id]
        if index_start >= index_end:
            #print(index_start,index_end,start_location.id,end_location.id)
            raise Exception('ERROR: the index of start location should never be higher as end locaiton')
        pom_dis = 0
        pom_tt = 0
        for i in range(index_start,index_end):
            pom_dis += self.distances[i]
            pom_tt += self.travel_times[i]
        return pom_dis,pom_tt

    def get_the_next_stop_for_vehicle(self, vehicle, location):
        # should be defined for Circle it is different after largest it switch to 0
        # FOR line start - end not containing stops for back to start need different logic
        raise Exception('ERROR: Sending vehicle to next stop is not implemented')

    def take_passenger_from_actual_station_and_continue(self, vehicle: Vehicle, location: Location):
            if self.simulator.config.detailed_terminal_print_of_simulation:
                print('FM line',self.line_id, 'taking passangers', vehicle.empty_space(), location.total_number_of_passangers)
            if vehicle.empty_space() > 0 and location.total_number_of_passangers > 0:
                if self.simulator.config.detailed_terminal_print_of_simulation:
                    print(' THERE IS SPACE ON VEHICLE AND THERE ARE PASSANGERS ON LOCATION')
                self.board_passengers(vehicle, location)
            destination, artificial_trip = self.get_the_next_stop_for_vehicle(vehicle, location)
            location_index = self.get_segment_index(destination)
            destination_index = self.get_segment_index(destination)
            vehicle.location.remove_vehicle(vehicle)
            dis = self.case_study.get_distance(self, vehicle, location, destination, location_index, destination_index)
            tt = self.case_study.get_travel_time(self, vehicle, location, destination, location_index, destination_index)
            self.simulator.add_event(VehicleStationArrivalEvent(self.simulator.time_line.actual_time + tt,
                                                                vehicle, destination, dis, tt, None, artificial_trip))

    def vehicle_arrived_to_location(self, event: VehicleStationArrivalEvent):

       #if self.line_id == 0:
        if self.simulator.config.detailed_terminal_print_of_simulation:
            print(self.simulator.time_line.actual_time, 'FM line', self.line_id, ' vehicle_arrived', event.vehicle.id,
                  'on location',event.location.id)
        #if self.simulator.time_line.actual_time%1000 <= 100:
        #    self.case_study.stop_simulation_if_all_passengers_served()
        # try to unload the passengers with destination
        if event.vehicle.total_boarded > 0:
            if event.vehicle.location == event.location:
                #for j, obj in enumerate(event.vehicle.passengers):
                  #  if self.simulator.time_line.actual_time - event.vehicle.passengers[obj].borded_times[0] > 4000:
                  #      print(event.execution_time)
                  #      print('passenger still on board after 3000 seconds',
                  #            self.line_id,event.vehicle.id, event.vehicle.passengers[obj].id,
                  #            event.vehicle.passengers[obj].location.id,
                  #            event.vehicle.passengers[obj].destination_location.id)
                  #      print(event.vehicle.passengers[obj].transfers)
                  #      for i in range(0,len(event.vehicle.passengers[obj].transfers)):
                  #          print(event.vehicle.passengers[obj].transfers[i][0].id,event.vehicle.passengers[obj].transfers[i][1].id)
                  #      print('at the moment looking for des:', event.vehicle.passengers[obj].transfer_index)
                  #      for i, obj in enumerate(event.vehicle.passengers_leaving_on_location):
                  #          for j in range(0,len(event.vehicle.passengers_leaving_on_location[obj])):
                  #              print(obj,event.vehicle.passengers_leaving_on_location[obj][j].id)
                  #      exit(0)
                if self.simulator.config.detailed_terminal_print_of_simulation:
                    print(self.simulator.time_line.actual_time,' FM line',self.line_id,'unload',event.vehicle.id, event.location.id)
                t_array = event.vehicle.get_leaving_passengers(event.location)
                if t_array is not None and len(t_array) > 0:
                    if self.simulator.config.detailed_terminal_print_of_simulation:
                        print('     unloading :', len(t_array), 'number of passenger', 'on board',
                              event.vehicle.total_boarded, 'on vehicle:', event.vehicle.id)
                    for i in range(0, len(t_array)):
                        if self.simulator.config.detailed_terminal_print_of_simulation:
                            print('         unload :', t_array[i].id)
                        act_trip = t_array[i].journey_collection.active_journey.active_trip
                        self.simulator.immediate_procees_event(PassengerUnloadEvent(self.simulator.time_line.actual_time,
                                                                                    t_array[i], event.location,
                                                                                    event.vehicle, event.travel_time,
                                                                                    event.distance,
                                                                                    event.on_board))
                        self.passengers_served += 1
                        event.vehicle.departure.served_passengers += 1
                else:
                    if self.simulator.config.detailed_terminal_print_of_simulation:
                        print(self.simulator.time_line.actual_time,' no one to leave taxi')
                if self.simulator.config.detailed_terminal_print_of_simulation:
                    print(self.simulator.time_line.actual_time,' served passengers', self.passengers_served)
            else:
                print(event.vehicle.location.id, event.passenger.location.id)
                raise Exception('ERROR: Vehicle is not on dedicated station as it should arrived')
        # if there is someone on stop with destination in plan take them
        self.case_study.stop_simulation_if_all_passengers_served()
        if event.vehicle.departure is None:
            dep = self.create_new_departure_for_vehicle(event.vehicle, self.simulator.time_line.actual_time,
                                                        event.location, self.list_of_stops_in_order[-1])
        else:
            event.vehicle.departure.n_segments += 1
        self.take_passenger_from_actual_station_and_continue(event.vehicle, event.location)


class PublicTransportCircleLineManager(PublicTransporLineManager):

    def __init__(self, line_id, case_study: CaseStudy, ordered_locations_for_line: list, artificial_movements_not_to_count:list = None):
        super(PublicTransportCircleLineManager, self).__init__(line_id, case_study, ordered_locations_for_line,artificial_movements_not_to_count)
        self.type = 'public transport CIRCLE LINE fleet manager'
        # end circle line pairs should be not counted as the trip with passenger or empty, it is artificial movement trip
        # to operate same line in oposite order

    def get_the_next_stop_for_vehicle(self, vehicle, location):
        if vehicle.location.id in self.location_id_to_index_in_list:
            new_index = self.location_id_to_index_in_list[vehicle.location.id] + 1
            if new_index >= len(self.list_of_stops_in_order):
                new_index = 0
                vehicle.departure.end_time = self.simulator.time_line.actual_time
                dep = self.create_new_departure_for_vehicle(vehicle, self.simulator.time_line.actual_time,
                                                            self.list_of_stops_in_order[new_index],
                                                            self.list_of_stops_in_order[-1])

            if self.simulator.config.detailed_terminal_print_of_simulation:
                print(self.simulator.time_line.actual_time, ' vehicle ', vehicle.id, ' continue from', vehicle.location.id,
                      'to location', self.list_of_stops_in_order[new_index].id, 'with', vehicle.total_boarded, 'passengers',
                      'on line',self.line_id)
            # check if the trip to made is artifical and forward that information to Event to not count
            # EMPTY/OCPUTIED trips and create TRIP event
            if str(self.location_id_to_index_in_list[vehicle.location.id])+'|'+str(new_index) \
                    in self.artificial_movements_not_to_count:
                return self.list_of_stops_in_order[new_index],True
            else:
                return self.list_of_stops_in_order[new_index],False
        else:
            print(vehicle.location.id, self.location_id_to_index_in_list)
            raise Exception('ERROR: Vehicle location is not on this line')


class CaseStudy_PTwithLineDirectionCaseStudy(CaseStudy):

    def __init__(self):
        super(CaseStudy_PTwithLineDirectionCaseStudy, self).__init__()
        self.threshold_for_delayed_vehicle_to_start_departure = 1800

    def find_new_pt_vehicle_to_serve_departure(self,manager: TransitLineDepartureManager):
        raise Exception('!!! NOT IMPLEMENTED assignment of new vehicle yet')


    def estimated_waiting_for_the_pt_vehicle_to_be_available_for_departure_manager(self, vehicle: VehiclePT_with_departures_plan, manager: TransitLineDepartureManager):
        #print('!!! NOT TESTED YET: estimating new time for vehicle avaibility for next departure')
        if not vehicle.available_for_assignment:
            if vehicle.manager is not None:
                if vehicle.manager.status == DepartureManagerStatus.in_progress.value:
                     return vehicle.manager.get_estimated_time_to_end_departure()
                elif vehicle.manager.status == DepartureManagerStatus.completed.value:
                    return self.simulator.time_line.actual_time
                elif  vehicle.manager.status == DepartureManagerStatus.completed.planned:
                     return vehicle.manager.get_estimated_time_to_end_departure()
            else:
                return self.simulator.time_line.actual_time
        else:
            return self.simulator.time_line.actual_time
        return None


    def is_pt_vehicle_available_for_departure_manager(self, vehicle: VehiclePT_with_departures_plan, manager: TransitLineDepartureManager):
        if vehicle.available_for_assignment:
            intended_vehicle_manager = vehicle.get_active_departure_manager()
            # 1. so far we only check if vehicle assigned comming departure manager is this one
            if intended_vehicle_manager is None and vehicle.departure_managers.trips.num > 0:
                if manager.departure_id == 18912:
                    print('Now trip yet')
                intended_vehicle_manager = vehicle.get_next_departure_manager()

            if intended_vehicle_manager is not None:
                if manager == intended_vehicle_manager:
                    if manager.departure_id == 18912:
                        print('Same managers -> no need to wait')
                        print(self.simulator.time_line.actual_time, ' vehicle:',vehicle.id,' IS available for manager"',manager.id,'dep',manager.departure_id,' planned for vehicle',intended_vehicle_manager.id)
                    return True, 0
                else:
                    if vehicle.is_departure_manager_in_plan(manager):
                        estimated_time_avaibility = self.estimated_waiting_for_the_pt_vehicle_to_be_available_for_departure_manager(vehicle, manager)
                        if self.simulator.config.detailed_terminal_print_of_simulation:
                            print(self.simulator.time_line.actual_time, ' vehicle:', vehicle.id,' IS NOT available at the moment for manager -> estiamted time"', manager.id, 'dep', manager.departure_id)
                        return True, estimated_time_avaibility
                    else:
                        print('!!! HERE is potential to check if vehicle can squeeze another departure before or after the planned one')
                        print(self.simulator.time_line.actual_time, ' vehicle:', vehicle.id,' IS available but NOT planned for this Departure in plan intended:', manager.id, 'dep',manager.departure_id, ' planned for vehicle is',intended_vehicle_manager.id)
                        return False, 0
            else:
                if manager.departure_id == 18912:
                    print('No-manager -> so available')
                    print(self.simulator.time_line.actual_time, ' vehicle:',vehicle.id,' IS available for manager AS there is no plan for it at the moment',manager.id,'dep',manager.departure_id)
                return True, 0

        else:
            if manager.departure_id == 18912:
                print('Vehicle no available - checking if manager is in plan and estimating time')
            if vehicle.is_departure_manager_in_plan(manager):
                intended_vehicle_manager = vehicle.get_active_departure_manager()
                if manager.departure_id == 18912:
                    print('Yes it is in plan')
                    print(manager.id, intended_vehicle_manager.id)
                if manager == intended_vehicle_manager:
                    print('Already this manager reserved')
                    return True, 0
                else:
                    estimated_time_avaibility = self.estimated_waiting_for_the_pt_vehicle_to_be_available_for_departure_manager(vehicle, manager)
                    if self.simulator.config.detailed_terminal_print_of_simulation:
                        print(self.simulator.time_line.actual_time, ' vehicle:',vehicle.id,' IS NOT available at the moment for manager"',manager.id,'dep',manager.departure_id)
                    return True, estimated_time_avaibility
            else:
                return False, 0

#    def PT_line_departure_manager_vehicle_request_and_decission(self, manager: TransitLineDepartureManager, vehicle: VehiclePT_with_departures_plan):
#        intended_vehicle_manager = vehicle.get_active_departure_manager()
#        # 1. so far we only check if vehicle assigned comming departure manager is this one
#        if intended_vehicle_manager is None and vehicle.departure_managers.trips.num > 0:
#            intended_vehicle_manager = vehicle.get_next_departure_manager()
#
#        if intended_vehicle_manager is not None:
#            if manager == intended_vehicle_manager:
#                manager.add_vehicle(vehicle)
#                return vehicle
#            elif vehicle.is_departure_manager_next(manager):
#                # the departure is next in plan for vehicle but not finished yet, THE new departure should be delayed!
#                estimated_delay =
#                !!! here decide based on delay if to assign different vehicle and when available
#            elif vehicle.is_departure_manager_in_plan(self, manager):
#                # the departure is still in plan for vehicle but not its turn, THE new departure should be delayed!
#                estimated_delay =
#                !!! here decide based on delay if to assign different vehicle and when available#
#
#        return vehicle

    def register_passenger_observation(self, passenger: Passenger, start_location: Location, end_location: Location,
                                       start_time: int, end_time:int, distance: int, distance_complete:bool = True,
                                       on_board:int = None, vehicle:Vehicle = None, manager = None):
        if isinstance(manager, TransitLineDepartureManager):
            passenger.register_observed_trips(start_location, end_location,
                                                   manager.departure_id,
                                                   manager.transit_line_manager.line_manager.line_id,
                                                   manager.transit_line_manager.direction_id,
                                                   start_time, end_time, distance,distance_complete, on_board,
                                                   vehicle, manager)
        else:
            passenger.register_observed_trips(start_location, end_location,
                                                   None,
                                                   None,
                                                   None,
                                                   start_time, end_time, distance,distance_complete, on_board,
                                                   vehicle, manager)

    def add_passenger_next_trip_arrival_to_simulation(self, passenger: Passenger, arrival_execution_time: int, trip:TripPassanger, immediate_processing:bool = False):
        if not immediate_processing:
            self.simulator.add_event(PassengerArrivalEvent_line_with_direction(
                                                                       arrival_execution_time,
                                                                       passenger,
                                                                       trip.start_location,
                                                                       trip.line_id,
                                                                       trip.direction_id))
        else:
            self.simulator.immediate_procees_event(PassengerArrivalEvent_line_with_direction(
                                                                       arrival_execution_time,
                                                                       passenger,
                                                                       trip.start_location,
                                                                       trip.line_id,
                                                                       trip.direction_id))

    def inicialize_vehicles_for_simulation(self):
        for i in range(0, len(self.vehicles)):
            if self.vehicles[i].manager is not None:
                if not isinstance(self.vehicles[i].manager, TransitLineDepartureManager):
                    self.vehicles[i].manager.add_vehicle(self.vehicles[i])

    def inicialize_passengers_for_simulation(self):
        print('num', len(self.passengers))
        for i in range(0, len(self.passengers)):
            if self.simulator.config.detailed_terminal_print_of_simulation:
                print('passanger',i, len(self.passengers))
            elif i%10000 == 0:
                print('passanger',i, len(self.passengers))
            #pass_trip = self.passengers[i].get_next_trip()
            #pass_trip = self.passengers[i].get_current_trip_in_progress()
            #line_id = pass_trip.line_id
            #direction_id = pass_trip.direction_id
            self.passengers[i].add_next_trip_to_simulation()
            #self.simulator.add_event(PassengerArrivalEvent_line_with_direction(
            #                                               self.passengers[i].arrival_times[0],
            #                                               self.passengers[i],
            #                                               self.passengers[i].location,
            #                                               line_id, direction_id))

    def export_individual_passangers(self,output_dir:str=None):
        file_o = open(output_dir+'individual_passenger_trips.csv','w')

        file_o.write('passanger_id;passanger_arrival_time;n_executed_journeys;n_NOTexecuted_journeys;n_trips;passanger_waiting_time;final_trip;passanger_trip_id;start_time;end_time;'
                     'travel_time;distance;departure_key;segments_on_board;avg_on_board;avg_occupancy_rate;'
                     'travel_time_from_departure;expected_start_location;expected_end_location;expected_trip_id;expected_line_id;expected_direction_id.id;expected_vehicle_id;expected_manager_id;observed_start_location;'
                     'observed_end_location;observed_start_time;observed_end_time;observed_denied_boarding;observed_trip_id;observed_line_id;'
                     'observed_direction_id;observed_distance;observed_distance_complete;observed_on_board;observed_vehicle;observed_manager;arrival_times;borded_times;allighting_times\n')
        for i in range(0, len(self.passengers)):
            #print(i, self.passengers[i].id, self.passengers[i].arrival_times,
            #      self.passengers[i].alighting_times, self.passengers[i].borded_times)
            i_trip = 0
            #print('passanger journeys', len(self.passengers[i].journey_collection.executed_journeys))
            for j in range(0, len(self.passengers[i].journey_collection.executed_journeys)):
                #print('   trips:', len(self.passengers[i].journey_collection.executed_journeys[j].executed_trips))
                for k in range(0, len(self.passengers[i].journey_collection.executed_journeys[j].executed_trips)):
                        trip_t = self.passengers[i].journey_collection.executed_journeys[j].executed_trips[k]
                        waiting_time = self.passengers[i].borded_times[i_trip] - self.passengers[i].arrival_times[i_trip]
                        i_trip += 1
                        final_trip = 0
                        if j == len(self.passengers[i].journey_collection.executed_journeys) -1 and k == len(self.passengers[i].journey_collection.executed_journeys[j].executed_trips) - 1:
                            final_trip = 1
                        trip_info = trip_t.to_csv_str()
                        file_o.write(str(self.passengers[i].id)+';'+str(self.passengers[i].arrival_times[0])
                                     + ';' + str(len(self.passengers[i].journey_collection.executed_journeys))
                                     + ';' + str(self.passengers[i].journey_collection.journeys.num)
                                     + ';' + str(len(self.passengers[i].borded_times))
                                     + ';' +str(waiting_time)+';'+str(final_trip)+';'+trip_info
                                     + ';' +str(self.passengers[i].arrival_times).replace(',','|')
                                     + ';' +str(self.passengers[i].borded_times).replace(',','|')
                                     + ';' +str(self.passengers[i].alighting_times).replace(',','|') + '\n')
        file_o.close()
