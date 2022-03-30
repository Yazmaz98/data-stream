import numpy as np


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
