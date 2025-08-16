import pandas as pd

df_rabi = pd.read_csv("/content/all_districts_rabi_aggregated.csv")
ind_df = pd.read_csv("/content/mp_all_district_indicies.csv")
all_crops = pd.read_csv("/content/all_crops_all_districts.csv")

all_crops['Year'] = all_crops['Year'].astype(str).str.split(' - ').str[0].astype(int)
df_rabi.rename(columns={'rabi_year': 'year'}, inplace=True)
merged_df = pd.merge(df_rabi, ind_df, on=['district', 'year'], how='inner')
merged_df = all_crops.merge(merged_df, right_on=['district', 'year'], left_on=['district', 'Year'], how='left')
merged_df = merged_df.dropna()

merged_df.to_csv("./../data/full_data_crop_yield.csv", index=False)