// Run a query and ting

import src.util.Util

import groovy.json.*

if(!application) {
  application = request.getApplication(true)
}

def params = Util.extractParams(request)

def query = params.query
def rManager = application.rManager

def owlThing = '<http://www.w3.org/2002/07/owl#Thing>'

if(query) {
    query = java.net.URLDecoder.decode(query, "UTF-8")

    // find superclasses
    def supers = [query]
    int it = 0
    while(true) {
	q = supers[it]
	parents = rManager.runQuery(q, 'superclass', true, false).toArray()
	if (parents.size() == 0 || parents[0].owlClass == owlThing) {
	    break
	}
	supers.add(parents[0].owlClass)
	it++
    }

    supers = supers.reverse()

    // expand children
    def result = rManager.runQuery(owlThing, 'subclass', true, false).toArray()
    def classes = result
    it = 0
    for (int i = 0; i < supers.size(); i++) {
	for (int j = 0; j < classes.size(); j++) {
	    if (classes[j].owlClass == supers[i]) {
		def children = rManager.runQuery(
		    classes[j].owlClass, 'subclass', true, false).toArray()
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


