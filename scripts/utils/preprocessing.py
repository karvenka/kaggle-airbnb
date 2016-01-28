"""Utils used in the preprocessing stage."""

import pandas as pd
import numpy as np
from datetime import date
import holidays
from xgboost.sklearn import XGBClassifier


def one_hot_encoding(data, categorical_features):
    """Encode a list of categorical features using a one-hot scheme.

    Parameters
    ----------
    data : Pandas DataFrame
        DataFrame containing the categorical features.
    categorical_features : list
        Names of the categorial features to encode

    Returns
    -------
    data : DataFrame
        Returns a pandas DataFrame with one-hot scheme binary columns.
    """
    for feature in categorical_features:
        data_dummy = pd.get_dummies(data[feature], prefix=feature)
        data.drop([feature], axis=1, inplace=True)
        data = pd.concat((data, data_dummy), axis=1)

    return data


class XGBFeatureSelection(XGBClassifier):
    """A custom XGBClassifier with feature importances computation.

    This class implements XGBClassifier and also computes feature importances
    based on the fscores. Implementing feature_importances_ property allow us
    to use `SelectFromModel` with XGBClassifier.
    """

    def __init__(self, n_features, *args, **kwargs):
        """Init method adding n_features."""
        super(XGBFeatureSelection, self).__init__(*args, **kwargs)
        self._n_features = n_features

    @property
    def n_features(self):
        """Number of classes to predict."""
        return self._n_features

    @n_features.setter
    def n_features(self, value):
        self._n_features = value

    @property
    def feature_importances_(self):
        """Return the feature importances.

        Returns
        -------
        feature_importances_ : array, shape = [n_features]
        """
        booster = self.booster()
        fscores = booster.get_fscore()

        importances = np.zeros(self.n_features)

        for k, v in fscores.iteritems():
            importances[int(k[1:])] = v

        return importances


def _sanitize_holiday_name(name):
    new_name = [c for c in name if c.isalpha() or c.isdigit() or c == ' ']
    new_name = "".join(new_name).lower().replace(" ", "_")
    return new_name


def process_holidays(df):
    """Append the distance of several holidays in days to the users DataFrame.

    Parameters
    ----------
    df : Pandas DataFrame
        DataFrame containing the dates.

    Returns
    -------
    df : DataFrame
        Returns the original pandas DataFrame with the new features.
    """
    # Create a date object
    user_date = date(
        df['year_account_created'],
        df['month_account_created'],
        df['day_account_created']
    )

    # Get US holidays for this year
    holidays_dates = holidays.US(years=df['year_account_created'])

    for holiday_date, name in holidays_dates.iteritems():
        # Compute difference in days
        days = (holiday_date - user_date).days

        # Clean holiday name
        name = _sanitize_holiday_name(name)

        # Add the computed days to holiday into our DataFrame
        df['days_to_' + name] = days

    return df
