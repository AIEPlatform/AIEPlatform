import datetime as dt
import json

def AverageRewardByTime(df, selectedAssigners = [], selectedVersions = [], perDay = ""):
   result_df = None
   # convert to date yyyy-mm-dd
   if len(selectedAssigners) > 0:
      df = df[df['assigner'].isin(selectedAssigners)]
   if len(selectedVersions) > 0:
      df = df[df['treatment'].isin(selectedVersions)]
   df['outcome.timestamp'] = df['outcome.timestamp'].apply(lambda x: x.date())
   # drop rows that have no outcome.timestamp
   df = df.dropna(subset=['outcome.timestamp'])

   result_df = df.groupby(['treatment', 'outcome.timestamp']) \
      .agg(mean=('outcome', 'mean'), sem=('outcome', 'sem')) \
      .reset_index()
    
   result_df = result_df.sort_values(by=['outcome.timestamp'])

   result_df.rename(columns={'outcome.timestamp': 'x', 'treatment': 'group', 'mean': 'y', 'sem': 'errorBar'}, inplace=True)

    
   pivoted_df = result_df.pivot(index='x', columns='group', values='y').reset_index()
   error_bars = result_df.pivot(index='x', columns='group', values='errorBar')

   # Merge the pivoted DataFrame and error bars
   pivoted_df = pivoted_df.merge(error_bars, on='x', suffixes=('', '-errorBar'))



   pivoted_df['x'] = pivoted_df['x'].apply(lambda x: x.strftime('%Y-%m-%d'))
   pivoted_df = pivoted_df.rename_axis(None, axis=1)

   return json.loads(pivoted_df.to_json(orient="records")), [c for c in pivoted_df.columns if c != 'x']