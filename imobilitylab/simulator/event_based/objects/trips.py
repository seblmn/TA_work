
from imobilitylab.simulator.event_based.supporting_libraries.priority_front import PriorityFront
from imobilitylab.simulator.event_based.objects.location import Location

class TripBasic(object):

    def __init__(self, start_location: Location, end_location: Location, distance: int = None, start_time: int = None,
                 end_time: int = None, vehicle=None, manager=None):
        self.start_location = start_location
        self.end_location = end_location
        self.start_time = start_time
        self.end_time = end_time
        self.distance = distance
        self.vehicle = vehicle
        self.manager = manager


class TripVehicle(TripBasic):

    def __init__(self, start_location: Location, end_location: Location,distance: int, on_board: int, start_time: int,
                 end_time: int, vehicle=None, manager=None):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(TripVehicle, self).__init__(start_location, end_location, distance,start_time,
                                          end_time,vehicle,manager)
        self.pasengers_on_board = on_board

    def to_csv_str(self):
        return str(self.vehicle.id)+';'+str(self.manager.id)+';None;None;None;'+str(self.start_time)+';'+str(self.end_time)+';'+str(self.end_time-self.start_time)+';' \
               +str(self.distance)+';'+str(self.pasengers_on_board)+';' \
               +str(round(self.pasengers_on_board/float(self.vehicle.capacity), 4))+';'+str(self.start_location.id)+';' \
               +str(self.end_location.id)+';None;None;None;None'


class TripPassanger(TripBasic):

    def __init__(self, passanger_trip_id: int, vehicle_trip_id:int, line_id: int, direction_id: int,
                 start_location: Location, end_location: Location, distance: int, on_board: int, start_time: int,
                 end_time: int, vehicle=None, manager=None):
        self.passanger_trip_id = passanger_trip_id
        self.vehicle_trip_id = vehicle_trip_id
        self.line_id = line_id
        self.direction_id = direction_id
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(TripPassanger, self).__init__(start_location, end_location, distance,
                                            start_time,end_time,vehicle,manager)

        if vehicle is not None:
            if vehicle.type == 'pt_vehicle':
                if vehicle.departure is not None:
                    self.departure_key = vehicle.departure.departure_id
                    self.segments_on_board, self.avg_on_board, self.avg_occupancy_rate, self.travel_time_from_departure = \
                        vehicle.departure.export_avg_occupancy_and_on_board_from_location_to_location(start_location,
                                                                                                      end_location)
                else:
                    self.departure_key = None
                    self.avg_on_board = None
                    self.segments_on_board = None
                    self.avg_occupancy_rate = None
                    self.travel_time_from_departure = None
            else:
                self.departure_key = None
                self.avg_on_board = on_board
                self.segments_on_board = 1
                self.avg_occupancy_rate = round(on_board/float(self.vehicle.capacity), 4)
                self.travel_time_from_departure = self.end_time-self.start_time
        else:
            self.departure_key = None
            self.avg_on_board = None
            self.segments_on_board = None
            self.avg_occupancy_rate = None
            self.travel_time_from_departure = None

    def to_csv_str(self):
        tt = None
        if self.start_time is not None and self.end_time is not None:
            tt = self.end_time-self.start_time
        str_t = str(self.passanger_trip_id)+';'+str(self.start_time)+';'+str(self.end_time)+';'+str(tt)+';' \
               +str(self.distance)+';'+str(self.departure_key)+';'+str(self.segments_on_board)+';'+str(self.avg_on_board)+';' \
               +str(self.avg_occupancy_rate)+';'+str(self.travel_time_from_departure)+';'+str(self.start_location.id)+';'+str(self.end_location.id)+';' \
                + str(self.vehicle_trip_id) + ';' + str(self.line_id) + ';' + str(self.direction_id)

        if self.vehicle is not None:
            str_t += ';' + str(self.vehicle.id)
        else:
            str_t += ';None'
        if self.manager is not None:
            str_t += ';' + str(self.manager.id)
        else:
            str_t += ';None'
        return str_t


