#!/usr/bin/env nodejs

/*
  Node.js tool for performing an OTA update
  @copyright (c) Rigado, LLC. All rights reserved.


  Source code licensed under BMD-200 Software License Agreement.
  You should have received a copy with purchase of BMD-200 product.
  If not, contact info@rigado.com for for a copy. 
*/
var noble = require('noble');
var async = require('async');
var util = require('util');
var fs = require('fs');
var commander = require('commander');
var sprintf = require('sprintf-js').sprintf;
var bitsyntax = require('bitsyntax');

function printf() {
    var args = Array.prototype.slice.call(arguments);
    console.log(sprintf.apply(null, args));
}
function errx() {
    var args = Array.prototype.slice.call(arguments);
    var retval = args.shift();
    console.error("ERROR: " + sprintf.apply(null, args));
    process.exit(retval);
}

// DFU constants

var DFU_NAME = 'RigDfu';
//var DFU_SERVICE_UUID       = '00001530eb684181a6df42562b7fef98';
//var DFU_CONTROL_POINT_UUID = '00001531eb684181a6df42562b7fef98';
//var DFU_PACKET_UUID        = '00001532eb684181a6df42562b7fef98';

var DFU_SERVICE_UUID        = '000015301212efde1523785feabcd123';
var DFU_CONTROL_POINT_UUID  = '000015311212efde1523785feabcd123';
var DFU_PACKET_UUID         = '000015321212efde1523785feabcd123';
                                   //c841903017564c3093cca8fcc2fb0202
var NEW_DFU_SERVICE_UUID        = '41c8903017564c3093cca8fcc2fb0202'
var NEW_DFU_CONTROL_POINT_UUID  = '41c8903217564c3093cca8fcc2fb0202'
var NEW_DFU_PACKET_UUID         = '41c8903117564c3093cca8fcc2fb0202'

var control_uuid
var packet_uuid

var DIS_SERVICE_UUID = '180a';
var DIS_FWREV_UUID = '2a26';

var OP_START_DFU = 1;
var OP_INITIALIZE_DFU = 2;
var OP_RECEIVE_FIRMWARE_IMAGE = 3;
var OP_VALIDATE_FIRMWARE_IMAGE = 4;
var OP_ACTIVATE_FIRMWARE_AND_RESET = 5;
var OP_SYSTEM_RESET = 6;
var OP_REQ_PKT_RCPT_NOTIF = 8;
var OP_CONFIG = 9;
var OP_PATCH_INIT = 10;
var OP_RECEIVE_PATCH_IMAGE = 11;
var OP_MTU_REQUEST = 13;
var OP_RESPONSE = 16;
var OP_PKT_RCPT_NOTIF = 17;

var DFU_UPDATE_SD = 1;
var DFU_UPDATE_BL = 2;
var DFU_UPDATE_APP = 4;

var OPS = {
    1: 'Start DFU',
    2: 'Initialize DFU',
    3: 'Receive firmware image',
    4: 'Validate firmware image',
    5: 'Activate firmware and reset',
    6: 'System reset',
    7: 'Request written image size',
    8: 'Request packet receipt notification',
    9: 'Config',
    10: 'Initialize Patch',
    11: 'Receive patch image',
    13: 'Request MTU size',
    16: 'Response',
    17: 'Packet receipt notification',
};

var RESP_SUCCESS = 1;
var RESP_MORE_DATA_NEEDED = 7;
var RESP_PATCH_INPUT_FULL = 8;
var RESPONSES = {
    1: 'success',
    2: 'invalid state',
    3: 'not supported',
    4: 'data size exceeds limit',
    5: 'CRC error',
    6: 'operation failed',
    7: 'patch needs more data',
    8: 'patch input is full'
};

//flag for requesting MTU from device
GET_MTU = false;

// Configuration

// Recieve a notification every Nth firmware packet sent
var FW_NOTIFY_PACKETS = 2;

// Packet size, fixed by FW
var FW_PACKET_SIZE = 20;

// Require a specific BT address for the target
var mac_address = "";

// Implementation

function validate_hex_string(str, numbytes) {
    out = str.replace(/[^0-9a-f]/gi,'').toLowerCase();
    if (out.length != 2 * numbytes)
        errx(1, "Invalid hex argument %s: wanted %d digits, got %d",
             str, 2 * numbytes, out.length);
    return out;
}

var mode_test = false;
var mode_config = false;
var mode_dfu = false;
var mode_patch = false;

var check_version = false;

var hr_time = 0;

