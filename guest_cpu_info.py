#!/usr/bin/env python2

import libvirt
import sys
import time

# INIT - establish a connection with a local QEMU instance
conn = libvirt.openReadOnly("qemu:///system")
if None == conn:
    print 'Failed to open connection to the hypervisor'
    sys.exit(1)

class DomInfo:
    # state: one of the state values (virDomainState)
    # maxMemory: the maximum memory used by the domain
    # memory: the current amount of memory used by the domain
    # nbVirtCPU: the number of virtual CPU
    # cpuTime: the time used by the domain in nanoseconds
    name = ""
    state = 0
    maxMemory = 0
    memory = 0
    nbVirtCPU = 0
    cpuTime = 0

    def __init__ (self, name, infoDTO):
        self.name = name
        self.state = infoDTO[0]
        self.maxMemory = infoDTO[1]
        self.memory = infoDTO[2]
        self.nbVirtCPU = infoDTO[3]
        self.cpuTime = infoDTO[4]

    def toString(self):
        return "[%s]\nState:\t\t%d\nmaxMemory:\t%d\nmemory:\t\t%d\nnbVirtCPU:\t%d\ncpuTime:\t%d\n" % (self.name, self.state, self.maxMemory, self.memory, self.nbVirtCPU, self.cpuTime)

class DerivedDomInfo(DomInfo):
    cpuUsagePercent = 0

    def __init__(self, previousDomInfo, currentDomInfo, beforeTime, nowTime):
        self.name = currentDomInfo.name
        self.state = currentDomInfo.state
        self.maxMemory = currentDomInfo.maxMemory
        self.memory = currentDomInfo.memory
        self.nbVirtCPU = currentDomInfo.nbVirtCPU
        self.cpuTime = currentDomInfo.cpuTime

        percentBase = (((self.cpuTime - previousDomInfo.cpuTime) * 100.0) / ((nowTime - beforeTime) * 1000.0 * 1000.0 * 1000.0))
        self.cpuUsagePercent = percentBase / self.nbVirtCPU

    def toString(self):
        return "[%s]\nState:\t\t%d\nmaxMemory:\t%d\nmemory:\t\t%d\nnbVirtCPU:\t%d\ncpuTime:\t%d\nCPU usage:\t%f%%\n" % (self.name, self.state, self.maxMemory, self.memory, self.nbVirtCPU, self.cpuTime, self.cpuUsagePercent)

def makeInfo(domainName, data):
    return DomInfo(domainName, data)

def makeDerivedInfo(previousDomInfo, currentDomInfo, beforeTime, nowTime):
    return DerivedDomInfo(previousDomInfo, currentDomInfo, beforeTime, nowTime)

class DomainInfoPoller:
    previousRecords = {}
    before = {}
    domainsToPoll = []
    now = -1

    def getDomainInfo(self, domainName):
        try:
            domain = conn.lookupByName(domainName)
            return makeInfo(domainName, domain.info())
        except:
            print 'Failed to find the \'%s\' domain' % (domainName)
            sys.exit(1)

    def includeDomain(self, domainName):
        self.domainsToPoll.append(domainName)

    def includeDomains(self, domainNames):
        self.domainsToPoll = self.domainsToPoll + domainNames

    def run(self, domainInfoReceiver):
        while 1:
            for domainName in self.domainsToPoll:
                self.now = time.time()
                currentRecord = self.getDomainInfo(domainName)

                if domainName in self.previousRecords:
                    domainInfoReceiver(makeDerivedInfo(self.previousRecords[domainName], currentRecord, self.before[domainName], self.now))

                self.previousRecords[domainName] = currentRecord
                self.before[domainName] = self.now
            time.sleep(.5)

# EDIT THE CODE BELOW.

def printDomainInfo(info):
    print info.toString()

dp = DomainInfoPoller()

dp.includeDomains(["test", "test2"])

# These also work:
# dp.includeDomain("test")
# dp.includeDomain("test2")

# You can pass any function You like here.
# Every 500ms, it will receive an instance of `DerivedDomInfo` for each included domain.
dp.run(printDomainInfo)