from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.objects.location import Location
from imobilitylab.simulator.event_based.objects.trips import TripCollection
from imobilitylab.simulator.event_based.objects.trips import TripVehicle
from imobilitylab.simulator.event_based.objects.trips import TripBasic
from imobilitylab.simulator.event_based.objects.vehicle import Vehicle
from imobilitylab.simulator.event_based.objects.case_study import CaseStudy
from imobilitylab.simulator.event_based.objects.fleet_management import FleetManager
from imobilitylab.simulator.event_based.event.transport import VehicleStationArrivalEvent, PassengerUnloadEvent








class VehiclePassive(Vehicle):

    def __init__(self, vehicle_id: int, location: Location, capacity: int, manager=None, trip_collection=None, observed_vehicle:bool = False):
        super(VehiclePassive, self).__init__(vehicle_id, location, capacity, manager, trip_collection, observed_vehicle)
        self.available = True
        self.speed = None

    def take_vehicle(self, passanger:Passenger, destination: Location, time: int):
        if self.available:
            self.available = False
            return self.add_passenger(passanger, destination, time)
        else:
            raise Exception('LOGIC ERROR - vehicle can not be taken if it is not available')

    def leave_vehicle(self):
        if not self.available:
            self.available = True
            #location.add_vehicle(self) # it has been already added in VehicleArrivalEvent
        else:
            raise Exception('LOGIC ERROR - vehicle can be not leaved if it is already available')

    def estimate_travel_time(self, origin:Location, destination:Location):
        raise Exception('Estimating travel time not implemented yet')


class ScooterVehicle(VehiclePassive):

    def __init__(self, vehicle_id: int, location: Location, capacity: int, manager=None, trip_collection=None,
                 observed_vehicle: bool = False):
        super(ScooterVehicle, self).__init__(vehicle_id, location, capacity, manager, trip_collection, observed_vehicle)
        self.capacity = 1
        self.speed_kmh = 20 #kmh
        self.battery = None
        self.battery_consumption_per_kmh = None
        self.battery_state = 'unknown'  # possible values: 'unknown', 'charged', 'low'


class TripMicromobility(TripBasic):

    def __init__(self, start_location: Location, end_location: Location, start_time:int, vehicle=None, manager=None):
        super(TripMicromobility, self).__init__(start_location, end_location, None, start_time, None, vehicle, manager)


class MicromobilityFleetManager(FleetManager):

    def __init__(self, case_study: CaseStudy):
        super(MicromobilityFleetManager, self).__init__(case_study)
        self.distance_tt_matrix = None

    def get_distance(self, start_location: Location, end_location: Location):
        if self.distance_tt_matrix is None:
            raise Exception('ERROR - there is no distance or tt matrix defined')
        if start_location.id in self.distance_tt_matrix:
            if end_location.id in self.distance_tt_matrix[start_location.id]:
                return self.distance_tt_matrix[start_location.id][end_location.id][0]
            else:
                return None
        else:
            return None

    def get_distance_and_travel_time_between_passenger_origin_destination(self, start_location: Location, end_location: Location):
        if self.distance_tt_matrix is None:
            raise Exception('ERROR - there is no distance or tt matrix defined')
        if start_location.id in self.distance_tt_matrix:
            if end_location.id in self.distance_tt_matrix[start_location.id]:
                return self.distance_tt_matrix[start_location.id][end_location.id][0],self.distance_tt_matrix[start_location.id][end_location.id][1]
            else:
                return None, None
        else:
            return None, None

    def get_travel_time(self, start_location: Location, end_location: Location):
        if self.distance_tt_matrix is None:
            raise Exception('ERROR - there is no distance or tt matrix defined')
        if start_location.id in self.distance_tt_matrix:
            if end_location.id in self.distance_tt_matrix[start_location.id]:
                return self.distance_tt_matrix[start_location.id][end_location.id][1]
            else:
                return None
        else:
            return None

    def vehicle_departured_the_location(self, event: VehicleStationArrivalEvent):
        pass

    def is_trip_to_destination_from_location_possible(self, start_location:Location, end_location: Location):
        dis = self.get_distance(start_location, end_location)
        if dis is not None:
            return True
        else:
            return False

    def leave_vehicle(self, passanger:Passenger, vehicle: Vehicle, location: Location):
        vehicle.leave_vehicle()
        PassengerUnloadEvent(self.simulator.time_line.actual_time, passanger, location, vehicle, )

    def vehicle_arrived_to_location(self, event: VehicleStationArrivalEvent):
        if event.passenger is not None and len(event.vehicle.passengers)>0:
            current_trip = event.passenger.get_current_trip_in_progress()
            if event.location != current_trip.end_location:
                raise Exception('LOGIC ERROR: micromobility vehicle arrived to location but it is not the desired end-location -> this should not happen')
            else:
                self.simulator.immediate_procees_event(PassengerUnloadEvent(self.simulator.time_line.actual_time, event.passenger, event.location, event.vehicle, event.travel_time, event.distance, event.on_board),)
                event.vehicle.leave_vehicle()

    def take_vehicle(self, passanger:Passenger, vehicle:Vehicle, start_location:Location, end_location: Location):
        if vehicle.id in self.vehicle_id_to_index:
            dis, tt = self.get_distance_and_travel_time_between_passenger_origin_destination(start_location, end_location)
            if tt:
                passanger.register_borded_time(self.simulator.time_line.actual_time)
                vehicle.take_vehicle(passanger, end_location, self.simulator.time_line.actual_time)
                self.simulator.add_event(VehicleStationArrivalEvent(self.simulator.time_line.actual_time+tt, self, vehicle, end_location,
                                           start_location, dis, tt, passanger))
                return True
            else:
                # trip not allowed or possible
                return False
        else:
            raise Exception('LOGIC ERROR: vehicle is not registered in this manager')

    def passanger_is_taking_vehicle(self, vehicle: Vehicle, passenger:Passenger, location: Location, destination: Location):
        vehicle.available = False
        vehicle.passengers.append(passenger)
        vehicle.total_served_passengers += 1
        vehicle.total_boarded += 1
        passenger.vehicle = vehicle
        vehicle.number_of_occupied_trips += 1




