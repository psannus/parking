#!/usr/bin/env python3
#

import sys, argparse, logging, requests, json, time, datetime

def read_secrets(filename):
    logging.info("Trying to read secrets file.")

    secrets = {}

    try:
        with open(filename) as f:
            secrets = json.load(f)
    except:
        logging.info(f"Could not open/read file: {args.secrets}")
        sys.exit()

    return secrets
    # TODO: Add secrets schema validation


def login_request(secrets):
    login_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyDBmr_rIAtZ1hPlIJzzjQ15ky03GJTDw8Q"
    login_data = {"email": secrets["email"], "password": secrets["password"], "returnSecureToken": True}

    login_ans = requests.post(login_url, json = login_data).json()

    if "idToken" in login_ans:
        logging.info("Fetching login token succeeded.")
        return login_ans
    else:
        logging.info("Fetching login token failed. Exiting...")
        sys.exit()


def profile_request(secrets, token):
    profile_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getAccountInfo?key=AIzaSyDBmr_rIAtZ1hPlIJzzjQ15ky03GJTDw8Q"
    profile_data = {"idToken": token}

    profile_ans = requests.post(profile_url, json = profile_data).json()

    if "users" in profile_ans:
        logging.info("Fetching profile succeeded.")
        return profile_ans
    else:
        logging.info("Fetching profile failed. Exiting...")
        sys.exit()


def epoch_days_to_timestamp(epoch_day, week_day_only = False):
    return time.strftime("%A" if week_day_only else "%a, %d %b %Y", time.localtime(epoch_day * 86400))


def calculate_epoch_days(day_count, include_today):
    logging.debug("Calculating epoch days.")

    days_since_epoch = (datetime.datetime.now() - datetime.datetime(1970,1,1)).days

    start_day = days_since_epoch + (1 if include_today else 0)
    days_to_reserve = [d for d in range(start_day, days_since_epoch + 1 + day_count)]

    days_to_reserve_filtered = []

    for day in days_to_reserve:
        week_day = epoch_days_to_timestamp(day, True)
        if week_day not in ["Saturday", "Sunday"]:
            days_to_reserve_filtered.append(day)

    return days_since_epoch, days_to_reserve_filtered


def reserve_request(secrets, token, user_id, days_to_reserve):
    reserve_url = "https://us-central1-project-3687381701726997562.cloudfunctions.net/reserve2"
    reserve_headers = {"Authorization": f"Bearer {token}"}

    for day in days_to_reserve:
        reserve_data = {
            "me": user_id,
            "parkingId": secrets["parkingId"],
            "uid": user_id,
            "spotId": secrets["spotId"],
            "day": day,
            "addShifts": ["08000900", "09001000", "10001100", "11001200", "12001300", "13001400", "14001500", "15001600", "16001700", "17001800", "18001900"],
            "removeShifts": [],
            "v": "xKpQV"
        }

        logging.debug(reserve_data)

        reserve_ans = requests.post(reserve_url, json = reserve_data, headers = reserve_headers).text
        logging.debug(reserve_ans)

        if reserve_ans == """{"challenge":null}""":
            logging.info(f"Reserved for {epoch_days_to_timestamp(day)}")
        else:
            logging.info(f"Failed to reserve for {epoch_days_to_timestamp(day)}")


def main(args, loglevel, logformat):
    logging.basicConfig(format = logformat, level = loglevel)

    secrets = read_secrets(args.secrets_path)

    logging.info("Starting to reserve parking spots.")

    login_json = login_request(secrets)
    token = login_json["idToken"]

    profile_json = profile_request(secrets, token)
    user_id = profile_json["users"][0]["localId"]

    logging.debug(f"Your user_id - {user_id}")

    days_since_epoch, days_to_reserve = calculate_epoch_days(args.days, args.include_today)

    logging.info(f"Today is {days_since_epoch} days since epoch = {epoch_days_to_timestamp(days_since_epoch)}")
    logging.info(f"Reserving the following days (filtered): {days_to_reserve}")

    reserve_request(secrets, token, user_id, days_to_reserve)

    logging.info("Script finished running!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                                    description = "Add parking reservations to Parkalot.",
                                    epilog = "Enjoy! =)")

    parser.add_argument(
                        "-d",
                        "--days",
                        help = "range of DAYS to try reserve parking (1 - 7)",
                        metavar = "DAYS",
                        type = int,
                        choices = range(1, 8))
    parser.add_argument(
                        "secrets_path",
                        help = "secrets file path",
                        metavar = "SECRETS_FILE")
    parser.add_argument(
                        "-t",
                        "--include-today",
                        help = "include today in reservations",
                        action = "store_false")
    parser.add_argument(
                        "-v",
                        "--verbose",
                        help = "increase output verbosity",
                        action = "store_true")
    args = parser.parse_args()
  
    # Setup logging
    if args.verbose:
        loglevel = logging.DEBUG
        logformat = "%(levelname)s: %(message)s"
    else:
        loglevel = logging.INFO
        logformat = "%(message)s"
  
    main(args, loglevel, logformat)
