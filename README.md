## PyVHDL - A happy marriage of Python and VHDL
PyVHDL is an open source project for simulating VHDL hardware designs. It cleanly integrates the general purpose [Python](https://www.python.org/) programming language with the specialized [VHDL](https://en.wikipedia.org/wiki/VHDL)  hardware description language. You can write the testbench for your VHDL design in Python. You can use Python for more than just testbenches. You can also create architectures in your VHDL design that are written in Python. Standard VHDL syntax is used to link the VHDL architecture to a python file. 
 
## Features

* PyVHDL includes Python classes for concurrent processes, std_logic and std_logic_vector signals. Python processes can wait for signal transitions, wait for a specified period of time, read values of signals in the design, or update the values of signals with an optional delay.

* PyVHDL features a unified execution environment. VHDL is translated to Python bytecode, and runs on the same interpreter as the python code. There is no overhead wasted on passing data and maintaining synchronization between separate Python and VHDL environments.

* The excellent [ZamiaCAD](http://zamiacad.sourceforge.net/web/) Eclipse based IDE is packaged with PyVHDL. The IDE manages projects, simulation runs, and displays waveforms generated during the simulation. The IDE also syntax checks VHDL files, and parses and elaborates the VHDL design.

* PyVHDL includes features for generating a value change dump file (.VCD) as the simulation runs. VCD is a standard format for encoding waveforms for display of simulation results. The zamiaCAD IDE can optionally graphically display the VCD output of a simulation.

* PyVHDL includes a sample project which is the design for the 32-bit, MIPs compatible plasma CPU. The plasma processor executes the MIPs instruction set. The project includes Python files that implement the CPU register file, 8K of external memory that can initialize itself from a hex file, and a testbench to run the simulation.

## Documentation

View the documentation for PyVHDL at [ReadTheDocs](http://pyvhdl-docs.readthedocs.io/en/latest/).

## Installation

See the installation section of the documentation at [ReadTheDocs](http://pyvhdl-docs.readthedocs.io/en/latest/).
.

## Contribute

An important goal of PyVHDL is to create a VHDL simulator that is accessible for improvement by the open source community. The simulator is written in Python, a language familiar to many programmers. The python sources are in the `Runtime\share\python\Sim` folder. The files `peripheral.py, plasma_ram.py and reg_block.py` in the plasma design project are examples of using a Python file as a testbench, and for general design units in a project.   

## License

PyVHDL is copyright 2016 by Vern Muhr and is covered by the [GNU General Public License Version 3](http://www.gnu.org/licenses/gpl-3.0-standalone.html).