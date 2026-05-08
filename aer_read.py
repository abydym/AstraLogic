import pymystic
import pandas as pd
import numpy as np

def msg2df(messages):
    """将AFSIM消息列表转换为DataFrame"""
    entity_data = []
    orbital_data = []
    
    for msg in messages:
        if msg['msgtype'] == 'MsgEntityState':
            state = msg['state']
            entity_data.append({
                'simTime': msg['simTime'],
                'platformIndex': state['platformIndex'],
                'x': state['locationWCS']['x'],
                'y': state['locationWCS']['y'],
                'z': state['locationWCS']['z'],
                'vx': state['velocityWCS']['x'] if state.get('velocityWCSValid', False) else np.nan,
                'vy': state['velocityWCS']['y'] if state.get('velocityWCSValid', False) else np.nan,
                'vz': state['velocityWCS']['z'] if state.get('velocityWCSValid', False) else np.nan,
                'damage': state.get('damageFactor', 0.0)
            })
        
        elif msg['msgtype'] == 'MsgOrbitalElements':
            orbital_data.append({
                'simTime': msg['simTime'],
                'platformIndex': msg['platformIndex'],
                'semiMajorAxis': msg['semiMajorAxis'],
                'eccentricity': msg['eccentricity'],
                'inclination': msg['inclination'],
                'raan': msg['raan'],
                'trueAnomaly': msg.get('trueAnomaly', 0)
            })
    
    df_entity = pd.DataFrame(entity_data)
    df_orbital = pd.DataFrame(orbital_data)
    
    return df_entity, df_orbital


with pymystic.Reader('demo_output.aer') as reader:
    # for msg in reader:
    #     print(msg)
    messages = list(reader)
    df_entity, df_orbital = msg2df(messages)
# print(df_entity.head())
# print(df_orbital.head())
df_entity.to_csv("output/entity.csv", index=False)
df_orbital.to_csv("output/orbital.csv", index=False)