class CaseStudy_micromobility(CaseStudy):

    def __init__(self):
        super(CaseStudy_micromobility, self).__init__()

    def get_distance(self, manager, vehicle: Vehicle, org: Location, des: Location, org_index:int = None, des_index:int = None):
        if manager is None:
            raise Exception('Error no case-study GetDistance version implemented')
        else:
            if org_index is None:
                return manager.get_distance(vehicle, org, des)
            else:
                return manager.get_distance(vehicle, org, des, org_index, des_index)

    def get_travel_time(self, manager, vehicle: Vehicle, org: Location, des: Location, org_index:int = None, des_index:int = None):
        if manager is None:
            raise Exception('Error no case-study GetDistance version implemented')
        else:
            if org_index is None:
                return manager.get_travel_time(vehicle, org, des)
            else:
                return manager.get_travel_time(vehicle, org, des, org_index, des_index)

    def register_passenger_observation(self, passenger: Passenger, start_location: Location, end_location: Location,
                                       start_time: int, end_time:int, distance: int, distance_complete:bool = True,
                                       on_board:int = None, vehicle:Vehicle = None, manager = None):

        passenger.register_observed_trips(start_location, end_location,
                                                   None,
                                                   None,
                                                   None,
                                                   start_time, end_time, distance,distance_complete, on_board,
                                                   vehicle, manager)
    
