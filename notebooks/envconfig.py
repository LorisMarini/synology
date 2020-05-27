from imports import *

from IPython.display import SVG
from IPython.display import set_matplotlib_formats
from IPython.core.interactiveshell import InteractiveShell
from IPython.core.display import display, HTML

ip = get_ipython()

# Enable autoreload to propagate changes in noteboooks
ip.run_line_magic('load_ext', 'autoreload')
ip.run_line_magic('autoreload', '2')

# Enable matplotlib inline (plots displayed after each cell)
InteractiveShell.enable_matplotlib

# Display all outputs from a single cell (not just the last one)
# https://ipython.readthedocs.io/en/stable/config/options/kernel.html?highlight=ast_node_interactivity#configtrait-InteractiveShell.ast_node_interactivity
InteractiveShell.ast_node_interactivity = "all"

# Set resolution to retina
# https://ipython.readthedocs.io/en/stable/api/generated/IPython.display.html?highlight=set_matplotlib_formats#IPython.display.set_matplotlib_formats
set_matplotlib_formats('retina')

# Suppress warnings (or maybe not?)
warnings.filterwarnings('ignore')

# Make Jupyter Notebook cells larger
display(HTML("<style>.container { width:85% !important; }</style>"))

# Configure pandas look and feel
pd.set_option('max_colwidth', 600)
pd.set_option("display.max_columns", 1000)
pd.set_option("display.max_rows", 1000)
pd.set_option('display.float_format', lambda x: '%.3f' % x)

# Configure matplotlib
matplotlib.rc_file("matplotlibrc")
