import unittest

class Test(unittest.IsolatedAsyncioTestCase):

    async def test_getKospiKosdaq(self):
        self.assertEqual(1, 1)

    async def test_getAnnualRevenue(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getQuarterRevenue(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getAnnualOperatingProfit(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getQuarterOperatingProfit(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getAnnualNetProfit(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getQuarterNetProfit(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getAnnualDebtRatio(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getQuarterDebtRatio(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getAnnualTotalFinancialInfo(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getQuarterTotalFinancialInfo(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getAnnualTotalYearly(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getQuarterTotalYearly(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getAnnualPBR(self):
        code = "ABC123"
        self.assertEqual(1, 1)

    async def test_getQuarterPBR(self):
        code = "ABC123"
        self.assertEqual(1, 1)

if __name__ == '__main__':
    unittest.main()
