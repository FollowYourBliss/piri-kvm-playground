#!/usr/bin/env python2
import libvirt
import sys
import time

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

def makeInfo(domainName, data):
    return DomInfo(domainName, data)

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
        return "[%s]\nState:\t\t%d\nmaxMemory:\t%d\nmemory:\t\t%d\nnbVirtCPU:\t%d\ncpuTime:\t%d\nCPU usage:\t%2f%%\n" % (self.name, self.state, self.maxMemory, self.memory, self.nbVirtCPU, self.cpuTime, self.cpuUsagePercent)

def makeDerivedInfo(previousDomInfo, currentDomInfo, beforeTime, nowTime):
    return DerivedDomInfo(previousDomInfo, currentDomInfo, beforeTime, nowTime)

def getDomainInfo(domainName):
    try:
        domain = conn.lookupByName(domainName)
        return makeInfo(domainName, domain.info())
    except:
        print 'Failed to find the \'%s\' domain' % (domainName)
        sys.exit(1)

def pollDomainInfo(domainName):
    previousRecord = -1
    before = -1
    while 1:
        currentRecord = getDomainInfo(domainName)
        now = time.time()
        if previousRecord != -1:
            print makeDerivedInfo(previousRecord, currentRecord, before, now).toString()
        previousRecord = currentRecord
        before = now
        time.sleep(.5)

pollDomainInfo("test")