'''
from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.objects.location import Location
from imobilitylab.simulator.event_based.objects.trips import TripCollection
from imobilitylab.simulator.event_based.objects.trips import TripVehicle
from imobilitylab.simulator.event_based.objects.trips import TripBasic
from imobilitylab.simulator.event_based.objects.vehicle import Vehicle
from imobilitylab.simulator.event_based.objects.case_study import CaseStudy
from imobilitylab.simulator.event_based.objects.fleet_management import FleetManager
from imobilitylab.simulator.event_based.event.transport import VehicleStationArrivalEvent, PassengerUnloadEvent








class VehiclePassive(Vehicle):

    def __init__(self, vehicle_id: int, location: Location, capacity: int, manager=None, trip_collection=None, observed_vehicle:bool = False):
        super(VehiclePassive, self).__init__(vehicle_id, location, capacity, manager, trip_collection, observed_vehicle)
        self.available = True
        self.speed = None

    def take_vehicle(self, passanger:Passenger, destination: Location, time: int):
        if self.available:
            self.available = False
            return self.add_passenger(passanger, destination, time)
        else:
            raise Exception('LOGIC ERROR - vehicle can not be taken if it is not available')

    def leave_vehicle(self):
        if not self.available:
            self.available = True
            #location.add_vehicle(self) # it has been already added in VehicleArrivalEvent
        else:
            raise Exception('LOGIC ERROR - vehicle can be not leaved if it is already available')

    def estimate_travel_time(self, origin:Location, destination:Location):
        raise Exception('Estimating travel time not implemented yet')


class ScooterVehicle(VehiclePassive):

    def __init__(self, vehicle_id: int, location: Location, capacity: int, manager=None, trip_collection=None,
                 observed_vehicle: bool = False):
        super(ScooterVehicle, self).__init__(vehicle_id, location, capacity, manager, trip_collection, observed_vehicle)
        self.capacity = 1
        self.speed_kmh = 20 #kmh
        self.battery = None
        self.battery_consumption_per_kmh = None


class TripMicromobility(TripBasic):

    def __init__(self, start_location: Location, end_location: Location, start_time:int, vehicle=None, manager=None):
        super(TripMicromobility, self).__init__(start_location, end_location, None, start_time, None, vehicle, manager)


class MicromobilityFleetManager(FleetManager):

    def __init__(self, case_study: CaseStudy):
        super(MicromobilityFleetManager, self).__init__(case_study)
        self.distance_tt_matrix = None

    def get_distance(self, start_location: Location, end_location: Location):
        if self.distance_tt_matrix is None:
            raise Exception('ERROR - there is no distance or tt matrix defined')
        if start_location.id in self.distance_tt_matrix:
            if end_location.id in self.distance_tt_matrix[start_location.id]:
                return self.distance_tt_matrix[start_location.id][end_location.id][0]
            else:
                return None
        else:
            return None

    def get_distance_and_travel_time_between_passenger_origin_destination(self, start_location: Location, end_location: Location):
        if self.distance_tt_matrix is None:
            raise Exception('ERROR - there is no distance or tt matrix defined')
        if start_location.id in self.distance_tt_matrix:
            if end_location.id in self.distance_tt_matrix[start_location.id]:
                return self.distance_tt_matrix[start_location.id][end_location.id][0],self.distance_tt_matrix[start_location.id][end_location.id][1]
            else:
                return None, None
        else:
            return None, None

    def get_travel_time(self, start_location: Location, end_location: Location):
        if self.distance_tt_matrix is None:
            raise Exception('ERROR - there is no distance or tt matrix defined')
        if start_location.id in self.distance_tt_matrix:
            if end_location.id in self.distance_tt_matrix[start_location.id]:
                return self.distance_tt_matrix[start_location.id][end_location.id][1]
            else:
                return None
        else:
            return None

    def vehicle_departured_the_location(self, event: VehicleStationArrivalEvent):
        pass

    def is_trip_to_destination_from_location_possible(self, start_location:Location, end_location: Location):
        dis = self.get_distance(start_location, end_location)
        if dis is not None:
            return True
        else:
            return False

    def leave_vehicle(self, passanger:Passenger, vehicle: Vehicle, location: Location):
        vehicle.leave_vehicle()
        PassengerUnloadEvent(self.simulator.time_line.actual_time, passanger, location, vehicle, )

    def vehicle_arrived_to_location(self, event: VehicleStationArrivalEvent):
        if event.passenger is not None and len(event.vehicle.passengers)>0:
            current_trip = event.passenger.get_current_trip_in_progress()
            if event.location != current_trip.end_location:
                raise Exception('LOGIC ERROR: micromobility vehicle arrived to location but it is not the desired end-location -> this should not happen')
            else:
                self.simulator.immediate_procees_event(PassengerUnloadEvent(self.simulator.time_line.actual_time, event.passenger, event.location, event.vehicle, event.travel_time, event.distance, event.on_board),)
                event.vehicle.leave_vehicle()

    def take_vehicle(self, passanger:Passenger, vehicle:Vehicle, start_location:Location, end_location: Location):
        if vehicle.id in self.vehicle_id_to_index:
            dis, tt = self.get_distance_and_travel_time_between_passenger_origin_destination(start_location, end_location)
            if tt:
                passanger.register_borded_time(self.simulator.time_line.actual_time)
                vehicle.take_vehicle(passanger, end_location, self.simulator.time_line.actual_time)
                self.simulator.add_event(VehicleStationArrivalEvent(self.simulator.time_line.actual_time+tt, self, vehicle, end_location,
                                           start_location, dis, tt, passanger))
                return True
            else:
                # trip not allowed or possible
                return False
        else:
            raise Exception('LOGIC ERROR: vehicle is not registered in this manager')

    def passanger_is_taking_vehicle(self, vehicle: Vehicle, pasasnger:Passenger, location: Location, destination: Location):
        vehicle.passengers



class CaseStudy_micromobility(CaseStudy):

    def __init__(self):
        super(CaseStudy_micromobility, self).__init__()

    def get_distance(self, manager, vehicle: Vehicle, org: Location, des: Location, org_index:int = None, des_index:int = None):
        if manager is None:
            raise Exception('Error no case-study GetDistance version implemented')
        else:
            if org_index is None:
                return manager.get_distance(vehicle, org, des)
            else:
                return manager.get_distance(vehicle, org, des, org_index, des_index)

    def get_travel_time(self, manager, vehicle: Vehicle, org: Location, des: Location, org_index:int = None, des_index:int = None):
        if manager is None:
            raise Exception('Error no case-study GetDistance version implemented')
        else:
            if org_index is None:
                return manager.get_travel_time(vehicle, org, des)
            else:
                return manager.get_travel_time(vehicle, org, des, org_index, des_index)

    def register_passenger_observation(self, passenger: Passenger, start_location: Location, end_location: Location,
                                       start_time: int, end_time:int, distance: int, distance_complete:bool = True,
                                       on_board:int = None, vehicle:Vehicle = None, manager = None):

        passenger.register_observed_trips(start_location, end_location,
                                                   None,
                                                   None,
                                                   None,
                                                   start_time, end_time, distance,distance_complete, on_board,
                                                   vehicle, manager)

'''
