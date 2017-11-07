import groovy.json.JsonBuilder
import org.json.simple.JSONValue;
import src.util.Util

if(!application) {
    application = request.getApplication(true)
}

def params = Util.extractParams(request)
def ontology = params.ontology
def managers = application.managers

response.contentType = 'application/json'

if(ontology && managers.containsKey(ontology)) {
    def objectProperties = managers[ontology].getObjectProperties()
    response.contentType = 'application/json'
    print(new JsonBuilder(objectProperties))
} else {
    print('{status: "error", message: "Please provide an ontology!"}')
}
