import pandas as pd
import numpy as np
import sys
from credentials import *
import itertools
from scipy import stats
from statsmodels.stats.power import FTestAnovaPower



def get_all_combinations(array):
    all_combinations = []
    for r in range(1, len(array) + 1):
        combinations = itertools.combinations(array, r)
        all_combinations.extend(combinations)
    return all_combinations


def get_stats(df, group_by):
    # stats = {}
    # stats['Mean outcome'] = group['outcome'].mean()
    # stats['Count'] = group['outcome'].count()
    # # stats['Count of non-response'] = group['reward'].isnull().sum()
    # # stats['% of non-response'] = round(group['reward'].isnull().mean() * 100,2)

    df = df.groupby(group_by) \
       .agg(count=('outcome', 'size'), 
            mean=('outcome', lambda x: round(x.mean(), 3)), 
            count_of_non_response=('outcome', lambda x: x.isnull().sum()),
            percent_of_non_response=('outcome', lambda x: round((x.isnull().mean() * 100), 3))) \
       .reset_index()
    df = df.rename(columns={
        "count": "Count",
        "mean": "Mean",
        "count_of_non_response": "Count of non-response",
        "percent_of_non_response": "% of non-response"
    })   
    return df


def filter_dataframe(df, filter_dict):
    # Using boolean indexing
    conditions = [(df[column].isin([filter_dict[column]])) for column in filter_dict]
    # conditions[0] only filter the fist condition, if you want to apply all conditons, check next line
    final_condition = np.all(conditions, axis=0)
    filtered_df_boolean = df[final_condition].reset_index(drop=True) # TODO: why conditions[0]? - solved
    
    return filtered_df_boolean
    # return filtered_df_boolean

# Statistical power
def calculate_statistical_power(df, outcome_var):
    nobs = len(df[outcome_var])  # total number of observations
    n_groups = df[outcome_var].nunique()  # unique outcome

    # Calculate effect size (eta squared)
    ss_total = np.sum((df[outcome_var] - np.mean(df[outcome_var]))**2)
    ss_explained = (np.sum(df.groupby('treatment')[outcome_var].count() *
                           (df.groupby('treatment')[outcome_var].mean() - np.mean(df[outcome_var]))**2))
    eta_squared = ss_explained / ss_total

    # Perform power analysis
    analysis = FTestAnovaPower()
    
    # Statistical Power calculations F-test for one factor balanced ANOVA
    # This is based on Cohen’s f as effect size measure.
    power = analysis.solve_power(eta_squared, nobs=nobs, alpha=0.05, k_groups=n_groups)
    
    return round(power, 3)  # return rounded power

# Final function
def basic_reward_summary_table(df, selectedVariables, selectedAssigners = []):

    result_df = None
    data = df
    # filter out selected assigners
    if len(selectedAssigners) > 0:
        data = df[df['assigner'].isin(selectedAssigners)]
    all_combs = get_all_combinations(selectedVariables)
    if len(selectedVariables) == 0:
        result_df = get_stats(data, ['treatment'])
    else:
        # group by treatment and all combinations of selected variables
        group_bys = [['treatment']] + [['treatment'] + list(comb) for comb in all_combs]
        grouped_dfs = []
        for group in group_bys:
            grouped = get_stats(data, group)
            grouped_dfs.append(grouped)

        result_df = pd.concat(grouped_dfs, axis=0, ignore_index=True)
    desired_columns = [col for col in result_df.columns if col not in ['Count', 'Mean','Count of non-response',"% of non-response"]] + ['Count', 'Mean','Count of non-response',"% of non-response"]
    
    # Reorder the columns
    result_df = result_df[desired_columns]
    result_df = result_df.replace(np.nan, -np.inf, regex=True)
    result_df = result_df.sort_values(by= selectedVariables + ['treatment'], ascending=True)
    result_df = result_df.replace(-np.inf, '', regex=True) # not sure how to sort ascendingly but put empty on top.
    # temporarily fill empty strings or NaN values with a value that's guaranteed to be smaller than all other values during the sort, and then replace it back to the empty string afterwards. In this case, -np.inf serves that purpose. 


    unique_versions = result_df['treatment'].unique()
    # Get the filter conditions -> TODO: since the table won't have many rows, it is fine to do a for loop? - solved
        
    filter_conditions = []
    for comb in all_combs:
        comb = list(comb)
        filter_empty = result_df[comb].ne('').all(axis=1) 
        unique_combinations = result_df[filter_empty].drop_duplicates(subset=comb)[comb].to_dict(orient='records')
        filter_conditions.extend(unique_combinations)
    
    
    # ! Use ANOVA to calculate p-value and power 
    for filter_condition in filter_conditions:
        filtered_df = filter_dataframe(df, filter_condition)
        outcomes = [filtered_df[filtered_df['treatment'] == version]['outcome'].dropna() for version in unique_versions]
        f_value, p_value = stats.f_oneway(*outcomes)
        
        # calculate power for the filtered dataframe
        power = calculate_statistical_power(filtered_df, 'outcome')
        
        for index, row in result_df.iterrows():
            if all(row[key] == value for key, value in filter_condition.items()):
                result_df.loc[index, 'P value'] = round(p_value,3)
                result_df.loc[index, 'Power'] = power

    # ! calculate p value, power for the whole dataset.
    outcomes = [df[df['treatment'] == version]['outcome'].dropna() for version in unique_versions]
    f_value, p_value = stats.f_oneway(*outcomes)
    power = calculate_statistical_power(df, 'outcome')
    for index, row in result_df.iterrows():
        if all(row[key] == "" for key in selectedVariables):
            result_df.loc[index, 'P value'] = round(p_value,3)
            result_df.loc[index, 'Power'] = power
            
    # change P-value to string
    result_df["P value"] = result_df["P value"].astype("string")
    
    
    
    # Calculate overall statistics
    outcomes = [df[df['treatment'] == version]['outcome'].dropna() for version in unique_versions]
    f_value, overall_p_value = stats.f_oneway(*outcomes)
    
    # Create a new DataFrame for overall statistics with no version
    overall_df = pd.DataFrame({"treatment": ["All versions"], 
                               "Count": [data["outcome"].size],# size is the count including NA valuess
                               "Mean": [round(data['outcome'].mean(),3)],
                               "Count of non-response": [data['outcome'].isnull().sum()],
                               "% of non-response": [round(data['outcome'].isnull().mean() * 100,3)],
                               "P value": [round(overall_p_value,3)],
                               "Power": [calculate_statistical_power(data, 'outcome')]})

    # Append the overall statistics DataFrame to the result DataFrame
    result_df = pd.concat([result_df, overall_df], ignore_index=True)
    # Fill NaN with ""
    result_df = result_df.fillna("")
    result_df = result_df.reindex([result_df.index[-1]] + list(result_df.index[:-1]))
    # order by treatment.
    result_df = result_df.sort_values(by= 'treatment', ascending=True)
    print(result_df['treatment'])
    return result_df