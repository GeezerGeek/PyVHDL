#------------------------------------------------------------------------------
#
# Boot.py for customized ZamiaCad 0.11.3  -  11/6/14
#
#------------------------------------------------------------------------------
 
from java.io import File, PrintWriter, BufferedWriter, FileWriter, PrintStream
from java.lang import System
from java.math import BigInteger
from org.zamia import ERManager, FSCache, SourceFile, SourceLocation, ZamiaException, ZamiaProject, ZamiaLogger, ExceptionLogger, Toplevel, ToplevelPath
from org.zamia.analysis import SourceLocation2IG, SourceLocation2AST
from org.zamia.analysis.ig import IGReferencesSearch
from org.zamia.analysis.ast import ASTDeclarationSearch, ASTReferencesSearch
from org.zamia.vhdl.ast import DMUID,AST2DOT
from org.zamia.instgraph import IG2DOT, IGOperationObject
from org.zamia.instgraph.sim.ref import IGSimRef
from org.zamia.rtl import RTLVisualGraphContentProvider,RTLVisualGraphLabelProvider,RTLVisualGraphSelectionProvider
from org.zamia.util import PathName, FileUtils
from org.zamia.vg import VGLayout, VGGCSVG
import sys
sys.path.append(System.getenv().get("PYTHONPATH"))

import os

logger = ZamiaLogger.getInstance()
el = ExceptionLogger.getInstance()

def printf(format, *args):
##    sys.stdout.write(format % args)
    logger.info(format, args)

#----

def zamia_build_init():
    printf('*** zamia_build_init() executed')

#----
     
def help():
  print "zamiaCAD builtin python functions:"
  print "=================================="
  print ""
  print "Builtins:"
  print "---------"
  print "zamia_source(uri)"
  print "copy(src, dest)"
  print "unzipAll(zipFileName)"
  print "unzip(zipFileName, filePathsToUnzip)"
  print ""
  print "Builder:"
  print "--------"
  print "clean()"
  print "rebuild()"
  print ""
  print "Markers:"
  print "--------"
  print "marker_add(path,line,column,msg,is_error)"
  print "marker_list()"
  print "marker_clean(path)"
  print ""
  print "DM/AST:"
  print "-------"
  print "dm_list()"
  print "dm_list_2file(filename)"
  print "dm_dump_dot(dmuid,filename)"
  print ""
  print "IG:"
  print "---"
  print "ig_list()"
  print "ig_dump_dot(dmuid,filename)"
  print "ig_ref_search(filename, line, col, toplevelpath)"
  print "ig_ref_search_2file(filename, line, col, toplevelpath, destinationfile)"
  print ""
  print "RTL (Synth):"
  print "------------"
  print "rtl_list()"
  print "rtl_dump_svg(dmuid,filename)"
  print ""
  print "Simulator:"
  print "------------"
  print "openSim()"
  print "run(sim, ns)"
  print ""

def zamia_source(uri):
  project.getZCJ().evalFile(uri)

def getBase():
  return project.fBasePath.toString()

def file(path):
  return File( getBase() + File.separator + path )

def copy(src, dest):
  ok = FileUtils.copy(file(src), file(dest))
  if (not ok):
    printf('Failed to copy %s', src)

def unzipAll(zipFileName):
  ok = FileUtils.unzip(file(zipFileName))
  if (not ok):
    printf('Failed to unzip %s cleanly', zipFileName)

def unzip(zipFileName, filePathsToUnzip):
  ok = FileUtils.unzip(file(zipFileName), filePathsToUnzip)
  if (not ok):
    printf('Failed to unzip %s cleanly', zipFileName)

#
# Builder
#

def clean():
  project.clean()

def rebuild():
  builder = project.getBuilder()
  builder.build(True, True, None)

  n = project.getERM().getNumErrors()
  printf ('python: Build finished. Found %d errors.', n)

#
# Markers
#

def marker_add(path,line,column,msg,is_error):

  erm = project.getERM()
                        
  # make path absolute
  f = File(path)
  if not f.isAbsolute():
    f = file(path)
  
  sf = SourceFile(f)

  if not FSCache.getInstance().exists(sf, True):
    logger.error("python: script tried to add error to non-existant file: %s", sf.getAbsolutePath())
  else:
    location = SourceLocation(sf, line, column)
    erm.addError(ZamiaException(ZamiaException.ExCat.EXTERNAL, is_error, msg, location))
    
def marker_list():

  erm = project.getERM()

  n = erm.getNumErrors()

  for i in range(n):
    em = erm.getError(i)
    printf('%s', em.toString())


def marker_clean(path):
                        
  erm = project.getERM()
                        
  sf = SourceFile(File (path))
                        
  erm.removeErrors(sf, ZamiaException.ExCat.EXTERNAL)

#
# DM (AST)
#

def dm_list():

  dmm = project.getDUM()

  n = dmm.getNumStubs()
  for i in range(n):
    printf('%s', dmm.getStub(i).getDUUID())

def dm_list_2file(filename):

  f = open(filename, 'a')
  dmm = project.getDUM()

  n = dmm.getNumStubs()
  for i in range(n):
    s = str(dmm.getStub(i).getDUUID())
    f.write(s)
    f.write('\n')

  f.close()


def dm_dump_dot(dmuid,filename):

  dmm = project.getDUM()

  uid = DMUID.parse(dmuid)

  dm = dmm.getDM(uid)

  if dm == None:
    printf('DM %s not found', dmuid)
  else:
    printf('Dumping %s...', dm)

    dot = AST2DOT(dm, project.getZDB())

    dot.blacklistField("fParent")
