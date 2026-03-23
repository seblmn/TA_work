from imobilitylab.simulator.event_based.objects.vehicle import Vehicle
from imobilitylab.simulator.event_based.objects.location import Location
from imobilitylab.simulator.event_based.objects.case_study import CaseStudy
from imobilitylab.simulator.event_based.event.transport import VehicleStationArrivalEvent


class FleetManager(object):

    def __init__(self, case_study: CaseStudy):
        self.vehicles = []
        self.vehicle_id_to_index = {}
        self.simulator = case_study.simulator
        self.case_study = case_study
        case_study.register_manager(self)
        self.passengers_served = 0
        self.type = 'no specified fleet manager type'
        self.id = -1

    def get_distance_and_travel_time_between_passenger_origin_destination(self, start_location: Location, end_location: Location):
        pass

    def get_distance(self, start_location: Location, end_location: Location):
        pass

    def get_travel_time(self, start_location: Location, end_location: Location):
        pass

    def decide_next_step_for_vehicle(self, vehicle: Vehicle):
        pass

    def add_vehicle(self, vehicle: Vehicle):
        if vehicle.id not in self.vehicle_id_to_index:
            self.vehicle_id_to_index[vehicle.id] = len(self.vehicles)
            self.vehicles.append(vehicle)

    def number_of_vehicles(self):
        return len(self.vehicles)

    def is_trip_to_destination_from_location_possible(self, start_location:Location, end_location: Location):
        pass

    def vehicle_arrived_to_location(self, event: VehicleStationArrivalEvent):
        pass

    def vehicle_departured_the_location(self, event: VehicleStationArrivalEvent):
        pass

    def board_passengers(self, vehicle: Vehicle, location: Location, destination: Location):
        pass

