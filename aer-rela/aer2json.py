import pymystic
import json

with pymystic.Reader('../scenarios/demo_output.aer') as reader:
    with open('../output/messages.json', 'w') as f:
        for msg in reader:
            f.write(json.dumps(msg, indent=2) + '\n')