#    dot.blacklistField("fSource")
#    dot.blacklistField("fStartCol")
#    dot.blacklistField("fStartLine")
    dot.blacklistField("fEndCol")
    dot.blacklistField("fEndLine")
    dot.blacklistField("fDeclarationMap")

    out = PrintWriter(BufferedWriter(FileWriter(filename)));

    dot.convert(out);
    out.close()

    printf("python: wrote dot file to %s", filename)

#
# IG
#

def ig_list():

  bp = project.getBuildPath()
  n = bp.getNumToplevels()
  for i in range(n):
    tl = bp.getToplevel(i)
    printf ("%s", tl.getDUUID())


def ig_dump_dot(dmuid,filename):

  igm = project.getIGM()

  uid = DMUID.parse(dmuid)

  module = igm.findModule(Toplevel(uid, None))

  if module == None:
    printf('DM %s not found', dmuid)
  else:
    printf('Dumping %s...', module)

    dot = IG2DOT(module);

    dot.blacklistField("fImportedLibs");
    dot.blacklistField("fImportedPackages");
    dot.blacklistField("fZPrjID");
    dot.blacklistField("fSFDBID");
    dot.blacklistField("fLine");
    dot.blacklistField("fCol");
    dot.blacklistField("fScore");
    dot.blacklistField("fFailed");
    dot.blacklistField("fReject");
    dot.blacklistField("fInertial");
    dot.blacklistField("fDelay");

    out = PrintWriter(BufferedWriter(FileWriter(filename)));

    dot.convert(out);
    out.close()

    printf("python: wrote dot file to %s", filename)


# filename = examples/gcounter/addg.vhdl
# toplevelpath = "COUNTER_TB:COUNTER0.ADDG"
# 22, 35
def ig_ref_search(filename, line, col, toplevelpath):

  sf = SourceFile(File(filename))
  location = SourceLocation(sf, line, col)

  start = System.currentTimeMillis()

  if not toplevelpath:

    nearest = SourceLocation2AST.findNearestASTNode(location, True, project)

    if not nearest:
      printf('No AST item found at %s:%s,%s', filename, line, col)
      return

    declaration = ASTDeclarationSearch.search(nearest, project)

    if not declaration:
      printf('Failed to find declaration of %s', nearest)
      return

    result = ASTReferencesSearch.search(declaration, True, True, project)
    item = nearest

  else:
    tlp = ToplevelPath(toplevelpath)

    res = SourceLocation2IG.findNearestItem(location, tlp, project)

    if not res:
      printf('No IG item found at %s:%s,%s', filename, line, col)
      return

    item = res.getFirst()
    if not item:
      printf('No IG item found at %s:%s,%s', filename, line, col)
      return
    path = res.getSecond()

    rs = IGReferencesSearch(project)

    if isinstance(item, IGOperationObject):
      item = item.getObject()

    result = rs.search(item, path, True, True, False, False)

  time = System.currentTimeMillis() - start

  if not result or result.countRefs() == 0:
    print('Search returned no result.')
  else:
    printf('Found %s references of %s in %s ms:', result.countRefs(), item, time)
    result.dump(0, sys.stdout)

def ig_ref_search_2file(filename, line, col, toplevelpath, destinationfile):

  sf = SourceFile(File(filename))
  tlp = ToplevelPath(toplevelpath)
  location = SourceLocation(sf, line, col)

  start = System.currentTimeMillis()

  res = SourceLocation2IG.findNearestItem(location, tlp, project)

  if res == None:
    printf('No IG item found at %s:%s,%s', filename, line, col)
    return

  item = res.getFirst()
  if item == None:
    printf('Failed to find nearest IG Item')
    return
  path = res.getSecond()

  rs = IGReferencesSearch(project)

  if isinstance(item, IGOperationObject):
    item = item.getObject()

  result = rs.search(item, path, True, True, False, False)

  time = System.currentTimeMillis() - start

  out = PrintStream(File(destinationfile))
  printf('Found %s references of %s in %s ms.', result.countRefs(), item, time)
  out.printf('Found %s references of %s in %s ms:\n', result.countRefs(), item, time)
  result.dump(0, out)

#
# RTL
#

def rtl_list():

  bp = project.getBuildPath()
  n = bp.getNumSynthTLs()
  for i in range(n):
    tl = bp.getSynthTL(i)
    printf ("%s", tl.getDUUID())


def rtl_dump_svg(dmuid,filename):

  rtlmanager = project.getRTLM()

  uid = DMUID.parse(dmuid)

  rtlm = rtlmanager.findModule(Toplevel(uid, None))

  if rtlm == None:
    printf('RTLM %s not found', dmuid)
  else:
    printf('Dumping %s...', rtlm)

    out = PrintWriter(BufferedWriter(FileWriter(filename)))

    gc = VGGCSVG(out)

    contentProvider = RTLVisualGraphContentProvider(rtlm)

    labelProvider = RTLVisualGraphLabelProvider(rtlm)

    selectionProvider = RTLVisualGraphSelectionProvider()

    layout = VGLayout(contentProvider, labelProvider, gc)

    layout.paint(selectionProvider);

    out.close()

    printf("python: wrote svg file to %s", filename)

#
# Sim
#

def getUID():

  bp = project.getBuildPath()

  tl = bp.getToplevel(0)

  return project.getDUM().getArchDUUID(tl.getDUUID())

def openSim():

  sim = IGSimRef()

  tlDUUID = getUID()

  tl = Toplevel(tlDUUID, None)
  tlp = ToplevelPath(tl, PathName(""))

  sim.open(tlp, None, None, project)

  return sim

def run(sim, ns):

  sim.run(BigInteger(ns).multiply(BigInteger("1000000")))
