import numpy as np
import pmdarima as pm

# statsmodels version: 0.13
from statsmodels.tsa.arima.model import ARIMA
from tqdm import tqdm


class ARIMA_model():
    def __init__(self, p=None, q=None, r=None, auto=False):
        """
        p, q, r: params of ARIMA model,
        see https://www.statsmodels.org/devel/generated/statsmodels.tsa.arima.model.ARIMA.html
        """
        self.auto = auto
        self.p = p
        self.q = q
        self.r = r

    def fit_predict(self, X, y):
        y_pred = np.zeros_like(y)

        if self.auto:
            for i in tqdm(range(len(X))):
                ts = X[i]
                model = pm.arima.auto_arima(
                    ts, d=0, max_p=10, max_d=5,
                    max_q=10, trace=True, error_action='ignore',
                    suppress_warnings=True
                )
                model_fit = model.fit(ts)
                y_pred[i] = model_fit.predict(n_periods=1)[0]
            return y_pred

        for i in tqdm(range(len(X))):
            ts = X[i]
            model = ARIMA(ts, order=(self.p, self.q, self.r))
            model_fit = model.fit()
            y_pred[i] = model_fit.forecast()[0]
        return y_pred
