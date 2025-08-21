import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
# Added imports for the new transformer
from scipy import stats

# I don't want the BoxCox transformer to mess up data that it cannot fix.
# TODO: Review how I estimate if it's worth the transformation
epsilon = 1e-100


# TODO:    ('conditional_boxcox', ConditionalBoxCox()),
class ConditionalBoxCox(BaseEstimator, TransformerMixin):

    def __init__(self, p_value_threshold=0.05):
        self.p_value_threshold = p_value_threshold
        self.columns_to_transform_ = []
        self.lambdas_ = {}

    def fit(self, X: pd.DataFrame, y=None):
        for col in X.columns:
            # if (data := X[col]).isna().any():
            #     raise NotImplementedError('I do not know yet how this would be handled')
            if (data := X[col]).dtypes == 'object':
                continue
            if data.dtypes not in ('float64', 'int64'):
                raise NotImplementedError(X[col].dtypes)
            if data.nunique() < 10:  # Not worth the change
                continue
            data = data + (shift := epsilon - (0 if (data > 0).all() else data.min()))
            _, initial_p = stats.shapiro(data)
            print(initial_p)
            print(data.min(), data.max())
            transformed_data, lmbda = stats.boxcox(data)
            if len(transformed_data) < 3: continue
            _, transformed_p = stats.shapiro(transformed_data)
            if transformed_p > initial_p and transformed_p > self.p_value_threshold:
                self.columns_to_transform_.append(col)
                self.lambdas_[col] = {'lambda': lmbda, 'shift': shift}

        print(f"ConditionalBoxCox: Found {len(self.columns_to_transform_)} columns to transform.")
        if self.columns_to_transform_:
            print(f"Columns: {self.columns_to_transform_}")
        return self

    def transform(self, X):
        X_transformed = X.copy()
        for col in self.columns_to_transform_:
            if col in X_transformed.columns:
                col_params = self.lambdas_[col]
                data = X_transformed[col]

                shifted_data = data + col_params['shift']
                shifted_data[shifted_data <= 0] = 1e-6

                X_transformed[col] = stats.boxcox(
                    shifted_data,
                    lmbda=col_params['lambda']
                )
        return X_transformed

