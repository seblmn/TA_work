import matplotlib
matplotlib.use('Agg')

import pandas as pd
import psycopg2
import sys
import os
import csv
from imobilitylab.simulator.event_based.objects.location import Location_with_passive_vehicles
from imobilitylab.simulator.event_based.objects.passenger import Passenger
from imobilitylab.simulator.event_based.micromobility.objects import MicromobilityFleetManager, CaseStudy_micromobility, ScooterVehicle
from imobilitylab.simulator.event_based.core.simulator import Simulator, TimeLine_with_TimeBins
from imobilitylab.simulator.event_based.micromobility.events import PassengerRequestEvent, PickupEvent, DropoffEvent, RebalanceDropoffEvent



def load_events_to_df():
    """Load scooter events from PostgreSQL."""
    db_password = os.getenv("DB_PASSWORD")
    conn_info = {
        'host': '130.237.60.131',
        'port': 3221,
        'dbname': 'itsdev',
        'user': 'sebastien',
        'password': db_password
    }

    sql = """
    SELECT provider_device_id, event_type_id, event_time,
           ST_X(ST_Centroid(the_geom)) AS lon,
           ST_Y(ST_Centroid(the_geom)) AS lat
    FROM e_scooters.events_stockholm
    WHERE event_time >= '2022-09-10 07:00:00' AND event_time < '2022-09-10 10:00:00'
            AND event_type_id IN (1,2,7)
    ORDER BY provider_device_id ASC, event_time ASC, event_type_id ASC
    """

    conn = psycopg2.connect(**conn_info)
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()

    return df


def get_od_matrix_location_ids(manager) -> set:
    """Collect all location IDs that are usable in the loaded OD matrix."""
    valid_location_ids = set()
    for from_id, destinations in manager.distance_tt_matrix.items():
        valid_location_ids.add(from_id)
        for to_id in destinations.keys():
            valid_location_ids.add(to_id)
    return valid_location_ids


def load_location_points(location_file: str, allowed_location_ids: set):
    """Load location points filtered to IDs present in the OD matrix."""
    location_points = []

    with open(location_file) as f:
        f.readline()  # skip header
        for line in f:
            parts = line.strip('\n\r').split(';')
            location_id = int(parts[0])
            if location_id not in allowed_location_ids:
                continue
            location_lon = float(parts[4])
            location_lat = float(parts[5])
            location_points.append((location_id, location_lon, location_lat))

    return location_points


def nearest_location(location_points, lon: float, lat: float):
    """Find nearest OD-matrix location by Euclidean distance."""
    nearest_id = None
    nearest_distance = float('inf')

    for location_id, location_lon, location_lat in location_points:
        distance = ((location_lon - lon) ** 2 + (location_lat - lat) ** 2) ** 0.5
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_id = location_id

    return nearest_id


def add_location_id_column(df: pd.DataFrame, location_points):
    """Add location_id based on nearest location restricted to the OD matrix."""
    location_ids = []
    for _, row in df.iterrows():
        location_ids.append(nearest_location(location_points, float(row['lon']), float(row['lat'])))
    df = df.copy()
    df['location_id'] = location_ids
    return df


def load_locations(case_study, location_file):
    """Load locations from CSV file."""
    print('Loading locations...')
    with open(location_file) as f:
        f.readline()  # skip header
        count = 0
        for line in f:
            parts = line.strip('\n\r').split(';')
            location_id = int(parts[0])
            location_name = parts[2]
            location = Location_with_passive_vehicles(location_id, location_name)
            case_study.add_location(location)
            count += 1
    print(f'Locations loaded: {count}')


def load_distance_matrix(manager, distance_matrix_folder):
    """Load distance/TT matrix from CSV files."""
    print('Loading distance/TT matrix...')
    manager.distance_tt_matrix = {}
    
    for filename in os.listdir(distance_matrix_folder):
        filepath = os.path.join(distance_matrix_folder, filename)
        if os.path.isfile(filepath) and filename.endswith('.csv'):
            with open(filepath) as f:
                f.readline()  # skip header
                for line in f:
                    parts = line.strip('\n\r').split(';')
                    from_id, to_id, distance, travel_time = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                    if from_id not in manager.distance_tt_matrix:
                        manager.distance_tt_matrix[from_id] = {}
                    manager.distance_tt_matrix[from_id][to_id] = (distance, travel_time)
    
    print('Distance/TT matrix loaded')


