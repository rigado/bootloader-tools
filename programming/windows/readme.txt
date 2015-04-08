BMD-200 Programmer Script:

1. Install Python 3.x
2. Place your application binary (named application.bin) into the folder with program.py
3. Run script with "python program.py <args>", see below:

	- The script must receive --savemac or -m/--mac as an argument
	- If no key is specified with -k/--key the key is set to 00000000000000000000000000000000 (no-encryption)
	- MAC address and key are input big-endian and can be separated by colons: "11:22:33:44:55:66" <-> "112233445566"
	- When a module is successfully programmed the MAC, key and device tag are written to a logfile (default: log.txt)

	Program the application and save the currently set MAC address in the module:
	"python program.py --savemac"

	Program the application and set the MAC as 112233445566 with device tag "prototype1":
	"python program.py --mac 11:22:33:44:55:66 --tag prototype1

	Program the application setting MAC to 112233445566 and key to 00112233445566778899AABBCCDDEEFF:
	"python program.py --key 00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF --mac 112233445566"

	Program the application and save the currently set MAC address in the module and set logfile to "alternate_log.txt":
	"python program.py --savemac --logfile alternate_log.txt"

	Show help dialog:
	"python program.py --help"


Binary Versions:
Softdevice_S110/7.1.0
RigDFU2/2.4