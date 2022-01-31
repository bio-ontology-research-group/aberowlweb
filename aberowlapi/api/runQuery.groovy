// Run a query and ting

import groovy.json.*
import src.util.Util
import groovyx.gpars.GParsPool

if(!application) {
    application = request.getApplication(true)
}

def params = Util.extractParams(request)

def query = params.query
def type = params.type
def direct = params.direct
def labels = params.labels
def axioms = params.axioms
def ontology = params.ontology
def managers = application.managers

if (type == null) {
    type = "all"
}

direct = (direct.equals("true")) ? true : false;
labels = (labels.equals("true")) ? true : false;
axioms = (axioms.equals("true")) ? true : false;

response.contentType = 'application/json'

try {
    def results = new HashMap()
    def start = System.currentTimeMillis()

    if (ontology != null) {
	def out = managers[ontology].runQuery(query, type, direct, labels, axioms)
	def end = System.currentTimeMillis()
	results.put('time', (end - start))
	results.put('result', out)
    } else {
	def res = []
	GParsPool.withPool {
	    managers.values().eachParallel { manager ->
		def out = manager.runQuery(query, type, direct, labels, false)
		res.addAll(out)
	    }
	}
	def end = System.currentTimeMillis()
	results.put('time', (end - start))
	results.put('result', res)
	
    }
    print new JsonBuilder(results).toString()
} catch(java.lang.IllegalArgumentException e) {
    response.setStatus(400)
    print new JsonBuilder([ 'error': true, 'message': 'Ontology not found.' ]).toString() 
} catch(org.semanticweb.owlapi.manchestersyntax.renderer.ParserException e) {
    response.setStatus(400)
    print new JsonBuilder([ 'error': true, 'message': 'Query parsing error: ' + e.getMessage() ]).toString() 
} catch(Exception e) {
    response.setStatus(400)
    print new JsonBuilder([ 'error': true, 'message': 'Generic query error: ' + e.getMessage() ]).toString() 
}

