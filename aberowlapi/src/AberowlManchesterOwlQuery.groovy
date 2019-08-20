package src

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Bean class for Aberowl manchester owl query elements.
 **/
public class AberowlManchesterOwlQuery {

    String queryType;
    String sparqlServiceUrl;
    String ontologyIri;
    String query;
    String variable;
    boolean inValueFrame = false;

    String getQueryType() {
        return queryType;
    }

    void setQueryType(String queryType) {
        this.queryType = queryType;
    }

    String getSparqlServiceUrl() {
        return sparqlServiceUrl;
    }

    void setSparqlServiceUrl(String sparqlServiceUrl) {
        this.sparqlServiceUrl = sparqlServiceUrl;
    }

    String getOntologyIri() {
        return ontologyIri;
    }

    void setOntologyIri(String ontologyIri) {
        this.ontologyIri = ontologyIri;
    }

    String getQuery() {
        return query;
    }

    void setQuery(String query) {
        this.query = query;
    }

    String getVariable() {
        return variable;
    }

    void setVariable(String variable) {
        this.variable = variable;
    }

    boolean isInValueFrame() {
        return inValueFrame;
    }

    void setInValueFrame(boolean inValueFrame) {
        this.inValueFrame = inValueFrame;
    }
}