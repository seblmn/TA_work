from imobilitylab.simulator.event_based.event.transport import PassengerArrivalEvent
from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.objects.location import Location


class PassengerArrivalEventDemandResponsive(PassengerArrivalEvent):

    def __init__(self, execution_time: int, passenger: Passenger, location: Location):
        """Stop Object Definition: Location (Lat/Lon) type, and first use, last use"""
        super(PassengerArrivalEventDemandResponsive, self).__init__(execution_time, passenger, location)

    def execute(self):
        super(PassengerArrivalEventDemandResponsive, self).execute()
        self.passenger.manager.register_passenger(self.passenger)
