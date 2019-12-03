// An Api for SPARQL query rewriting.

import groovy.json.*
import org.apache.log4j.*
import groovy.util.logging.*
import src.util.Util
import groovyx.gpars.GParsPool
import src.AberowlManchesterOwlQueryEngine;

if(!application) {
    application = request.getApplication(true)
}
if (!application.log) {
    Logger log = Logger.getInstance(getClass())
    log.level = Level.INFO
    // add an appender to log to file
    log.addAppender(new RollingFileAppender(new TTCCLayout(), 'queries.log', true))
    application.log = log
    log.info 'Logger created'
}
def log = application.log
def queryEngine = new AberowlManchesterOwlQueryEngine();
def params = Util.extractParams(request)

def query = params.query
def managers = application.managers

try {
    def response = queryEngine.expandAndExecQuery(managers, query)
    print new JsonBuilder(response).toString() 
} catch(java.lang.IllegalArgumentException e) {
    response.setStatus(400)
    print new JsonBuilder([ 'error': true, 'message': 'Invalid Sparql query' ]).toString() 
} catch(org.semanticweb.owlapi.manchestersyntax.renderer.ParserException e) {
    response.setStatus(400)
    print new JsonBuilder([ 'error': true, 'message': 'Query parsing error: ' + e.getMessage() ]).toString() 
} catch(RuntimeException e) {
    response.setStatus(400)
    e.printStackTrace();
    print new JsonBuilder([ 'error': true, 'message': e.getMessage() ]).toString() 
}catch(Exception e) {
    response.setStatus(400)
    print new JsonBuilder([ 'error': true, 'message': 'Generic query error: ' + e.getMessage() ]).toString() 
}

