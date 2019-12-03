package test.src;

import groovyx.net.http.RESTClient
import groovy.util.GroovyTestCase
import groovy.json.JsonSlurper;

/**
 * API tests for sparql api in aberowl.
 * Rightnow the tests are run under some assumptions including 
 * there is ECO onotology already loaded into the aberowl 
 * repository and there is DDIEM sparql endpoint available. 
 **/
class SparqlApiTest extends GroovyTestCase {
    static String aberowlURL = "http://localhost:8000"

    RESTClient restClient = new RESTClient(aberowlURL)

    void testExecuteSparqlWhenValue(){
        def sparql = "SELECT ?OMIM_ID ?class \n" +
                    "WHERE \n" +
                    "          { \n" +
                    "<http://ddiem.phenomebrowser.net/202110> <http://purl.org/dc/elements/1.1/identifier> ?OMIM_ID . \n" +
                    "        VALUES ?class {  \n" +
                    "            OWL equivalent <http://ontolinator.kaust.edu.sa:8891/sparql> <ECO> {  \n" +
                    "             evidence \n" +
                    "            }  \n" +
                    "        } .  \n" +
                    "    }";

        def response = restClient.get(path: '/api/sparql', query : [query : sparql, result_format:'application/sparql-results+json'])

        assertEquals(200, response.status)

        def jsonSlurper = new JsonSlurper()
        def object = jsonSlurper.parseText(new String(response.responseData.getBytes(), 'UTF-8'));

        assertNotNull(object.head.vars)

        assertEquals(object.head.vars.size(), 2)
        assertEquals(object.head.vars[0], 'OMIM_ID')
        assertEquals(object.head.vars[1], 'class')


        assertNotNull(object.results.bindings)
        assertEquals(object.results.bindings.size(), 1)


        assertEquals(object.results.bindings[0].OMIM_ID.value, 'https://www.omim.org/entry/202110')
        assertEquals(object.results.bindings[0].class.value, 'http://purl.obolibrary.org/obo/ECO_0000000')
    }

    void testExecuteSparqlWhenFilter(){
        def sparql = "SELECT ?OMIM_ID ?class  \n" +
                "WHERE \n" +
                "          { \n" +
                "              <http://ddiem.phenomebrowser.net/202110> <http://purl.org/dc/elements/1.1/identifier> ?OMIM_ID . \n" +
                "              <http://ddiem.phenomebrowser.net/202110> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?class . \n" +
                "       FILTER ( ?class in ( \n" +
                "                              OWL subclass <http://ontolinator.kaust.edu.sa:8891/sparql> <ECO> {  \n" +
                "                                  equivalent \n" +
                "                              }  \n" +
                "       ))  \n" +
                "    }";

        def response = restClient.get(path: '/api/sparql', query : [query : sparql, result_format:'application/sparql-results+json'])

        assertEquals(200, response.status)

        def jsonSlurper = new JsonSlurper()
        def object = jsonSlurper.parseText(new String(response.responseData.getBytes(), 'UTF-8'));
        assertNotNull(object.head.vars)

        assertEquals(object.head.vars.size(), 2)
        assertEquals(object.head.vars[0], 'OMIM_ID')
        assertEquals(object.head.vars[1], 'class')

        assertNotNull(object.results.bindings)
        assertEquals(object.results.bindings.size(), 1)


        assertEquals(object.results.bindings[0].OMIM_ID.value, 'https://www.omim.org/entry/202110')
        assertEquals(object.results.bindings[0].class.value, 'http://ddiem.phenomebrowser.net/Disease')
    }

}