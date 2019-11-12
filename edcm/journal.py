import logging
import json
from datetime import datetime
from os import environ, listdir
from os.path import join, isfile, getmtime

logger = logging.getLogger(__name__)


def get_latest_journal(player_journal_location=None):
    """Returns the full path of the latest (most recent) elite log file (journal) from specified path"""
    if not player_journal_location:
        player_journal_location = environ['USERPROFILE'] + "\\Saved Games\\Frontier Developments\\Elite Dangerous"

    list_of_logs = [join(player_journal_location, f) for f in listdir(player_journal_location) if
                    isfile(join(player_journal_location, f)) and f.startswith('Journal.')]
    if not list_of_logs:
        return None
    latest_log = max(list_of_logs, key=getmtime)
    return latest_log


def get_ship_status():
    """Returns a 'status' dict containing relevant game status information (state, fuel, ...)"""
    latest_log = get_latest_journal()
    ship = {
        'time': (datetime.now() - datetime.fromtimestamp(getmtime(latest_log))).seconds,
        'status': None,
        'type': None,
        'location': None,
        'star_class': None,
        'target': None,
        'cargo_count': None,
        'cargo_capacity': None,
        'fuel_capacity': None,
        'fuel_level': None,
        'fuel_percent': None,
        'is_scooping': False,
    }
    # Read log line by line and parse data
    with open(latest_log, encoding="utf-8") as f:
        for line in f:
            log = json.loads(line)

            # parse data
            try:
                # parse ship status
                log_event = log['event']

                if log_event == 'StartJump':
                    logger.debug("%s: ship['status'] = %s" % (json.dumps(log), ship['status']))
                    ship['status'] = str('starting_' + log['JumpType']).lower()

                elif log_event == 'SupercruiseEntry' or log_event == 'FSDJump':
                    logger.debug("%s: ship['status'] = %s" % (json.dumps(log), ship['status']))
                    ship['status'] = 'in_supercruise'

                elif log_event == 'SupercruiseExit' or log_event == 'DockingCancelled' or (
                        log_event == 'Music' and ship['status'] == 'in_undocking') or (
                        log_event == 'Location' and not log['Docked']):
                    logger.debug("%s: ship['status'] = %s" % (json.dumps(log), ship['status']))
                    ship['status'] = 'in_space'

                elif log_event == 'Undocked':
                    # ship['status'] = 'starting_undocking'
                    ship['status'] = 'in_space'
                    logger.debug("%s: ship['status'] = %s" % (json.dumps(log), ship['status']))

                elif log_event == 'DockingRequested':
                    logger.debug("%s: ship['status'] = %s" % (json.dumps(log), ship['status']))
                    ship['status'] = 'starting_docking'

                elif log_event == "Music":
                    if log['MusicTrack'] == "DockingComputer":
                        if ship['status'] == 'starting_undocking':
                            logger.debug("%s: ship['status'] = %s" % (json.dumps(log), ship['status']))
                            ship['status'] = 'in_undocking'
                        elif ship['status'] == 'starting_docking':
                            logger.debug("%s: ship['status'] = %s" % (json.dumps(log), ship['status']))
                            ship['status'] = 'in_docking'
                        else:
                            logger.debug("%s: ship['status'] = %s" % (json.dumps(log), ship['status']))
                            ship['status'] = 'docking'
                    elif log['MusicTrack'] == "NoTrack":
                        logger.debug("%s: ship['status'] = %s" % (json.dumps(log), ship['status']))
                        ship['status'] = 'in_space'
                    elif log['MusicTrack'] == "Starport":
                        logger.debug("%s: ship['status'] = %s" % (json.dumps(log), ship['status']))
                        ship['status'] = 'in_station'

                elif log_event == 'Docked':
                    logger.debug("%s: ship['status'] = %s" % (json.dumps(log), ship['status']))
                    ship['status'] = 'in_station'

                # parse ship type
                if log_event == 'LoadGame' or log_event == 'Loadout':
                    ship['type'] = log['Ship']

                if log_event == 'Loadout':
                    ship['cargo_capacity'] = log['CargoCapacity']

                # parse fuel
                if 'FuelLevel' in log and ship['type'] != 'TestBuggy':
                    ship['fuel_level'] = log['FuelLevel']
                if 'FuelCapacity' in log and ship['type'] != 'TestBuggy':
                    try:
                        ship['fuel_capacity'] = log['FuelCapacity']['Main']
                    except Exception as e:
                        ship['fuel_capacity'] = log['FuelCapacity']
                        logger.error(e)
                if log_event == 'FuelScoop' and 'Total' in log:
                    ship['fuel_level'] = log['Total']
                if ship['fuel_level'] and ship['fuel_capacity']:
                    ship['fuel_percent'] = round((ship['fuel_level'] / ship['fuel_capacity']) * 100)
                else:
                    ship['fuel_percent'] = 10

                # parse scoop
                if log_event == 'FuelScoop' and ship['time'] < 10 and ship['fuel_percent'] < 100:
                    ship['is_scooping'] = True
                else:
                    ship['is_scooping'] = False

                # parse location
                if (log_event == 'Location' or log_event == 'FSDJump') and 'StarSystem' in log:
                    ship['location'] = log['StarSystem']
                if 'StarClass' in log:
                    ship['star_class'] = log['StarClass']

                # parse target
                if log_event == 'FSDTarget':
                    if log['Name'] == ship['location']:
                        ship['target'] = None
                    else:
                        ship['target'] = log['Name']
                elif log_event == 'FSDJump':
                    if ship['location'] == ship['target']:
                        ship['target'] = None

                # parse cargo
                if log_event == 'Cargo':
                    if log['Vessel'] == 'Ship':
                        ship['cargo_count'] = log['Count']

            # exceptions
            except Exception as e:
                logging.exception("Exception occurred")
                print(e)
    return ship
