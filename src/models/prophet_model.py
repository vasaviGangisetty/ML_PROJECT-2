from prophet import Prophet
import pandas as pd

class SalesProphetModel:
    def __init__(self):
        self.model = Prophet(yearly_seasonality=True, daily_seasonality=False)

    def train(self, df):
        # Prophet requires columns 'ds' and 'y'
        train_df = df[['Date', 'Sales']].rename(columns={'Date': 'ds', 'Sales': 'y'})
        self.model.fit(train_df)
        return self.model

    def predict(self, periods=30):
        future = self.model.make_future_dataframe(periods=periods)
        forecast = self.model.predict(future)
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]