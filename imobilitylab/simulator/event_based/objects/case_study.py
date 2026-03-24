from imobilitylab.simulator.event_based.objects.location import Location
from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.objects.vehicle import Vehicle
from imobilitylab.simulator.event_based.core.simulator import Simulator
from imobilitylab.simulator.event_based.event.transport import PassengerArrivalEvent
from imobilitylab.simulator.event_based.objects.trips import TripBasic

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from pylab import figure, show, legend, ylabel

class CaseStudy(object):

    def __init__(self):
        self.locations = []
        self.passengers = []
        self.vehicles = []
        self.location_id_to_index = {}
        self.vehicle_id_to_index = {}
        self.simulator = None
        self.managers = []
        self.boarding_time_bus = 3
        self.boarding_time_tram = 3
        self.boarding_time_metro = 1
        self.boarding_time_train = 1
        self.boarding_time_default = 2
        # settings for passanger behavior/acceptance of decission

        # below attribute if FALSE -> Journey starts of planed time "start_time" but inside of journey trips times can
        #   be delayed but never allows to accept earlier arrival to any location on stop (there can or can not be
        #   activity we do not know BUT we want to keep time as planned for sub-trips inside of journeys
        # below attribute if TRUE -> Journey starts of planed time "start_time" but inside of journey trips times can
        #   be delayed but ALSO arrive earlier if earlier supply prodived or found (this can be tricky if transfer
        #   walking time is unknown, whicle in FALSE it may be considered in "start_time" plans
        self.passanger_can_be_delayed_but_never_arrive_earlier_as_planned_times_during_the_journey_execution = True

    #def add_passenger_next_trip_arrival_to_simulation(self, passenger: Passenger, immediate_processing:bool = False):
    #    # 'True' means competed; 'False' means still trip to realize
    #    if not immediate_processing:
    #        self.simulator.add_event(PassengerArrivalEvent(passenger.arrival_times[0],
    #                                                       passenger,
    #                                                       passenger.location))
    #    else:
    #        self.simulator.immediate_procees_event(PassengerArrivalEvent(passenger.arrival_times[0],
    #                                                       passenger,
    #                                                       passenger.location))
    #    return True

    def add_passenger_next_trip_arrival_to_simulation(self, passenger: Passenger, arrival_execution_time: int, trip:TripBasic, immediate_processing:bool = False):
        if not immediate_processing:
            self.simulator.add_event(PassengerArrivalEvent(arrival_execution_time,
                                                                       passenger,
                                                                       trip.start_location))
        else:
            self.simulator.immediate_procees_event(PassengerArrivalEvent(arrival_execution_time,
                                                                       passenger,
                                                                       trip.start_location))

    def register_passenger_observation(self, passanger: Passenger):
        pass

    def register_manager(self, manager):
        self.managers.append(manager)

    def inicialize_vehicles_for_simulation(self):
        for i in range(0, len(self.vehicles)):
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

    def start_simulation(self):
        print('#### Inicialization for simulation ....')
        if self.simulator is not None:
            print('   Inicialization: passengers arrivals ....')
            self.inicialize_passengers_for_simulation()
            print('   Inicialization: vehicles ....')
            self.inicialize_vehicles_for_simulation()
            #for i in range(0, len(self.managers)):
            #    print(' Number of vehicles in manager', i, ':', self.managers[i].number_of_vehicles())
            print(' Number of event in time-line:',self.simulator.time_line.num_events())
            print('#### Inicialized!')
            print('#### Simullation ....')
            self.simulator.start()
            print('#### Simullation end!')
            #Afor i in range(0,len(self.locations)):
            #        print(i, self.locations[i].id,
            #              self.locations[i].get_actual_number_of_passangers())
        else:
            raise Exception('ERROR: simulator is not defined for case study yet')

    def add_simulator(self, simulator: Simulator):
        simulator.case_study = self
        self.simulator = simulator

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

    def add_location(self, location: Location):
        location.case_study = self
        self.location_id_to_index[location.id] = len(self.locations)
        self.locations.append(location)

    def add_passenger(self, passenger: Passenger):
        passenger.case_study = self
        self.passengers.append(passenger)

    def get_vehicle(self, vehicle_id: int):
        if vehicle_id in self.vehicle_id_to_index:
            return self.vehicles[self.vehicle_id_to_index[vehicle_id]]
        else:
            return None

    def add_vehicle(self, vehicle: Vehicle):
        if vehicle.id not in self.vehicle_id_to_index:
            self.vehicle_id_to_index[vehicle.id] = len(self.vehicles)
            self.vehicles.append(vehicle)

    def get_location_based_on_id(self, location_id: str):
        return self.locations[self.location_id_to_index[location_id]]

    def get_boarding_time(self, number_of_passangers: int, mode: str, location: Location = None, vechicle:Vehicle = None):
        if mode in ('BUS','BUSTERM'):
            return number_of_passangers * self.boarding_time_bus
        elif mode in ('METRO','METROSTN'):
            return number_of_passangers * self.boarding_time_metro
        elif mode in ('TRAM','TRAMSTN'):
            return number_of_passangers * self.boarding_time_tram
        elif mode in ('TRAIN', 'RAIL', 'RAILWSTN'):
            return number_of_passangers * self.boarding_time_train
        else:
            return number_of_passangers * self.boarding_time_default

    def stop_simulation_if_all_passengers_served(self):
        total_served = 0
        #for i in range(0,len(self.managers)):
        #    total_served += self.managers[i].passengers_served
        for i in range(0, len(self.passengers)):
            if self.passengers[i].served:
                total_served += 1
        if self.simulator.config.detailed_terminal_print_of_simulation:
            print('# served passengers so far ',total_served)
        if len(self.passengers) == total_served:
            print('Stoping simulator')
            self.simulator.stop()
        if len(self.passengers) < total_served:
            raise Exception('ERROR: Served more passengers as is in the system')

    def export_individual_passangers(self,output_dir:str=None):
        file_o = open(output_dir+'individual_passenger_trips.csv','w')

        file_o.write('passanger_id;passanger_arrival_time;passanger_waiting_time;final_trip;passanger_trip_id;start_time;end_time;travel_time;distance;departure_key;segments_on_board;avg_on_board;avg_occupancy_rate;travel_time_from_departure;start_location;end_location;vehicle_trip_id,line_id,direction_id,vehicle_id;manager_id'+'\n')
        for i in range(0, len(self.passengers)):
            print('passanger journeys', len(self.passengers[i].journey_collection.executed_journeys))
            for j in range(0, len(self.passengers[i].journey_collection.executed_journeys)):
                print('   trips:', len(self.passengers[i].journey_collection.executed_journeys[j].executed_trips))
                for k in range(0, len(self.passengers[i].journey_collection.executed_journeys[j].executed_trips)):
                        trip_t = self.passengers[i].journey_collection.executed_journeys[j].executed_trips[k]
                        waiting_time = self.passengers[i].borded_times[j] - self.passengers[i].arrival_times[j]
                        final_trip = 0
                        if j == len(self.passengers[i].journey_collection.executed_journeys) -1 and k == len(self.passengers[i].journey_collection.executed_journeys[j].executed_trips) - 1:
                            final_trip = 1
                        trip_info = trip_t.to_csv_str()
                        file_o.write(str(self.passengers[i].id)+';'+str(self.passengers[i].arrival_times[0])+';'
                                     +str(waiting_time)+';'+str(final_trip)+';'+trip_info+'\n')
        file_o.close()

    def export_individual_trips_stat(self,output_dir:str=None):
        self.export_individual_passangers(output_dir)

        file_o = open(output_dir+'individual_vehicle_trips.csv','w')
        file_o.write('vehicle_id;manager_id;departure_id;departure_time;segment_order_index;in_simulation_start_time;in_simulation_end_time;'
                     'in_simulation_travel_time;in_simulation_distance;in_simulation_on_board;sharing_rate;'
                     'start_location;end_location;planned_start_time;planned_end_time;planned_travel_time;planned_distance\n')

        for i in range(0, len(self.vehicles)):
            for j in range(0, len(self.vehicles[i].trip_collection)):
                trip_info = self.vehicles[i].trip_collection[j].to_csv_str()
                file_o.write(trip_info+'\n')
        file_o.close()

        file_o = open(output_dir+'individual_departures.csv','w')

        file_o.write('departure_id;manager_id;vehicle_id;departure_time;end_time;start_location;start_location_index;'
                     'total_time;n_segments;served_passengers;'
                     'total_empty_trips;total_occupied_trips;avg_occupancy;std_occupancy;max_occupancy;'
                     'avg_occupancy_rate;std_occupancy_rate;max_occupancy_rate;;individual_segment_trips_from_here(-1 is for not applicable)'+'\n')

        for i in range(0, len(self.managers)):
            if 'public transport' in self.managers[i].type:
                for j in range(0,len(self.managers[i].departures)):
                    trip_info = self.managers[i].departures[j].to_csv_str()
                    file_o.write(trip_info+'\n')
        file_o.close()


    def make_statistic(self,output_dir:str=None,computational_time:int=None,print_individual_trips_stat = False):

        print('#### FINAL STATISTIC')
        print(' # OVERALL stat')
        if computational_time is not None:
            print('    comp time:',str(computational_time))
        print('   simulation end time:', self.simulator.time_line.actual_time)
        if output_dir is not None:
            file_o = open(output_dir+'statistics.txt','w')
            file_o.write('# OVERALL stat;'+'\n')
            if computational_time is not None:
                file_o.write('comp time;'+str(computational_time)+'\n')
            file_o.write('end time;'+str(self.simulator.time_line.actual_time)+'\n')
        served = 0
        not_served_passangers = 0
        in_simulation = 0
        total_waiting_time = 0
        total_time_on_board = 0
        total_time_on_board_vehicle_event = 0
        total_distance_on_board_vehicle_event = 0
        total_time = 0
        max_waiting_time = 0
        max_time_on_board = 0
        max_time_vehicle_event = 0
        max_distance_vehicle_event = 0
        max_time = 0
        num_on_planned_destination = 0

        num_of_bins = int(self.simulator.time_line.actual_time/900)+1
        bins = []
        for i in range(0, num_of_bins):
                bins.append([0, 0, 0, 0, 0, 0])

        for i in range(0, len(self.passengers)):
            #print('passanger', self.passengers[i].id, len(self.passengers[i].arrival_times), len(self.passengers[i].borded_times))
            #if self.passengers[i].location.id == self.passengers[i].destination_location.id:
            #    num_on_planned_destination += 1
            if self.passengers[i].in_simulation:
                if self.passengers[i].served:
                    in_simulation += 1
                    val = self.passengers[i].get_total_waiting_time(self.simulator.time_line.actual_time)
                    bins[int(self.passengers[i].arrival_times[0]/900)][0] += 1
                    bins[int(self.passengers[i].arrival_times[0]/900)][1] += val
                    bins[int(self.passengers[i].borded_times[0]/900)][2] += 1
                    bins[int(self.passengers[i].borded_times[0]/900)][3] += val
                    bins[int(self.passengers[i].arrival_times[len(self.passengers[i].arrival_times)-1]/900)][4] += 1
                    bins[int(self.passengers[i].arrival_times[len(self.passengers[i].arrival_times)-1]/900)][5] += val
                    if max_waiting_time < val:
                        max_waiting_time = val
                    total_waiting_time += val
                    val = self.passengers[i].get_total_time(self.simulator.time_line.actual_time)
                    if max_time < val:
                        max_time = val
                    total_time += val
                    if self.passengers[i].served:
                        val = self.passengers[i].get_travel_time_on_board(self.simulator.time_line.actual_time)
                        if max_time_on_board < val:
                            max_time_on_board = val
                        if max_distance_vehicle_event < self.passengers[i].total_distance_on_board_from_vehicleEvent:
                            max_distance_vehicle_event = self.passengers[i].total_distance_on_board_from_vehicleEvent
                        if max_time_vehicle_event < self.passengers[i].total_travel_time_on_board_from_vehicleEvent:
                            max_time_vehicle_event = self.passengers[i].total_travel_time_on_board_from_vehicleEvent
                        total_time_on_board += val
                        total_time_on_board_vehicle_event += self.passengers[i].total_travel_time_on_board_from_vehicleEvent
                        total_distance_on_board_vehicle_event += self.passengers[i].total_distance_on_board_from_vehicleEvent
                        served += 1
                else:
                    not_served_passangers += 1

        y_arrivals = []
        y_arrivals_waiting = []
        y2_borded = []
        y2_borded_waiting = []
        y3_des = []
        y3_des_waiting = []
        x = []
        for i in range(0, num_of_bins):
            y_arrivals.append(bins[i][0])
            y2_borded.append(bins[i][2])
            y3_des.append(bins[i][4])
            if bins[i][0]>0:
                y_arrivals_waiting.append(bins[i][1]/float(bins[i][0]))
            else:
                y_arrivals_waiting.append(0)
            if bins[i][2]>0:
                y2_borded_waiting.append(bins[i][3]/float(bins[i][2]))
            else:
                y2_borded_waiting.append(0)
            if bins[i][4]>0:
                y3_des_waiting.append(bins[i][5]/float(bins[i][4]))
            else:
                y3_des_waiting.append(0)
            x.append(i+1)

        fig = plt.figure()

        ax = fig.add_subplot(111)
        ax.set_title('Waiting times and arrival')
        ax2 = fig.add_subplot(111, sharex=ax, frameon=False)
        ax.bar(x, y_arrivals, color='#8da0cb')
        ylabel("arrived passengers")
        ax2.plot(x, y_arrivals_waiting, color='#fc8d62')
        ax2.yaxis.tick_right()
        ax2.yaxis.set_label_position("right")
        ylabel("waiting time")
        #plt.show()
        plt.savefig(output_dir+'waiting_times_and_arrivals.png')

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_title('Waiting times and boardings')
        ax2 = fig.add_subplot(111, sharex=ax, frameon=False)
        ax.bar(x, y2_borded, color='#66c2a5')
        ylabel("borded passengers")
        ax2.plot(x, y2_borded_waiting, color='#fc8d62')
        ax2.yaxis.tick_right()
        ax2.yaxis.set_label_position("right")
        ylabel("waiting time")
        #plt.show()
        plt.savefig(output_dir+'waiting_times_and_boarding.png')

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_title('Waiting times and destinations times')
        ax2 = fig.add_subplot(111, sharex=ax, frameon=False)
        line1 = ax.bar(x, y3_des, color='#e41a1c')
        ylabel("passengers in final")
        line2 = ax2.plot(x, y3_des_waiting, color='#fc8d62')
        ax2.yaxis.tick_right()
        ax2.yaxis.set_label_position("right")
        ylabel("waiting time")
        legend((line1, line2), ("1", "2"))
        #plt.show()
        plt.savefig(output_dir+'waiting_times_and_final_destination_times.png')


        print(' # PASSENGERS stat')
        print('   number of all passengers', len(self.passengers))
        print('   number of served passengers', served)
        print('   number of unserved passengers', len(self.passengers)-served, not_served_passangers)
        print('   number in simulation', in_simulation)
        print('   number of passenger or their destinations', num_on_planned_destination)
        print('   total waiting time', total_waiting_time)
        print('   total time on board', total_time_on_board)
        print('   total time on board from vehicle events (for double check)', total_time_on_board_vehicle_event)
        print('   total distance on board from vehicle events (for double check)', total_distance_on_board_vehicle_event)
        print('   total_time', total_time)
        print('   AVG waiting time', total_waiting_time/float(in_simulation))
        print('   AVG time on board', total_time_on_board/float(served))
        print('   AVG time on board from vehicle events (for double check)', total_time_on_board_vehicle_event/float(served))
        print('   AVG distance on board from vehicle events', total_distance_on_board_vehicle_event/float(served))
        print('   AVG total_time', total_time/float(in_simulation))
        print('   MAX total waiting time', max_waiting_time)
        print('   MAX total time on board', max_time_on_board)
        print('   MAX total_time', max_time)
        print('   MAX time from vehicle events', max_time_vehicle_event)
        print('   MAX distance from vehicle events', max_distance_vehicle_event)
        if output_dir is not None:
            file_o.write('# PASSENGERS stat;'+'\n')
            file_o.write('number of all passengers;'+str(len(self.passengers))+'\n')
            file_o.write('number of served passengers;'+str(served)+'\n')
            file_o.write('number of unserved passengers;'+str(len(self.passengers)-served)+'\n')
            file_o.write('number in simulation;'+str(in_simulation)+'\n')
            file_o.write('number of passenger or their destinations;'+str(num_on_planned_destination)+'\n')
            file_o.write('total waiting time;'+str(total_waiting_time)+'\n')
            file_o.write('total time on board;'+str(total_time_on_board)+'\n')
            file_o.write('total time on board from vehicle events (for double check);'+str(total_time_on_board_vehicle_event)+'\n')
            file_o.write('total distance on board from vehicle events;'+str(total_distance_on_board_vehicle_event)+'\n')
            file_o.write('total_time;'+str(total_time)+'\n')
            file_o.write('AVG total waiting time;'+str(total_waiting_time/float(in_simulation))+'\n')
            file_o.write('AVG total time on board;'+str(total_time_on_board/float(served))+'\n')
            file_o.write('AVG time on board from vehicle events (for double check);'+str(total_time_on_board_vehicle_event/float(served))+'\n')
            file_o.write('AVG distance on board from vehicle events;'+str(total_distance_on_board_vehicle_event/float(served))+'\n')
            file_o.write('AVG total_time;'+str(total_time/float(in_simulation))+'\n')
            file_o.write('MAX total waiting time;'+str(max_waiting_time)+'\n')
            file_o.write('MAX total time on board;'+str(max_time_on_board)+'\n')
            file_o.write('MAX total_time;'+str(max_time)+'\n')
            file_o.write('MAX time from vehicle events;'+str(max_time_vehicle_event)+'\n')
            file_o.write('MAX distance from vehicle events;'+str(max_distance_vehicle_event)+'\n')

        total_served = 0
        total_occupied_distance = 0
        total_empty_distance = 0
        total_occupied_travel_time = 0
        total_empty_travel_time = 0
        total_occupied_trips = 0
        total_empty_trips = 0
        number_passengers_on_board_at_end = 0
        number_of_empty_vehicles = 0

        for i in range(0, len(self.vehicles)):
            total_served += self.vehicles[i].total_served_passengers
            total_occupied_distance += self.vehicles[i].total_distance_occupied
            total_empty_distance += self.vehicles[i].total_distance_empty
            total_occupied_travel_time += self.vehicles[i].total_travel_time_occupied
            total_empty_travel_time += self.vehicles[i].total_travel_time_empty
            total_occupied_trips += self.vehicles[i].number_of_occupied_trips
            total_empty_trips += self.vehicles[i].number_of_empty_trips
            number_passengers_on_board_at_end += self.vehicles[i].empty_space()-self.vehicles[i].capacity
            if self.vehicles[i].empty_space() == self.vehicles[i].capacity:
                number_of_empty_vehicles += 1
        print(' # VEHICLES stat')
        print('   number of passengers still on vehicles',number_passengers_on_board_at_end)
        print('   number of empty vehicles at end', number_of_empty_vehicles)
        print('   number of served passengers', total_served)
        print('   occuped total distance', total_occupied_distance)
        print('   empty total distance', total_empty_distance)
        print('   occuped total tt', total_occupied_travel_time)
        print('   empty total tt', total_empty_travel_time)
        print('   number of occupied trips', total_occupied_trips)
        print('   number of empty trips', total_empty_trips)
        if output_dir is not None:
            file_o.write('# VEHICLES stat;'+'\n')
            file_o.write('number of passengers still on vehicles;'+str(number_passengers_on_board_at_end)+'\n')
            file_o.write('number of empty vehicles at end;'+str(number_of_empty_vehicles)+'\n')
            file_o.write('number of served passengers;'+str(total_served)+'\n')
            file_o.write('occuped total distance;'+str(total_occupied_distance)+'\n')
            file_o.write('empty total distance;'+str(total_empty_distance)+'\n')
            file_o.write('occuped total travel time;'+str(total_occupied_travel_time)+'\n')
            file_o.write('empty total travel time;'+str(total_empty_travel_time)+'\n')
            file_o.write('number of occupied trips;'+str(total_occupied_trips)+'\n')
            file_o.write('number of empty trips;'+str(total_empty_trips)+'\n')

        n_passengers_FIFO = 0
        n_passengers_dict = 0
        passengers_served = 0
        available_empty_vehicles = 0
        passengers_served_vehicles = 0
        total_occupied_distance = 0
        total_empty_distance = 0
        total_occupied_travel_time = 0
        total_empty_travel_time = 0

        for i in range(0, len(self.managers)):
            if hasattr(self.managers[i], 'passengers'):
                n_passengers_FIFO += self.managers[i].passengers.length
                n_passengers_dict += len(self.managers[i].passengers_dict)
                passengers_served += self.managers[i].passengers_served
                available_empty_vehicles += len(self.managers[i].available_empty_vehicles)

            if hasattr(self.managers[i], 'vehicles'):
                for j in range(0, len(self.managers[i].vehicles)):
                    #print(i,j,len(self.managers[i].vehicles),self.managers[i],self.managers[i].vehicles)
                    passengers_served_vehicles += self.managers[i].vehicles[j].total_served_passengers
                    total_occupied_distance += self.managers[i].vehicles[j].total_distance_occupied
                    total_empty_distance += self.managers[i].vehicles[j].total_distance_empty
                    total_occupied_travel_time += self.managers[i].vehicles[j].total_travel_time_occupied
                    total_empty_travel_time += self.managers[i].vehicles[j].total_travel_time_empty

        print('### FLEET managers AVG stat')
        print('   number of passengers still registered in queue FIRST FIFO check', n_passengers_FIFO)
        print('   number of passengers still registered in queue SECOND dict check', n_passengers_dict)
        print('   number of passengers served by managers', passengers_served)
        print('   number of passengers served by vehicles under managers', passengers_served_vehicles)
        print('   number of available empty vehicles', available_empty_vehicles)
        if output_dir is not None:
            file_o.write('### FLEET manager AVG stat;'+'\n')
            file_o.write('number of passengers still registered in queue FIRST FIFO check;'+str(n_passengers_FIFO)+'\n')
            file_o.write('number of passengers still registered in queue SECOND dict check;'+str(n_passengers_dict)+'\n')
            file_o.write('number of passengers served by managers;'+str(passengers_served)+'\n')
            file_o.write('number of passengers served by vehicles under manager;'+str(passengers_served_vehicles)+'\n')
            file_o.write('number of available empty vehicles;'+str(available_empty_vehicles)+'\n')
            file_o.write('occuped total distance;'+str(total_occupied_distance)+'\n')
            file_o.write('empty total distance;'+str(total_empty_distance)+'\n')
            file_o.write('occuped total travel time;'+str(total_occupied_travel_time)+'\n')
            file_o.write('empty total travel time;'+str(total_empty_travel_time)+'\n')

        for i in range(0, len(self.managers)):
            n_passengers_FIFO = 0
            n_passengers_dict = 0
            passengers_served = 0
            passengers_served_vehicles = 0
            available_empty_vehicles = 0
            total_occupied_distance = 0
            total_empty_distance = 0
            total_occupied_travel_time = 0
            total_empty_travel_time = 0
            first_served_passenger_boarding_time = None
            last_served_passenger_alighting_time = None
            number_of_empty_trips_only_until_last_served = 0
            number_of_occupied_trips_only_until_last_served = 0
            number_of_empty_trips = 0
            number_of_occupied_trips = 0

            self.first_served_passenger_boarding_time = None
            self.last_served_passenger_alighting_time = 0
            if hasattr(self.managers[i], 'passengers'):
                n_passengers_FIFO += self.managers[i].passengers.length
                n_passengers_dict += len(self.managers[i].passengers_dict)
                passengers_served += self.managers[i].passengers_served
                available_empty_vehicles += len(self.managers[i].available_empty_vehicles)
                print(' # FLEET manager', self.managers[i].id, 'stat')
                print('   number of passengers still registered in queue FIRST FIFO check', self.managers[i].passengers.length)
                print('   number of passengers still registered in queue SECOND dict check', len(self.managers[i].passengers_dict))
                print('   number of passengers served by managers', self.managers[i].passengers_served)
                print('   number of available empty vehicles', len(self.managers[i].available_empty_vehicles))

            if hasattr(self.managers[i], 'vehicles'):
                for j in range(0, len(self.managers[i].vehicles)):
                        total_served += self.managers[i].vehicles[j].total_served_passengers
                        passengers_served_vehicles += self.managers[i].vehicles[j].total_served_passengers
                        total_occupied_distance += self.managers[i].vehicles[j].total_distance_occupied
                        total_empty_distance += self.managers[i].vehicles[j].total_distance_empty
                        total_occupied_travel_time += self.managers[i].vehicles[j].total_travel_time_occupied
                        total_empty_travel_time += self.managers[i].vehicles[j].total_travel_time_empty
                        number_of_empty_trips_only_until_last_served += self.managers[i].vehicles[j].number_of_empty_trips_only_until_last_served
                        number_of_occupied_trips_only_until_last_served += self.managers[i].vehicles[j].number_of_occupied_trips_only_until_last_served
                        number_of_empty_trips += self.managers[i].vehicles[j].number_of_empty_trips
                        number_of_occupied_trips += self.managers[i].vehicles[j].number_of_occupied_trips
                        if self.managers[i].vehicles[j].first_served_passenger_boarding_time is not None and (
                                first_served_passenger_boarding_time is None or first_served_passenger_boarding_time >
                                self.managers[i].vehicles[j].first_served_passenger_boarding_time):
                            first_served_passenger_boarding_time = self.managers[i].vehicles[j].first_served_passenger_boarding_time
                        if self.managers[i].vehicles[j].last_served_passenger_alighting_time is not None and (
                                last_served_passenger_alighting_time is None or last_served_passenger_alighting_time <
                                self.managers[i].vehicles[j].last_served_passenger_alighting_time):
                            last_served_passenger_alighting_time = self.managers[i].vehicles[j].last_served_passenger_alighting_time

            #print('   occuped total distance', total_occupied_distance)
            #print('   empty total distance', total_empty_distance)
            if output_dir is not None:
                    file_o.write('# FLEET manager stat '+str(self.managers[i].id)+';'+str(self.managers[i].type)+'\n')
                    file_o.write('number of passengers still registered in queue FIRST FIFO check;'+str(n_passengers_FIFO)+'\n')
                    file_o.write('number of passengers still registered in queue SECOND dict check;'+str(n_passengers_dict)+'\n')
                    file_o.write('number of passengers served by managers;'+str(passengers_served)+'\n')
                    file_o.write('number of passengers served by vehicles under manager;'+str(passengers_served_vehicles)+'\n')
                    if hasattr(self.managers[i], 'vehicles'):
                        file_o.write('number of registered vehicles;'+str(len(self.managers[i].vehicles))+'\n')
                    elif hasattr(self.managers[i], 'vehicle'):
                        file_o.write('number of registered vehicles;1'+'\n')
                    file_o.write('number of available empty vehicles;'+str(available_empty_vehicles)+'\n')
                    file_o.write('occuped total distance;'+str(total_occupied_distance)+'\n')
                    file_o.write('empty total distance;'+str(total_empty_distance)+'\n')
                    file_o.write('occuped total travel time;'+str(total_occupied_travel_time)+'\n')
                    file_o.write('empty total travel time;'+str(total_empty_travel_time)+'\n')
                    file_o.write('time of the first boarded passenger;'+str(first_served_passenger_boarding_time)+'\n')
                    file_o.write('time of the last served passenger;'+str(last_served_passenger_alighting_time)+'\n')
                    file_o.write('number_of_empty_trips;'+str(number_of_empty_trips)+'\n')
                    file_o.write('number_of_occupied_trips;'+str(number_of_occupied_trips)+'\n')
                    file_o.write('number_of_empty_trips_only_until_last_served;'+str(number_of_empty_trips_only_until_last_served)+'\n')
                    file_o.write('number_of_occupied_trips_only_until_last_served;'+str(number_of_occupied_trips_only_until_last_served)+'\n')

        n_passengers_FIFO = 0
        n_passengers_dict = 0
        n_passengers_count = 0
        n_of_vehicles_on_locations_FIFO = 0
        n_of_vehicles_on_locations_dict = 0
        n_of_vehicles_on_locations = 0
        for i in range(0,len(self.locations)):
            n_passengers_FIFO += self.locations[i].passangers.length
            n_passengers_dict += len(self.locations[i].passangers_dict)
            n_passengers_count += self.locations[i].total_number_of_passangers
            n_of_vehicles_on_locations += self.locations[i].total_number_of_vehicles
            n_of_vehicles_on_locations_dict += len(self.locations[i].vehicles_dict)
            n_of_vehicles_on_locations_FIFO += self.locations[i].vehicles.length
        print(' # Locations stat')
        print('   number of passengers still registered on stations FIRST FIFO check', n_passengers_FIFO)
        print('   number of passengers still registered on stations SECOND dict check', n_passengers_dict)
        print('   number of passengers still registered on stations THIRD count check', n_passengers_count)
        print('   number of vehicles registered on stations FIRST FIFO check', n_of_vehicles_on_locations_FIFO)
        print('   number of vehicles registered on stations SECOND dict check', n_of_vehicles_on_locations_dict)
        print('   number of vehicles registered on stations THIRD count check', n_of_vehicles_on_locations)
        if output_dir is not None:
            file_o.write('# Locations stat;'+'\n')
            file_o.write('number of passengers still registered on stations FIRST FIFO check;'+str(n_passengers_FIFO)+'\n')
            file_o.write('number of passengers still registered on stations SECOND dict check;'+str(n_passengers_dict)+'\n')
            file_o.write('number of passengers still registered on stations THIRD count check;'+str(n_passengers_count)+'\n')
            file_o.write('number of vehicles registered on stations FIRST FIFO check;'+str(n_of_vehicles_on_locations_FIFO)+'\n')
            file_o.write('number of vehicles registered on stations SECOND dict check;'+str(n_of_vehicles_on_locations_dict)+'\n')
            file_o.write('number of vehicles registered on stations THIRD count check;'+str(n_of_vehicles_on_locations)+'\n')

        print('####################')

        if output_dir is not None:
            file_o.close()

        if print_individual_trips_stat:
            self.export_individual_trips_stat(output_dir)



class CaseStudyDistanceMatrix(CaseStudy):

    def __init__(self, distance_matrix: list = None, travel_time_matrix: list = None):
        super(CaseStudyDistanceMatrix, self).__init__()
        self.distance_matrix = distance_matrix
        self.travel_time_matrix = travel_time_matrix

    def load_distance_matrix(self, locations: list, distance_matrix: list, travel_time_matrix: list = None):
        for i in range(0, len(locations)):
            self.add_location(locations[i])
        self.distance_matrix = distance_matrix
        self.travel_time_matrix = travel_time_matrix

    def get_distance(self, manager, vehicle: Vehicle, org: Location, des: Location):
        if manager is None:
            if self.distance_matrix is None:
                raise Exception('ERROR: distance matrix is not defined')
            return self.distance_matrix[self.location_id_to_index[org.id]][self.location_id_to_index[des.id]]
        else:
            manager.get_distance()

    def get_travel_time(self, manager, vehicle: Vehicle, org: Location, des: Location):
        if manager is None:
            if self.travel_time_matrix is None:
                raise Exception('ERROR: distance matrix is not defined')
            return self.travel_time_matrix[self.location_id_to_index[org.id]][self.location_id_to_index[des.id]]
        else:
            manager.get_travel_time()
