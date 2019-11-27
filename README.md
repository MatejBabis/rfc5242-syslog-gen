#RFC 5424-compliant Syslog generator

A script that generates random `syslog` messages adhering to the [RFC 5242](https://tools.ietf.org/html/rfc5424) standard.

### Description

The script generates random log messages that can be used for testing, including hostnames, process names, structured data containers etc. It then proceeds to transmit such logs (once or periodically) via UDP to a host of choice.

### Requirements

The script is developed in Python 3 and with the only dependency being NumPy.

### Tutorial

The user can specify 4 arguments:
* `--h`: hostname of the recipient
* `--p`: port on which the host is listening
* `--c`: number of messages to be transmitted at once
* `--d`: delay (periodicity) in seconds, for when the transmission should be indefinite

There are two main ways of creating logs: one-time generation or periodic:
1. `$ python3 syslog_gen.py --h 127.0.0.1 --p 9234 --c 20`
2. `$ python3 syslog_gen.py --h 127.0.0.1 --p 9234 --c 1 --d 1`