commander.
    version('2.0').
    usage('[options] <data.bin>').
    option('-m, --mac <MAC>', 'Only update device with this MAC').
    option('-k, --oldkey <KEY>', 'Configure device: required, if '
           + 'device has a key').
    option('-K, --newkey <KEY>', 'Configure device: change key to KEY').
    option('-M, --newmac <MAC>', 'Configure device: change MAC to MAC').
    option('-t, --test', "Just test connection, don't configure or send image").
    option('-p, --patch', 'Send a patch file instead of a full image').
    option('-s, --sizepacket', 'Request the device MTU, and use that as packet size').
    option('<data.bin>', 'Packed data file to send').
    parse(process.argv);

// Parse MAC address
if (commander.mac) {
    mac_address = parse_hex_string(commander.mac, 6);
    printf("Target address: " + mac_address);
}

if (commander.test) {
    mode_test = true;
}

if (commander.oldkey || commander.newkey || commander.newmac) {
    mode_config = true;

    var old_key = new Buffer(16);
    var new_key = new Buffer(16);
    var new_mac = new Buffer(6);

    if (commander.oldkey) {
        old_key = new Buffer(validate_hex_string(commander.oldkey, 16), 'hex');
        printf("Old device key: %s", old_key.toString('hex'));
    } else {
        old_key.fill(0);
    }

    if (commander.newkey) {
        new_key = new Buffer(validate_hex_string(commander.newkey, 16), 'hex');
        printf("New device key: %s", new_key.toString('hex'));
    } else {
        new_key.fill(0);
    }

    if (commander.newmac) {
        new_mac = new Buffer(validate_hex_string(commander.newmac, 6), 'hex');
        printf("New device MAC: %s", new_mac.toString('hex'));
    } else {
        new_mac.fill(0);
    }

    if (!(commander.newkey || commander.newmac))
        errx(2, "--oldkey should only be specified with --newkey or --newmac")
}


if (commander.args.length >= 1) {
    if(commander.patch)
        mode_patch = true;
    else
        mode_dfu = true;

    if (commander.args.length > 1) {
        commander.outputHelp();
        errx(2, "only one data file, please")
    }

    // Read packed file
    var buf = fs.readFileSync(commander.args[0])

    var patch_key = bitsyntax.matcher('patch_key:12/binary')(buf)

    console.log("check sizepacket flag")
    if (commander.sizepacket){
        console.log("sizepacket set")
        GET_MTU = true;
    }

    // Extract data
    if(commander.patch) {
        var firmware = bitsyntax.matcher(
            'key:16/binary',
            'start_packet:12/binary',
            'init_packet:32/binary',
            'patch_packet:12/binary', 
            'image/binary')(buf)
    } else {
        var firmware = bitsyntax.matcher(
            'start_packet:12/binary',
            'init_packet:32/binary',
            'image/binary')(buf)
    }
    var sizes = bitsyntax.matcher(
        'sd:32/little-unsigned-integer',
        'bl:32/little-unsigned-integer',
        'app:32/little-unsigned-integer')(firmware.start_packet)
    var crypto = bitsyntax.matcher(
        'iv:16/binary',
        'tag:16/binary')(firmware.init_packet)
    if(commander.patch) {
        var patch = bitsyntax.matcher(
            'len:32/little-unsigned-integer',
            'crc:32/little-unsigned-integer',
            'oldcrc:32/little-unsigned-integer')(firmware.patch_packet)
    }

    // Check data
    if (!(sizes.sd || sizes.bl || sizes.app))
        errx(1, "sizes are all zero, no data?");

    if (patch && (sizes.bl || sizes.sd)) {
        errx(1, "only applications can be patched")
    }

    if (sizes.sd) {
        printf("Softdevice: %d bytes", sizes.sd);
        check_version = true
    }
    if (sizes.bl){
        printf("Bootloader: %d bytes", sizes.bl);
        check_version = true
    }

    if (sizes.app)
        printf("Application: %d bytes", sizes.app);
    if (patch)
        printf("Patch: %d bytes", patch.len);

    if(patch && (patch.crc == 0 || patch.oldcrc == 0))
        errx(1, "crc values for patch and old firmare must be available")

    if ((sizes.sd % 4) || (sizes.bl % 4) || (sizes.app % 4))
        errx(1, "sizes must be a multiple of 4");

    if (sizes.app && (sizes.sd || sizes.bl))
        errx(1, "application must be sent by itself");

    if (patch && patch.len != firmware.image.length)
        errx(1, "total patch length %d doesn't match expected %d",
            firmware.image.length, patch.len)

    if (!patch && ((sizes.sd + sizes.bl + sizes.app) != firmware.image.length))
        errx(1, "total image length %d doesn't match expected %d",
             firmware.image.length, sizes.sd + sizes.bl + sizes.app);

    printf(" IV: %s", crypto.iv.toString('hex'));
    printf("Tag: %s", crypto.tag.toString('hex'));
}

