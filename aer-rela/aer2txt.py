import pymystic

with pymystic.Reader('../scenarios/demo_output.aer') as reader:
    with open('../output/messages.txt', 'w') as f:
        for msg in reader:
            f.write(str(msg) + '\n')