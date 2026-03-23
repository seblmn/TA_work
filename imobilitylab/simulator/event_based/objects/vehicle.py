from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.objects.location import Location
from imobilitylab.simulator.event_based.objects.trips import TripCollection
from imobilitylab.simulator.event_based.objects.trips import TripVehicle
# from imobilitylab.simulator.event_based.objects.fleet_management import FleetManager


class Vehicle(object):

    def __init__(self, vehicle_id: int, location: Location, capacity: int, manager=None, trip_collection=None, observed_vehicle:bool = False):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        self.id = vehicle_id
        self.type = 'unknown'
        self.location = location
        if location is not None:
            location.add_vehicle(self)
        # self.location_line_index =f None
        self.capacity = capacity
        self.total_boarded = 0
        self.planned_destination = None
        self.total_served_passengers = 0
        self.total_distance_occupied = 0
        self.total_distance_empty = 0
        self.total_travel_time_occupied = 0
        self.total_travel_time_empty = 0
        self.total_travel_time = 0
        self.total_time_at_stops = 0
        self.number_of_occupied_trips = 0
        self.number_of_empty_trips = 0
        self.number_of_empty_trips_only_until_last_served = 0
        self.number_of_occupied_trips_only_until_last_served = 0
        self.first_served_passenger_boarding_time = None
        self.last_served_passenger_alighting_time = None
        self.passengers = {}
        self.passengers_leaving_on_location = {}
        self.manager = manager
        self.observed_vehicle = observed_vehicle
        # this is made in incilaization of case study
        #if self.manager is not None:
        #    self.manager.add_vehicle(self)
        self.trip_collection = trip_collection
        if trip_collection is None:
            self.trip_collection = []

    def collect_trip(self, start_location: int, end_location: int, distance: int, on_board: int, start_time: int,
                     end_time: int):
        if self.trip_collection is not None:

            self.trip_collection.append(TripVehicle(start_location, end_location, distance,
                                                    on_board, start_time, end_time, self, self.manager))

    def register_manager(self, manager):
        self.manager = manager

    def get_leaving_passengers(self, location: Location):
        if location.id in self.passengers_leaving_on_location:
            pom = self.passengers_leaving_on_location[location.id]
            del self.passengers_leaving_on_location[location.id]
            return pom
        else:
            return None

    def add_passenger(self, passenger: Passenger, destination: Location, boarded_time: int):
        #if passenger.id == 64103765:
        #    raise Exception('!!! 64103765 boarding')
        # self.manager.board_passengers(self,self.location)
        # self.passenger.boarded_time = self.simulator.time_line.actual_time
        if len(self.passengers) == self.capacity:
            return False
        else:
            self.total_boarded += 1
            self.passengers[passenger.id] = passenger
            #destination = passenger.select_destination()
            if destination.id not in self.passengers_leaving_on_location:
                self.passengers_leaving_on_location[destination.id] = []
            self.passengers_leaving_on_location[destination.id].append(passenger)
            passenger.vehicle = self
            #passenger.register_borded_time(boarded_time)
            if self.first_served_passenger_boarding_time is None:
                self.first_served_passenger_boarding_time = boarded_time
            return True
        # if self.planned_destination is None or self.planned_destination == passenger.get_destination():
        #    self.total_boarded += 1
        #    self.passengers[passenger.id] = passenger
        #    destination = passenger.select_destination()
        #    self.planned_destination = destination
        #    if destination.id not in self.passengers_leaving_on_location:
        #        self.passengers_leaving_on_location[destination.id] = []
        #    self.passengers_leaving_on_location[destination.id].append(passenger)
        #    passenger.vehicle = self
        #    return True
        # else:
        #   return False

    def unload_passenger(self, passenger: Passenger):
        self.total_served_passengers += 1
        self.total_boarded -= 1
        del self.passengers[passenger.id]
        self.number_of_empty_trips_only_until_last_served = self.number_of_empty_trips
        self.number_of_occupied_trips_only_until_last_served = self.number_of_occupied_trips
        self.last_served_passenger_alighting_time = self.manager.simulator.time_line.actual_time
        if self.total_boarded == 0:
            self.planned_destination = None

    def empty_space(self):
        return self.capacity-self.total_boarded

    def get_destination_location(self):
        pass
