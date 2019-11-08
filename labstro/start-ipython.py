from IPython import get_ipython
ipython = get_ipython()

ipython.magic("load_ext autoreload")
ipython.magic("autoreload 2")
print("loaded magic functions")
import os
import sys
sys.path.insert(0,os.path.abspath(os.path.pardir) + '/')
print("updated system path", sys.path)