def get_or_create_scooter(case_study, manager, scooter_id, default_location):
    if scooter_id not in case_study.vehicle_id_to_index:
        vehicle = ScooterVehicle(scooter_id, default_location, 1, manager)
        case_study.add_vehicle(vehicle)
    return case_study.vehicles[case_study.vehicle_id_to_index[scooter_id]]


def add_or_move_scooter_from_sql_row(case_study, manager, row):
    """Ensure a scooter exists and is located at row.location_id."""
    location_id = int(row['location_id'])
    if location_id not in case_study.location_id_to_index:
        return
    location_obj = case_study.locations[case_study.location_id_to_index[location_id]]
    scooter_id = row['provider_device_id']
    scooter = get_or_create_scooter(case_study, manager, scooter_id, location_obj)
    scooter.location = location_obj


def schedule_rebalance_dropoff_events(case_study, manager, df, reference_time_unix: int):
    """Schedule rebalance drop-off events (event_type_id=7)."""
    rebalances = df[df['event_type_id'] == 7].sort_values('event_time')
    count = 0

    for _, row in rebalances.iterrows():
        location_id = int(row['location_id'])
        if location_id not in case_study.location_id_to_index:
            continue

        location_obj = case_study.locations[case_study.location_id_to_index[location_id]]
        scooter_id = row['provider_device_id']
        scooter = get_or_create_scooter(case_study, manager, scooter_id, location_obj)

        event_time_absolute = int(row['event_time'].timestamp())
        event_time_rel = (event_time_absolute - reference_time_unix) + 20
        if event_time_rel < 0:
            event_time_rel = 0

        case_study.simulator.add_event(RebalanceDropoffEvent(event_time_rel, scooter, location_obj))
        count += 1

    return count


def build_trips_from_sql(case_study, manager, df, reference_time_unix: int):
    """Create passenger request + pickup + dropoff events from all valid SQL pairs."""
    grouped = df.groupby('provider_device_id')
    traces = []
    passenger_id_counter = 1

    for scooter_id, events in grouped:
        events = events.sort_values('event_time').reset_index(drop=True)
        i = 0
        while i < len(events) - 1:
            pickup = events.iloc[i]
            dropoff = events.iloc[i + 1]
            if int(pickup['event_type_id']) != 1 or int(dropoff['event_type_id']) != 2:
                i += 1
                continue

            pickup_location_id = int(pickup['location_id'])
            dropoff_location_id = int(dropoff['location_id'])
            if pickup_location_id not in case_study.location_id_to_index or dropoff_location_id not in case_study.location_id_to_index:
                i += 2
                continue

            pickup_location = case_study.locations[case_study.location_id_to_index[pickup_location_id]]
            dropoff_location = case_study.locations[case_study.location_id_to_index[dropoff_location_id]]

            if not manager.is_trip_to_destination_from_location_possible(pickup_location, dropoff_location):
                i += 2
                continue

            pickup_time_absolute = int(pickup['event_time'].timestamp())
            dropoff_time_absolute = int(dropoff['event_time'].timestamp())
            pickup_time_rel = (pickup_time_absolute - reference_time_unix) + 20
            request_time_rel = pickup_time_rel - 1
            if request_time_rel < 0:
                request_time_rel = 0

            scooter = get_or_create_scooter(case_study, manager, scooter_id, pickup_location)
            scooter.location = pickup_location

            planned_distance, planned_tt = manager.get_distance_and_travel_time_between_passenger_origin_destination(
                pickup_location,
                dropoff_location
            )

            if planned_tt is not None and planned_tt > 0:
                dropoff_time_rel = pickup_time_rel + planned_tt
            else:
                dropoff_time_rel = (dropoff_time_absolute - reference_time_unix) + 20
                if dropoff_time_rel <= pickup_time_rel:
                    dropoff_time_rel = pickup_time_rel + 1

            passenger = Passenger(passenger_id_counter, request_time_rel, pickup_location)
            case_study.add_passenger(passenger)
            passenger_id_counter += 1

            case_study.simulator.add_event(PassengerRequestEvent(request_time_rel, passenger, pickup_location))
            case_study.simulator.add_event(PickupEvent(pickup_time_rel, scooter, passenger, pickup_location))
            case_study.simulator.add_event(DropoffEvent(dropoff_time_rel, scooter, passenger, dropoff_location))

            traces.append({
                'passenger_id': passenger.id,
                'scooter_id': scooter_id,
                'origin_location_id': pickup_location.id,
                'destination_location_id': dropoff_location.id,
                'request_time_rel': request_time_rel,
                'pickup_time_rel': pickup_time_rel,
                'dropoff_time_rel': dropoff_time_rel,
                'pickup_time_sql_unix': pickup_time_absolute,
                'dropoff_time_sql_unix': dropoff_time_absolute,
                'planned_distance': planned_distance,
                'planned_travel_time': planned_tt
            })
            i += 2

    return traces


