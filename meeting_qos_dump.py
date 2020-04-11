#!/usr/bin/python

import requests
import json
import argparse
import datetime
import dateutil.relativedelta
import os.path
import sys
import base64

JWT_TOKEN = "[YOUR JWT TOKEN HERE]"

JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')

DEFAULT_TYPE = "past"

PREFIX_MEETING_DETAILS = "meeting"
PREFIX_PARTICIPANT = "user"

verbose = False

def get_response(path, params=None):
    if not path.startswith("/"):
        raise Exception("Path {} is not valid".format(path))

    headers = {
        'authorization': "Bearer {}".format(JWT_TOKEN),
        'content-type': "application/json"
    }
    
    if params:
        r = requests.get("http://api.zoom.us{}".format(path), verify=True, headers=headers, params=params)
    else:
        r = requests.get("http://api.zoom.us{}".format(path), verify=True, headers=headers) 
    
    if verbose:
        print(r.url)
        print(r.status_code)
        print(r.text)
    return r.json()

def get_all_meetings(start, end, type=DEFAULT_TYPE):
    uri = "/v2/metrics/meetings"
    params = {
        "type": type,
        "from": start.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d"),
        "page_size": 300,
    }

    cont = True
    while cont:
        data = get_response(uri, params)

        params["next_page_token"] = data["next_page_token"]
        if params["next_page_token"] == '':
            cont = False
        
        for m in data["meetings"]:
            yield m

def get_meetings(meeting_id, start, end, type=DEFAULT_TYPE):
    uuid = []
    for m in get_all_meetings(start, end):
        if m["id"] == meeting_id:
            uuid.append(m)
    return uuid

def get_meeting_details(uuid, type=DEFAULT_TYPE):
    uri = "/v2/metrics/meetings/{}".format(uuid)
    params = {
        "type": type,
    }

    return get_response(uri, params)

def get_user_qos(uuid, type=DEFAULT_TYPE):
    uri = "/v2/metrics/meetings/{}/participants/qos".format(uuid)
    params = {
        "type": type,
        "page_size": 10
    }

    cont = True
    while cont:
        data = get_response(uri, params)
        params["next_page_token"] = data["next_page_token"]
        if params["next_page_token"] == '':
            cont = False
        
        for u in data["participants"]:
            yield u

def print_uuid_selection(uuids):
    print("Multiple Meeting UUIDs found, select one of the followings")
    for m in uuids:
        print("uuid: {} start: {}, end: {}, topic: {}".format(m["uuid"], m["start_time"], m["end_time"], m["topic"]))

def check_args():
    parser = argparse.ArgumentParser(description="Dump User QoS in a specific Zoom meeting")
    parser.add_argument('--id', metavar='XXXXXXXXX', help='Meeting ID')
    parser.add_argument('--uuid', metavar='UUID', help='Meeting UUID')
    parser.add_argument('--start', metavar='YYYY-MM-DD', type=datetime.date.fromisoformat, help="Start date to lookup the meeting, default: same with the end date")
    parser.add_argument('--end', metavar='YYYY-MM-DD', type=datetime.date.fromisoformat, help='End date to lookup the meeting. default: today, or the same date with the start date if the start date is specified')
    parser.add_argument('--path', metavar='path', required=True, help='Path to save json files')
    parser.add_argument('--verbose', action="store_true", help="verbose output")

    args = vars(parser.parse_args())
    
    global verbose
    verbose = args["verbose"]

    if args["id"] is None and args["uuid"] is None:
        raise Exception("Meeting ID or Meeting UUID is required")

    if not args["id"].isdigit():
        id_norm = "".join(args["id"].split("-"))
        if id_norm.isdigit():
            args["id"] = int(id_norm)
        else:
            raise Exception("Invalid Meeting ID")
    else:
        args["id"] = int(args["id"])

    if args["end"] is None and args["start"] is None:
        args["end"] = datetime.datetime.now(JST).date()
    if args["start"] is None:
        args["start"] = args["end"]
    if args["end"] is None:
        args["end"] = args["start"]
    if args["end"] > args["start"] + dateutil.relativedelta.relativedelta(months=1):
        raise Exception("Duration between the start date and the end date should only be by one month")

    if not os.path.isdir(args["path"]):
        raise Exception("Path {} is not found, or not a directory")
    
    return args

if __name__ == '__main__':
    params = check_args()

    if params["uuid"] is not None:
        meeting_uuid = params["uuid"]
    else:
        meeting_uuids = get_meetings(params["id"], params["start"], params["end"])
        if len(meeting_uuids) > 1:
            print_uuid_selection(meeting_uuids)
            sys.exit(1)
        elif len(meeting_uuids) == 0:
            print("No Meeting Found")
            sys.exit(1)
        else:
            meeting_uuid = meeting_uuids[0]["uuid"]
    
    meeting_details = get_meeting_details(meeting_uuid)
    meeting_uuid_hex = base64.b64decode(meeting_uuid).hex()

    # dump meeting details
    filename_meeting_details = "{}/{}_{}_{}.json".format(params["path"], PREFIX_MEETING_DETAILS, meeting_details["id"], meeting_uuid_hex)
    with open(filename_meeting_details, "w") as f:
        json.dump(meeting_details, f)
    if verbose:
        print("Meeting Details have been saved at {}".format(filename_meeting_details))
    
    # dump user qos
    for u in get_user_qos(meeting_uuid):
        filename_user_qos = "{}/{}_{}_{}_{}.json".format(params["path"], PREFIX_PARTICIPANT, meeting_details["id"], meeting_uuid_hex, u["user_id"])
        with open(filename_user_qos, "w") as f:
            json.dump(u, f)
            if verbose:
                print("User QoS has been saved at {}".format(filename_user_qos))
