/*
  Tool to validate operation of node.js noble package.  Scans
  for all advertising BLE devices.
  
  @copyright (c) Rigado, LLC. All rights reserved.

  Source code licensed under BMD-200 Software License Agreement.
  You should have received a copy with purchase of BMD-200 product.
  If not, contact info@rigado.com for for a copy. 
*/
#!/usr/bin/env nodejs

var noble = require('noble');
var async = require('async');
var util = require('util');

// Pass a single argument to only show devices with that local name
match_name = "";
if (process.argv.length == 3)
    match_name = process.argv[2];

// Start the scanning process
noble.on('stateChange', function(state) {
    if (state === "poweredOn") {
        if (match_name === "") {
            console.log("Scanning for DFU devices...");
        } else {
            console.log("Scanning for DFU devices with name '%s'...",
                        match_name);
        }
        startScan();
    } else {
        console.error("unexpected state change: %s", state);
        process.exit(1);
    }
});

function startScan() {
    noble.on('discover', onDiscover);
    noble.startScanning([], true);
}

function onDiscover(peripheral) {
    var adv = peripheral.advertisement;
    var uuids = adv.serviceUuids;

    if (match_name !== "" && match_name !== adv.localName)
        return;

    console.log("Found: name %s, address %s, RSSI %d",
		adv.localName, peripheral.uuid, peripheral.rssi);
}