def export_trip_lifecycle(output_dir: str, traces: list, case_study):
    """Export documented lifecycle steps for all simulated SQL trips."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, 'trip_lifecycle_steps.csv')
    rows = []
    passengers_by_id = {p.id: p for p in case_study.passengers}

    for trace in traces:
        passenger_id = trace['passenger_id']
        if passenger_id not in passengers_by_id:
            continue
        passenger = passengers_by_id[passenger_id]

        observed_pickup = passenger.borded_times[0] if len(passenger.borded_times) > 0 else None
        observed_dropoff = passenger.alighting_times[0] if len(passenger.alighting_times) > 0 else None
        observed_trip_time = None
        if observed_pickup is not None and observed_dropoff is not None:
            observed_trip_time = observed_dropoff - observed_pickup

        rows.extend([
            {
                'step': 'passenger_request',
                'passenger_id': trace['passenger_id'],
                'scooter_id': trace['scooter_id'],
                'location_id': trace['origin_location_id'],
                'time_rel': trace['request_time_rel'],
                'time_sql_unix': trace['pickup_time_sql_unix'],
                'planned_distance': trace['planned_distance'],
                'planned_travel_time': trace['planned_travel_time']
            },
            {
                'step': 'pickup',
                'passenger_id': trace['passenger_id'],
                'scooter_id': trace['scooter_id'],
                'location_id': trace['origin_location_id'],
                'time_rel': observed_pickup if observed_pickup is not None else trace['pickup_time_rel'],
                'time_sql_unix': trace['pickup_time_sql_unix'],
                'planned_distance': trace['planned_distance'],
                'planned_travel_time': trace['planned_travel_time']
            },
            {
                'step': 'dropoff',
                'passenger_id': trace['passenger_id'],
                'scooter_id': trace['scooter_id'],
                'location_id': trace['destination_location_id'],
                'time_rel': observed_dropoff if observed_dropoff is not None else trace['dropoff_time_rel'],
                'time_sql_unix': trace['dropoff_time_sql_unix'],
                'planned_distance': trace['planned_distance'],
                'planned_travel_time': trace['planned_travel_time']
            },
            {
                'step': 'trip',
                'passenger_id': trace['passenger_id'],
                'scooter_id': trace['scooter_id'],
                'location_id': f"{trace['origin_location_id']}->{trace['destination_location_id']}",
                'time_rel': observed_trip_time,
                'time_sql_unix': trace['dropoff_time_sql_unix'] - trace['pickup_time_sql_unix'],
                'planned_distance': trace['planned_distance'],
                'planned_travel_time': trace['planned_travel_time']
            }
        ])

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['step', 'passenger_id', 'scooter_id', 'location_id', 'time_rel', 'time_sql_unix', 'planned_distance', 'planned_travel_time']
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f'Trip lifecycle exported: {filepath}')


def export_individual_outputs_for_micromobility(output_dir: str, case_study):
    """Refresh individual_* outputs for this micromobility use case."""
    os.makedirs(output_dir, exist_ok=True)

    passenger_path = os.path.join(output_dir, 'individual_passenger_trips.csv')
    with open(passenger_path, 'w') as f:
        f.write(
            'passanger_id;passanger_arrival_time;passanger_waiting_time;final_trip;'
            'passanger_trip_id;start_time;end_time;travel_time;distance;departure_key;'
            'segments_on_board;avg_on_board;avg_occupancy_rate;travel_time_from_departure;'
            'start_location;end_location;vehicle_trip_id,line_id,direction_id,vehicle_id;manager_id\n'
        )

    vehicle_path = os.path.join(output_dir, 'individual_vehicle_trips.csv')
    with open(vehicle_path, 'w') as f:
        f.write(
            'vehicle_id;manager_id;departure_id;departure_time;segment_order_index;'
            'in_simulation_start_time;in_simulation_end_time;in_simulation_travel_time;'
            'in_simulation_distance;in_simulation_on_board;sharing_rate;start_location;'
            'end_location;planned_start_time;planned_end_time;planned_travel_time;planned_distance\n'
        )
        for vehicle in case_study.vehicles:
            for trip in vehicle.trip_collection:
                f.write(trip.to_csv_str() + '\n')

    departures_path = os.path.join(output_dir, 'individual_departures.csv')
    with open(departures_path, 'w') as f:
        f.write(
            'departure_id;manager_id;vehicle_id;departure_time;end_time;start_location;start_location_index;'
            'total_time;n_segments;served_passengers;total_empty_trips;total_occupied_trips;'
            'avg_occupancy;std_occupancy;max_occupancy;avg_occupancy_rate;std_occupancy_rate;'
            'max_occupancy_rate;;individual_segment_trips_from_here(-1 is for not applicable)\n'
        )

    print(f'Individual outputs refreshed: {passenger_path}, {vehicle_path}, {departures_path}')


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: mmm.py <location_file> <distance_matrix_folder> <output_dir>')
        sys.exit(1)

    location_file = sys.argv[1]
    distance_matrix_folder = sys.argv[2]
    output_dir = sys.argv[3]
    if not output_dir.endswith('/'):
        output_dir += '/'

    case_study = CaseStudy_micromobility()
    case_study.add_simulator(Simulator(None, TimeLine_with_TimeBins(300)))
    case_study.simulator.config.detailed_terminal_print_of_simulation = True
    manager = MicromobilityFleetManager(case_study)

    print('=== LOADING DATA ===')
    load_locations(case_study, location_file)
    load_distance_matrix(manager, distance_matrix_folder)
    od_location_ids = get_od_matrix_location_ids(manager)
    od_location_points = load_location_points(location_file, od_location_ids)
    print(f'OD matrix locations available for matching: {len(od_location_points)}')
    if len(od_location_points) == 0:
        print('No OD-matrix locations available for SQL matching.')
        sys.exit(1)

    # Load SQL events and map each row to nearest simulation location
    df = load_events_to_df()
    df = add_location_id_column(df, od_location_points)
    print(f'Events loaded: {len(df)}')

    if len(df) == 0:
        print('No SQL events loaded.')
        sys.exit(1)
    reference_time_unix = int(df['event_time'].min().timestamp())

    rebalance_count = schedule_rebalance_dropoff_events(case_study, manager, df, reference_time_unix)
    print(f'Scheduled rebalance dropoff events: {rebalance_count}')

    # Build trips from all valid SQL pickup->dropoff pairs
    trip_traces = build_trips_from_sql(case_study, manager, df, reference_time_unix)
    if len(trip_traces) == 0:
        print('No valid pickup/dropoff pair found in SQL data.')
        sys.exit(1)
    print(f'Scheduled SQL trips: {len(trip_traces)}')

    print('INPUT DATA LOADED')
    print('Simulation starts')
    case_study.inicialize_passengers_for_simulation = lambda: None
    case_study.start_simulation()
    export_individual_outputs_for_micromobility(output_dir, case_study)
    case_study.make_statistic(output_dir, None, False)
    export_trip_lifecycle(output_dir, trip_traces, case_study)
    print('End of Simulation')
    sys.exit(0)
