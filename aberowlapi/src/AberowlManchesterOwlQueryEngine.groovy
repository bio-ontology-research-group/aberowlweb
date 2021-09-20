package src


import org.eclipse.rdf4j.repository.sparql.SPARQLRepository;
import org.eclipse.rdf4j.http.client.SPARQLProtocolSession;
import org.eclipse.rdf4j.query.QueryLanguage;
import org.eclipse.rdf4j.repository.RepositoryConnection;
import org.eclipse.rdf4j.query.TupleQueryResultHandler;
import org.eclipse.rdf4j.query.resultio.sparqljson.SPARQLResultsJSONWriter;
import org.eclipse.rdf4j.query.TupleQuery;

import java.io.ByteArrayOutputStream;

import groovyx.gpars.GParsPool;

/**
 * Aberowl manchester owl query engine process the query and retrieve 
 * results from a Sparql endpoint provided in query itself. Query processing
 * includes parsing the query to extract aberowl manchester owl query elements given
 * in the query, then retrieving classes using the element from ontologies loaded in
 * aberowl repository. Later, rewriting the given sparql query after replacing list of
 * class uris with the aberowl mancherter owl query snippet in sparql query. 
 *
 * Lastly, running the sparql query on extracted sparql endpoint. 
 **/
public class AberowlManchesterOwlQueryEngine {

    public def expandAndExecQuery(def managers, def sparql) {
        AberowlManchesterOwlParser parser = new AberowlManchesterOwlParser();
        AberowlManchesterOwlQuery query = parser.parseSparql(sparql);
        if (query == null) {
            throw new RuntimeException("Invalid Sparql query");
        }

        println("Query: "+ query.query + "| Service Url" + query.sparqlServiceUrl + "| Ontology:" + query.ontologyIri + "| Type:" + query.queryType) 

        def classes = this.executeQuery(managers, query);
        def queryString;

        if (classes != null && classes.size() > 0) { 
            def commaJoinedClassesIriList;
            if (query.isInValueFrame()) {
                commaJoinedClassesIriList = this.toClassIRIString(classes, " ")
            } else {
                commaJoinedClassesIriList = this.toClassIRIString(classes, ", ")
            }
            queryString = parser.replaceAberowlManchesterOwlFrame(sparql, commaJoinedClassesIriList);
        } else {
            // queryString = parser.removeAberowlManchesterOwlFrame(sparql),;
            queryString = parser.replaceAberowlManchesterOwlFrame(sparql, '');
        }

        println("Expanded Sparql: " + queryString)  
        return ["query": queryString, "endpoint": query.sparqlServiceUrl];
        // return executeSparql(query, queryString);
    }

    // private def executeSparql(AberowlManchesterOwlQuery query, String sparql) {
    //     SPARQLRepository repo = new SPARQLRepository(query.sparqlServiceUrl);
    //     repo.initialize();
    //     RepositoryConnection conn;
    //     try {
    //         conn = repo.getConnection();
    //         TupleQuery tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, sparql);
    //         def out = new ByteArrayOutputStream();
    //         TupleQueryResultHandler jsonWriter = new SPARQLResultsJSONWriter(out);
	// 		tupleQuery.evaluate(jsonWriter);
    //         return out.toString("UTF-8")
    //     } finally {
    //         conn.close();
    //     }
    // }

    private def executeQuery(def managers, AberowlManchesterOwlQuery query) {
        if (query.getOntologyIri() != null && !query.getOntologyIri().isEmpty() && managers[query.getOntologyIri()] != null) {
            def out = managers[query.getOntologyIri()].runQuery(query.query, query.queryType, false, true, false)
            return out;
        } else {
            def res = []
            GParsPool.withPool {
                managers.values().eachParallel { manager ->
                    def out = manager.runQuery(query.query, query.queryType, false, true, false)
                    res.addAll(out)
                }
            }
            return res;
        }
    }

    private def toClassIRIString(def classes, def delimiter) {
        return classes.collect{it.owlClass}.join(delimiter);
    }
}