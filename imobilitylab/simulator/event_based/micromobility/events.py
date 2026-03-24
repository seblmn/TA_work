from imobilitylab.simulator.event_based.event.transport import VehicleEvent, PassengerEvent


class PassengerRequestEvent(PassengerEvent):
    """Passenger request event (instantaneous). Registers request presence in simulation timeline."""

    def __init__(self, time: int, passenger, location):
        super(PassengerRequestEvent, self).__init__(time, passenger, location)

    def execute(self):
        self.passenger.location = self.location
        if len(self.passenger.arrival_times) == 0 or self.passenger.arrival_times[-1] != self.execution_time:
            self.passenger.register_arrival_time(self.execution_time)
        self.passenger.in_simulation = True
        self.passenger.served = False

class PickupEvent(VehicleEvent):
    """
    Scooter pickup event (instantaneous).
    Sets scooter location to pickup location and updates passenger state.
    """

    def __init__(self, time: int, vehicle, passenger, location):
        super(PickupEvent, self).__init__(time, vehicle)
        self.passenger = passenger
        self.location = location

    def execute(self):
        self.vehicle.location = self.location
        self.vehicle.in_use = True

        self.passenger.location = self.location
        if len(self.passenger.borded_times) == 0 or self.passenger.borded_times[-1] != self.execution_time:
            self.passenger.borded_times.append(self.execution_time)

        if self.vehicle.first_served_passenger_boarding_time is None:
            self.vehicle.first_served_passenger_boarding_time = self.execution_time
        if self.vehicle.total_boarded < self.vehicle.capacity:
            self.vehicle.total_boarded += 1

        self.passenger.vehicle = self.vehicle
        self.passenger.in_simulation = True
        self.passenger.served = True


class DropoffEvent(VehicleEvent):
    """
    Scooter dropoff event (instantaneous).
    Sets scooter location to dropoff location and updates passenger state.
    """

    def __init__(self, time: int, vehicle, passenger, location):
        super(DropoffEvent, self).__init__(time, vehicle)
        self.passenger = passenger
        self.location = location

    def execute(self):
        origin_location = self.passenger.location
        self.vehicle.location = self.location
        self.vehicle.in_use = False

        self.passenger.location = self.location
        if len(self.passenger.alighting_times) == 0 or self.passenger.alighting_times[-1] != self.execution_time:
            self.passenger.alighting_times.append(self.execution_time)

        dis = None
        if hasattr(self.vehicle, 'manager') and origin_location is not None:
            dis, _ = self.vehicle.manager.get_distance_and_travel_time_between_passenger_origin_destination(
                origin_location,
                self.location
            )
            if dis is not None:
                self.passenger.total_distance_on_board_from_vehicleEvent += dis

        if len(self.passenger.borded_times) > 0:
            tt = self.execution_time - self.passenger.borded_times[-1]
        else:
            tt = 0
        self.passenger.total_travel_time_on_board_from_vehicleEvent += tt

        if self.vehicle.total_boarded > 0:
            self.vehicle.total_boarded -= 1
        self.vehicle.total_served_passengers += 1
        self.vehicle.number_of_occupied_trips += 1
        if dis is not None:
            self.vehicle.total_distance_occupied += dis

        self.vehicle.total_travel_time_occupied += tt

        if origin_location is not None:
            self.vehicle.collect_trip(
                origin_location,
                self.location,
                dis,
                1,
                self.execution_time - tt,
                self.execution_time,
            )

        self.vehicle.number_of_empty_trips_only_until_last_served = self.vehicle.number_of_empty_trips
        self.vehicle.number_of_occupied_trips_only_until_last_served = self.vehicle.number_of_occupied_trips

        self.passenger.vehicle = None
        self.vehicle.last_served_passenger_alighting_time = self.execution_time
        self.passenger.in_simulation = True


class RebalanceDropoffEvent(VehicleEvent):
    """Scooter rebalancing drop-off (instantaneous, no passenger)."""

    def __init__(self, time: int, vehicle, location):
        super(RebalanceDropoffEvent, self).__init__(time, vehicle)
        self.location = location

    def execute(self):
        origin_location = self.vehicle.location

        dis = None
        tt = 0
        if origin_location is not None and origin_location.id != self.location.id and hasattr(self.vehicle, 'manager') and self.vehicle.manager is not None:
            dis, tt_from_matrix = self.vehicle.manager.get_distance_and_travel_time_between_passenger_origin_destination(
                origin_location,
                self.location,
            )
            if tt_from_matrix is not None:
                tt = tt_from_matrix

        if dis is not None:
            self.vehicle.total_distance_empty += dis
        self.vehicle.total_travel_time_empty += tt
        self.vehicle.number_of_empty_trips += 1

        if origin_location is not None:
            self.vehicle.collect_trip(
                origin_location,
                self.location,
                dis,
                0,
                self.execution_time - tt,
                self.execution_time,
            )

        self.vehicle.location = self.location
        self.vehicle.in_use = False