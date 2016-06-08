
from java.io import PrintStream
from org.zamia.instgraph.interpreter.logger import Report

def checkSignalValue(signalName, expectedValue, sim):
  value = sim.getValue(PathName(signalName))
  return value.toString() == expectedValue

rebuild()

passedAssignments = []
failedAssignments = []
passedBranches = []
failedBranches = []
passedConditions = []
failedConditions = []

# Run Tests
for i in range(1, 37):
  if (i == 27 or i == 30 or i == 31 or i == 32 or i == 36):
    continue

  copy("SOFTWARE/SPARTAN3_STARTERKIT/TEST_PROCESSOR_PROGRAMS/" + str(i) + "/object_code.oc.mif", "SOFTWARE/SPARTAN3_STARTERKIT/TEST_PROCESSOR_PROGRAMS/OBJECT_CODE.OC.MIF")

  sim = openSim()
  run(sim, "3020")

  assignmentsLog = sim.collectExecutedAssignments(str(i))
  branchesLog = sim.collectExecutedBranches(str(i))
  conditionsLog = sim.collectExecutedConditions(str(i))

  ok = checkSignalValue("LEDS_LD", "11111111", sim)
  if (not ok):
    failedAssignments.append(assignmentsLog)
    failedBranches.append(branchesLog)
    failedConditions.append(conditionsLog)
  else:
    passedAssignments.append(assignmentsLog)
    passedBranches.append(branchesLog)
    passedConditions.append(conditionsLog)

reportAssignments = Report.createReport(failedAssignments, passedAssignments, "Assignments")
reportBranches = Report.createReport(failedBranches, passedBranches, "Branches")
reportConditions = Report.createReport(failedConditions, passedConditions, "Conditions")

reportAssignments.printStat(PrintStream(file("assignments.txt")))
reportAssignments.getSuspects().printStat(PrintStream(file("assignments_red.txt")))
reportBranches.printStat(PrintStream(file("branches.txt")))
reportBranches.getSuspects().printStat(PrintStream(file("branches_red.txt")))
reportConditions.printStat(PrintStream(file("conditions.txt")))
reportConditions.getSuspects().printStat(PrintStream(file("conditions_red.txt")))
