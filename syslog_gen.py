"""
RFC 5424-compliant Syslog generator useful for testing.
"""

import argparse
import time
import logging
from logging.handlers import SysLogHandler
from datetime import datetime, timezone
import numpy as np
from random import choices
from string import ascii_lowercase, ascii_uppercase, digits

# Allowed priority levels for SysLogHandler's RootLogger
PRIORITY_LEVELS = ["info", "error", "warning", "critical", "debug"]
# Some made up hostnames
HOSTNAMES = ["woodmicrosystems.net", "losslessnetworks.io",
             "unauthenticatedcomms.com", "physicalvirtualmachines.com",
             "desktopserverz.net", "legacymethodologies.com",
             "backwardsbenchmarks.com"]

# Some common unix programs/processes
PROCESSES = ["batch", "chmod", "chown", "cp", "dd", "echo", "find", "grep",
             "id", "kill", "make", "nc", "ps", "rm", "sh"]


# Generate RFC 3339 compatible timestamp (used in RFC 5424)
def gen_timestamp():
   local_time = datetime.now(timezone.utc).astimezone()
   return local_time.isoformat()


# Generate a random hostname
def gen_hostname():
   # Helper function to generate a random IP
   def random_ip():
      return ".".join(map(str, (np.random.randint(0, 255)
                                for _ in range(4))))
   # Choose randomly between an IP or one of predefined hostnames
   return np.random.choice([random_ip(),
                            np.random.choice(HOSTNAMES)])


# Generate a random structured data container
def gen_sd():
   sd_string = "-"
   # Hacky way to say that in 33% of cases, we don't want to generate SD
   if np.random.random() < 0.3333:
      return sd_string

   # Generate up to 3 SD elements
   for i in range(np.random.randint(1, 4)):
      random_sdid = "exampleSDID@" + str(np.random.choice(range(10000, 99999)))
      sd_string = "[{0} ".format(random_sdid)
      # Allow for multiple parameters (up to 3)
      for _ in range(np.random.randint(1, 4)):
         # Generate a random param-name
         random_pname = ''.join(choices(ascii_lowercase,
                                        k=choices(range(3, 11))[0]))
         # Generate a random param-value
         random_pval = ''.join(choices(ascii_lowercase + ascii_uppercase + digits,
                                       k=choices(range(1, 11))[0]))
         sd_string += "{0}=\"{1}\" ".format(random_pname, random_pval)
      # Close the SD element (and remove the trailing whitespace)
      sd_string = sd_string[:-1] + "]"
   return sd_string


# Some fields may be left unspecified in the syslog
#  This function will output a NILVALUE for 33% of inputs (where applicable)
def possibly_undefined(input_val):
   return input_val if np.random.random() > 0.3333 else "-"


# Randomly make the content of a log
def create_random_log(logger, log_handler):
   # Randomize some fields
   time_output = gen_timestamp()
   # Generate a random hostname
   random_hostname = possibly_undefined(gen_hostname())
   # Generate random process name / process ID
   random_pname = possibly_undefined(np.random.choice(PROCESSES))
   random_pid = possibly_undefined(np.random.choice(range(500, 9999)))
   # Generate random message id
   random_msgid = possibly_undefined("ID" + str(np.random.choice(range(10, 999))))
   # Generate random structured data container
   random_sd = gen_sd()
   # Optionally generate a gibberish message string (50% chance)
   if np.random.random() > 0.5:
      random_msg = ''.join(choices(ascii_lowercase + ascii_uppercase + digits,
                                   k=choices(range(10, 30))[0]))
   else: random_msg = ""

   log_format = logging.Formatter(
      ('1 %(date_field)s %(host_field)s '
       '%(pname_field)s %(pid_field)s '
       '%(msgid_field)s %(sd_field)s '
       '%(msg_field)s\r\n'
       )
   )
   log_handler.setFormatter(log_format)

   extra_fields = {'date_field': time_output,
                   'host_field': random_hostname,
                   'pname_field': random_pname,
                   'pid_field': random_pid,
                   'msgid_field': random_msgid,
                   'sd_field': random_sd,
                   'msg_field': random_msg
                   }

   # All priority levels from RFC 5424 are not supported - using custom list
   random_priority = np.random.choice(PRIORITY_LEVELS)
   # All facility levels are supported - using a list from SysLogHandler
   random_facility = np.random.choice(list(log_handler.facility_names.keys()))
   log_handler.facility = random_facility
   # Set the log content
   #   Equal to logger.`random_priority`(random_msg, extra=fields)
   getattr(logger, random_priority)(random_msg, extra=extra_fields)

   # Confirm in stdout
   print("> log sent @", time_output)

   return logger, log_handler


# Send syslog message
def send_syslog():
   # Initialize SysLogHandler
   logger = logging.getLogger()
   # Logging level has to be set but we don't really care about its value
   logger.setLevel(logging.NOTSET)
   # Specify where the messages are being sent
   syslog = SysLogHandler(address=(args.h, args.p))
   logger.addHandler(syslog)

   # Loop specified amount of times
   for _ in range(args.c):
      logger, syslog = create_random_log(logger, syslog)

   logger.removeHandler(syslog)
   syslog.close()


if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("--h", required=True, help="Target hostname")
   parser.add_argument("--p", required=True, type=int, help="Target port")
   parser.add_argument("--c", type=int, default=10, help="Number of messages")
   parser.add_argument("--d", type=int, help="Delay in seconds")
   args = parser.parse_args()

   print("Target: %s:%d" % (args.h, args.p))
   print(" (for localhost, run"
         " `nc -lvuk %d -w %d` to listen to the logs)\n" % (args.p, args.d))

   # Setting delay means that we want to send messages indefinitely
   if args.d:
      print("Sending %d message(s) every %d seconds..." % (args.c, args.d))
      try:
         # Loop infinitely
         while True:
            send_syslog()
            time.sleep(args.d)
      # Stop by pressing ^C
      except KeyboardInterrupt:
         print("Stopping...")
   else:
      print("Sending %d messages..." % args.c)
      send_syslog()
