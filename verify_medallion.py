import pandas as pd
from bronze import prepare_bronze_data
from silver import prepare_silver_data
from gold import prepare_gold_data

raw_df = pd.DataFrame({'id':[1,2], 'name':['Alice','Bob']})
bronze_df = prepare_bronze_data([('customers.csv', raw_df)])
silver_df = prepare_silver_data(bronze_df)
gold_df = prepare_gold_data(silver_df)
print('bronze_ok', bronze_df['layer'].eq('bronze').all(), len(bronze_df))
print('silver_ok', silver_df['status'].eq('validated').all(), silver_df['amount'].dtype.kind in 'if')
print('gold_ok', gold_df['layer'].eq('gold').all(), gold_df.iloc[0]['total_amount'])
