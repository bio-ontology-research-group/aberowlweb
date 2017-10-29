@Grapes([
	@Grab(group='javax.servlet', module='javax.servlet-api', version='3.1.0'),
        @Grab(group='javax.servlet.jsp', module='javax.servlet.jsp-api', version='2.3.1'),
        @Grab(group='org.eclipse.jetty', module='jetty-server', version='9.4.7.v20170914'),
        @Grab(group='org.eclipse.jetty', module='jetty-servlet', version='9.4.7.v20170914'),
        @Grab(group='com.google.code.gson', module='gson', version='2.3.1'),
        @Grab(group='com.googlecode.json-simple', module='json-simple', version='1.1.1'),
	@Grab(group='org.slf4j', module='slf4j-nop', version='1.7.25'),
	@Grab(group='org.semanticweb.elk', module='elk-owlapi', version='0.4.3'),
        @Grab(group='net.sourceforge.owlapi', module='owlapi-api', version='4.3.2'),
        @Grab(group='net.sourceforge.owlapi', module='owlapi-apibinding', version='4.3.2'),
        @Grab(group='net.sourceforge.owlapi', module='owlapi-impl', version='4.3.2'),
        @Grab(group='net.sourceforge.owlapi', module='owlapi-parsers', version='4.3.2'),
	
	@Grab(group='com.google.guava', module='guava', version='19.0'),
	
	@Grab(group='org.codehaus.groovy.modules.http-builder', module='http-builder', version='0.7.1' ),
	@GrabExclude(group='xml-apis', module='xml-apis'),
	@Grab(group='aopalliance', module='aopalliance', version='1.0'),
	@Grab(group='javax.el', module='javax.el-api', version='3.0.0'),
	@GrabConfig(systemClassLoader=true)
])

 
import org.eclipse.jetty.server.Server
import org.eclipse.jetty.server.ServerConnector
import org.eclipse.jetty.servlet.*
import org.eclipse.jetty.server.handler.*
import groovy.servlet.*
import src.*
import java.util.concurrent.*
import org.apache.log4j.Logger
import org.apache.log4j.Level
import org.eclipse.jetty.server.nio.*
import org.eclipse.jetty.util.thread.*
import org.eclipse.jetty.util.log.Log
import org.eclipse.jetty.util.log.StdErrLog
import groovyx.net.http.HTTPBuilder
import groovyx.net.http.Method
import groovyx.net.http.ContentType

Log.setLog(new StdErrLog())

def startServer(def ontId, def ontIRI, def port) {

  Server server = new Server(port)
  if (!server) {
    System.err.println("Failed to create server, cannot open port.")
    System.exit(-1)
  }
  
  def context = new ServletContextHandler(server, '/', ServletContextHandler.SESSIONS)
  context.resourceBase = '.'

  println "Starting $ontId"
  def localErrorHandler = new ErrorHandler()
  localErrorHandler.setShowStacks(true)
  context.setErrorHandler(localErrorHandler)
  context.resourceBase = '.'
  context.addServlet(GroovyServlet, '/api/runQuery.groovy')
  context.addServlet(GroovyServlet, '/api/getClass.groovy')
  context.addServlet(GroovyServlet, '/api/getStats.groovy')
  context.addServlet(GroovyServlet, '/api/reloadOntology.groovy')
  context.addServlet(GroovyServlet, '/api/findRoot.groovy')
  context.addServlet(GroovyServlet, '/api/getObjectProperties.groovy')
  context.addServlet(GroovyServlet, '/api/retrieveRSuccessors.groovy')
  context.addServlet(GroovyServlet, '/api/retrieveAllLabels.groovy')
  context.setAttribute("ontology", ontId)
  context.setAttribute('port', port)
  context.setAttribute('version', '0.2')
  server.start()
  println "Server started on " + server.getURI()
  println "Classifying..."

  context.setAttribute("rManager", new RequestManager(ontId, ontIRI))
}

def ontId = args[0]
def ontIRI = args[1]
def port = args[2] as Integer
startServer(ontId, ontIRI, port)
