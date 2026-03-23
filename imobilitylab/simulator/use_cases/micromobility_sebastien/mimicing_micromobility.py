import sys
import os
from imobilitylab.simulator.event_based.objects.location import Location_with_passive_vehicles
from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.objects.trips import JourneyCollection, TripCollection, TripBasic
from imobilitylab.simulator.event_based.micromobility.objects import MicromobilityFleetManager, CaseStudy_micromobility,ScooterVehicle, TripMicromobility
from imobilitylab.simulator.event_based.core.simulator import Simulator, TimeLine_with_TimeBins

location_file = sys.argv[1]
distance_matrix_escooter_folder = sys.argv[2] + '/'
output_dir = sys.argv[3] + '/'

case_study = CaseStudy_micromobility()
case_study.add_simulator(Simulator(None, TimeLine_with_TimeBins(300)))
case_study.simulator.config.detailed_terminal_print_of_simulation = True

manager = MicromobilityFleetManager(case_study)
print('LOADING INPUT DATA')
print('     # loading locations for case study')
file = open(location_file)
#id;type;original_id;original_type;lon;lat;node_id_car;distance_to_car;node_id_walk;distance_to_walk
file.readline()
while 1:
    line = file.readline()
    if not line:
        break
    pass
    parts = line.strip('\n\r').split(';')
    locaiton_t = Location_with_passive_vehicles(int(parts[0]), parts[2])
    case_study.add_location(locaiton_t)
file.close()

print('        locations loaded', len(case_study.locations))

def add_record_to_distance_tt_matrix(manager_in:MicromobilityFleetManager, from_node: int, to_node:int, distance:int, tt:int):
    if from_node not in manager_in.distance_tt_matrix:
        manager_in.distance_tt_matrix[from_node] = {}
    if to_node not in manager_in.distance_tt_matrix[from_node]:
        manager_in.distance_tt_matrix[from_node][to_node] = (distance, tt)

print('     # loading distance matrix')
manager.distance_tt_matrix = {}
listning = os.listdir(distance_matrix_escooter_folder)
for i in range(0, len(listning)):
    if os.path.isfile(distance_matrix_escooter_folder + '/' + listning[i]):
        print('             - loading part of distance matrix ',i,'/',len(listning),'from file:', distance_matrix_escooter_folder + '/' + listning[i])
        file = open(distance_matrix_escooter_folder + '/' + listning[i])
        file.readline()
        while 1:
            line = file.readline()
            if not line:
                break
            pass
            parts = line.strip('\n\r').split(';')
            add_record_to_distance_tt_matrix(manager, int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
        file.close()
print('        matrix loaded to case-study')

location_102 = case_study.locations[case_study.location_id_to_index[102]]
location_118 = case_study.locations[case_study.location_id_to_index[118]]

case_study.add_vehicle(ScooterVehicle(1, location_102, 1, manager))

journey_t = TripCollection(1, location_102, location_118)
journey_t.register_trip(TripMicromobility(location_102, location_118, 20))
passanger_t_jcollection = JourneyCollection()
passanger_t_jcollection.register_journey(journey_t)

passanger_t = Passenger(1, 20, location_102, passanger_t_jcollection)
case_study.add_passenger(passanger_t)

print('INPUT DATA LOADED')

print('Simulation starts')

case_study.start_simulation()
case_study.make_statistic(output_dir, None, True)

print('End of Simulation')

