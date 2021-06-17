from scipy.stats import mannwhitneyu


def non_parametric(X, Y, option='less'):

    _, p = mannwhitneyu(X, Y, alternative=option)

    return p