class TripCollection(object):

    def __init__(self, journey_id: int, origin_location: Location = None, destination_location: Location = None):
        self.journey_id = journey_id
        self.origin_location = origin_location
        self.destination_location = destination_location
        self.executed_trips = []
        self.trips = PriorityFront(True)
        self.active_trip = None

    def move_active_trip_to_executed(self, trip:TripBasic):
        if self.active_trip == trip:
            self.executed_trips.append(self.active_trip)
            self.active_trip = None

    def register_trip(self, trip: TripBasic):
        #if trip.manager is not None:
        #    print('*****',trip.manager.departure_id)
        #if trip.vehicle is not None and trip.vehicle.id == 46949:
        #    print('adding trip:', trip.vehicle.id, trip.manager.departure_id, self.trips.num, trip.start_time)
        self.trips.AddItem(trip, trip.start_time)

    def get_next_trip(self):
        if self.active_trip is not None:
            raise Exception('Logic ERROR: There is active_trip, First it should be moved or labeled as executed')
        item = self.trips.RemoveItem()
        if item is not None:
            self.active_trip = item[0]
            return self.active_trip
        else:
            self.active_trip = None
            return None


class JourneyCollection(object):

    def __init__(self):
        self.executed_journeys = []
        self.journeys = PriorityFront(True)
        self.active_journey = None

    def register_journey(self, trip_collection: TripCollection):
        #print(trip_collection.trips.start.obj.start_time)
        self.journeys.AddItem(trip_collection, trip_collection.trips.start.obj.start_time)

    def get_next_journey(self):
        if self.active_journey is not None:
            self.executed_journeys.append(self.active_journey)
        item = self.journeys.RemoveItem()
        if item is not None:
            self.active_journey = item[0]
            return self.active_journey
        else:
            self.active_journey = None
            return None

    def get_next_trip(self):
        if self.active_journey is None or self.active_journey.trips.num <= 0:
            self.get_next_journey()
        if self.active_journey is not None:
            return self.active_journey.get_next_trip()
        else:
            return None


class ObservedPassangerTrip_in_simulation(object):

    def __init__(self):
        self.observed_start_time = None
        self.observed_end_time = None
        self.observed_start_location = None
        self.observed_end_location = None
        self.observed_start_location_index = None
        self.observed_end_location_index = None
        self.observed_trip_id = None
        self.observed_line_id = None
        self.observed_direction_id = None
        self.observed_distance = None
        self.observed_distance_complete = None
        self.observed_on_board = None
        self.observed_vehicle = None
        self.observed_manager = None
        self.observed_denied_boarding = 0

    def to_csv_str(self):
        str_t = str(self.observed_start_location.id)
        str_t += ';'+ str(self.observed_end_location.id)
        str_t += ';'+ str(self.observed_start_time)
        str_t += ';'+ str(self.observed_end_time)
        str_t += ';'+ str(self.observed_denied_boarding)
        str_t += ';'+ str(self.observed_trip_id)
        str_t += ';'+ str(self.observed_line_id)
        str_t += ';'+ str(self.observed_direction_id)
        str_t += ';'+ str(self.observed_distance)
        str_t += ';'+ str(self.observed_distance_complete)
        str_t += ';'+ str(self.observed_on_board)
        str_t += ';'+ str(self.observed_vehicle.id)
        str_t += ';'+ str(self.observed_manager.id)
        return str_t


class TripPassangerWithObservation(TripPassanger, ObservedPassangerTrip_in_simulation):

    def __init__(self, trip_id: int, vehicle_trip_id: int, line_id: int, direction_id: int, start_location: Location, end_location: Location, distance: int, on_board: int, start_time: int, end_time: int,
                 vehicle=None, manager=None):

        TripPassanger.__init__(self, trip_id, vehicle_trip_id, line_id, direction_id, start_location, end_location, distance, on_board, start_time, end_time,vehicle,manager)
        ObservedPassangerTrip_in_simulation.__init__(self)

    def to_csv_str(self):
        str_t = TripPassanger.to_csv_str(self)
        str_t += ';' + ObservedPassangerTrip_in_simulation.to_csv_str(self)
        return str_t
