import numpy as np
import pmdarima as pm

# statsmodels version: 0.13
from statsmodels.tsa.arima.model import ARIMA
from tqdm import tqdm

def create_dataset(X: np.array, n_samples: int, mode: str='direct'):
    """
    Function takes time-series X as an input and provides time-series X0 and
    the test data yo for output.
    ----------------------------------
    n_samples : int, number of samples
    mode : string,
    - 'direct': X0 are the generated batches, yo is x[t+1]
    - 'log': X0 - outputs the log-returns of the data,
             y0 is the next log-return.
    ----------------------------------
    X0: np.array, shape: (len(X) - n_samples - 1, n_samples)
    y0: np.array, shape: len(X) - n_samples - 1
    """
    if mode == 'direct':
        X0 = np.zeros((len(X) - n_samples - 1, n_samples))
        y0 = np.zeros(len(X) - n_samples - 1)
        for i in range(len(X) - n_samples - 1):
            X0[i] = X[i: i + n_samples]
            y0[i] = X[i + n_samples + 1]
    elif mode == 'log':
        X0 = np.zeros((len(X) - n_samples - 2, n_samples))
        y0 = np.zeros(len(X) - n_samples - 2)
        X_return = np.log(X[1:] / X[:-1])
        for i in range(len(X) - n_samples - 2):
            X0[i] = X_return[i:i + n_samples]
            y0[i] = X_return[i + n_samples + 1]
    else:
        raise(NotImplementedError("Unknown method"))

    return X0, y0


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
