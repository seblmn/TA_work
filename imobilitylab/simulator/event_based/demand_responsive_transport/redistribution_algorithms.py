from imobilitylab.supporting_libraries.fifo import FIFO
from imobilitylab.simulator.event_based.objects.vehicle import Vehicle
from imobilitylab.simulator.event_based.objects.location import Location
from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.objects.fleet_management import FleetManager


def get_closet_empty_vehicle(passenger: Passenger,manager: FleetManager):
    if manager.case_study.simulator.config.detailed_terminal_print_of_simulation:
        print('   available vehicles', len(manager.available_empty_vehicles), manager.simulator.time_line.actual_time)
    minDis = None
    minLoc = None
    for i, obj in enumerate(manager.vehicles_on_locations):
        if manager.vehicles_on_locations[obj].length > 0:
            dis = manager.case_study.get_travel_time(passenger.location, manager.case_study.get_location_based_on_id(obj))
            if minDis is None or minDis > dis:
                minDis = dis
                minLoc = obj

    if minLoc is not None:
        if manager.case_study.simulator.config.detailed_terminal_print_of_simulation:
            print('  available vehicles, num before removing', len(manager.available_empty_vehicles))
            print('  closesd station with available vehicle', minLoc, 'number of vehicles',
              manager.vehicles_on_locations[minLoc].length)
        #print(len(self.vehicles_on_locations),len(self.available_empty_vehicles))
        vehicle = manager.vehicles_on_locations[minLoc].get_item()
        vehicle.location.remove_vehicle(vehicle)
        del manager.available_empty_vehicles[vehicle.id]
        if manager.vehicles_on_locations[obj].length == 0:
            del manager.vehicles_on_locations[obj]
        if manager.case_study.simulator.config.detailed_terminal_print_of_simulation:
            if minLoc in manager.vehicles_on_locations:
                print('  closed vehicle',vehicle.id,'; total available', len(manager.available_empty_vehicles),
                      '; on station',minLoc,'is', manager.vehicles_on_locations[minLoc].length)
            else:
                print('  closed vehicle',vehicle.id,' ; total available', len(manager.available_empty_vehicles),
                      '; on station',minLoc, 'EMPTY - No Vehicle on location')
        return vehicle
    else:
        if manager.case_study.simulator.config.detailed_terminal_print_of_simulation:
            print('  There is none available vehicle!')
        return None


def do_nothing(passenger: Passenger, manager: FleetManager):
    return None


def only_empty_vehicle_on_station(passenger: Passenger, manager: FleetManager):
    if passenger.location.id in manager.vehicles_on_locations:
        if manager.case_study.simulator.config.detailed_terminal_print_of_simulation:
            print('   on station available vehicles', manager.vehicles_on_locations[passenger.location.id].length,
                  'total', len(manager.available_empty_vehicles))
        vehicle = manager.vehicles_on_locations[passenger.location.id].get_item()
        if vehicle is not None:
            del manager.available_empty_vehicles[vehicle.id]

            vehicle.location.remove_vehicle(vehicle)
            if manager.vehicles_on_locations[passenger.location.id].length == 0:
                del manager.vehicles_on_locations[passenger.location.id]
            if manager.case_study.simulator.config.detailed_terminal_print_of_simulation:
                if passenger.location.id in manager.vehicles_on_locations:
                    print('   on station vehicle on station ', vehicle.id, ' after removal',
                          manager.vehicles_on_locations[passenger.location.id].length,
                          'total', len(manager.available_empty_vehicles))
                else:
                    print('   on station vehicle on station ', vehicle.id, ' after removal',
                          'EMPTY - No Vehicle on location ',
                          'Total', len(manager.available_empty_vehicles))
        return vehicle
    else:
        if manager.case_study.simulator.config.detailed_terminal_print_of_simulation:
            print('   no vehicle on station ', passenger.id, passenger.location.id)
    return None
