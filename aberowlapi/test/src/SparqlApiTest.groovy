package test.src;

import groovyx.net.http.RESTClient
import groovy.util.GroovyTestCase
import groovy.json.JsonSlurper;

/**
 * API tests for sparql api in aberowl.
 * Rightnow the tests are run under some assumptions including 
 * there is EDAM onotology already loaded into the aberowl 
 * repository and there is DDIEM sparql endpoint available. 
 **/
class SparqlApiTest extends GroovyTestCase {
    static String aberowlURL = "http://localhost:8000"

    RESTClient restClient = new RESTClient(aberowlURL)

    void testExecuteSparqlWhenValue(){
        def sparql = "SELECT ?OMIM_ID ?class \n" +
                    "WHERE \n" +
                    "          { \n" +
                    "<https://www.omim.org/entry/202110> <http://www.cbrc.kaust.edu.sa/ddiem/terms/has_omim_id> ?OMIM_ID . \n" +
                    "        VALUES ?class {  \n" +
                    "            OWL subclass <http://ontolinator.kaust.edu.sa:8891/sparql> <EDAM> {  \n" +
                    "            <http://edamontology.org/format_1915> \n" +
                    "            }  \n" +
                    "        } .  \n" +
                    "    }";

        def response = restClient.get(path: '/api/sparql', query : [query : sparql])

        assertEquals(200, response.status)

        def jsonSlurper = new JsonSlurper()
        def object = jsonSlurper.parseText(response.responseData.toString());

        assertNotNull(object.head.vars)

        assertEquals(object.head.vars.size(), 2)
        assertEquals(object.head.vars[0], 'OMIM_ID')
        assertEquals(object.head.vars[1], 'class')


        assertNotNull(object.results.bindings)
        assertEquals(object.results.bindings.size(), 6)


        assertEquals(object.results.bindings[0].OMIM_ID.value, '202110')
        assertEquals(object.results.bindings[0].class.value, 'http://edamontology.org/format_2333')
    }

    void testExecuteSparqlWhenFilter(){
        def sparql = "SELECT ?OMIM_ID ?class  \n" +
                "WHERE \n" +
                "          { \n" +
                "              <https://www.omim.org/entry/202110> <http://www.cbrc.kaust.edu.sa/ddiem/terms/has_omim_id> ?OMIM_ID . \n" +
                "              <https://www.omim.org/entry/202110> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?class . \n" +
                "       FILTER ( ?class in ( \n" +
                "                              OWL subclass <http://ontolinator.kaust.edu.sa:8891/sparql> <EDAM> {  \n" +
                "                                  <http://edamontology.org/format_1915> \n" +
                "                              }  \n" +
                "       ))  \n" +
                "    }";

        def response = restClient.get(path: '/api/sparql', query : [query : sparql])

        assertEquals(200, response.status)

        def jsonSlurper = new JsonSlurper()
        def object = jsonSlurper.parseText(response.responseData.toString());

        assertNotNull(object.head.vars)

        assertEquals(object.head.vars.size(), 0)
        assertEquals(object.head.vars[0], 'OMIM_ID')
        assertEquals(object.head.vars[1], 'class')


        assertNotNull(object.results.bindings)
        assertEquals(object.results.bindings.size(), 0)
    }

}