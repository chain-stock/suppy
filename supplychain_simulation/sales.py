from collections import UserDict


class Sales(UserDict[int, int]):
    """dict of sales per period"""

    def pop_sales(self, period: int) -> int:
        """Remove and return the sales for a specific period

        If there were no sales for the period, returns 0
        """
        return self.data.pop(period, 0)
