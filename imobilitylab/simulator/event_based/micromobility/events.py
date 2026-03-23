from imobilitylab.simulator.event_based.event.transport import VehicleEvent, PassengerEvent


class PassengerRequestEvent(PassengerEvent):
    """Passenger request event (instantaneous). Registers request presence in simulation timeline."""

    def __init__(self, time: int, passenger, location):
        super(PassengerRequestEvent, self).__init__(time, passenger, location)

    def execute(self):
        self.passenger.location = self.location
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

        if hasattr(self.vehicle, 'passengers') and self.passenger.id in self.vehicle.passengers:
            self.vehicle.unload_passenger(self.passenger)

        if hasattr(self.vehicle, 'manager') and origin_location is not None:
            dis, tt = self.vehicle.manager.get_distance_and_travel_time_between_passenger_origin_destination(
                origin_location,
                self.location
            )
            if dis is not None:
                self.passenger.total_distance_on_board_from_vehicleEvent += dis
            if tt is not None:
                self.passenger.total_travel_time_on_board_from_vehicleEvent += tt

        self.passenger.vehicle = None
        self.vehicle.last_served_passenger_alighting_time = self.execution_time
        self.passenger.in_simulation = True