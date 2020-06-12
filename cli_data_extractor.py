﻿import pythoncom
import win32com.client as win32
import pywintypes
import numpy as np

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

server = win32.Dispatch('PISDK.PISDK.1').Servers('POSCOPOWER')
pisdk = win32.gencache.EnsureModule('{0EE075CE-8C31-11D1-BD73-0060B0290178}',0, 1, 1,bForDemand = False)

point = []
iter_cnt = 1
err_cnt= 0
reason = set()

tag = np.loadtxt('./tag.csv', dtype=np.str, delimiter=',')

for x in tag:
    point.append(server.PIPoints(x).Data)
l = len(point)
trends = []
n_samples = int((12*30+11)*24*6)
space = 10
unit = 'm'
end_time = '2020-06-10 00:00'

printProgressBar(0, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
for i, p in enumerate(point):
    if p is not None:
        data2 = pisdk.IPIData2(p)
        #print('Extracting Data...')
        while True:
            try:
                results = data2.InterpolatedValues2(end_time+'-'+str(n_samples*space)+unit,end_time,str(space)+unit,asynchStatus=None)
                #print('**************************Successful!')
                break
            except pywintypes.com_error:
                #print('Error occured, retrying...')
                pass
        tmpValue = []
        tmpTime = []
        for v in results:
            try:
                if i == 0:
                    t = float(v.TimeStamp.LocalDate.timestamp())
                    tmpTime.append(t)
                s = str(v.Value)
                tmpValue.append(float(s))
            except ValueError:
                if s == 'N RUN' or s == 'NRUN' or s == 'N OPEN':
                    tmpValue.append(0.0)
                elif s == 'RUN' or s == 'OPEN':
                    tmpValue.append(1.0)
                else:
                    try:
                        tmpValue.append(np.nan)
                    #    tmpValue.append(tmpValue[-1])
                    #except IndexError:
                    #    tmpValue.append(0.0)
                    finally:
                        err_cnt += 1
                        reason.add(str(v.Value))
        if i == 0:
            tmpTime.pop()
            trends.append(tmpTime)
        tmpValue.pop()
        trends.append(tmpValue)
        printProgressBar(i + 1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
        
print('Total Error Counter: ', end='')
print(err_cnt)

print('Reason: ', end='')
print(*reason if reason else '', sep=', ')

trends = np.array(trends, dtype=np.float32).transpose()
#trends = trends[~np.isnan(trends).any(axis=1)]
np.savetxt(end_time.split()[0]+'_'+str(space)+unit+'_'+str(n_samples)+'.csv', trends, delimiter=',')