#from imobilitylab.simulator.event_based.objects.vehicle import Vehicle
#from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.supporting_libraries.fifo import FIFO, FifoItem


class Location(object):

    def __init__(self, station_id: int, type:str = None):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        self.id = station_id
        self.type = type
        self.passangers = FIFO()
        self.passangers_dict = {}
        self.vehicles = FIFO()
        self.vehicles_dict = {}
        self.case_study = None
        self.total_number_of_passangers = 0
        self.total_number_of_vehicles = 0
        self.number_of_served_passangers = 0
        self.number_of_leaved_passangers = 0

    def is_passenger_on_station(self, passenger):
        if passenger.id in self.passangers_dict:
            return True
        else:
            return False

    def board_passenger_if_vehicle_serving_destination_is_on_stop(self, passenger):
        raise Exception('Board passenger on location by searching for vehicle already on locationm is not implemented HERE')

    def add_passenger(self, passanger):#: Passenger):
        self.total_number_of_passangers += 1
        item = FifoItem(passanger)
        self.passangers.add_item(item)
        self.passangers_dict[passanger.id] = item
        if passanger.id == 62595908:
            print('    - Passanger added to location', passanger.id, 'number of passangers on location', self.passangers.length, self)
        if self.id == 50579 and passanger.id == 62595908:
            print(' LOCATION - ADDING Number of passangers at location 50579', self.passangers.length,self.total_number_of_passangers)
            item = self.passangers.start
            while item != None:
                print('     pass - ', item.obj.id)
                item = item.next_item
        return True

    def add_vehicle(self, vehicle):#: Vehicle):
        if vehicle.id not in self.vehicles_dict:
            self.total_number_of_vehicles += 1
            item = FifoItem(vehicle)
            self.vehicles.add_item(item)
            self.vehicles_dict[vehicle.id] = item

    def remove_vehicle(self, vehicle):
        if vehicle.id == 47032:
            print('       - Removing vehicle 47032 at Location',self.id)
        self.vehicles.remove_item(self.vehicles_dict[vehicle.id])
        del self.vehicles_dict[vehicle.id]
        self.total_number_of_vehicles -= 1

    def get_actual_number_of_passangers(self):
        return self.passangers.length

    def remove_passenger(self, passenger):
        if self.id == 50579 and passenger.id == 62595908:
            print(' LOCATION - REMOVING Number of passangers at location 50579', self.passangers.length, self.total_number_of_passangers)
            item = self.passangers.start
            while item != None:
                print('     pass - ', item.obj.id)
                item = item.next_item
        if passenger.id in self.passangers_dict:
            self.passangers.remove_item(self.passangers_dict[passenger.id])
            del self.passangers_dict[passenger.id]
            self.total_number_of_passangers -= 1
        else:
            raise Exception('LOGIC ERROR at LOCATION trying to remove passanger from location that is not at the location')
        if self.id == 50579 and passenger.id == 62595908:
            print(' LOCATION - REMOVING', passenger.id, self.passangers.length, self.total_number_of_passangers)

    def first_passanger(self):
        return self.passangers.start.obj

    def get_passanger(self):
        if self.total_number_of_passangers > 0:
            self.total_number_of_passangers -= 1
            passenger = self.passangers.get_item()
            del self.passangers_dict[passenger.id]
            return passenger
        else:
            return None

    def get_vehicle(self):
        if self.total_number_of_vehicles > 0:
            self.total_number_of_vehicles -= 1
            vehicle = self.vehicles.get_item()
            del self.vehicles_dict[vehicle.id]
            return vehicle
        else:
            return None


class Location_with_passive_vehicles(Location):

    def __init__(self, station_id: int, type:str = None):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(Location_with_passive_vehicles, self).__init__(station_id, type)

    def add_passenger(self, passanger):#: Passenger):

        if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
            print('# Adding passanger',passanger.id, ' to location', self.id)
        if self.total_number_of_vehicles > 0:
            if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                print('   adding passanger - there is at least one vehicle')
            current_trip = passanger.get_current_trip_in_progress()
            destination = current_trip.end_location
            vehicle_t = self.vehicles.start.obj
            if vehicle_t.manager.take_vehicle(passanger, vehicle_t, self, destination):
                self.remove_vehicle(vehicle_t)
                self.number_of_served_passangers += 1
            else:
                raise Exception('NOT IMPLEMENTED YET case when trip with passive vehicle is not possible - that means this trip can not be realized')

        else:
            super(Location_with_passive_vehicles, self).add_passenger(passanger)
            return True


