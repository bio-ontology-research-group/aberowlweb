@Grab(group='org.codehaus.groovy.modules.http-builder', module='http-builder', version='0.7' )
@Grab(group='redis.clients', module='jedis', version='2.6.2')
@Grab(group='commons-io', module='commons-io', version='2.4')

import groovyx.net.http.HTTPBuilder
import groovyx.net.http.RESTClient
import static groovyx.net.http.Method.HEAD
import static groovyx.net.http.ContentType.TEXT
import java.text.SimpleDateFormat
import db.*
import groovy.json.*
import java.nio.file.*
import java.io.File
import java.util.zip.GZIPInputStream
import org.apache.commons.io.FileUtils
import org.apache.commons.codec.digest.DigestUtils
import redis.clients.jedis.*


ONTDIR = "/home/hohndor/aberowl-meta/aberowl-server/onts/"
REPODIR = "/home/hohndor/aberowl-meta/ontologies/"
String BIO_API_ROOT = 'http://data.bioontology.org/'
String BIO_API_KEY = '24e0413e-54e0-11e0-9d7b-005056aa3316'
List<String> ABEROWL_API = ['http://aber-owl.net/service/api/']
String OBOFOUNDRY_FILE = "http://www.obofoundry.org/registry/ontologies.jsonld"

DB_PREFIX = 'ontos:'
def db = new JedisPool(new JedisPoolConfig(), "localhost").getResource()

def slurper = new JsonSlurper()
def obo = slurper.parse(new URL(OBOFOUNDRY_FILE))

def uptodate = false

HTTPBuilder builder = new HTTPBuilder()
builder.getClient().getParams().setParameter("http.connection.timeout", new Integer(1000*1000))
builder.getClient().getParams().setParameter("http.socket.timeout", new Integer(3000*1000))

def oid = args[0]
def bpath = REPODIR + oid + "/" // base [path

def oRec = slurper.parseText(db.get(DB_PREFIX+oid))
//def oRec = slurper.parse(new File(bpath + "config.json"))

//println "Processing ${oRec.id}..."
def fileName = bpath + "new/"+oid+".owl"
def tempFile = new File(bpath + "new/"+oid+"-raw.owl")

def released = 0 
if(oRec.source == 'manual') {
  // do nothing, we won't update this
  println "Ontology source \'manual\', won't do anything"
  System.exit(-1)
} else if(oRec.source == 'bioportal') {
  println "Synchronizing with BioPortal"
  try {
    builder.get( uri: BIO_API_ROOT + 'ontologies/' + oRec.id + '/submissions', query: [ 'apikey': BIO_API_KEY ] ) { eResp, submissions ->
      println '[' + eResp.status + '] ' + oRec.id
      if(!submissions[0]) {
	println "No releases"
	System.exit(-1)
      }
      SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm");
      def lastSubDate = dateFormat.parse(submissions[0].released).toTimestamp().getTime() / 1000; //
      released = lastSubDate
      println "Released on $released"
      if(lastSubDate > oRec.lastSubDate) {
	println "New version found..."
	def urlForCmd = submissions[0].ontology.links.download?.trim()?.toString()?.replaceAll("\"","")
	def proc = ("curl -L "+urlForCmd+"?apikey="+BIO_API_KEY + " -o "+tempFile.getPath()).execute()
	proc.waitFor()
      } else {
	println "Current version already present"
	uptodate = true
      }
    }
  } catch(groovyx.net.http.HttpResponseException e) {
    e.printStackTrace()
    println "Ontology disappeared"
    System.exit(-1)
  } catch(java.net.SocketException e) {
    println "Socket exception"
    System.exit(-1)
  } catch(Exception e) {
    e.printStackTrace()
    System.exit(-1)
  }
} else if(oRec.source == 'obofoundry') {
  obo.ontologies.findAll { it.id?.toLowerCase() == oRec.id?.toLowerCase() }.each { ont ->
    def purl = "http://purl.obolibrary.org/obo/"+ont.id?.toLowerCase()+".owl"
    println "Downloading ${ont.id} from $purl..."
    try {
      def proc = ("curl -L "+purl+" -o "+tempFile.getPath()).execute()
      proc.waitFor()
      released = (int) (System.currentTimeMillis() / 1000L) // current unix time (pretty disgusting line though)

    } catch (Exception E) {
      E.printStackTrace()
      System.exit(-1)
    }
  }
} else if(oRec.source != null) { // try it as a url
  // We just attempt to add the new submission, since that will check if it is new or not
  try {
    def proc = ("curl -L "+oRec.source?.trim()+" -o "+tempFile.getPath()).execute()
    proc.waitFor()
    released = (int) (System.currentTimeMillis() / 1000L) // current unix time (pretty disgusting line though)
  } catch (Exception E) {
    println "Failure do download "+oRec.id+" from "+oRec.source+": "+E.getMessage()
    E.printStackTrace()
    System.exit(-1)
  }
}

try {
  println "Attempting to unzip file..."
  byte[] buffer = new byte[1024]
  GZIPInputStream gzis = new GZIPInputStream(new FileInputStream(tempFile))
  def tf = File.createTempFile("aber-gz", ".tmp")
  FileOutputStream out = new FileOutputStream(tf)
  int len = 0
  while ((len = gzis.read(buffer)) > 0) {
    out.write(buffer, 0, len)
  }
  gzis.close()
  out.close()
  Files.move(tf.toPath(),tempFile.toPath(),StandardCopyOption.REPLACE_EXISTING)
} catch (Exception E) {
  println "Not a Gzip file: " + E.getMessage()
}

if (!uptodate) {
  // Get the checksum of the most recent release.
  def oldSum = 0
  try {
    def currentFile = new FileInputStream(new File(bpath+"release/${oid}_"+oRec.submissions.size()+".ont"))
    if(currentFile) {
      oldSum = DigestUtils.md5Hex(currentFile)
    }
    currentFile.close()
  } catch (Exception E) {
    oldsum = 0
  }
  def newSum = DigestUtils.md5Hex(new FileInputStream(tempFile))
  if(oldSum == newSum) {
    println "File is not new"
    uptodate = true
  } else {

  }
}
if (!uptodate) {
  oRec.releaseInProgress = released
  oRec.uptodate = false
} else {
  oRec.uptodate = true
}
db.set(DB_PREFIX + oid, JsonOutput.toJson(oRec))
db.close()


// PrintWriter fout = new PrintWriter(new BufferedWriter(new FileWriter(new File(bpath + "config.json"))))
// fout.println(JsonOutput.toJson(oRec))
// fout.flush()
// fout.close()

// now there is a new file SIO.owl in the new subdir; next need to classify
