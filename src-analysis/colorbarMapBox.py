import numpy as np 

xxmin = 4.e-6
xxmax = 1.17

yymin = np.log(xxmin)/np.log(10)
yymax = np.log(xxmax)/np.log(10)

yy = np.linspace(yymin,yymax,8)

xx = np.exp(yy*np.log(10))

print(xx)