class LineDirectionsLocation(Location):

    def __init__(self, station_id: int, parent_location:Location, type: str, line_id: int, direction_id: int):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(LineDirectionsLocation, self).__init__(station_id)
        self.line_id = line_id
        self.direction_id = direction_id
        self.parent_location = parent_location

    def board_passenger_if_vehicle_serving_destination_is_on_stop(self, passenger):
        trip_in_plan = passenger.get_current_trip_in_progress()
        destination = trip_in_plan.end_location
        item = self.vehicles.start
        while item is not None:
            if item.obj.manager is not None:
                if item.obj.manager.simulator.config.detailed_terminal_print_of_simulation:
                    print('   Considering departure', item.obj.manager.departure_id, 'line', item.obj.manager.transit_line_manager.line_manager.line_id, 'dir', item.obj.manager.transit_line_manager.direction_id, 'FOR destination:', destination.id)
                if destination.id in item.obj.manager.location_id_to_index:
                    if passenger.will_you_board_departure(item.obj.manager):
                        if item.obj.manager.simulator.config.detailed_terminal_print_of_simulation:
                            print('       destination in departure plan')
                        des_index = item.obj.manager.get_segment_index_last_occurance(destination)
                        org_index = item.obj.manager.get_segment_index_first_occurance(self)
                        if des_index > org_index:
                            if item.obj.manager.simulator.config.detailed_terminal_print_of_simulation:
                                print('       destination in departure downstream plan')
                            if item.obj.manager.simulator.config.detailed_terminal_print_of_simulation:
                                print('   @@ Boarded immediately at arrival', item.obj.id, destination.id, item.obj.empty_space(), 'passenger ', passenger.id, 'line',
                                      item.obj.manager.transit_line_manager.line_manager.line_id, 'dep:', item.obj.manager.departure_id, 'des:',
                                      destination.id)
                            if item.obj.id == 47032:
                                print('     Immediate-Boarding 47032', item.obj.manager.departure_id, passenger.id, destination.id)
                            if passenger.id == 57278568:
                                print('     Immediate-Boarding pass: 57278568 on vehicle',item.obj.id,'dep:',item.obj.manager.departure_id,' des:', destination.id)
                            passenger.register_borded_time(item.obj.manager.simulator.time_line.actual_time)
                            # self.unregister_passenger(passenger)
                            self.parent_location.remove_passenger(passenger, self.line_id, self.direction_id)
                            # !!! Unregister from DRS
                            if passenger.manager is not None:
                                passenger.manager.unregister_passenger(passenger)
                            #if passenger.id == 57278568:
                            #    print('boarding 57278568 at', self.id,'to',destination.id,item.obj.manager.last_location_index,des_index)
                            #    exit(0)
                            act_trip = passenger.journey_collection.active_journey.active_trip
                            act_trip.observed_start_location_index = item.obj.manager.last_location_index
                            item.obj.add_passenger(passenger, destination, item.obj.manager.simulator.time_line.actual_time)
                            break
            item = item.next_item

        #print('   @@ NOT Boarded immediately at arrival, waiting ... passenger ', passenger.id, 'line', self.line_id, 'dir', self.direction_id)

