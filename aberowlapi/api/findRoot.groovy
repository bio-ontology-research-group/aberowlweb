// Run a query and ting

import src.util.Util

import groovy.json.*

if(!application) {
  application = request.getApplication(true)
}

def params = Util.extractParams(request)

def query = params.query
def ontology = params.ontology
def managers = application.managers

def owlThing = '<http://www.w3.org/2002/07/owl#Thing>'

if(query && ontology && managers.containsKey(ontology)) {
    def manager = managers[ontology]
    query = java.net.URLDecoder.decode(query, "UTF-8")

    // find superclasses
    def supers = [query]
    int it = 0
    while(true) {
	q = supers[it]
	parents = manager.runQuery(q, 'superclass', true, false, true).toArray()
	if (parents.size() == 0 || parents[0].owlClass == owlThing) {
	    break
	}
	supers.add(parents[0].owlClass)
	it++
    }

    supers = supers.reverse()

    // expand children
    def result = manager.runQuery(owlThing, 'subclass', true, false, true).toArray()
    def classes = result
    it = 0
    for (int i = 0; i < supers.size(); i++) {
	for (int j = 0; j < classes.size(); j++) {
	    if (classes[j].owlClass == supers[i]) {
		def children = manager.runQuery(
		    classes[j].owlClass, 'subclass', true, false, true).toArray()
		classes[j]["children"] = children
		classes = children
		break
	    }
	}
    }

    response.contentType = 'application/json'
    print(new JsonBuilder(["result": result]).toString())
} else {
  print('{result: []}')
}
