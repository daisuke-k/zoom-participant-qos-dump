# Usage
```
$ python meeting_qos_dump.py --id [Meeting ID] --start [start date to lookup the meeting, YYYY-MM-DD] --end [end date to lookup the meeting, YYYY-MM-DD] --path [Path to the directory to save json files] [--verbose]
```

If there are multiple meeting instances in one meeting ID, --uuid [Meeting UUID] is required.

## Example
```
$ python meeting_qos_dump.py --id 123-456-789 --uuid fdjapewajsc --start 2020-04-10 --end 2020-04-10 --path ./data
```

This will generate:
- ./data/meeting_[Meeting ID]_[Meeting Instance UUID].json: for meeting details
- ./data/user_[Meeting ID]_[Meeting Instance UUID]_[User ID].json: for each user QoS
recorded in the meeting instance fdjapewajsc of the meeting id 123-456-789.