class MultiLineAndDirectionsLocation(Location):

    def __init__(self, station_id: int, type:str):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(MultiLineAndDirectionsLocation, self).__init__(station_id, type)
        self.line_direction_locations = {}

    def register_line_directional_location_if_not_exists(self, station_id: int, type:str, line_id: int, direction_id: int):
        #print('@@ registering line and direction', line_id, direction_id, ' for location:', self.id)
        if station_id == self.id:
            key_string = str(line_id) + '|' + str(direction_id)
            if key_string not in self.line_direction_locations:
                self.line_direction_locations[key_string] = LineDirectionsLocation(station_id,self, type, line_id, direction_id)

    def is_passenger_on_station(self, passenger):
        if passenger.id in self.passangers_dict:
            return True
        else:
            return False

    def first_passanger(self):
        return self.passangers.start.obj

    def add_passenger(self, passanger, line_id: int, direction_id: int):#: Passenger):
        if passanger.id == 62595908:
            print('    - Addiing passanger to MULTILINEdirectLocat', passanger.id, 'to location', self.id, line_id, direction_id)
        super(MultiLineAndDirectionsLocation, self).add_passenger(passanger)
        key_string = str(line_id) + '|' + str(direction_id)
        if key_string in self.line_direction_locations:
            #print('Adding passanger at stop', passanger.id)
            self.line_direction_locations[key_string].add_passenger(passanger)
            self.line_direction_locations[key_string].board_passenger_if_vehicle_serving_destination_is_on_stop(passanger)
            return True
        else:
            print(self.line_direction_locations)
            raise Exception('Line id:'+str(line_id)+' and dir:'+str(direction_id)+' not registered at location '+str(self.id)+' for passanger:'+str(passanger.id))
            return False

    def add_vehicle(self, vehicle, line_id: int, direction_id: int):#: Vehicle):
        super(MultiLineAndDirectionsLocation, self).add_vehicle(vehicle)
        key_string = str(line_id) + '|' + str(direction_id)
        if key_string in self.line_direction_locations:
            if vehicle.id not in self.line_direction_locations[key_string].vehicles_dict:
                self.line_direction_locations[key_string].add_vehicle(vehicle)
        else:
            raise Exception('Line id:'+str(line_id)+' and dir:'+str(direction_id)+' not registered at stop for vehicle:'+str(vehicle.id))
            return False

    def remove_vehicle(self, vehicle, line_id: int, direction_id: int):
        if vehicle.id == 47032:
            print('       - Removing vehicle 47032 at MultiLineAndDirectionsLocation',self.id)
        key_string = str(line_id) + '|' + str(direction_id)
        if key_string in self.line_direction_locations:
            if vehicle.id in self.line_direction_locations[key_string].vehicles_dict:
                self.line_direction_locations[key_string].remove_vehicle(vehicle)
        if vehicle.id in self.vehicles_dict:
            super(MultiLineAndDirectionsLocation, self).remove_vehicle(vehicle)

    def remove_passenger(self, passenger, line_id: int, direction_id: int):
        key_string = str(line_id) + '|' + str(direction_id)
        if key_string in self.line_direction_locations:
            if passenger.id in self.line_direction_locations[key_string].passangers_dict:
                self.line_direction_locations[key_string].remove_passenger(passenger)
        if passenger.id in self.passangers_dict:
            super(MultiLineAndDirectionsLocation, self).remove_passenger(passenger)

    def get_passanger(self, line_id: int = None, direction_id: int = None):
        if line_id is not None and direction_id is not None:
            key_string = str(line_id) + '|' + str(direction_id)
            passenger = None
            if self.total_number_of_passangers > 0:
                if key_string in self.line_direction_locations:
                    if self.line_direction_locations[key_string].total_number_of_passangers > 0:
                        passenger = self.line_direction_locations[key_string].passangers.get_item()
                        if passenger is not None:
                            del self.line_direction_locations[key_string].passangers_dict[passenger.id]
                            del self.passangers_dict[passenger.id]
                            self.line_direction_locations[key_string].total_number_of_passangers += -1
                            self.total_number_of_passangers -= 1
            return passenger
        else:
            passenger = None
            if self.total_number_of_passangers > 0:
                passenger = super(MultiLineAndDirectionsLocation, self).get_passanger()
                for i, obj in enumerate(self.line_direction_locations):
                    if passenger.id in self.line_direction_locations[obj].passangers_dict:
                        self.line_direction_locations[obj].passangers.remove_item(self.line_direction_locations[obj].passangers_dict[passenger.id])
                        del self.line_direction_locations[obj].passangers_dict[passenger.id]
                        self.line_direction_locations[obj].total_number_of_passangers += -1
            return passenger

    def get_vehicle(self, line_id: int = None, direction_id: int = None):
        if line_id is not None and direction_id is not None:
            key_string = str(line_id) + '|' + str(direction_id)
            vehicle = None
            if self.total_number_of_vehicles > 0:
                if key_string in self.line_direction_locations:
                    if self.line_direction_locations[key_string].total_number_of_vehicles > 0:
                        vehicle = self.line_direction_locations[key_string].vehicles.get_item()
                        if vehicle is not None:
                            del self.line_direction_locations[key_string].vehicles_dict[vehicle.id]
                            del self.vehicles_dict[vehicle.id]
                            self.line_direction_locations[key_string].total_number_of_vehicles += -1
                            self.total_number_of_vehicles -= 1
            return vehicle
        else:
            vehicle = None
            if self.total_number_of_vehicles > 0:
                vehicle = super(MultiLineAndDirectionsLocation, self).get_passanger()
                for i, obj in enumerate(self.line_direction_locations):
                    if vehicle.id in self.line_direction_locations[obj].vehicles_dict:
                        self.line_direction_locations[obj].vehicles.remove_item(self.line_direction_locations[obj].vehicles_dict[vehicle.id])
                        del self.line_direction_locations[obj].vehicles_dict[vehicle.id]
                        self.line_direction_locations[obj].total_number_of_vehicles += -1
            return vehicle


