#from imobilitylab.simulator.event_based.objects.transport import Passenger
from imobilitylab.simulator.event_based.objects.vehicle import Vehicle
from imobilitylab.simulator.event_based.objects.location import Location
#from imobilitylab.simulator.event_based.objects.fleet_management import FleetManager
from imobilitylab.supporting_libraries.fifo import FIFO
from imobilitylab.supporting_libraries.fifo import FifoItem


class TransitLine(object):

    def __init__(self, line_id:int, mode: str, direction_id: int, ordered_list_of_locations: list):
        self.line_id = line_id
        self.mode = mode
        self.direction_id = direction_id
        self.ordered_list_of_locations = ordered_list_of_locations
        self.location_id_to_index = {}
        for i in range(0, len(ordered_list_of_locations)):
            self.location_id_to_index[ordered_list_of_locations[i]]
        self.vehicles = {}

    def AssignVehicle(self, vehicle: Vehicle):
        vehicle.line = self
        self.vehicles[vehicle.id] = vehicle

    def GetNextLocationIndexTo(self, current_location_index:int):
        if current_location_index == len(self.ordered_list_of_locations):
            index = 0
        else:
            index = current_location_index+1
        return index

    def GetLocation(self, location_index: int):
        return self.ordered_list_of_locations[location_index]

    def GetIndexOfLocation(self, location: Location):
        pass


class TransitLineDeparture(object):

    def __init__(self, transit_line: TransitLine, departure_id, ordered_list_of_locations: list,
                 vehicle: Vehicle = None):
        self.transit_line = transit_line
        self.departure_id = departure_id
        self.ordered_list_of_locations = ordered_list_of_locations
        self.location_id_to_index = {}
        for i in range(0, len(ordered_list_of_locations)):
            self.location_id_to_index[ordered_list_of_locations[i]]
        self.vehicle = vehicle
        if self.vehicle is not None:
            self.transit_line.AssignVehicle(vehicle)

    def AssignVehicle(self, vehicle: Vehicle):
        if self.vehicle is None:
            self.vehicle = vehicle
            self.transit_line.AssignVehicle(vehicle)
        else:
            raise Exception('Logical ERROR: there can not be assign more as one vehicle to departure')

    def GetNextLocationIndexTo(self, current_location_index:int):
        if self.ordered_list_of_locations is not None:
            if current_location_index == len(self.ordered_list_of_locations):
                index = 0
            else:
                index = current_location_index+1
            return index
        else:
            return self.transit_line.GetNextLocationIndexTo(current_location_index)

    def GetLocation(self, location_index: int):
        if self.ordered_list_of_locations is not None:
            return self.ordered_list_of_locations[location_index]
        else:
            self.transit_line.GetLocation(location_index)

    def GetIndexOfLocation(self, location: Location):
        pass

