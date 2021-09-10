# pyAMP
pyAMP enables point-to-multipoint (PTMP) file transfers over amateur radio with the Amatuer Multicast Protocol and using the popular fldigi as a software modem.  It is, of course, inspired by flamp, fldigi, and the rest of the Narrow Band Emergency Messaging System (NBEMS) suite of applications.

The main goal of the project is to allow radio operators to more efficeiently and reliably handle emergency communications with fewer retries and duplicate transmissions.  Once received, messages are kept in the received file queue until explicitly removed, even after closing and restarting the application or rebooting the computer.  This greatly reduces the chance that operators relaying messages end up sending "different versions" of the same file... or worse yet, partially receiving the same file twice, and still being unable to decode it.

In the case of partially received files, pyAMP can recognize when transmissions with different AMP "queue IDs" are actually the same file (with the same compression and encoding).  As long as each block in a file has been received at least once, pyAMP can combine the partial receptions to successfully decode the file.

### Status
[A preview version capable of receiving and relaying files](https://github.com/dB-SPL/pyAMP/releases/) is currently available while I work on the features required for encoding and transmitting files.  Executable files are available for Windows as well as Raspberry Pi OS.  The Raspberry Pi version will likely work on other Linux systems using ARM.  They can be launched with a simple double-click.

*PLEASE NOTE*
At this time, there is a known issue with pyAMP on Windows in which fldigi will not transmit text that is manually entered into the transmit pane while pyAMP is connected.  This bug also prevents fldigi from transmitting data from flamp while pyAMP is connected.

If you prefer to install pyAMP as a Python module directly, I suggest creating a folder for it, then installing to that folder using pip to handle the dependencies using:

`python3 -m pip --target=/path/to/your/folder https://github.com/dB-SPL/pyAMP/archive/refs/heads/main.zip`

To launch the Python module, use:
`pythom3 -m pyamp`

### Collaboration
Have a great idea to improve pyAMP?  Please submit a pull request or issue here on GitHub.

### Credits
Dave Freese W1HKJ's [fldigi application](http://www.w1hkj.com/) provides the modems.  pyAMP uses Niel Jansen KM4YRI's [pyFldigi library](https://github.com/KM4YRI/pyFldigi) to interface with fldigi via XML-RPC, and Raymond Buvel's [crcmod](http://crcmod.sourceforge.net/) is used for the required checksums.  The GUI is built with [PySimpleGUI](http://pysimplegui.org), and the executable files were created with [pyinstaller](http://pyinstaller.org).