class DirectionalLocation(Location):

    def __init__(self, main_location: Location, station_id: int):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(DirectionalLocation, self).__init__(station_id)
        self.main_location = main_location
        self.stops = []

    def register_directional_location(self, directional_location: Location):
        if directional_location.main_location.id == self.main_location.id:
            self.stops.append(directional_location)

    def is_passenger_on_station(self, passenger):
        if passenger.id in self.main_location.passangers_dict:
            return True
        else:
            return False

    def first_passanger(self):
        return self.main_location.passangers.start.obj

    def add_passenger(self, passanger):#: Passenger):
        if passanger.id == 62595908:
            print('       - Addiing passanger to DirectionalLocation', passanger.id, 'to location', self.id)
        if passanger is None:
            raise Exception('Logic Error: Inserted passanger can not be NONE')
        else:
            super(DirectionalLocation, self).add_passenger(passanger)
            self.main_location.add_passenger(passanger)
            return True

    def add_vehicle(self, vehicle):#: Vehicle):
        super(DirectionalLocation, self).add_vehicle(vehicle)
        if vehicle.id not in self.main_location.vehicles_dict:
            self.main_location.add_vehicle(vehicle)

    def remove_vehicle(self, vehicle):
        if vehicle.id == 47032:
            print('       - Removing vehicle 47032 at DirectionalLocation',self.id)
        for i in range(0, len(self.stops)):
            if vehicle.id in self.stops[i].vehicles_dict:
                super(DirectionalLocation, self.stops[i]).remove_vehicle(vehicle)
        if vehicle.id in self.vehicles_dict:
            super(DirectionalLocation, self).remove_vehicle(vehicle)
        self.main_location.remove_vehicle(vehicle)

    def get_actual_number_of_passangers(self):
        res = 0
        for i in range(0, len(self.stops)):
            res += self.stops[i].passangers.length
        return res

    def remove_passenger(self, passenger):
        for i in range(0, len(self.stops)):
            if passenger.id in self.stops[i].passangers_dict:
                super(DirectionalLocation, self.stops[i]).remove_passenger(passenger)
        if passenger.id in self.passangers_dict:
            super(DirectionalLocation, self).remove_passenger(passenger)
        self.main_location.remove_passenger(passenger)

    def get_passanger(self):
        if self.main_location.total_number_of_passangers > 0:
            self.main_location.total_number_of_passangers -= 1
            passenger = self.main_location.passangers.get_item()
            del self.main_location.passangers_dict[passenger.id]
            for i in range(0, len(self.stops)):
                if passenger.id in self.stops[i].passangers_dict:
                    super(DirectionalLocation, self.stops[i]).remove_passenger(passenger)
            if passenger.id in self.passangers_dict:
                super(DirectionalLocation, self).remove_passenger(passenger)
            return passenger
        else:
            return None

    def get_vehicle(self):
        if self.main_location.total_number_of_vehicles > 0:
            self.main_location.total_number_of_vehicles -= 1
            vehicle = self.main_location.vehicles.get_item()
            del self.main_location.vehicles_dict[vehicle.id]
            for i in range(0, len(self.stops)):
                if vehicle.id in self.stops[i].vehicles_dict:
                    super(DirectionalLocation, self.stops[i]).remove_vehicle(vehicle)
            if vehicle.id in self.vehicles_dict:
                super(DirectionalLocation, self).remove_vehicle(vehicle)
            return vehicle
        else:
            return None

#    def first_passanger(self):
#        if len(self.stops) > 0:
#            min_stop = None
#            min_value = None
#            for i in range(0,len(self.stops)):
#                if min_value is None or min_value > self.stops[i].passangers.start.obj.arrival_times:
#                    min_value = self.stops[i].passangers.start.obj.arrival_times
#                    min_stop = i
#            if min_stop is None:
#                return None
#            else:
#                return self.stops[min_stop].start.obj
#        else:
#            return self.passangers.start.obj

#    def get_passanger(self):
#        if len(self.stops) > 0:
#            min_stop = None
#            min_value = None
#            for i in range(0,len(self.stops)):
#                if self.stops[i].total_number_of_passangers > 0:
#                    if min_value is None or min_value > self.stops[i].passangers.start.obj.arrival_times:
#                        min_value = self.stops[i].passangers.start.obj.arrival_times
#                        min_stop = i
#            if min_stop is None:
#                return None
#            else:
#                if self.stops[min_stop].id != self.id:
#                    print(self.stops[min_stop].id, self.id)
#                    exit(0)
#                self.stops[min_stop].total_number_of_passangers -= 1
#                passenger = self.stops[min_stop].passangers.get_item()
#                del self.stops[min_stop].passangers_dict[passenger.id]
#                return passenger
#        else:
#            if self.total_number_of_passangers > 0:
#                self.total_number_of_passangers -= 1
#                passenger = self.passangers.get_item()
#                del self.passangers_dict[passenger.id]
#                return passenger
#            else:
#                return None