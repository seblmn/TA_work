from imobilitylab.simulator.event_based.objects.vehicle import Vehicle
from imobilitylab.simulator.event_based.objects.case_study import CaseStudyDistanceMatrix
from imobilitylab.simulator.event_based.objects.location import Location
from imobilitylab.simulator.event_based.objects.location import DirectionalLocation
from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.objects.fleet_management import FleetManager
from imobilitylab.simulator.event_based.objects.case_study import CaseStudy
from imobilitylab.supporting_libraries.fifo import FIFO
from imobilitylab.supporting_libraries.fifo import FifoItem
from imobilitylab.simulator.event_based.event.transport import VehicleBoardingEvent
from imobilitylab.simulator.event_based.event.transport import PassengerUnloadEvent
from imobilitylab.simulator.event_based.event.transport import VehicleStationArrivalEvent
from imobilitylab.simulator.event_based.demand_responsive_transport.events import PassengerArrivalEventDemandResponsive
import imobilitylab.simulator.event_based.demand_responsive_transport.redistribution_algorithms as red_alg_lib
import os


class CaseStudyDemandResponsive(CaseStudyDistanceMatrix):

    def inicialize_passengers_for_simulation(self):
        for i in range(0, len(self.passengers)):
            if i % 10000 == 0:
                print(i, len(self.passengers))
            self.simulator.add_event(PassengerArrivalEventDemandResponsive(self.passengers[i].arrival_times[0],
                                                                           self.passengers[i],
                                                                           self.passengers[i].location))


