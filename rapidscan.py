#!/usr/bin/python
#                               __         __
#                              /__)_   '_/(  _ _
#                             / ( (//)/(/__)( (//)
#                                  /
#
# Author:      Shankar Damodaran
# Tool:        RapidScan
# Usage: .     /rapidscan.py target.com
# Description: This scanner automates the process of security scanning by using a 
#              multitude of available linux security tools and some custom scripts. 
#

# Importing the libraries
import sys
import socket
import subprocess
import os
import time
import threading
import collections

# Initializing the color module class
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    CLEARLINE = '\033[F'


# Initiliazing the idle loader/spinner class
class Spinner:
    busy = False
    delay = 0.05

    @staticmethod
    def spinning_cursor():
        while 1: 
            for cursor in '|/-\\': yield cursor

    def __init__(self, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay): self.delay = delay

    def spinner_task(self):
        while self.busy:
            sys.stdout.write(next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write('\b')
            sys.stdout.flush()

    def start(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def stop(self):
        self.busy = False
        time.sleep(self.delay)
# End ofloader/spinner class        

# Instantiating the spinner/loader class
spinner = Spinner()

# Scanners that will be used 
tool_names = [
              ("host","Host - Checks for existence of IPV6 address."),
              ("aspnet_config_err", "ASP.Net Misconfiguration - Checks for ASP.Net Misconfiguration."),
              ("wp_check","WordPress Check - Checks for WordPress Installation."),
              ("drp_check", "Drupal Check - Checks for Drupal Installation."),
              ("joom_check", "Joomla Check - Checks for Joomla Installation."),
              ("uniscan","Uniscan - Checks for robots.txt & sitemap.xml"),
              ("wafw00f","Wafw00f - Checks for Application Firewalls."),
              ("nmap","NMap - Fast Scan (Only Few Port Checks)"),
              ("theharvester","The Harvester - Scans for emails using Google's passive search."),
              ("fierce","Fierce - Attempts Zone Transfer (No Brute Forcing)"),
              ("dnswalk","DNSWalk - Attempts Zone Transfer."),
              ("whois","WHOis - Checks for Administrator's Contact Information."),
              ("nmap_header","NMap (XSS Filter Check) - Checks if XSS Protection Header is present."),
              ("nmap_sloris","NMap (Slowloris DoS) - Checks for Slowloris Denial of Service Vulnerability."),
              ("sslyze","SSLyze - Checks only for Heartbleed vulnerability,"),
              ("nmap_hbleed","NMap (Heartbleed) - Checks only for Heartbleed vulnerability,"),
              ("nmap_poodle","NMap (POODLE) - Checks only for Poodle vulnerability,"),
              ("nmap_ccs","NMap (OpenSSL CCS Injection) - Checks only for CCS Injection."),
              ("nmap_freak","NMap (FREAK) - Checks only for FREAK vulnerability."),
              ("lbd","LBD - Checks for DNS/HTTP Load Balancers.")
             ]

# Making the dictionary ordered (as it is)           
tool_names = collections.OrderedDict(tool_names)

# Command that is used to initiate the tool (with parameters and extra params)
tool_cmd   = [
                ("host",""),
                ("wget -O temp_aspnet_config_err","/%7C~.aspx"),
                ("wget -O temp_wp_check","/wp-admin"),
                ("wget -O temp_drp_check","/user"),
                ("wget -O temp_joom_check","/administrator"),
                ("uniscan -e -u",""),
                ("wafw00f",""),
                ("nmap -F --open",""),
                ("theharvester -l 50 -b google -d",""),
                ("fierce -wordlist xxx -dns",""),
                ("dnswalk -d","."),
                ("whois",""),
                ("nmap -p80 --script http-security-headers",""),
                ("nmap -p80,443 --script http-slowloris --max-parallelism 500",""),
                ("sslyze --heartbleed",""),
                ("nmap -p 443 --script ssl-heartbleed",""),
                ("nmap -p 443 --script ssl-poodle",""),
                ("nmap -p 443 --script ssl-ccs-injection",""),
                ("nmap -p 443 --script ssl-enum-ciphers",""),
                ("lbd","")
             ]

# Making the dictionary ordered (as it is)           
tool_cmd = collections.OrderedDict(tool_cmd)

# Tool test conditions
tool_cond = [
                "has IPv6",
                "Server Error",
                "wp-login",
                "drupal",
                "joomla",
                "[+]",
                "No WAF",
                "tcp open",
                "No emails found",
                "Whoah, it worked",
                "0 failures",
                "Admin Email:",
                "XSS filter is disabled",
                "vulnerable",
                "Server is vulnerable to Heartbleed",
                "vulnerable",
                "vulnerable",
                "vulnerable",
                "vulnerable",
                "does NOT use Load-balancing"
            ]

# Tool positive response
tool_pos = [
                "[+] Has an IPv6 Address.",
                "[+] No Misconfiguration Found.",
                "[+] No WordPress Installation Found.",
                "[+] No Drupal Installation Found.",
                "[+] No Joomla Installation Found.",
                "[+] robots.txt/sitemap.xml not found.",
                "[+] Web Application Firewall Detected.",
                "[+] Common Ports are Closed.",
                "[+] No Email Addresses Found.",
                "[+] Zone Transfer using fierce Failed.",
                "[+] Zone Transfer using dnswalk Failed.",
                "[+] Whois Information Hidden.",
                "[+] XSS Protection Filter is Enabled.",
                "[+] Not Vulnerable to Slowloris Denial of Service.",
                "[+] Not Prone to HEARTBLEED Vulnerability.",
                "[+] Not Prone to HEARTBLEED Vulnerability.",
                "[+] Not Prone to POODLE Vulnerability.",
                "[+] Not Prone to OpenSSL CCS Injection.",
                "[+] Not Prone to FREAK Vulnerability.",
                "[+] Load Balancer(s) Detected."
           ]

# Tool negative response
tool_neg = [
                "[-] Does not have an IPv6 Address. It is good to have one.",
                "[-] ASP.Net is misconfigured to throw server stack errors on screen.",
                "[-] WordPress Installation Found. Check for vulnerabilities corresponds to that version.",
                "[-] Drupal Installation Found. Check for vulnerabilities corresponds to that version.",
                "[-] Joomla Installation Found. Check for vulnerabilities corresponds to that version.",
                "[-] robots.txt/sitemap.xml found. Check those files for any information.",
                "[-] No Web Application Firewall Detected",
                "[-] Some ports are open. Perform a full-scan manually.",
                "[-] Few email addresses found.",
                "[-] Zone Transfer Successful using fierce. Reconfigure DNS immediately.",
                "[-] Zone Transfer Successful using dnswalk. Reconfigure DNS immediately.",
                "[-] Whois Information Publicly Available.",
                "[-] XSS Protection Filter is Disabled.",
                "[-] Vulnerable to Slowloris Denial of Service.",
                "[-] HEARTBLEED Vulnerability Found.",
                "[-] HEARTBLEED Vulnerability Found.",
                "[-] POODLE Vulnerability Detected.",
                "[-] OpenSSL CCS Injection Detected.",
                "[-] FREAK Vulnerability Detected.",
                "[-] No DNS/HTTP based Load Balancers Found."
           ]

# Tool Opcode (If pos fails and you still want to check for another condition)
tool_opcode = [1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0]

tool = 0

# For accessing tool_cmd dictionary elements
arg1 = 0
arg2 = 1




if len(sys.argv)<=0 :
    print "[-] Program needs atleast one argument, try again. Quitting now..."
    sys.exit(1)
else:
    target = sys.argv[1]
    
    if target == '--update':
        print "RapidScan is updating.. Please wait..."
        spinner.start()
        os.system('wget -N https://raw.githubusercontent.com/skavngr/rapidscan/master/rapidscan.py -O rapidscan.py > /dev/null 2>&1')
        spinner.stop()
        print "RapidScan updated to latest version."
        # Do the thing
    elif target == '--help':
        print "Information:"
        print "------------"
        print "./rapidscan.py --update: Updates the scanner to the latest version."
        print "./rapidscan.py --help:   Displays this help context."
        # Do the other thing
    else:
    
        os.system('rm te*') # Clearing previous scan files
        os.system('clear')
        os.system('setterm -cursor off')
        print bcolors.BOLD + "RapidScan | Initiating tools and scanning procedures for " + target+ "...\n" + bcolors.ENDC
        

        
        for temp_key,temp_val in tool_names.items():
            print "[:] Deploying "+bcolors.WARNING+temp_val+bcolors.ENDC
            spinner.start()
            temp_file = "temp_"+temp_key
            cmd = tool_cmd.items()[tool][arg1]+" "+target+tool_cmd.items()[tool][arg2]+" > "+temp_file+" 2>&1"
            os.system(cmd)
            if tool_cond[tool] not in open(temp_file).read():
                if tool_opcode[tool] == 0:
                    print bcolors.CLEARLINE
                    print "\t"+bcolors.OKGREEN + tool_pos[tool] + bcolors.ENDC
                else:
                    print bcolors.CLEARLINE
                    print "\t"+bcolors.FAIL + tool_neg[tool] + bcolors.ENDC
            else:
                if tool_opcode[tool] == 1:
                    print bcolors.CLEARLINE
                    print "\t"+bcolors.OKGREEN + tool_pos[tool] + bcolors.ENDC
                else:
                    print bcolors.CLEARLINE
                    print "\t"+bcolors.FAIL + tool_neg[tool] + bcolors.ENDC
            spinner.stop()
            tool=tool+1
            #os.system('setterm -cursor on')

        os.system('rm te*') # Clearing previous scan files

