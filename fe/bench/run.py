
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
rootPath2 = os.path.split(rootPath)[0]
sys.path.append(rootPath2)

from fe.bench.workload import Workload
from fe.bench.session import Session

def run_bench():
    wl = Workload()
    wl.gen_database()

    sessions = []
    for i in range(0, wl.session):
        ss = Session(wl)
        sessions.append(ss)

    for ss in sessions:
        ss.start()

    for ss in sessions:
        ss.join()


if __name__ == "__main__":
    #serve.be_run()
    run_bench()
