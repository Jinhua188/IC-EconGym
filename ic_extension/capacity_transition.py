"""Shared investment-to-capacity queue, including the external physical-unit case."""
def schedule_capacity(queue,period,amount,lag,efficiency):
    if int(lag)<1 or efficiency<0:raise ValueError('invalid capacity lag/efficiency')
    due=int(period)+int(lag)
    queue[due]=queue.get(due,0.0)+efficiency*amount