class DemandResponsiveServiceManager(FleetManager):

    def __init__(self, case_study: CaseStudy, probability_send_vehicle_to_longest_waiting: float=0.0,
                 defualt_redistribution_algorithm=None):
        super(DemandResponsiveServiceManager, self).__init__(case_study)
        self.passengers = FIFO()
        self.passengers_dict = {}
        self.passengers_served = 0
        self.available_empty_vehicles = {}
        self.vehicles_on_locations = {}
        self.defualt_redistribution_algorithm = defualt_redistribution_algorithm
        self.probability_send_vehicle_to_longest_waiting = probability_send_vehicle_to_longest_waiting
        if defualt_redistribution_algorithm is None:
            self.defualt_redistribution_algorithm = red_alg_lib.get_closet_empty_vehicle
        self.redistribution_algorithms = []
        self.type = 'DRT'

    def get_the_distance_and_travel_time_from_stop_to_stop(self, start_location: Location, end_location: Location):
        return self.case_study.get_distance(start_location,end_location), self.case_study.get_travel_time(start_location,end_location)

    def register_redistribution_algorithm(self,probability: float,redistribution_algorithm):
        self.redistribution_algorithms.append((probability, redistribution_algorithm))

    def add_vehicle(self, vehicle: Vehicle):
        self.vehicles.append(vehicle)
        self.register_vehicle_for_redistribution(vehicle)

    def register_vehicle_for_redistribution(self, vehicle: Vehicle):
        self.available_empty_vehicles[vehicle.id] = vehicle
        if vehicle.location.id not in self.vehicles_on_locations:
            self.vehicles_on_locations[vehicle.location.id] = FIFO()
        self.vehicles_on_locations[vehicle.location.id].add_item(FifoItem(vehicle))
        self.do_action_for_empty_vehicle_waiting_passenger()
        num = 0
        for i, obj in enumerate(self.vehicles_on_locations):
            num += self.vehicles_on_locations[obj].length
        if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
            print('registering', vehicle.id, 'number available',len(self.available_empty_vehicles), ' on stations', num)
        if len(self.available_empty_vehicles) > len(self.vehicles):
            raise Exception('ERROR: There can be not more available vehicles on stations as is the number of vehicles')
        if num > len(self.vehicles):
            raise Exception('ERROR: There can be not more registered vehicles on stations as is the number of vehicles')
        if num != len(self.available_empty_vehicles):
            raise Exception('ERROR: Overal available should be the same as count across available on stations')



    def redistribute_vehicle(self, passenger: Passenger):
        if len(self.redistribution_algorithms) > 0:
            probability = int.from_bytes(os.urandom(8), byteorder="big") / ((1 << 64) - 1)
            #print(probability,self.redistribution_algorithms[0][0])

            for i in range(0, len(self.redistribution_algorithms)):
                if probability <= self.redistribution_algorithms[i][0]:
                    vehicle = self.redistribution_algorithms[i][1](passenger, self)
                    if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                        print(self.simulator.time_line.actual_time,'@@@ redistributting',vehicle.id,passenger.id)
                    return vehicle
        return self.defualt_redistribution_algorithm(passenger, self)

    def redistribute_vehicle_for_longest_passenger(self, vehicle: Vehicle):
        if self.passengers.length > 0:
            #print(self.passengers.length)
            passenger = self.passengers.start.obj
            probability = int.from_bytes(os.urandom(8), byteorder="big") / ((1 << 64) - 1)
            #print(probability,self.redistribution_algorithms[0][0])
            if probability <= self.probability_send_vehicle_to_longest_waiting:
                self.unregister_passenger(passenger)
                if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                    print(self.simulator.time_line.actual_time,'@@@ redistributting', vehicle.id, passenger.id,
                          self.passengers.length)
                vehicle.location.remove_vehicle(vehicle)
                self.send_vehicle_for_passenger(vehicle, passenger)
                return True
        return False
        #return self.defualt_redistribution_algorithm(passenger, self)

    def send_vehicle_for_passenger(self, vehicle: Vehicle, passenger: Passenger):
        #print('sending vehicle', vehicle.id, self.simulator.time_line.actual_time +
        #      self.case_study.get_travel_time(vehicle.location, passenger.location))
        dis = self.case_study.get_distance(vehicle.location, passenger.location)
        tt = self.case_study.get_travel_time(vehicle.location, passenger.location)
        #vehicle.location.remove_passenger(vehicle)
        self.simulator.add_event(VehicleStationArrivalEvent(self.simulator.time_line.actual_time + tt,
                                                            vehicle,
                                                            passenger.location, dis, tt,
                                                            passenger))

    def take_passenger_from_actual_station_or_register(self, vehicle: Vehicle, location: Location):
        if vehicle.empty_space() > 0 and location.get_actual_number_of_passangers() > 0:
            passenger = location.get_passanger()
            self.unregister_passenger(passenger)
            destination = passenger.get_final_destination()#select_destination()
            vehicle.add_passenger(passenger, destination, self.simulator.time_line.actual_time)
            self.board_passengers(vehicle, location, destination, passenger)
            vehicle.location.remove_vehicle(vehicle)
            dis = self.case_study.get_distance(location, destination)
            tt = self.case_study.get_travel_time(location, destination)
            self.simulator.add_event(VehicleStationArrivalEvent(self.simulator.time_line.actual_time + tt,
                                                                vehicle, destination, dis, tt))

        else:
            self.register_vehicle_for_redistribution(vehicle)
            #location.add_vehicle(vehicle)

    def vehicle_arrived_to_location(self, event: VehicleStationArrivalEvent):
        if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
            print(self.simulator.time_line.actual_time, 'F M vehicle_arrived', event.vehicle.id)
        if event.vehicle.location.id != event.location.id:
            raise Exception('ERROR: Vehicle is not on dedicated station as it should arrived')
        if event.passenger is not None:
            if event.location.is_passenger_on_station(event.passenger):
                if event.vehicle.location.id == event.passenger.location.id:
                    destination = event.passenger.get_final_destination()#select_destination()
                    if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                        print(self.simulator.time_line.actual_time,' FM bording dedicated passenger', event.passenger.id,
                              event.vehicle.id, self.simulator.time_line.actual_time +
                              self.case_study.get_travel_time(event.location, destination))
                    event.location.remove_passenger(event.passenger)
                    event.vehicle.add_passenger(event.passenger, destination, self.simulator.time_line.actual_time)
                    self.board_passengers(event.vehicle, event.location, destination, event.passenger)
                    event.location.remove_vehicle(event.vehicle)
                    dis = self.case_study.get_distance(event.location, destination)
                    tt = self.case_study.get_travel_time(event.location, destination)
                    self.simulator.add_event(VehicleStationArrivalEvent(self.simulator.time_line.actual_time + tt,
                                                                        event.vehicle, destination, dis, tt))
                else:
                    print(event.vehicle.location.id, event.passenger.location.id)
                    raise Exception('ERROR: Vehicle is not on dedicated station as it should arrived')
            else:
                if not self.redistribute_vehicle_for_longest_passenger(event.vehicle):
                    if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                        print(self.simulator.time_line.actual_time,' FM someone took dedicated passenger from station',
                              event.location.id,' taking new one')
                    self.take_passenger_from_actual_station_or_register(event.vehicle, event.location)

        # event not mentioned for particular passenger,
        else:
            # vehicle is occupied IT is destination -> empty the vehicle
            if event.vehicle.total_boarded > 0:
                if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                    print(self.simulator.time_line.actual_time,' FM unlocad',event.vehicle.id, event.location.id)
                t_array = event.vehicle.get_leaving_passengers(event.location)
                if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                    print('     unloading :', len(t_array), 'number of passenger on vehicle:',event.vehicle.total_boarded)
                for i in range(0, len(t_array)):
                    if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                        print('         unload :', t_array[i].id)
                    self.simulator.immediate_procees_event(PassengerUnloadEvent(self.simulator.time_line.actual_time,
                                                                                t_array[i], event.location,
                                                                                event.vehicle, event.travel_time,
                                                                                event.distance, event.on_board))
                    self.passengers_served += 1
                if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                    print(self.simulator.time_line.actual_time,' served passengers', self.passengers_served, self.simulator.time_line.actual_time)

            # if there is someone already on stop take him
            if not self.redistribute_vehicle_for_longest_passenger(event.vehicle):
                if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                    print(self.simulator.time_line.actual_time,' FM unloaded and taking from station directly the longest')
                self.take_passenger_from_actual_station_or_register(event.vehicle, event.location)

    def board_passengers(self, vehicle: Vehicle, location: Location,destination: Location, first_passenger: Passenger):
        if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
            print(' Boarding ...', vehicle.id, vehicle.empty_space(), 'num of waiting passengers:',
                  location.passangers.length)
        if vehicle.empty_space() > 0:

            if isinstance(location, DirectionalLocation):
                if location.get_actual_number_of_passangers() > 0:
                    item = location.main_location.passangers.start
                else:
                    item = None
                    if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                        print(' No passenger on directional stations')
            else:
                if location.get_actual_number_of_passangers() > 0:
                    item = location.passangers.start
                else:
                    item = None
                    if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                        print(' No passenger on stations')

            if item is not None:
                    if item.obj.id != first_passenger.id:
                        while vehicle.empty_space() > 0 and item is not None:
                            if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                                print('   Boarding ...', vehicle.id, vehicle.empty_space(), 'looking for des:', destination.id,
                                      ' passenger des', item.obj.destination_location.id)
                            if item.obj.get_final_destination().id == destination.id:
                                passenger = item.obj
                                passenger.get_final_destination()#select_destination()
                                item = item.next_item
                                self.unregister_passenger(passenger)
                                location.remove_passenger(passenger)
                                #item.obj.register_borded_time(self.simulator.time_line.actual_time)
                                vehicle.add_passenger(passenger, destination, self.simulator.time_line.actual_time)
                                if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                                    print('   Boarded!', vehicle.id, vehicle.empty_space(),'passenger ',passenger.id)
                                #if vehicle.empty_space() == 0:
                                    #exit(0)
                            else:
                                item = item.next_item
                    else:
                        raise Exception('ERROR: First was already taken, should be not on Location any more')
                #else:
                #    print(' No passenger on stations')

    def decide_next_step_for_vehicle(self, vehicle: Vehicle):
        if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
            print(self.simulator.time_line.actual_time,' FM decide next step')
        if vehicle.location.get_actual_number_of_passangers() > 0:
            if vehicle.empty_space() > 0:
                self.simulator.immediate_procees_event(VehicleBoardingEvent(self.simulator.time_line.actual_time,
                                                                            vehicle,
                                                                            vehicle.location))
        # If station has no waiting passengers
        else:
            if vehicle.empty_space() == 0:
                self.register_vehicle_for_redistribution(vehicle)
            else:
                # at the moment we allow only ride-sharing for client with same ORG - DES
                pass

    def do_action_for_empty_vehicle_waiting_passenger(self):
        if len(self.available_empty_vehicles) > 0 and self.passengers.length > 0:
            #item = self.passengers.start
            while len(self.available_empty_vehicles) > 0 and self.passengers.length > 0:
                #print(len(self.available_empty_vehicles), self.passengers.length)
                passenger = self.passengers.start.obj
                vehicle = self.redistribute_vehicle(passenger)
                if vehicle is not None:
                    passenger = self.get_and_unregister_passenger()
                    self.send_vehicle_for_passenger(vehicle, passenger)
                #item = item.next_item

    def get_and_unregister_passenger(self):
        passenger = self.passengers.get_item()
        del self.passengers_dict[passenger.id]
        return passenger

    def unregister_passenger(self, passenger: Passenger):
        if passenger.id in self.passengers_dict:
            if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                print(self.simulator.time_line.actual_time, ' FM UNREGISTRING,',passenger.id,len(self.passengers_dict))
            self.passengers.remove_item(self.passengers_dict[passenger.id])
            del self.passengers_dict[passenger.id]
        else:
            if self.case_study.simulator.config.detailed_terminal_print_of_simulation:
                print(self.simulator.time_line.actual_time, ' passenger already unregistered',passenger.id)


class DemandResponsiveServiceManager_call_based(DemandResponsiveServiceManager):

    def __init__(self, case_study: CaseStudy, probability_send_vehicle_to_longest_waiting: float=0.0,
                 defualt_redistribution_algorithm=None):
        super(DemandResponsiveServiceManager_call_based, self).__init__(case_study,
                                                                        probability_send_vehicle_to_longest_waiting,
                                                                        defualt_redistribution_algorithm)
        self.type = 'DRT call based'

    def register_passenger(self, passenger: Passenger):
        if len(self.available_empty_vehicles) > 0 and self.passengers.length == 0:
            vehicle = self.redistribute_vehicle(passenger)
            if vehicle is not None:
                self.send_vehicle_for_passenger(vehicle, passenger)
            else:
                item = FifoItem(passenger)
                self.passengers_dict[passenger.id] = item
                self.passengers.add_item(item)
        else:
            item = FifoItem(passenger)
            self.passengers_dict[passenger.id] = item
            self.passengers.add_item(item)