// Verify args
if ((mode_test + mode_config + mode_dfu + mode_patch) != 1) {
    commander.outputHelp();
    errx(2, "please specify <data.bin>, one of the config options, or --test")
}

// Start the scanning process
noble.on('stateChange', function(state) {
    if (state === "poweredOn") {
        console.log("Scanning for DFU device...");
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

function checkError(error) {
    if (error !== null && error !== undefined) {
	console.error("Error: %s", error);
	process.exit(1);
    }
}

function unexpectedDisconnect() {
    console.error("Unexpected disconnect!");
    process.exit(1);
}

function onDiscover(peripheral) {
    var adv = peripheral.advertisement;
    var uuids = adv.serviceUuids;

    var bad = "";
    if (uuids && uuids.indexOf(DFU_SERVICE_UUID) < 0 && uuids.indexOf(NEW_DFU_SERVICE_UUID) < 0 )
        bad += " (wrong service)";
    if (adv.localName !== DFU_NAME)
        bad += " (wrong name)";
    if (mac_address && (mac_address !== peripheral.uuid))
        bad += " (wrong address)";
    console.log("Found: name %s, address %s, %s , RSSI %d%s",
		adv.localName, peripheral.uuid, uuids, peripheral.rssi, bad);
    if (bad)
        return; // not our device

    // Once we discover one DFU device, stop looking.
    noble.removeListener('discover', onDiscover);
    noble.stopScanning();

    // Print a message and quit if the device ever disconnects.
    peripheral.on('disconnect', unexpectedDisconnect);

    // Connect
    console.log("Connecting...");
    peripheral.connect(function(error) {
        checkError(error);
	console.log("Discovering services...");
        // This just hangs up sometimes; add a timeout
        timer = setTimeout(function() {
            timer = null;
            console.log("Timed out");
            peripheral.disconnect();
            process.exit(1);
        }, 5000);
        var service_uuids
        var char_uuids

        if(uuids.indexOf(NEW_DFU_SERVICE_UUID) >= 0) {
            service_uuids = [NEW_DFU_SERVICE_UUID, DIS_SERVICE_UUID]
            char_uuids = [NEW_DFU_CONTROL_POINT_UUID, NEW_DFU_PACKET_UUID, DIS_FWREV_UUID]
            control_uuid = NEW_DFU_CONTROL_POINT_UUID
            packet_uuid = NEW_DFU_PACKET_UUID
        } else {
            service_uuids = [DFU_SERVICE_UUID, DIS_SERVICE_UUID]
            char_uuids =  [DFU_CONTROL_POINT_UUID, DFU_PACKET_UUID, DIS_FWREV_UUID]
            control_uuid = DFU_CONTROL_POINT_UUID
            packet_uuid = DFU_PACKET_UUID
        }
        peripheral.discoverSomeServicesAndCharacteristics(
            service_uuids, char_uuids, function(error, services, characteristics) {
                if (!timer)
                    return;
                clearTimeout(timer);
		        checkError(error);
                var chars = {};
                for (var i = 0; i < characteristics.length; i++) {
                    chars[characteristics[i].uuid] = characteristics[i];
                    console.log(characteristics[i].uuid)
                }
                if (!(char_uuids[0] in chars) ||
                    !(char_uuids[1] in chars)) {
                    console.log("Device is missing DFU characteristics! %s", char_uuids);
                    process.exit(1);
                }

                async.series([
                    function(callback) {
                        printRevision(peripheral, chars, callback);
                    },
                    function(callback) {

                        if(check_version) {
                            checkVersion(peripheral, chars, callback)
                        } else {
                            callback()
                        }
                    },
                    function(callback) {
                        if (mode_test) {
                            performTest(peripheral, chars);
                        } else if (mode_config) {
                            performConfigure(peripheral, chars);
                        } else if (mode_dfu) {
                            hr_time = process.hrtime();
                            performDFU(peripheral, chars);
                        } else if (mode_patch) {
                            hr_time = process.hrtime();
                            performDFUPatch(peripheral, chars);
                        }
                    }]);
            });
    });
}

function disconnectWithMessage(peripheral, message, shouldExit, exitCode)
{
    peripheral.removeListener('disconnect', unexpectedDisconnect);
    peripheral.on('disconnect', function() {
        console.log(message);

        shouldExit = (shouldExit || false);
        exitCode = (exitCode || 0);
        if(shouldExit) {
            process.exit(exitCode);
        }
    });
    peripheral.disconnect();
}

function formatResponse(data) {
    var dstr = data.toString('hex');
    if (data[0] === OP_PKT_RCPT_NOTIF) {
        return "packet receipt notification: " + dstr.slice(2);
    } else if (data[0] === OP_RESPONSE && data.length >= 3) {
        var op = util.format("(unknown op %d)", data[1]);
        if (data[1] in OPS) {
            op = OPS[data[1]];
        }
        var resp = util.format("(unknown response %d)", data[2]);
        if (data[2] in RESPONSES) {
            resp = RESPONSES[data[2]];
        }
        return "response to \"" + op + "\": " + resp + " " + dstr.slice(6);
    } else {
        return "unknown response: " + dstr;
    }
}

function printRevision(peripheral, chars, callback) {
    if (DIS_FWREV_UUID in chars) {
        chars[DIS_FWREV_UUID].read(function(error, data) {
            // Ignore errors; missing FW revision is OK
            if (data) {
                console.log(
                    "Bootloader firmware revision: " +
                        data.toString('ascii'));
            }
            callback();
        });
    } else {
        callback();
    }
}

//This function ensures that a Bootloader or SoftDevice update is
//not attempted on RigDFU v3.2.1. 
function checkVersion(peripheral, chars, callback)
{
    if (DIS_FWREV_UUID in chars) {
        chars[DIS_FWREV_UUID].read(function(error, data) {
            // Ignore errors; missing FW revision is OK
            if (data) {
                var version = data.toString('ascii');
                if(version.indexOf('3.2.1') != -1) {
                    disconnectWithMessage(peripheral, 
                        'RigDFU v3.2.1 cannot be updated as a direct bootloader update.  See Errata information in Release Notes.',
                        true, 0)
                } else {
                    callback();
                }
            }
            else
            {
                disconnectWithMessage(peripheral, 'Could not verify RigDFU version for update!');
            }
        });
    } else {
        disconnectWithMessage(peripheral, 'Could not verify RigDFU version for update!');
    }
}

function performTest(peripheral, chars) {
    console.log("Test mode; disconnecting.");
    peripheral.removeListener('disconnect', unexpectedDisconnect);
    peripheral.on('disconnect', function() {
        process.exit(0);
    });
    peripheral.disconnect();
}

function performConfigure(peripheral, chars) {
    control = chars[control_uuid];
    packet = chars[packet_uuid];

    // Set up a handler for received data
    rxCallbackQueue = [];
    control.on('read', function(data, isNotification) {
        if (rxCallbackQueue.length === 0) {
            // If no callbacks have been registered, just print it out.
            console.log("unhandled " + formatResponse(data));
            return;
        }
        // Otherwise, call the next registered callback.  This is a
        // pretty simple model that just assumes we're waiting for one
        // response at a time and that they'll come in order.
        var callback = rxCallbackQueue.shift();
        callback(data);
    });

    async.series([
        function(callback) {
            console.log("Enabling notifications...");
            control.notify(true, callback);
        },
        function(callback) {
            console.log("Sending configuration packet...");
            var buf = new Buffer(1);
            buf.writeUInt8(OP_CONFIG, 0);
            control.write(buf, false, function(err) {
                checkError(err);

                // Packet interface is now expecting the config data:
                // 16 byte old key, 16 byte new key, 6 byte mac, 10 zeros
                var config_packet = new Buffer(48+44);
                config_packet.fill(0x00);
                old_key.copy(config_packet, 0+44);
                new_key.copy(config_packet, 16+44);
                new_mac.copy(config_packet, 32+44);

                // Send it in 3 16-byte chunks.  We'll get a response
                // to the last one one, after the config gets flashed.
                config1 = config_packet.slice(0, 12);
                config2 = config_packet.slice(12, 28);
                config3 = config_packet.slice(28, 44);
                config4 = config_packet.slice(44, 60);
                config5 = config_packet.slice(60, 76);
                config6 = config_packet.slice(76, 92);

                packet.write(config1, false, function(err) {
                    checkError(err);
                    packet.write(config2, false, function(err) {
                        checkError(err);
                        packet.write(config3, false, function(err) {
                            checkError(err);
                            packet.write(config4, false, function(err) {
                                checkError(err);
                                packet.write(config5, false, function(err) {
                                    // We'll get a response after the last packet
                                    rxCallbackQueue.push(function(data) {
                                        if (data[0] !== OP_RESPONSE ||
                                            data[1] !== OP_CONFIG ||
                                            data[2] !== RESP_SUCCESS) {
                                            callback("Bad response: " +
                                                     formatResponse(data));
                                            return;
                                        }
                                        callback();
                                    });
                                    packet.write(config6, false, checkError);
                                });
                            });
                        });
                    });
                });                
            });
        },
    ], function(err) {
        // Callback for when the async.series completes, or hits an error.
        var exitcode;
        if (err) {
            exitcode = 1;
            console.error("Error:", err);
        } else {
            exitcode = 0;
            console.log("Successfully reconfigured!");
        }
        console.log("Resetting and disconnecting...");
	peripheral.removeListener('disconnect', unexpectedDisconnect);
        peripheral.on('disconnect', function() {
            if (exitcode === 0)
                console.log("Done!");
            process.exit(exitcode);
        });
        var buf = new Buffer(1);
        buf.writeUInt8(OP_SYSTEM_RESET, 0);
        control.write(buf, false, function(err) {
            if (exitcode == 0)
                checkError(err);
            peripheral.disconnect();
        });
    });
}

function performDFU(peripheral, chars) {
    control = chars[control_uuid];
    packet = chars[packet_uuid];

    // Set up a handler for received data
    rxCallbackQueue = [];
    control.on('read', function(data, isNotification) {
        if (rxCallbackQueue.length === 0) {
            // If no callbacks have been registered, just print it out.
            console.log("unhandled " + formatResponse(data));
            return;
        }
        // Otherwise, call the next registered callback.  This is a
        // pretty simple model that just assumes we're waiting for one
        // response at a time and that they'll come in order.
        console.log("notify")
        var callback = rxCallbackQueue.shift();
        callback(data);
    });

    async.series([
        function(callback) {
            console.log("Enabling notifications...");
            console.log(callback.name)
            control.notify(true, callback);
        },
        function(callback) {
            console.log("Subscribing to packet receipt notifications...");
            var buf = new Buffer(3);
            buf.writeUInt8(OP_REQ_PKT_RCPT_NOTIF, 0);
            buf.writeUInt16LE(FW_NOTIFY_PACKETS, 1);
            control.write(buf, false, callback);
        },
        function(callback) {
            if(GET_MTU){
                console.log("Requesting MTU Size...");
                var buf = new Buffer(1);
                buf.writeUInt8(OP_MTU_REQUEST, 0);
                control.write(buf, false, function(err){
                    checkError(err);
                    rxCallbackQueue.push(function(data){
                        if(data[0] !== OP_RESPONSE ||
                           data[1] !== OP_MTU_REQUEST ||
                           data[2] < 20){                            
                            console.log("Bad response: " + formatResponse(data));
                            console.log("MTU Size = 20");
                        }
                        else{
                            //round the byte down to the nearest multiple of 4
                            FW_PACKET_SIZE = data[2] &= ~3;
                            console.log("MTU Size = %d", FW_PACKET_SIZE)
                        }
                        callback();
                    });
                });
            }
            else{
                callback();
            }
        },
        function(callback) {
            console.log("Start DFU...");
            var buf = new Buffer(1);
            buf.writeUInt8(OP_START_DFU, 0);
            control.write(buf, false, function(err) {
                checkError(err);
                // Packet interface is now expecting the start
                // packet, containing image sizes.
                rxCallbackQueue.push(function(data) {
                    if (data[0] !== OP_RESPONSE ||
                        data[1] !== OP_START_DFU ||
                        data[2] !== RESP_SUCCESS) {
                        callback("Bad response: " + formatResponse(data));
                        return;
                    }
                    //console.log(data);
                    callback();
                });
                //console.log(firmware.start_packet)
                console.log(firmware.start_packet);
                packet.write(firmware.start_packet, false, checkError);
            });
        },
        function(callback) {
            console.log("Initialize DFU...");
            var buf = new Buffer(1);
            buf.writeUInt8(OP_INITIALIZE_DFU, 0);
            control.write(buf, false, function(err) {
                checkError(err);
                // Packet interface is now expecting the "init packet".
                // It won't fit in one chunk, so send as two
                // (the first one will have no response)
                init1 = firmware.init_packet.slice(0, 16);
                init2 = firmware.init_packet.slice(16, 32);
                console.log("Sending IV and tag...");
                //console.log(init1);
                
                    packet.write(init1, false, function() {
                        //console.log(init2);
                        checkError(err);
                        // Response to second packet only
                        rxCallbackQueue.push(function(data) {
                            if (data[0] !== OP_RESPONSE ||
                                data[1] !== OP_INITIALIZE_DFU ||
                                data[2] !== RESP_SUCCESS) {
                                callback("Bad response: " + formatResponse(data));
                                return;
                            }
                            console.log(data)
                            callback();
                        });
                        packet.write(init2, false, checkError);
                    });
                });
        },
        function(callback) {
            console.log("Sending firmware image...");
            var buf = new Buffer(1);
            buf.writeUInt8(OP_RECEIVE_FIRMWARE_IMAGE, 0);
            control.write(buf, false, function(err) {
                checkError(err);
                // Packet interface is now expecting
                // FW_PACKET_SIZE-byte blocks of the firmware image.
                // After every FW_NOTIFY_PACKETS, we'll get a
                // notification back.
                image = firmware.image
                total_blocks = Math.ceil(image.length / FW_PACKET_SIZE);
                var block = 0;
                var bytes_sent = 0;
                var bytes_acked = 0;
                function printStatus() {
                    process.stdout.write(sprintf(
                        "Block: %d/%d | Bytes: %d sent, %d acknowledged\r",
                        block+1, total_blocks, bytes_sent, bytes_acked));
                }
                printStatus();
                async.whilst(
                    function() { return block < total_blocks; },
                    function(cb) {
                        function loop(err) {
                            checkError(err);
                            printStatus();
                            block++;
                            cb();
                        }
                        var chunk_start = block * FW_PACKET_SIZE;
                        var chunk_end = Math.min(chunk_start + FW_PACKET_SIZE,
                                                 image.length);
                        var chunk = image.slice(chunk_start, chunk_end);

                        bytes_sent += chunk.length;
                        var isComplete = ((block+1)==total_blocks);
                        var expectNotify = (((block+1)%FW_NOTIFY_PACKETS)==0);
                        if (expectNotify && !isComplete) {
                            // Expect a notification response to this one
                            rxCallbackQueue.push(function(data) {
                                if (data[0] !== OP_PKT_RCPT_NOTIF ||
                                    data.length !== 5) {
                                    console.log(data)
                                    cb("Bad response: " + formatResponse(data));
                                }
                                bytes_acked = data.readUInt32LE(1);
                                loop();
                            });
                            packet.write(chunk, false, checkError)
                        } else if (isComplete) {
                            // Expect a response to the completion
                            rxCallbackQueue.push(function(data) {
                                if (data[0] !== OP_RESPONSE ||
                                    data[1] !== OP_RECEIVE_FIRMWARE_IMAGE ||
                                    data[2] !== RESP_SUCCESS)
                                    cb("Bad response: " + formatResponse(data));
                                bytes_acked = bytes_sent;
                                loop();
                            });
                            packet.write(chunk, false, checkError);
                        } else {
                            // No response to this one
                            packet.write(chunk, true, loop);
                        }
                    },
                    function(err) {
                        process.stdout.write("\n");
                        checkError(err);
                        callback();
                    });
            });
        },
        function(callback) {
            console.log("Validating firmware image...");
            var buf = new Buffer(1);
            buf.writeUInt8(OP_VALIDATE_FIRMWARE_IMAGE, 0);
            rxCallbackQueue.push(function(data) {
                if (data[0] !== OP_RESPONSE ||
                    data[1] !== OP_VALIDATE_FIRMWARE_IMAGE ||
                    data[2] !== RESP_SUCCESS) {
                    callback("Bad response: " + formatResponse(data));
                    return;
                }
                callback();
            });
            control.write(buf, false, checkError);
        },
    ], function(err) {
        // Callback for when the async.series completes, or hits an error.
        var exitcode;
        var buf = new Buffer(1);
        if (err) {
            exitcode = 1;
            console.error("Error:", err);
            console.log("Resetting and disconnecting.");
            buf.writeUInt8(OP_SYSTEM_RESET, 0);
        } else {
            exitcode = 0;
            console.log("Activating new firmware image and disconnecting...");
            buf.writeUInt8(OP_ACTIVATE_FIRMWARE_AND_RESET, 0);
            var hrend = process.hrtime(hr_time);
            console.log("Update Time: %ds %dms", hrend[0], hrend[1]/1000000)
        }
	peripheral.removeListener('disconnect', unexpectedDisconnect);
        peripheral.on('disconnect', function() {
            if (exitcode === 0)
                console.log("Done!");
            process.exit(exitcode);
        });
        control.write(buf, false, function(err) {
            if (exitcode == 0)
                checkError(err);
            peripheral.disconnect();
        });
    });
}

function performDFUPatch(peripheral, chars) {
    control = chars[control_uuid];
    packet = chars[packet_uuid];

    // Set up a handler for received data
    rxCallbackQueue = [];
    control.on('read', function(data, isNotification) {
        if (rxCallbackQueue.length === 0) {
            // If no callbacks have been registered, just print it out.
            console.log("unhandled " + formatResponse(data));
            return;
        }
        // Otherwise, call the next registered callback.  This is a
        // pretty simple model that just assumes we're waiting for one
        // response at a time and that they'll come in order.
        //console.log("notify")
        var callback = rxCallbackQueue.shift();
        callback(data);
    });

    async.series([
        function(callback) {
            console.log("Enabling notifications...");
            console.log(callback.name)
            control.notify(true, callback);
        },
        function(callback) {
            if(GET_MTU){
                console.log("Requesting MTU Size...");
                var buf = new Buffer(1);
                buf.writeUInt8(OP_MTU_REQUEST, 0);
                control.write(buf, false, function(err){
                    checkError(err);
                    rxCallbackQueue.push(function(data){
                        if(data[0] !== OP_RESPONSE ||
                           data[1] !== OP_MTU_REQUEST ||
                           data[2] < 20){                            
                            console.log("Bad response: " + formatResponse(data));
                            console.log("MTU Size = 20");
                        }
                        else{
                            //round the byte down to the nearest multiple of 4
                            FW_PACKET_SIZE = data[2] &= ~3;
                            console.log("MTU Size = %d", FW_PACKET_SIZE)
                        }
                        callback();
                    });
                });
            }
            else{
                callback();
            }
        },
        function(callback) {
            console.log("Start DFU...");
            var buf = new Buffer(1);
            buf.writeUInt8(OP_START_DFU, 0);
            control.write(buf, false, function(err) {
                checkError(err);
                // Packet interface is now expecting the start
                // packet, containing image sizes.
                rxCallbackQueue.push(function(data) {
                    if (data[0] !== OP_RESPONSE ||
                        data[1] !== OP_START_DFU ||
                        data[2] !== RESP_SUCCESS) {
                        callback("Bad response: " + formatResponse(data));
                        return;
                    }
                    //console.log(data);
                    callback();
                });
                //console.log(firmware.start_packet)
                console.log(firmware.start_packet);
                packet.write(firmware.start_packet, false, checkError);
            });
        },
        function(callback) {
            console.log("Initialize DFU...");
            var buf = new Buffer(1);
            buf.writeUInt8(OP_INITIALIZE_DFU, 0);
            control.write(buf, false, function(err) {
                checkError(err);
                // Packet interface is now expecting the "init packet".
                // It won't fit in one chunk, so send as two
                // (the first one will have no response)
                init1 = firmware.init_packet.slice(0, 16);
                init2 = firmware.init_packet.slice(16, 32);
                console.log("Sending IV and tag...");
                //console.log(init1);
                
                    packet.write(init1, false, function() {
                        //console.log(init2);
                        checkError(err);
                        // Response to second packet only
                        rxCallbackQueue.push(function(data) {
                            if (data[0] !== OP_RESPONSE ||
                                data[1] !== OP_INITIALIZE_DFU ||
                                data[2] !== RESP_SUCCESS) {
                                callback("Bad response: " + formatResponse(data));
                                return;
                            }
                            console.log(data)
                            callback();
                        });
                        packet.write(init2, false, checkError);
                    });
                });
        },
        function(callback) {
            console.log("Initialize Patch...");
            var buf = new Buffer(1);
            buf.writeUInt8(OP_PATCH_INIT, 0);
            control.write(buf, false, function(err) {
                checkError(err);

                rxCallbackQueue.push(function(data) {
                    console.log(data);
                    if (data[0] !== OP_RESPONSE ||
                        data[1] !== OP_PATCH_INIT ||
                        data[2] !== RESP_SUCCESS) {
                        callback("Bad response: " + formatResponse(data));
                        return;
                    }
                    
                    callback();
                });
                
                // Packet interface is now expected the "patch init packet".
                console.log(firmware.patch_packet);
                packet.write(firmware.patch_packet, false, checkError);
            });
        },
        function(callback) {
            console.log("Sending patch image...");
            var buf = new Buffer(1);
            buf.writeUInt8(OP_RECEIVE_PATCH_IMAGE, 0);
            control.write(buf, false, function(err) {
                checkError(err);
                // Packet interface is now expecting
                // FW_PACKET_SIZE-byte blocks of the firmware image.
                // After every FW_NOTIFY_PACKETS, we'll get a
                // notification back.
                image = firmware.image
                console.log(image.length)
                total_blocks = Math.ceil(image.length / FW_PACKET_SIZE);
                var block = 0;
                var bytes_sent = 0;
                var bytes_acked = 0;
                function printStatus() {
                    process.stdout.write(sprintf(
                        "Block: %d/%d | Bytes: %d sent, %d acknowledged\r",
                        block+1, total_blocks, bytes_sent, bytes_acked));
                }
                //printStatus();
                async.whilst(
                    function() { return block < total_blocks; },
                    function(cb) {
                        function loop(err) {
                            checkError(err);
                            printStatus();
                            block++;
                            cb();
                        }
                        var chunk_start = block * FW_PACKET_SIZE;
                        var chunk_end = Math.min(chunk_start + FW_PACKET_SIZE,
                                                 image.length);
                        var chunk = image.slice(chunk_start, chunk_end);

                        bytes_sent += chunk.length;
                        var isComplete = ((block + 1) == total_blocks);
                        if(!isComplete) {
                            rxCallbackQueue.push(function(data) {
                                if (data[0] == OP_RESPONSE &&
                                    data[1] == OP_RECEIVE_PATCH_IMAGE) {
                                    if(data[2] == RESP_MORE_DATA_NEEDED) {
                                        bytes_acked = bytes_sent;
                                        loop();
                                    } else if(data[2] == RESP_PATCH_INPUT_FULL) {
                                        //do something about this
                                    } else if(data[2] = RESP_SUCCESS) {
                                        isComplete = true;
                                        bytes_acked = bytes_sent;
                                        loop();
                                    } else {
                                        cb("Bad response: " + formatResponse(data));
                                    }
                                } else {
                                    cb("Bad response: " + formatResponse(data));
                                } 
                            });
                            packet.write(chunk, false, checkError);
                        } else {
                            rxCallbackQueue.push(function(data) {
                                if (data[0] == OP_RESPONSE &&
                                    data[1] == OP_RECEIVE_PATCH_IMAGE) {
                                        if(data[2] == RESP_SUCCESS) {
                                            bytes_acked = bytes_sent;
                                            loop();
                                        } else if(data[2] == RESP_MORE_DATA_NEEDED) {
                                            cb("Bad response: " + formatResponse(data));
                                        }
                                }
                            });
                            packet.write(chunk, false, checkError);
                        }
                    },
                    function(err) {
                        process.stdout.write("\n");
                        checkError(err);
                        callback();
                    });
            });
        },
        function(callback) {
            console.log("Validating firmware image...");
            var buf = new Buffer(1);
            buf.writeUInt8(OP_VALIDATE_FIRMWARE_IMAGE, 0);
            rxCallbackQueue.push(function(data) {
                console.log(data)
                if (data[0] !== OP_RESPONSE ||
                    data[1] !== OP_VALIDATE_FIRMWARE_IMAGE ||
                    data[2] !== RESP_SUCCESS) {
                    callback("Bad response: " + formatResponse(data));
                    return;
                }
                callback();
            });
            control.write(buf, false, checkError);
        },
    ], function(err) {
        // Callback for when the async.series completes, or hits an error.
        var exitcode;
        var buf = new Buffer(1);
        if (err) {
            exitcode = 1;
            console.error("Error:", err);
            console.log("Resetting and disconnecting.");
            buf.writeUInt8(OP_SYSTEM_RESET, 0);
        } else {
            exitcode = 0;
            console.log("Activating new firmware image and disconnecting...");
            buf.writeUInt8(OP_ACTIVATE_FIRMWARE_AND_RESET, 0);
            var hrend = process.hrtime(hr_time);
            console.log("Update Time: %ds %dms", hrend[0], hrend[1]/1000000)
        }
    peripheral.removeListener('disconnect', unexpectedDisconnect);
        peripheral.on('disconnect', function() {
            if (exitcode === 0)
                console.log("Done!");
            process.exit(exitcode);
        });
        control.write(buf, false, function(err) {
            if (exitcode == 0)
                checkError(err);
            peripheral.disconnect();
        });
    });
}