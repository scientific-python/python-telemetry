from scipy import stats

stats.norm.pdf(x=1, loc=1, scale=0.01)
stats.norm(loc=1, scale=0.02).pdf(1)
stats.chatterjeexi([1, 2, 3, 4], [1.1, 2.2, 3.3, 4.4])

# X = stats.Normal()
# Y = stats.exp((X + 1)*0.01)
# from scipy import test
# test()
