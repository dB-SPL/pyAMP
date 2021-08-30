# pyAMP
pyAMP enables point-to-multipoint (PTMP) file transfers over amateur radio with the Amatuer Multicast Protocol and using Dave Freese W1HKJ's popular [fldigi application](http://www.w1hkj.com/) as a software modem.  It is, of course, inspired by flamp, fldigi, and the rest of the Narrow Band Emergency Messaging System (NBEMS) suite of applications.

The main goal of the project is to allow radio operators to more efficeiently and reliably handle emergency communications with fewer retries and duplicate transmissions.  Once received, messages are kept in the received file queue until explicitly removed, even after closing and restarting the application, rebooting the computer, or a software crash.  This greatly reduces the chance of operators relaying messages to send "different versions" of the same file.

In the case of partially received files, pyAMP can recognize when transmissions with different AMP "queue IDs" are actually the same file (with the same compression and encoding).  As long as each block in a file has been received at least once, pyAMP can combine the partial receptions to successfully decode the file.

pyAMP uses Niel Jansen MK4YRI's [pyFldigi library](https://github.com/KM4YRI/pyFldigi) to interface with fldigi via XML-RPC and Raymond Buvel's [crcmod](http://crcmod.sourceforge.net/) for the required checksums.  The GUI is built with [PySimpleGUI](http://pysimplegui.org)
