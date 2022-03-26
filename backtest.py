import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class Backtest:
    """
    列是票子，行数是天
    """
    def __init__(self, price_df):
        self.prc = price_df
        self.ret_df = self.prc.shift(-2, axis=1) / self.prc.shift(-1, axis=1) - 1
        self.index_ret = self.ret_df.mean()

    @staticmethod
    def cal_maxdd(array):
        drawdowns = []
        max_so_far = array[0]
        for i in range(len(array)):
            if array[i] > max_so_far:
                drawdown = 0
                drawdowns.append(drawdown)
                max_so_far = array[i]
            else:
                drawdown = max_so_far - array[i]
                drawdowns.append(drawdown)
        return max(drawdowns)

    def ic_info(self, fac_df: pd.DataFrame):
        ic_list = fac_df.corrwith(self.ret_df)
        ic = ic_list.mean()
        rankic_list = fac_df.rank(axis=0).corrwith(self.ret_df.rank(axis=0))
        rankic = rankic_list.mean()
        return ic, rankic

    def ret_info(self, fac_df: pd.DataFrame):
        """
        buy demeaned >0 stock, and short others
        buy the next day and sell the day after next day
        """
        fac_dmean = fac_df - fac_df.mean()
        fac_std = fac_dmean / (fac_dmean.abs().sum() / 2)
        long_signal_df = ((fac_std >= 0) * fac_std).fillna(0)
        short_signal_df = ((fac_std <= 0) * (-1) * fac_std).fillna(0)
        long_ret_no_cost = ((long_signal_df * self.ret_df).sum(axis=0) / long_signal_df.sum(axis=0)).fillna(0)
        short_ret_no_cost = ((short_signal_df * self.ret_df).sum(axis=0) / short_signal_df.sum(axis=0)).fillna(0)
        if long_ret_no_cost.sum() < short_ret_no_cost.sum():
            long_ret_no_cost, short_ret_no_cost = short_ret_no_cost, long_ret_no_cost
            long_signal_df, short_signal_df = short_signal_df, long_signal_df
        weight_df = (long_signal_df / long_signal_df.sum(axis=0)).fillna(0).replace(np.inf, 0)
        turnover = np.abs(weight_df - weight_df.shift(1, axis=1)).sum(axis=0)
        turnover_series = turnover.fillna(0).replace(np.infty, 0)
        annual_coef = 252 / len(long_ret_no_cost)
        data_dict = dict()
        data_dict['TurnOver'] = turnover_series.mean()
        data_dict['RetNC'] = (long_ret_no_cost - self.index_ret).cumsum().dropna().values[-1] * annual_coef
        data_dict['SharpeNC'] = (long_ret_no_cost - self.index_ret).mean() / (
                long_ret_no_cost - self.index_ret).std() * np.sqrt(
            252)
        data_dict['DDNC'] = self.cal_maxdd((long_ret_no_cost - self.index_ret).cumsum().dropna().values)
        return data_dict
