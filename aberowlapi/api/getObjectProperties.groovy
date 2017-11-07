import groovy.json.JsonBuilder
import org.json.simple.JSONValue;
import java.net.URLDecoder;
import src.util.Util

if(!application) {
    application = request.getApplication(true);
}

def params = Util.extractParams(request);
def ontology = params.ontology;
def property = params.property;
def managers = application.managers;

response.contentType = 'application/json';

if(ontology && managers.containsKey(ontology)) {
    if (property == null) {
	def objectProperties = managers[ontology].getObjectProperties()
	print(new JsonBuilder(objectProperties))
    } else {
	property = URLDecoder.decode(property, "UTF-8")
	def objectProperties = managers[ontology].getObjectProperties(property)
	print(new JsonBuilder(objectProperties))
    }
} else {
    print('{status: "error", message: "Please provide an ontology!"}')
}
