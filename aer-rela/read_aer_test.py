import pymystic
import aermsg2dataframe as a2df

with pymystic.Reader('../scenarios/demo_output.aer') as reader:
    # for msg in reader:
    #     print(msg)
    messages = list(reader)
    df_entity, df_orbital = a2df.parse_aer_messages(messages)

print(df_entity.head())
print(df_orbital.head())

# df_entity.to_csv("../output/entity.csv", index=False)
# df_orbital.to_csv("../output/orbital.csv", index=False)