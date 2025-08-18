import pandas as pd
import os
import joblib



current_dir = os.path.dirname(__file__) 
all_crops_all_districts_path = os.path.join(current_dir, "../data/all_crops_all_districts.csv")
df = pd.read_csv(all_crops_all_districts_path)

price_path = os.path.join(current_dir, "../models/rf_april.pkl")
price_df_path = os.path.join(current_dir, "../data/All_Combined_April.xlsx")

price_model = joblib.load(price_path)
price_df = pd.read_excel(price_df_path)

price_df = pd.read_excel(price_df_path)
price_df = price_df.rename(columns={
    'Market Name': 'Market',
    'Price Date': 'Date',
    'Modal Price (Rs./Quintal)': 'Price'
})
price_df['Date'] = pd.to_datetime(price_df['Date'], errors='coerce')
price_df['Year'] = price_df['Date'].dt.year
price_df['Day'] = price_df['Date'].dt.day



def predPrice(year, district):
    X  = price_df[(price_df['Year'] == year) & (price_df['District Name'] == district)]
    X = pd.get_dummies(X[['Market','Year','Day']], drop_first=True)
    pred = price_model.predict(X)
    return pred

df['Year'] = df['Year'].str.split('-').str[0].astype(int)
def revenueProjection_early(area, pred_Yield, pred_price):        
    return area*pred_Yield*pred_price

def totalExpenses(monthly_expenses, tenure, Insurance_premium, Input_cost):
    return monthly_expenses * tenure + Insurance_premium + Input_cost

def Cnet(revenue, expenses, off_farm, tenure=6):
    return revenue - expenses + off_farm*tenure

def loanPayBack(principal, interest_rate, tenure):
    return principal * (1 + (interest_rate * tenure)/ 12)

def initial_yield_pred(district, crop, year):
    """
    Get initial yield prediction based on district, crop, and year.
    
    Args:
        district (str): Name of the district.
        crop (str): Type of crop.
        year (int): Year for which the prediction is made.
        
    Returns:
        float: Initial yield prediction.
    """

    print(f"initial Yield district: {district}, crop: {crop}, year: {year}")
    filtered = df[
        (df['district'] == district) &
        (df['crop_type'] == crop) &
        (df['Year'] < year)  # Adjust range as needed
    ]
    print(f"filtered: {filtered}")
    if not filtered.empty:
        return filtered['Crop_yield'].mean()

    return None 
    

def preSeasonCalc(**kwargs):
    """
    Calculate pre-season financials based on provided inputs.

    Expected kwargs:
        - area (float): Area of the farm.
        - district (str): Name of the district.
        - crop (str): Type of crop.
        - year (int): Year for the calculation.
        - monthly_expenses (float): Monthly farm expenses.
        - tenure (int, optional): Loan tenure in months. Default 6.
        - Insurance_premium (float): Insurance premium.
        - Input_cost (float): Input cost for the crop.
        - off_farm_income (float): Off-farm income.
        - interest_rate (float): Interest rate on loan.
        - principal (float): Loan principal.

    Returns:
        dict: Financial projections including revenue, expenses, net cash flow, and loan repayment.
    """
    area = kwargs.get('area')
    district = kwargs.get('district')
    crop = kwargs.get('crop')
    year = kwargs.get('year')
    monthly_expenses = kwargs.get('monthly_expenses', 10000)
    tenure = kwargs.get('tenure', 6)
    Insurance_premium = kwargs.get('Insurance_premium', 5000)
    Input_cost = kwargs.get('Input_cost', 30000)
    off_farm_income = kwargs.get('off_farm_income', 8000)
    interest_rate = kwargs.get('interest_rate')
    principal = kwargs.get('principal')


    print(f"area: {area}, district: {district}, crop: {crop}, year: {year}, interest_rate: {interest_rate}, principal: {principal}")
    # Get predicted yield
    pred_Yield = initial_yield_pred(district, crop, year)
    if pred_Yield is None:
        return {"error": "Yield prediction not available for the given parameters hello."}

    pred_price = 2000  # Placeholder for predicted price per unit of yield

    # Compute financial projections
    revenue = revenueProjection_early(area, pred_Yield, pred_price)
    expenses = totalExpenses(monthly_expenses, tenure, Insurance_premium, Input_cost)
    net_cash_flow = Cnet(revenue, expenses, off_farm_income)
    loan_repayment = loanPayBack(principal, interest_rate, tenure)

    return pred_Yield, pred_price

